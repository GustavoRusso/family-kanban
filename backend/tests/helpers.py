from __future__ import annotations

from fastapi.testclient import TestClient


def request_code(client: TestClient, email: str) -> dict:
    response = client.post("/api/v1/auth/code", json={"email": email})
    assert response.status_code == 200, response.text
    body = response.json()
    assert "devCode" in body
    return body


def sign_in(client: TestClient, email: str = "maya@example.com") -> dict:
    code_body = request_code(client, email)
    response = client.post(
        "/api/v1/auth/verify",
        json={"email": email, "code": code_body["devCode"]},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "accessToken" in body
    assert "user" in body
    assert "activeFamilyId" in body
    return body


def auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}
