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


def create_family(client: TestClient, headers: dict[str, str], name: str = "Rivera") -> dict:
    response = client.post("/api/v1/families", json={"name": name}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def two_member_family(client: TestClient) -> tuple[dict, dict, dict]:
    """Maya (admin) creates a family; Leo joins as member. Returns (maya_auth, leo_auth, family)."""
    maya = sign_in(client, "maya@example.com")
    family = create_family(client, auth_header(maya["accessToken"]))
    join_token = family["joinToken"]
    client.post("/api/v1/auth/sign-out", headers=auth_header(maya["accessToken"]))

    leo = sign_in(client, "leo@example.com")
    joined = client.post(
        "/api/v1/families/join",
        json={"token": join_token},
        headers=auth_header(leo["accessToken"]),
    )
    assert joined.status_code == 200, joined.text

    # Refresh Maya's session so both callers have valid tokens.
    client.post("/api/v1/auth/sign-out", headers=auth_header(leo["accessToken"]))
    maya = sign_in(client, "maya@example.com")
    leo = sign_in(client, "leo@example.com")
    return maya, leo, family
