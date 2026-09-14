"""In-memory mock database."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from app.models.auth import Session, User


@dataclass
class StoredSession:
    user_id: str
    active_family_id: str | None


class InMemoryStore:
    """Process-local store. Tests inject a fresh instance per case."""

    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.users_by_email: dict[str, str] = {}
        self.codes: dict[str, str] = {}
        self.sessions: dict[str, StoredSession] = {}
        # memberships filled in families step; used for activeFamilyId on verify
        self.memberships: list[tuple[str, str]] = []  # (user_id, family_id)

    def new_id(self, prefix: str) -> str:
        return f"{prefix}-{secrets.token_hex(4)}"

    def new_access_token(self) -> str:
        return secrets.token_urlsafe(32)

    def get_user(self, user_id: str) -> User | None:
        return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        user_id = self.users_by_email.get(email)
        if user_id is None:
            return None
        return self.users.get(user_id)

    def create_user(self, *, email: str, name: str) -> User:
        user = User(id=self.new_id("u"), email=email, name=name)
        self.users[user.id] = user
        self.users_by_email[email] = user.id
        return user

    def set_code(self, email: str, code: str) -> None:
        self.codes[email] = code

    def pop_code(self, email: str) -> str | None:
        return self.codes.pop(email, None)

    def get_code(self, email: str) -> str | None:
        return self.codes.get(email)

    def first_family_id(self, user_id: str) -> str | None:
        for uid, family_id in self.memberships:
            if uid == user_id:
                return family_id
        return None

    def create_session(self, user: User, *, active_family_id: str | None) -> tuple[str, Session]:
        token = self.new_access_token()
        self.sessions[token] = StoredSession(
            user_id=user.id,
            active_family_id=active_family_id,
        )
        return token, Session(user=user, activeFamilyId=active_family_id)

    def get_session(self, access_token: str) -> Session | None:
        stored = self.sessions.get(access_token)
        if stored is None:
            return None
        user = self.users.get(stored.user_id)
        if user is None:
            return None
        return Session(user=user, activeFamilyId=stored.active_family_id)

    def delete_session(self, access_token: str) -> bool:
        return self.sessions.pop(access_token, None) is not None
