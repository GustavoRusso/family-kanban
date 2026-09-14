from __future__ import annotations

from fastapi import APIRouter

from app.auth.deps import RequireSessionDep, StoreDep
from app.errors import AppError
from app.models.points import HistoryItem

router = APIRouter()


def _require_member(store, family_id: str, user_id: str) -> None:
    if store.get_family(family_id) is None:
        raise AppError("Family not found.", status_code=404)
    if store.get_member(family_id, user_id) is None:
        raise AppError("You are not a member of this family.", status_code=403)


@router.get("/families/{family_id}/history", response_model=list[HistoryItem])
def list_history(
    family_id: str,
    store: StoreDep,
    auth: RequireSessionDep,
) -> list[HistoryItem]:
    session, _token = auth
    _require_member(store, family_id, session.user.id)
    return store.list_history(family_id)
