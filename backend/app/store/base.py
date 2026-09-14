"""Store protocol — implementations filled as features land."""

from __future__ import annotations

from typing import Protocol

from app.models.auth import Session, User


class Store(Protocol):
    """Persistence boundary for the API (in-memory now, SQL later)."""

    def get_user_by_email(self, email: str) -> User | None: ...

    def create_user(self, *, email: str, name: str) -> User: ...

    def set_code(self, email: str, code: str) -> None: ...

    def get_code(self, email: str) -> str | None: ...

    def pop_code(self, email: str) -> str | None: ...

    def first_family_id(self, user_id: str) -> str | None: ...

    def create_session(
        self, user: User, *, active_family_id: str | None
    ) -> tuple[str, Session]: ...

    def get_session(self, access_token: str) -> Session | None: ...

    def delete_session(self, access_token: str) -> bool: ...
