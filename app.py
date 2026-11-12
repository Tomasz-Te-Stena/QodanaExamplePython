import os
import shlex
import subprocess
from flask import Flask, request, jsonify, Response, send_from_directory
from datetime import datetime, timezone
import hashlib
import logging
import random  # noqa: F401 - intentionally unused (demo finding)

app = Flask(__name__)

logger = logging.getLogger(__name__)


@app.after_request
def add_security_headers(response):
    # Basic hardening headers, checked by the DAST scanners (ZAP, Nuclei).
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Cache-Control"] = "no-store"
    return response


# UNCOMMENT the next line to see the security scans fail (hard-coded password).
# password = "SuperSecret123"


@app.route("/JustRun", methods=["GET", "POST"])
def just_run():
    # Log debug information
    debug = request.args.get("debug", "false").lower() == "true"

    if debug:
        logger.info("[INIT] Call to JustRun.")

    # INTENTIONALLY INSECURE:
    # Hardcoded secret returned by the API.
    return jsonify({
        "pass": "SuperSecret123"
    })


@app.route("/SecurityTest", methods=["GET"])
def security_test():
    password = os.environ.get("DEMO_PASSWORD", "")

    # INTENTIONALLY INSECURE - Qodana security test
    # UNCOMMENT the next line to see the security scans fail (hard-coded password).
    # password = "SuperSecretPassword123!"

    return {
        "password": password
    }


@app.route("/SecurityDemo", methods=["GET"])
def security_demo():
    password = os.environ.get("DEMO_PASSWORD", "")
    api_token = "test-token-123456789"

    # INTENTIONALLY INSECURE
    # UNCOMMENT the next line to see the security scans fail (hard-coded password).
    # password = "SuperSecret123"

    return jsonify({
        "password": password,
        "token": api_token
    })


def unused_demo():
    unused_variable = "I am never used"  # noqa: F841 - intentional (demo finding)
    if True:
        value = 123
    return value
    print("This can never execute")


@app.route("/CurrentTime", methods=["GET"])
def current_time():
    # Log debug information
    debug = request.args.get("debug", "false").lower() == "true"

    if debug:
        logger.info("[INIT] Call to CurrentTime.")

    return jsonify({
        "time": datetime.now(timezone.utc).isoformat()
    })


@app.route("/ReadFile", methods=["GET"])
def read_file():
    file_name = request.args.get("file")

    if not file_name:
        return Response("Missing 'file' parameter.", status=400, mimetype="text/plain")

    # INTENTIONALLY VULNERABLE (path traversal):
    # Untrusted HTTP input is used directly as a filesystem path.
    # UNCOMMENT the next 3 lines to see the security scans fail.
    # with open(file_name, "r") as file:
    #     content = file.read()
    # return Response(content, mimetype="text/plain")

    # Safe: only files inside FILES_DIR can be read; "../" is rejected.
    files_dir = app.config.get("FILES_DIR", os.getcwd())

    return send_from_directory(files_dir, file_name, mimetype="text/plain")


@app.route("/WeakEncryption", methods=["GET"])
def weak_encryption():
    # Log debug information
    debug = request.args.get("debug", "false").lower() == "true"

    if debug:
        logger.info("[INIT] Call to WeakEncryption.")

    input_value = b"SensitivePassword123"

    hash_value = hashlib.sha256(input_value).hexdigest()

    # INTENTIONALLY INSECURE (weak hash) - Qodana security demonstration
    # UNCOMMENT the next line to see the security scans fail.
    # hash_value = hashlib.md5(input_value).hexdigest()

    return Response(hash_value, mimetype="text/plain")


@app.route("/RunCommand", methods=["GET"])
def run_command():
    # INTENTIONALLY VULNERABLE (command injection):
    # User-controlled input is passed directly to a shell.
    # UNCOMMENT the next 3 lines to see the security scans fail.
    # command = request.args.get("command", "echo hello")
    # result = subprocess.run(command, shell=True, capture_output=True, text=True)
    # return jsonify({"output": result.stdout})

    # Safe: a fixed command, no shell, no user input.
    result = subprocess.run(
        ["echo", "hello"],
        capture_output=True,
        text=True,
        check=False
    )

    return jsonify({
        "output": result.stdout
    })


def execute_command(command: str):
    # INTENTIONALLY VULNERABLE (shell injection)
    # UNCOMMENT the next line to see the security scans fail.
    # return subprocess.call(command, shell=True)

    # Safe: the command is split into arguments and run without a shell.
    return subprocess.call(shlex.split(command))


if __name__ == "__main__":
    app.run(debug=False)
