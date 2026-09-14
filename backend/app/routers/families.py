from __future__ import annotations

from fastapi import APIRouter, Response

from app.auth.deps import RequireSessionDep, StoreDep
from app.errors import AppError
from app.models.auth import Session
from app.models.families import (
    CreateFamilyRequest,
    Family,
    JoinFamilyRequest,
    Member,
    RenameFamilyRequest,
    Role,
)

router = APIRouter(prefix="/families")


def _require_family(store, family_id: str) -> Family:
    family = store.get_family(family_id)
    if family is None:
        raise AppError("Family not found.", status_code=404)
    return family


def _require_membership(store, family_id: str, user_id: str) -> Member:
    _require_family(store, family_id)
    member = store.get_member(family_id, user_id)
    if member is None:
        raise AppError("You are not a member of this family.", status_code=403)
    return member


def _require_admin(store, family_id: str, user_id: str) -> Member:
    member = _require_membership(store, family_id, user_id)
    if member.role != Role.admin:
        raise AppError("Only an admin can do that.", status_code=403)
    return member


@router.get("", response_model=list[Family])
def list_mine(store: StoreDep, auth: RequireSessionDep) -> list[Family]:
    session, _token = auth
    return store.list_families_for_user(session.user.id)


@router.post("", response_model=Family, status_code=201)
def create_family(
    body: CreateFamilyRequest,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Family:
    session, token = auth
    name = body.name.strip()
    if not name:
        raise AppError("Give your family a name.")
    family = store.create_family(name=name, admin=session.user)
    store.set_active_family(token, family.id)
    return family


@router.post("/join", response_model=Family)
def join_by_token(
    body: JoinFamilyRequest,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Family:
    session, token = auth
    family = store.find_family_by_join_token(body.token)
    if family is None:
        raise AppError("We couldn't find a family for that code.")
    store.add_member(family, session.user, role=Role.member)
    store.set_active_family(token, family.id)
    return family


@router.get("/{family_id}", response_model=Family)
def get_family(family_id: str, store: StoreDep, auth: RequireSessionDep) -> Family:
    session, _token = auth
    _require_membership(store, family_id, session.user.id)
    family = store.get_family(family_id)
    assert family is not None
    return family


@router.patch("/{family_id}", response_model=Family)
def rename_family(
    family_id: str,
    body: RenameFamilyRequest,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Family:
    session, _token = auth
    _require_admin(store, family_id, session.user.id)
    name = body.name.strip()
    if not name:
        raise AppError("Give your family a name.")
    return store.rename_family(family_id, name)


@router.post("/{family_id}/activate", response_model=Session)
def activate_family(
    family_id: str,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Session:
    session, token = auth
    _require_membership(store, family_id, session.user.id)
    return store.set_active_family(token, family_id)


@router.get("/{family_id}/members", response_model=list[Member])
def list_members(
    family_id: str,
    store: StoreDep,
    auth: RequireSessionDep,
) -> list[Member]:
    session, _token = auth
    _require_membership(store, family_id, session.user.id)
    return store.list_members(family_id)


@router.delete("/{family_id}/members/{user_id}", status_code=204, response_class=Response)
def remove_member(
    family_id: str,
    user_id: str,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Response:
    session, _token = auth
    _require_admin(store, family_id, session.user.id)
    if not store.remove_member(family_id, user_id):
        raise AppError("Member not found.", status_code=404)
    return Response(status_code=204)
