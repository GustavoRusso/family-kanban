from __future__ import annotations

from fastapi.testclient import TestClient

from tests.helpers import auth_header, sign_in


def test_list_families_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/families")
    assert response.status_code == 401
    assert "message" in response.json()


def test_create_family_makes_caller_admin_and_sets_active(client: TestClient) -> None:
    auth = sign_in(client, "maya@example.com")
    headers = auth_header(auth["accessToken"])

    response = client.post("/api/v1/families", json={"name": "Rivera"}, headers=headers)
    assert response.status_code == 201, response.text
    family = response.json()
    assert family["id"]
    assert family["name"] == "Rivera"
    assert family["joinToken"]
    assert family["joinToken"] == family["joinToken"].upper()

    session = client.get("/api/v1/auth/session", headers=headers)
    assert session.status_code == 200
    assert session.json()["activeFamilyId"] == family["id"]

    members = client.get(f"/api/v1/families/{family['id']}/members", headers=headers)
    assert members.status_code == 200
    body = members.json()
    assert len(body) == 1
    assert body[0]["role"] == "admin"
    assert body[0]["userId"] == auth["user"]["id"]
    assert body[0]["email"] == "maya@example.com"


def test_create_family_rejects_blank_name(client: TestClient) -> None:
    auth = sign_in(client)
    response = client.post(
        "/api/v1/families",
        json={"name": "   "},
        headers=auth_header(auth["accessToken"]),
    )
    assert response.status_code == 400
    assert "message" in response.json()


def test_join_by_token_case_insensitive(client: TestClient) -> None:
    maya = sign_in(client, "maya@example.com")
    create = client.post(
        "/api/v1/families",
        json={"name": "Rivera"},
        headers=auth_header(maya["accessToken"]),
    )
    family = create.json()
    client.post("/api/v1/auth/sign-out", headers=auth_header(maya["accessToken"]))

    leo = sign_in(client, "leo@example.com")
    joined = client.post(
        "/api/v1/families/join",
        json={"token": family["joinToken"].lower()},
        headers=auth_header(leo["accessToken"]),
    )
    assert joined.status_code == 200, joined.text
    assert joined.json()["id"] == family["id"]

    session = client.get(
        "/api/v1/auth/session",
        headers=auth_header(leo["accessToken"]),
    )
    assert session.json()["activeFamilyId"] == family["id"]

    members = client.get(
        f"/api/v1/families/{family['id']}/members",
        headers=auth_header(leo["accessToken"]),
    )
    assert members.status_code == 200
    roles = {m["email"]: m["role"] for m in members.json()}
    assert roles["maya@example.com"] == "admin"
    assert roles["leo@example.com"] == "member"


def test_join_unknown_token_returns_400(client: TestClient) -> None:
    auth = sign_in(client)
    response = client.post(
        "/api/v1/families/join",
        json={"token": "NOPE"},
        headers=auth_header(auth["accessToken"]),
    )
    assert response.status_code == 400
    assert "message" in response.json()


def test_list_mine_returns_only_memberships(client: TestClient) -> None:
    maya = sign_in(client, "maya@example.com")
    a = client.post(
        "/api/v1/families",
        json={"name": "A"},
        headers=auth_header(maya["accessToken"]),
    ).json()
    client.post(
        "/api/v1/families",
        json={"name": "B"},
        headers=auth_header(maya["accessToken"]),
    )
    client.post("/api/v1/auth/sign-out", headers=auth_header(maya["accessToken"]))

    leo = sign_in(client, "leo@example.com")
    client.post(
        "/api/v1/families/join",
        json={"token": a["joinToken"]},
        headers=auth_header(leo["accessToken"]),
    )
    mine = client.get("/api/v1/families", headers=auth_header(leo["accessToken"]))
    assert mine.status_code == 200
    names = [f["name"] for f in mine.json()]
    assert names == ["A"]


def test_get_family_forbids_non_member(client: TestClient) -> None:
    maya = sign_in(client, "maya@example.com")
    family = client.post(
        "/api/v1/families",
        json={"name": "Rivera"},
        headers=auth_header(maya["accessToken"]),
    ).json()
    client.post("/api/v1/auth/sign-out", headers=auth_header(maya["accessToken"]))

    leo = sign_in(client, "leo@example.com")
    response = client.get(
        f"/api/v1/families/{family['id']}",
        headers=auth_header(leo["accessToken"]),
    )
    assert response.status_code == 403
    assert "message" in response.json()


def test_get_family_not_found(client: TestClient) -> None:
    auth = sign_in(client)
    response = client.get(
        "/api/v1/families/missing",
        headers=auth_header(auth["accessToken"]),
    )
    assert response.status_code == 404
    assert "message" in response.json()


def test_rename_family_admin_only(client: TestClient) -> None:
    maya = sign_in(client, "maya@example.com")
    family = client.post(
        "/api/v1/families",
        json={"name": "Rivera"},
        headers=auth_header(maya["accessToken"]),
    ).json()
    client.post("/api/v1/auth/sign-out", headers=auth_header(maya["accessToken"]))

    leo = sign_in(client, "leo@example.com")
    client.post(
        "/api/v1/families/join",
        json={"token": family["joinToken"]},
        headers=auth_header(leo["accessToken"]),
    )
    forbidden = client.patch(
        f"/api/v1/families/{family['id']}",
        json={"name": "Nope"},
        headers=auth_header(leo["accessToken"]),
    )
    assert forbidden.status_code == 403

    client.post("/api/v1/auth/sign-out", headers=auth_header(leo["accessToken"]))
    maya2 = sign_in(client, "maya@example.com")
    ok = client.patch(
        f"/api/v1/families/{family['id']}",
        json={"name": "Rivera Clan"},
        headers=auth_header(maya2["accessToken"]),
    )
    assert ok.status_code == 200
    assert ok.json()["name"] == "Rivera Clan"


def test_activate_family(client: TestClient) -> None:
    maya = sign_in(client, "maya@example.com")
    headers = auth_header(maya["accessToken"])
    first = client.post("/api/v1/families", json={"name": "One"}, headers=headers).json()
    second = client.post("/api/v1/families", json={"name": "Two"}, headers=headers).json()

    activated = client.post(
        f"/api/v1/families/{first['id']}/activate",
        headers=headers,
    )
    assert activated.status_code == 200
    body = activated.json()
    assert body["activeFamilyId"] == first["id"]
    assert body["user"]["id"] == maya["user"]["id"]
    assert second["id"] != first["id"]


def test_remove_member_admin_only(client: TestClient) -> None:
    maya = sign_in(client, "maya@example.com")
    family = client.post(
        "/api/v1/families",
        json={"name": "Rivera"},
        headers=auth_header(maya["accessToken"]),
    ).json()
    client.post("/api/v1/auth/sign-out", headers=auth_header(maya["accessToken"]))

    leo = sign_in(client, "leo@example.com")
    client.post(
        "/api/v1/families/join",
        json={"token": family["joinToken"]},
        headers=auth_header(leo["accessToken"]),
    )
    leo_id = leo["user"]["id"]

    forbidden = client.delete(
        f"/api/v1/families/{family['id']}/members/{maya['user']['id']}",
        headers=auth_header(leo["accessToken"]),
    )
    assert forbidden.status_code == 403

    client.post("/api/v1/auth/sign-out", headers=auth_header(leo["accessToken"]))
    maya2 = sign_in(client, "maya@example.com")
    removed = client.delete(
        f"/api/v1/families/{family['id']}/members/{leo_id}",
        headers=auth_header(maya2["accessToken"]),
    )
    assert removed.status_code == 204

    members = client.get(
        f"/api/v1/families/{family['id']}/members",
        headers=auth_header(maya2["accessToken"]),
    )
    assert len(members.json()) == 1
    assert members.json()[0]["email"] == "maya@example.com"
