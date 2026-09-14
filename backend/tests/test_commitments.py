from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from tests.helpers import auth_header, sign_in, two_member_family


@pytest.fixture
def family_ctx(client: TestClient):
    maya, leo, family = two_member_family(client)
    return {
        "client": client,
        "maya": maya,
        "leo": leo,
        "family_id": family["id"],
        "maya_headers": auth_header(maya["accessToken"]),
        "leo_headers": auth_header(leo["accessToken"]),
    }


def _create_card(
    ctx: dict,
    *,
    responsible_id: str | None = None,
    points: int = 3,
    headers: dict[str, str] | None = None,
    title: str = "Fix the back door",
):
    client: TestClient = ctx["client"]
    body = {
        "title": title,
        "type": "promise",
        "responsibleId": responsible_id or ctx["leo"]["user"]["id"],
        "points": points,
    }
    return client.post(
        f"/api/v1/families/{ctx['family_id']}/commitments",
        json=body,
        headers=headers or ctx["leo_headers"],
    )


def _move(ctx: dict, commitment_id: str, to: str, headers: dict[str, str]):
    return ctx["client"].post(
        f"/api/v1/commitments/{commitment_id}/move",
        json={"to": to},
        headers=headers,
    )


def test_create_commitment_in_backlog(family_ctx: dict) -> None:
    response = _create_card(family_ctx)
    assert response.status_code == 201, response.text
    card = response.json()
    assert card["status"] == "backlog"
    assert card["familyId"] == family_ctx["family_id"]
    assert card["points"] == 3
    assert card["startedOnce"] is False
    assert card["history"][0]["kind"] == "created"
    assert card["createdAt"]


def test_create_refuses_points_below_one(family_ctx: dict) -> None:
    response = _create_card(family_ctx, points=0)
    assert response.status_code == 400
    assert "message" in response.json()


def test_list_commitments(family_ctx: dict) -> None:
    created = _create_card(family_ctx).json()
    response = family_ctx["client"].get(
        f"/api/v1/families/{family_ctx['family_id']}/commitments",
        headers=family_ctx["leo_headers"],
    )
    assert response.status_code == 200
    ids = [c["id"] for c in response.json()]
    assert created["id"] in ids


def test_update_allowed_in_backlog_locked_in_doing(family_ctx: dict) -> None:
    card = _create_card(family_ctx).json()
    updated = family_ctx["client"].patch(
        f"/api/v1/commitments/{card['id']}",
        json={"points": 5, "title": "Fix the door properly"},
        headers=family_ctx["leo_headers"],
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["points"] == 5
    assert updated.json()["title"] == "Fix the door properly"

    assert _move(family_ctx, card["id"], "ready", family_ctx["leo_headers"]).status_code == 200
    assert _move(family_ctx, card["id"], "doing", family_ctx["leo_headers"]).status_code == 200

    locked = family_ctx["client"].patch(
        f"/api/v1/commitments/{card['id']}",
        json={"points": 9},
        headers=family_ctx["leo_headers"],
    )
    assert locked.status_code == 400
    assert "message" in locked.json()


def test_move_backlog_to_ready_only_responsible(family_ctx: dict) -> None:
    card = _create_card(
        family_ctx,
        responsible_id=family_ctx["maya"]["user"]["id"],
        headers=family_ctx["leo_headers"],
    ).json()
    blocked = _move(family_ctx, card["id"], "ready", family_ctx["leo_headers"])
    assert blocked.status_code == 400

    # Re-auth as Maya (same store; need her token again after Leo session)
    family_ctx["client"].post(
        "/api/v1/auth/sign-out",
        headers=family_ctx["leo_headers"],
    )
    maya = sign_in(family_ctx["client"], "maya@example.com")
    ok = _move(family_ctx, card["id"], "ready", auth_header(maya["accessToken"]))
    assert ok.status_code == 200
    assert ok.json()["status"] == "ready"


def test_full_flow_confirm_by_other_member(family_ctx: dict) -> None:
    card = _create_card(family_ctx).json()
    cid = card["id"]
    assert _move(family_ctx, cid, "ready", family_ctx["leo_headers"]).status_code == 200
    assert _move(family_ctx, cid, "doing", family_ctx["leo_headers"]).status_code == 200
    doing = _move(family_ctx, cid, "done", family_ctx["leo_headers"])
    assert doing.status_code == 200
    assert doing.json()["startedOnce"] is True

    self_confirm = family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/confirm",
        headers=family_ctx["leo_headers"],
    )
    assert self_confirm.status_code == 400

    family_ctx["client"].post("/api/v1/auth/sign-out", headers=family_ctx["leo_headers"])
    maya = sign_in(family_ctx["client"], "maya@example.com")
    confirmed = family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/confirm",
        headers=auth_header(maya["accessToken"]),
    )
    assert confirmed.status_code == 200, confirmed.text
    body = confirmed.json()
    assert body["status"] == "confirmed"
    assert body["confirmedById"] == maya["user"]["id"]
    assert body["confirmedAt"]


def test_unconfirm_returns_to_doing(family_ctx: dict) -> None:
    card = _create_card(family_ctx).json()
    cid = card["id"]
    for to in ("ready", "doing", "done"):
        assert _move(family_ctx, cid, to, family_ctx["leo_headers"]).status_code == 200

    family_ctx["client"].post("/api/v1/auth/sign-out", headers=family_ctx["leo_headers"])
    maya = sign_in(family_ctx["client"], "maya@example.com")
    maya_headers = auth_header(maya["accessToken"])
    assert family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/confirm",
        headers=maya_headers,
    ).status_code == 200

    unconfirmed = family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/unconfirm",
        headers=maya_headers,
    )
    assert unconfirmed.status_code == 200
    body = unconfirmed.json()
    assert body["status"] == "doing"
    assert body["confirmedAt"] is None
    assert body["confirmedById"] is None


def test_cancel_restore_preserves_points_and_history(family_ctx: dict) -> None:
    card = _create_card(family_ctx).json()
    cid = card["id"]
    assert _move(family_ctx, cid, "ready", family_ctx["leo_headers"]).status_code == 200

    cancelled = family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/cancel",
        headers=family_ctx["leo_headers"],
    )
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["cancelledAt"]

    restored = family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/restore",
        headers=family_ctx["leo_headers"],
    )
    assert restored.status_code == 200
    body = restored.json()
    assert body["status"] == "backlog"
    assert body["points"] == 3
    assert "cancelled" in [h["kind"] for h in body["history"]]
    assert "restored" in [h["kind"] for h in body["history"]]


def test_cancel_clears_confirmation(family_ctx: dict) -> None:
    card = _create_card(family_ctx).json()
    cid = card["id"]
    for to in ("ready", "doing", "done"):
        assert _move(family_ctx, cid, to, family_ctx["leo_headers"]).status_code == 200

    family_ctx["client"].post("/api/v1/auth/sign-out", headers=family_ctx["leo_headers"])
    maya = sign_in(family_ctx["client"], "maya@example.com")
    assert family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/confirm",
        headers=auth_header(maya["accessToken"]),
    ).status_code == 200

    family_ctx["client"].post("/api/v1/auth/sign-out", headers=auth_header(maya["accessToken"]))
    leo = sign_in(family_ctx["client"], "leo@example.com")
    cancelled = family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/cancel",
        headers=auth_header(leo["accessToken"]),
    )
    assert cancelled.status_code == 200
    body = cancelled.json()
    assert body["status"] == "cancelled"
    assert body["confirmedAt"] is None
    assert body["confirmedById"] is None


def test_archive_only_after_confirm_by_responsible(family_ctx: dict) -> None:
    card = _create_card(family_ctx).json()
    cid = card["id"]
    for to in ("ready", "doing", "done"):
        assert _move(family_ctx, cid, to, family_ctx["leo_headers"]).status_code == 200

    too_early = family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/archive",
        headers=family_ctx["leo_headers"],
    )
    assert too_early.status_code == 400

    family_ctx["client"].post("/api/v1/auth/sign-out", headers=family_ctx["leo_headers"])
    maya = sign_in(family_ctx["client"], "maya@example.com")
    maya_headers = auth_header(maya["accessToken"])
    assert family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/confirm",
        headers=maya_headers,
    ).status_code == 200

    not_responsible = family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/archive",
        headers=maya_headers,
    )
    assert not_responsible.status_code == 400

    family_ctx["client"].post("/api/v1/auth/sign-out", headers=maya_headers)
    leo = sign_in(family_ctx["client"], "leo@example.com")
    archived = family_ctx["client"].post(
        f"/api/v1/commitments/{cid}/archive",
        headers=auth_header(leo["accessToken"]),
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    assert archived.json()["archivedAt"]


def test_commitment_not_found(family_ctx: dict) -> None:
    response = family_ctx["client"].post(
        "/api/v1/commitments/missing/move",
        json={"to": "ready"},
        headers=family_ctx["leo_headers"],
    )
    assert response.status_code == 404
    assert "message" in response.json()
