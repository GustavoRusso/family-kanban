"""FastAPI dependencies for auth and store access."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_session
from app.errors import AppError
from app.models.auth import Session as ApiSession
from app.store.sqlalchemy_store import SqlAlchemyStore

_bearer = HTTPBearer(auto_error=False)


def get_store(session: Annotated[Session, Depends(get_session)]) -> SqlAlchemyStore:
    return SqlAlchemyStore(session)


StoreDep = Annotated[SqlAlchemyStore, Depends(get_store)]


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
) -> ApiSession | None:
    token = _token(credentials)
    if not token:
        return None
    return store.get_session(token)


async def require_session(
    store: StoreDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer)
    ] = None,
) -> tuple[ApiSession, str]:
    token = _token(credentials)
    if not token:
        raise AppError("You need to sign in first.", status_code=401)
    session = store.get_session(token)
    if session is None:
        raise AppError("You need to sign in first.", status_code=401)
    return session, token


OptionalSessionDep = Annotated[ApiSession | None, Depends(optional_session)]
RequireSessionDep = Annotated[tuple[ApiSession, str], Depends(require_session)]
