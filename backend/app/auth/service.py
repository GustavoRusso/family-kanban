"""Passwordless email + one-time code auth."""

from __future__ import annotations

import random
import re
from datetime import datetime, timedelta, timezone

from app.config import get_login_code_ttl_minutes
from app.email.sender import EmailSender
from app.errors import AppError
from app.models.auth import AuthSuccess, RequestCodeResponse, Session
from app.store.base import Store

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def request_code(
    store: Store, email_sender: EmailSender, email: str
) -> RequestCodeResponse:
    normalized = normalize_email(email)
    if not _EMAIL_RE.match(normalized):
        raise AppError("Enter a valid email address.")
    code = str(random.randint(100000, 999999))
    ttl_minutes = get_login_code_ttl_minutes()
    expires_at = _utcnow() + timedelta(minutes=ttl_minutes)
    store.set_code(normalized, code, expires_at=expires_at)
    email_sender.send_login_code(normalized, code, ttl_minutes=ttl_minutes)
    return RequestCodeResponse()


def verify_code(store: Store, email: str, code: str) -> AuthSuccess:
    normalized = normalize_email(email)
    stored = store.get_code(normalized)
    if stored is None or stored[0] != code.strip():
        raise AppError("That code doesn't match. Try again.")
    _stored_code, expires_at = stored
    if expires_at <= _utcnow():
        store.pop_code(normalized)
        raise AppError("That code has expired. Request a new one.")
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


def current_session(store: Store, access_token: str | None) -> Session | None:
    if not access_token:
        return None
    return store.get_session(access_token)


def sign_out(store: Store, access_token: str) -> None:
    if not store.delete_session(access_token):
        raise AppError("You need to sign in first.", status_code=401)
