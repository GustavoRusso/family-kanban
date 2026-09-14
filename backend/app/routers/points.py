from __future__ import annotations

from fastapi import APIRouter

from app.auth.deps import RequireSessionDep, StoreDep
from app.errors import AppError
from app.models.points import PointsEntry, PointsTotal

router = APIRouter()


def _require_member(store, family_id: str, user_id: str) -> None:
    if store.get_family(family_id) is None:
        raise AppError("Family not found.", status_code=404)
    if store.get_member(family_id, user_id) is None:
        raise AppError("You are not a member of this family.", status_code=403)


@router.get("/families/{family_id}/points/totals", response_model=list[PointsTotal])
def points_totals(
    family_id: str,
    store: StoreDep,
    auth: RequireSessionDep,
) -> list[PointsTotal]:
    session, _token = auth
    _require_member(store, family_id, session.user.id)
    return store.points_totals(family_id)


@router.get("/families/{family_id}/points/ledger", response_model=list[PointsEntry])
def points_ledger(
    family_id: str,
    store: StoreDep,
    auth: RequireSessionDep,
) -> list[PointsEntry]:
    session, _token = auth
    _require_member(store, family_id, session.user.id)
    return store.points_ledger(family_id)
