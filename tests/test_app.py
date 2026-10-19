"""
Test Suite: test_app.py
Unit and integration tests for TaskSecure REST API.
"""

import pytest
from app import create_app
from auth import hash_password, verify_password, generate_auth_token, verify_auth_token
from security_utils import sanitize_input, is_valid_username


@pytest.fixture
def client():
    app = create_app(test_config={"TESTING": True})
    with app.test_client() as client:
        yield client


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"
    assert "TaskSecure API" in data["service"]


def test_security_headers_present(client):
    response = client.get("/api/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "default-src 'self'" in response.headers.get("Content-Security-Policy", "")


def test_input_sanitization():
    raw_input = "<script>alert('xss')</script> Hello!"
    sanitized = sanitize_input(raw_input)
    assert "&lt;script&gt;" in sanitized
    assert "<script>" not in sanitized


def test_username_validation():
    assert is_valid_username("admin_user") is True
    assert is_valid_username("a") is False
    assert is_valid_username("admin; DROP TABLE users;--") is False


def test_password_hashing():
    raw_pwd = "SuperSecretPassword123!"
    hashed = hash_password(raw_pwd)
    assert verify_password(hashed, raw_pwd) is True
    assert verify_password(hashed, "WrongPassword") is False


def test_token_generation_and_verification():
    secret = "test-secret-key-12345"
    token = generate_auth_token("john_doe", secret)
    verified_user = verify_auth_token(token, secret)
    assert verified_user == "john_doe"
    assert verify_auth_token(token, "wrong-secret") is None


def test_user_registration_and_login(client):
    reg_payload = {"username": "testuser", "password": "Password123!"}
    reg_res = client.post("/api/register", json=reg_payload)
    assert reg_res.status_code == 201

    login_res = client.post("/api/login", json=reg_payload)
    assert login_res.status_code == 200
    assert "token" in login_res.get_json()


def test_task_creation_and_retrieval(client):
    task_payload = {"title": "Implement SAST", "description": "Configure Bandit in CI/CD pipeline"}
    res = client.post("/api/tasks", json=task_payload)
    assert res.status_code == 201
    task_id = res.get_json()["task_id"]

    get_res = client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.get_json()["task"]["title"] == "Implement SAST"
