from __future__ import annotations

from fastapi.testclient import TestClient

from tests.helpers import auth_header, request_code, sign_in


def test_request_code_returns_dev_code(client: TestClient) -> None:
    body = request_code(client, "maya@example.com")
    assert body["devCode"]
    assert isinstance(body["devCode"], str)


def test_request_code_rejects_invalid_email(client: TestClient) -> None:
    response = client.post("/api/v1/auth/code", json={"email": "not-an-email"})
    assert response.status_code == 400
    assert "message" in response.json()


def test_verify_auto_creates_account_and_normalizes_email(client: TestClient) -> None:
    body = sign_in(client, "Maya@Example.com ")
    assert body["user"]["email"] == "maya@example.com"
    assert body["activeFamilyId"] is None
    assert body["user"]["id"]
    assert body["user"]["name"]
    assert body["accessToken"]


def test_verify_rejects_wrong_code(client: TestClient) -> None:
    request_code(client, "leo@example.com")
    response = client.post(
        "/api/v1/auth/verify",
        json={"email": "leo@example.com", "code": "000000"},
    )
    assert response.status_code == 400
    assert "message" in response.json()


def test_same_email_returns_same_user_id(client: TestClient) -> None:
    first = sign_in(client, "maya@example.com")
    sign_out = client.post(
        "/api/v1/auth/sign-out",
        headers=auth_header(first["accessToken"]),
    )
    assert sign_out.status_code == 204

    second = sign_in(client, "maya@example.com")
    assert second["user"]["id"] == first["user"]["id"]
    assert second["accessToken"] != first["accessToken"]


def test_session_without_token_returns_null(client: TestClient) -> None:
    response = client.get("/api/v1/auth/session")
    assert response.status_code == 200
    assert response.json() is None


def test_session_with_valid_token_returns_session(client: TestClient) -> None:
    auth = sign_in(client, "maya@example.com")
    response = client.get(
        "/api/v1/auth/session",
        headers=auth_header(auth["accessToken"]),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["id"] == auth["user"]["id"]
    assert body["user"]["email"] == "maya@example.com"
    assert body["activeFamilyId"] is None
    assert "accessToken" not in body


def test_session_with_invalid_token_returns_null(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/session",
        headers=auth_header("not-a-real-token"),
    )
    assert response.status_code == 200
    assert response.json() is None


def test_sign_out_requires_auth(client: TestClient) -> None:
    response = client.post("/api/v1/auth/sign-out")
    assert response.status_code == 401
    assert "message" in response.json()


def test_sign_out_clears_session(client: TestClient) -> None:
    auth = sign_in(client, "maya@example.com")
    headers = auth_header(auth["accessToken"])

    response = client.post("/api/v1/auth/sign-out", headers=headers)
    assert response.status_code == 204

    session = client.get("/api/v1/auth/session", headers=headers)
    assert session.status_code == 200
    assert session.json() is None
