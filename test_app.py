import hashlib

import pytest

from app import app, execute_command, unused_demo


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_just_run(client):
    response = client.get("/JustRun")

    assert response.status_code == 200
    assert response.get_json() == {
        "pass": "SuperSecret123"
    }


def test_just_run_post(client):
    response = client.post("/JustRun")

    assert response.status_code == 200
    assert response.get_json() == {
        "pass": "SuperSecret123"
    }


def test_current_time(client):
    response = client.get("/CurrentTime")

    assert response.status_code == 200

    data = response.get_json()

    assert "time" in data
    assert data["time"] is not None


def test_weak_encryption(client):
    response = client.get("/WeakEncryption")

    assert response.status_code == 200

    expected_hash = hashlib.sha256(
        b"SensitivePassword123"
    ).hexdigest()

    assert response.get_data(as_text=True) == expected_hash


def test_read_file(client, tmp_path):
    # Arrange
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello from test file")

    app.config["FILES_DIR"] = str(tmp_path)

    # Act
    response = client.get(
        "/ReadFile",
        query_string={"file": "test.txt"}
    )

    # Assert
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Hello from test file"


# The two tests below cover plain (undecorated) functions.
# Mutmut skips decorated functions such as Flask routes, so without these
# it finds no test for any mutant and stops early.
def test_unused_demo():
    assert unused_demo() == 123


def test_execute_command(monkeypatch):
    calls = []

    def fake_call(*args, **kwargs):
        calls.append((args, kwargs))
        return 0

    monkeypatch.setattr("subprocess.call", fake_call)

    execute_command("echo hello")

    assert calls == [((["echo", "hello"],), {})]


def test_read_file_rejects_path_traversal(client, tmp_path):
    app.config["FILES_DIR"] = str(tmp_path)

    response = client.get(
        "/ReadFile",
        query_string={"file": "../secret.txt"}
    )

    assert response.status_code == 404


def test_read_file_requires_file_parameter(client):
    response = client.get("/ReadFile")

    assert response.status_code == 400


def test_run_command(client):
    response = client.get("/RunCommand")

    assert response.status_code == 200
    assert response.get_json()["output"].strip() == "hello"
