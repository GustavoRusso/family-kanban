"""Passwordless email + one-time code auth."""

from __future__ import annotations

import random
import re

from app.errors import AppError
from app.models.auth import AuthSuccess, RequestCodeResponse, Session
from app.store.memory import InMemoryStore

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def request_code(store: InMemoryStore, email: str) -> RequestCodeResponse:
    normalized = normalize_email(email)
    if not _EMAIL_RE.match(normalized):
        raise AppError("Enter a valid email address.")
    code = str(random.randint(100000, 999999))
    store.set_code(normalized, code)
    return RequestCodeResponse(devCode=code)


def verify_code(store: InMemoryStore, email: str, code: str) -> AuthSuccess:
    normalized = normalize_email(email)
    expected = store.get_code(normalized)
    if expected is None or expected != code.strip():
        raise AppError("That code doesn't match. Try again.")
    store.pop_code(normalized)

    user = store.get_user_by_email(normalized)
    if user is None:
        local = normalized.split("@", 1)[0] or normalized
        user = store.create_user(email=normalized, name=local)

    active_family_id = store.first_family_id(user.id)
    access_token, session = store.create_session(
        user, active_family_id=active_family_id
    )
    return AuthSuccess(
        user=session.user,
        activeFamilyId=session.activeFamilyId,
        accessToken=access_token,
    )


def current_session(store: InMemoryStore, access_token: str | None) -> Session | None:
    if not access_token:
        return None
    return store.get_session(access_token)


def sign_out(store: InMemoryStore, access_token: str) -> None:
    if not store.delete_session(access_token):
        raise AppError("You need to sign in first.", status_code=401)
