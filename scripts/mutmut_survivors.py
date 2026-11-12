"""Print every mutant that was not killed, with the exact source line it changed.

Run after ``mutmut run`` from the repository root:

    python scripts/mutmut_survivors.py

For each mutant that is not "killed" it prints:

    app.py:62  survived  app.x_unused_demo__mutmut_1
        - original line
        + mutated line

A surviving mutant means: this line can be changed as shown and no test
notices. The fix is a test that fails for the mutated line.
"""

import ast
import re
import subprocess
import sys
from pathlib import Path

RESULT_LINE = re.compile(r"^\s*(?P<name>\S+): (?P<status>.+?)\s*$")
HUNK_HEADER = re.compile(r"^@@ -(?P<start>\d+)(?:,\d+)? \+\d+(?:,\d+)? @@")
MUTANT_NAME = re.compile(r"^x(?:ǁ(?P<cls>[^ǁ]+)ǁ|_)(?P<func>.+)__mutmut_\d+$")


def parse_results(text):
    """Return [(mutant name, status)] from the output of ``mutmut results``."""
    mutants = []
    for line in text.splitlines():
        match = RESULT_LINE.match(line)
        if match and "__mutmut_" in match["name"]:
            mutants.append((match["name"], match["status"]))
    return mutants


def parse_show(text):
    """Return (source path, [(line in function, original, mutated)]) from ``mutmut show``."""
    path = None
    changes = []
    position = None      # current line of the original function, 1-based
    removed = []

    def flush():
        while removed:
            changes.append((*removed.pop(0), None))

    for line in text.splitlines():
        if line.startswith("--- "):
            path = line[4:].strip()
        elif line.startswith("+++ "):
            continue
        elif (header := HUNK_HEADER.match(line)):
            flush()
            position = int(header["start"])
        elif position is None:
            continue
        elif line.startswith("-"):
            removed.append((position, line[1:]))
            position += 1
        elif line.startswith("+"):
            if removed:
                at, original = removed.pop(0)
                changes.append((at, original, line[1:]))
            else:
                changes.append((position, None, line[1:]))
        else:
            flush()
            position += 1

    flush()
    return path, changes


def function_range(source, mutant_name):
    """Return (first line, last line) of the function a mutant belongs to, or None."""
    match = MUTANT_NAME.match(mutant_name.rsplit(".", 1)[-1])
    if not match:
        return None

    scope = ast.parse(source)
    if match["cls"]:
        classes = [n for n in ast.walk(scope) if isinstance(n, ast.ClassDef) and n.name == match["cls"]]
        if not classes:
            return None
        scope = classes[0]

    for node in ast.walk(scope):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == match["func"]:
            return node.lineno, node.end_lineno

    return None


def source_line(lines, func_range, line_in_function, original):
    """Map a line inside the function to a line number of the source file."""
    if func_range is None:
        return None

    first, last = func_range
    expected = first + line_in_function - 1

    if original is None:
        return expected
    if 1 <= expected <= len(lines) and lines[expected - 1] == original:
        return expected

    # The diff did not start exactly at the "def" line: find the text instead.
    for number in range(first, min(last, len(lines)) + 1):
        if lines[number - 1] == original:
            return number

    return expected


def describe(mutant_name, status, show_text):
    """Return the report lines for one mutant."""
    path, changes = parse_show(show_text)
    report = []

    if not path or not changes:
        return [f"{mutant_name}  {status}  (no diff available)"]

    source_path = Path(path)
    if not source_path.exists() and source_path.parts[:1] == ("mutants",):
        source_path = Path(*source_path.parts[1:])

    source = source_path.read_text(encoding="utf-8") if source_path.exists() else ""
    lines = source.splitlines()
    func_range = function_range(source, mutant_name) if source else None

    first_change = True
    for line_in_function, original, mutated in changes:
        number = source_line(lines, func_range, line_in_function, original)
        location = f"{source_path.as_posix()}:{number}" if number else source_path.as_posix()

        if first_change:
            report.append(f"{location}  {status}  {mutant_name}")
            first_change = False
        else:
            report.append(f"{location}")

        if original is not None:
            report.append(f"    - {original.strip()}")
        if mutated is not None:
            report.append(f"    + {mutated.strip()}")

    return report


def run_mutmut(*args):
    completed = subprocess.run(
        [sys.executable, "-m", "mutmut", *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout


def main():
    mutants = [(name, status) for name, status in parse_results(run_mutmut("results")) if status != "killed"]

    if not mutants:
        print("No surviving mutants.")
        return 0

    print(f"{len(mutants)} mutant(s) were not killed. Each entry shows the line and the change no test noticed:")
    print()

    for name, status in mutants:
        for line in describe(name, status, run_mutmut("show", name)):
            print(line)
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
