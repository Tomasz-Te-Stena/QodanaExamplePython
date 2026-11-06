import hashlib

import pytest

from app import app


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

    expected_hash = hashlib.md5(
        b"SensitivePassword123"
    ).hexdigest()

    assert response.get_data(as_text=True) == expected_hash


def test_read_file(client, tmp_path):
    # Arrange
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello from test file")

    # Act
    response = client.get(
        "/ReadFile",
        query_string={"file": str(test_file)}
    )

    # Assert
    assert response.status_code == 200
    assert response.get_data(as_text=True) == "Hello from test file"