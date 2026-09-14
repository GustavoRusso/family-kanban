from __future__ import annotations

from fastapi.testclient import TestClient

from tests.helpers import auth_header, sign_in, two_member_family


def _flow_to_confirmed(client: TestClient, family_id: str, leo: dict, maya: dict, *, title: str, points: int = 3) -> dict:
    leo_headers = auth_header(leo["accessToken"])
    created = client.post(
        f"/api/v1/families/{family_id}/commitments",
        json={
            "title": title,
            "type": "promise",
            "responsibleId": leo["user"]["id"],
            "points": points,
        },
        headers=leo_headers,
    )
    assert created.status_code == 201, created.text
    cid = created.json()["id"]
    for to in ("ready", "doing", "done"):
        assert client.post(
            f"/api/v1/commitments/{cid}/move",
            json={"to": to},
            headers=leo_headers,
        ).status_code == 200

    client.post("/api/v1/auth/sign-out", headers=leo_headers)
    maya_auth = sign_in(client, "maya@example.com")
    confirmed = client.post(
        f"/api/v1/commitments/{cid}/confirm",
        headers=auth_header(maya_auth["accessToken"]),
    )
    assert confirmed.status_code == 200, confirmed.text
    client.post("/api/v1/auth/sign-out", headers=auth_header(maya_auth["accessToken"]))
    leo_auth = sign_in(client, "leo@example.com")
    return confirmed.json(), leo_auth, maya_auth


def test_points_totals_after_confirm(client: TestClient) -> None:
    maya, leo, family = two_member_family(client)
    _flow_to_confirmed(client, family["id"], leo, maya, title="Fix the door", points=3)

    leo = sign_in(client, "leo@example.com")
    response = client.get(
        f"/api/v1/families/{family['id']}/points/totals",
        headers=auth_header(leo["accessToken"]),
    )
    assert response.status_code == 200, response.text
    totals = {t["userId"]: t for t in response.json()}
    assert totals[leo["user"]["id"]]["total"] == 3
    assert totals[leo["user"]["id"]]["name"]
    assert totals[maya["user"]["id"]]["total"] == 0


def test_points_totals_zero_after_unconfirm(client: TestClient) -> None:
    maya, leo, family = two_member_family(client)
    card, leo, _maya = _flow_to_confirmed(
        client, family["id"], leo, maya, title="Fix the door", points=3
    )

    maya = sign_in(client, "maya@example.com")
    unconfirmed = client.post(
        f"/api/v1/commitments/{card['id']}/unconfirm",
        headers=auth_header(maya["accessToken"]),
    )
    assert unconfirmed.status_code == 200

    response = client.get(
        f"/api/v1/families/{family['id']}/points/totals",
        headers=auth_header(maya["accessToken"]),
    )
    assert response.status_code == 200
    totals = {t["userId"]: t["total"] for t in response.json()}
    assert totals[leo["user"]["id"]] == 0


def test_points_totals_kept_after_archive(client: TestClient) -> None:
    maya, leo, family = two_member_family(client)
    card, leo, _maya = _flow_to_confirmed(
        client, family["id"], leo, maya, title="Fix the door", points=3
    )

    archived = client.post(
        f"/api/v1/commitments/{card['id']}/archive",
        headers=auth_header(leo["accessToken"]),
    )
    assert archived.status_code == 200

    response = client.get(
        f"/api/v1/families/{family['id']}/points/totals",
        headers=auth_header(leo["accessToken"]),
    )
    assert response.status_code == 200
    totals = {t["userId"]: t["total"] for t in response.json()}
    assert totals[leo["user"]["id"]] == 3


def test_points_ledger_newest_first(client: TestClient) -> None:
    maya, leo, family = two_member_family(client)
    for title in ("A", "B"):
        _flow_to_confirmed(client, family["id"], leo, maya, title=title, points=1)
        leo = sign_in(client, "leo@example.com")
        maya = sign_in(client, "maya@example.com")

    leo = sign_in(client, "leo@example.com")
    response = client.get(
        f"/api/v1/families/{family['id']}/points/ledger",
        headers=auth_header(leo["accessToken"]),
    )
    assert response.status_code == 200, response.text
    ledger = response.json()
    assert len(ledger) == 2
    assert ledger[0]["confirmedAt"] >= ledger[1]["confirmedAt"]
    assert {e["title"] for e in ledger} == {"A", "B"}


def test_history_includes_confirmed_archived_cancelled(client: TestClient) -> None:
    maya, leo, family = two_member_family(client)
    family_id = family["id"]

    confirmed, leo, _ = _flow_to_confirmed(
        client, family_id, leo, maya, title="Confirmed one", points=2
    )

    # Cancel another card from ready
    leo_headers = auth_header(leo["accessToken"])
    created = client.post(
        f"/api/v1/families/{family_id}/commitments",
        json={
            "title": "Cancelled one",
            "type": "request",
            "responsibleId": leo["user"]["id"],
            "points": 1,
        },
        headers=leo_headers,
    ).json()
    client.post(
        f"/api/v1/commitments/{created['id']}/move",
        json={"to": "ready"},
        headers=leo_headers,
    )
    cancelled = client.post(
        f"/api/v1/commitments/{created['id']}/cancel",
        headers=leo_headers,
    )
    assert cancelled.status_code == 200

    # Archive the confirmed one
    archived = client.post(
        f"/api/v1/commitments/{confirmed['id']}/archive",
        headers=leo_headers,
    )
    assert archived.status_code == 200

    response = client.get(
        f"/api/v1/families/{family_id}/history",
        headers=leo_headers,
    )
    assert response.status_code == 200, response.text
    items = response.json()
    statuses = {i["commitmentId"]: i["status"] for i in items}
    assert statuses[confirmed["id"]] == "archived"
    assert statuses[created["id"]] == "cancelled"
    assert all("responsibleName" in i for i in items)
    assert all("outcomeDate" in i for i in items)
    # Newest outcome first
    assert items[0]["outcomeDate"] >= items[-1]["outcomeDate"]


def test_points_requires_membership(client: TestClient) -> None:
    maya, _leo, family = two_member_family(client)
    client.post("/api/v1/auth/sign-out", headers=auth_header(maya["accessToken"]))
    outsider = sign_in(client, "nina@example.com")
    response = client.get(
        f"/api/v1/families/{family['id']}/points/totals",
        headers=auth_header(outsider["accessToken"]),
    )
    assert response.status_code == 403
    assert "message" in response.json()
