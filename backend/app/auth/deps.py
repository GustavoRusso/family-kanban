"""FastAPI dependencies for auth and store access."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.errors import AppError
from app.models.auth import Session
from app.store.memory import InMemoryStore

_bearer = HTTPBearer(auto_error=False)
_default_store = InMemoryStore()


def get_store() -> InMemoryStore:
    return _default_store


StoreDep = Annotated[InMemoryStore, Depends(get_store)]


def _token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    return credentials.credentials


async def optional_session(
    store: StoreDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ] = None,
) -> Session | None:
    token = _token(credentials)
    if not token:
        return None
    return store.get_session(token)


async def require_session(
    store: StoreDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ] = None,
) -> tuple[Session, str]:
    token = _token(credentials)
    if not token:
        raise AppError("You need to sign in first.", status_code=401)
    session = store.get_session(token)
    if session is None:
        raise AppError("You need to sign in first.", status_code=401)
    return session, token


OptionalSessionDep = Annotated[Session | None, Depends(optional_session)]
RequireSessionDep = Annotated[tuple[Session, str], Depends(require_session)]
