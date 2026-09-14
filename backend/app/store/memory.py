"""In-memory mock database."""

from __future__ import annotations

import secrets
from dataclasses import dataclass

from app.models.auth import Session, User
from app.models.families import Family, Member, Role


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
        self.families: dict[str, Family] = {}
        self.members: list[Member] = []

    def new_id(self, prefix: str) -> str:
        return f"{prefix}-{secrets.token_hex(4)}"

    def new_access_token(self) -> str:
        return secrets.token_urlsafe(32)

    def new_join_token(self) -> str:
        return secrets.token_hex(3).upper()

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
        for member in self.members:
            if member.userId == user_id:
                return member.familyId
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

    def set_active_family(self, access_token: str, family_id: str | None) -> Session:
        stored = self.sessions[access_token]
        stored.active_family_id = family_id
        session = self.get_session(access_token)
        assert session is not None
        return session

    def get_family(self, family_id: str) -> Family | None:
        return self.families.get(family_id)

    def find_family_by_join_token(self, token: str) -> Family | None:
        needle = token.strip().upper()
        for family in self.families.values():
            if family.joinToken.upper() == needle:
                return family
        return None

    def list_families_for_user(self, user_id: str) -> list[Family]:
        family_ids = {m.familyId for m in self.members if m.userId == user_id}
        return [self.families[fid] for fid in family_ids if fid in self.families]

    def get_member(self, family_id: str, user_id: str) -> Member | None:
        for member in self.members:
            if member.familyId == family_id and member.userId == user_id:
                return member
        return None

    def list_members(self, family_id: str) -> list[Member]:
        return [m for m in self.members if m.familyId == family_id]

    def create_family(self, *, name: str, admin: User) -> Family:
        family = Family(
            id=self.new_id("fam"),
            name=name,
            joinToken=self.new_join_token(),
        )
        self.families[family.id] = family
        self.members.append(
            Member(
                userId=admin.id,
                familyId=family.id,
                name=admin.name,
                email=admin.email,
                role=Role.admin,
            )
        )
        return family

    def add_member(self, family: Family, user: User, *, role: Role = Role.member) -> Member:
        existing = self.get_member(family.id, user.id)
        if existing is not None:
            return existing
        member = Member(
            userId=user.id,
            familyId=family.id,
            name=user.name,
            email=user.email,
            role=role,
        )
        self.members.append(member)
        return member

    def rename_family(self, family_id: str, name: str) -> Family:
        family = self.families[family_id]
        updated = family.model_copy(update={"name": name})
        self.families[family_id] = updated
        return updated

    def remove_member(self, family_id: str, user_id: str) -> bool:
        before = len(self.members)
        self.members = [
            m
            for m in self.members
            if not (m.familyId == family_id and m.userId == user_id)
        ]
        return len(self.members) < before
