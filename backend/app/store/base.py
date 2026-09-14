"""Persistence protocol — implemented by the SQLAlchemy store."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.models.auth import Session, User
from app.models.commitments import (
    Commitment,
    CommitmentInput,
    HistoryEventKind,
)
from app.models.families import Family, Member, Role
from app.models.points import HistoryItem, PointsEntry, PointsTotal


class Store(Protocol):
    """Database-backed persistence boundary for the API."""

    def get_user(self, user_id: str) -> User | None: ...

    def get_user_by_email(self, email: str) -> User | None: ...

    def create_user(self, *, email: str, name: str) -> User: ...

    def set_code(self, email: str, code: str, *, expires_at: datetime) -> None: ...

    def get_code(self, email: str) -> tuple[str, datetime] | None: ...

    def pop_code(self, email: str) -> str | None: ...

    def first_family_id(self, user_id: str) -> str | None: ...

    def create_session(
        self, user: User, *, active_family_id: str | None
    ) -> tuple[str, Session]: ...

    def get_session(self, access_token: str) -> Session | None: ...

    def delete_session(self, access_token: str) -> bool: ...

    def set_active_family(self, access_token: str, family_id: str | None) -> Session: ...

    def get_family(self, family_id: str) -> Family | None: ...

    def find_family_by_join_token(self, token: str) -> Family | None: ...

    def list_families_for_user(self, user_id: str) -> list[Family]: ...

    def get_member(self, family_id: str, user_id: str) -> Member | None: ...

    def list_members(self, family_id: str) -> list[Member]: ...

    def create_family(self, *, name: str, admin: User) -> Family: ...

    def add_member(
        self, family: Family, user: User, *, role: Role = Role.member
    ) -> Member: ...

    def rename_family(self, family_id: str, name: str) -> Family: ...

    def remove_member(self, family_id: str, user_id: str) -> bool: ...

    def get_commitment(self, commitment_id: str) -> Commitment | None: ...

    def list_commitments(self, family_id: str) -> list[Commitment]: ...

    def append_history(
        self,
        commitment: Commitment,
        *,
        kind: HistoryEventKind,
        detail: str,
        by_user_id: str,
    ) -> None: ...

    def create_commitment(
        self,
        family_id: str,
        input_data: CommitmentInput,
        *,
        by_user_id: str,
    ) -> Commitment: ...

    def points_totals(self, family_id: str) -> list[PointsTotal]: ...

    def points_ledger(self, family_id: str) -> list[PointsEntry]: ...

    def list_history(self, family_id: str) -> list[HistoryItem]: ...
