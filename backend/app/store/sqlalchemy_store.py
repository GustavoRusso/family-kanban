"""SQLAlchemy-backed store (works with any dialect DATABASE_URL supports)."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.auth import Session as ApiSession
from app.models.auth import User
from app.models.commitments import (
    Commitment,
    CommitmentInput,
    CommitmentType,
    HistoryEvent,
    HistoryEventKind,
    Status,
)
from app.models.families import Family, Member, Role
from app.models.points import (
    HistoryItem,
    HistoryOutcomeStatus,
    PointsEntry,
    PointsTotal,
)
from app.orm import (
    CommitmentRow,
    FamilyRow,
    HistoryEventRow,
    LoginCodeRow,
    MemberRow,
    SessionRow,
    UserRow,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class SqlAlchemyStore:
    """Persistence via a request-scoped SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def new_id(self, prefix: str) -> str:
        return f"{prefix}-{secrets.token_hex(4)}"

    def new_access_token(self) -> str:
        return secrets.token_urlsafe(32)

    def new_join_token(self) -> str:
        return secrets.token_hex(3).upper()

    def get_user(self, user_id: str) -> User | None:
        row = self._session.get(UserRow, user_id)
        return None if row is None else User(id=row.id, email=row.email, name=row.name)

    def get_user_by_email(self, email: str) -> User | None:
        row = self._session.scalar(select(UserRow).where(UserRow.email == email))
        return None if row is None else User(id=row.id, email=row.email, name=row.name)

    def create_user(self, *, email: str, name: str) -> User:
        row = UserRow(id=self.new_id("u"), email=email, name=name)
        self._session.add(row)
        self._session.flush()
        return User(id=row.id, email=row.email, name=row.name)

    def set_code(self, email: str, code: str) -> None:
        row = self._session.get(LoginCodeRow, email)
        if row is None:
            self._session.add(LoginCodeRow(email=email, code=code))
        else:
            row.code = code
        self._session.flush()

    def get_code(self, email: str) -> str | None:
        row = self._session.get(LoginCodeRow, email)
        return None if row is None else row.code

    def pop_code(self, email: str) -> str | None:
        row = self._session.get(LoginCodeRow, email)
        if row is None:
            return None
        code = row.code
        self._session.delete(row)
        self._session.flush()
        return code

    def first_family_id(self, user_id: str) -> str | None:
        row = self._session.scalar(
            select(MemberRow).where(MemberRow.user_id == user_id).limit(1)
        )
        return None if row is None else row.family_id

    def create_session(
        self, user: User, *, active_family_id: str | None
    ) -> tuple[str, ApiSession]:
        token = self.new_access_token()
        self._session.add(
            SessionRow(
                access_token=token,
                user_id=user.id,
                active_family_id=active_family_id,
            )
        )
        self._session.flush()
        return token, ApiSession(user=user, activeFamilyId=active_family_id)

    def get_session(self, access_token: str) -> ApiSession | None:
        row = self._session.get(SessionRow, access_token)
        if row is None:
            return None
        user = self.get_user(row.user_id)
        if user is None:
            return None
        return ApiSession(user=user, activeFamilyId=row.active_family_id)

    def delete_session(self, access_token: str) -> bool:
        row = self._session.get(SessionRow, access_token)
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def set_active_family(self, access_token: str, family_id: str | None) -> ApiSession:
        row = self._session.get(SessionRow, access_token)
        assert row is not None
        row.active_family_id = family_id
        self._session.flush()
        session = self.get_session(access_token)
        assert session is not None
        return session

    def get_family(self, family_id: str) -> Family | None:
        row = self._session.get(FamilyRow, family_id)
        return None if row is None else self._family_from_row(row)

    def find_family_by_join_token(self, token: str) -> Family | None:
        needle = token.strip().upper()
        row = self._session.scalar(
            select(FamilyRow).where(FamilyRow.join_token == needle)
        )
        return None if row is None else self._family_from_row(row)

    def list_families_for_user(self, user_id: str) -> list[Family]:
        rows = self._session.scalars(
            select(FamilyRow)
            .join(MemberRow, MemberRow.family_id == FamilyRow.id)
            .where(MemberRow.user_id == user_id)
        ).all()
        return [self._family_from_row(row) for row in rows]

    def get_member(self, family_id: str, user_id: str) -> Member | None:
        row = self._session.get(MemberRow, (user_id, family_id))
        return None if row is None else self._member_from_row(row)

    def list_members(self, family_id: str) -> list[Member]:
        rows = self._session.scalars(
            select(MemberRow).where(MemberRow.family_id == family_id)
        ).all()
        return [self._member_from_row(row) for row in rows]

    def create_family(self, *, name: str, admin: User) -> Family:
        family = Family(
            id=self.new_id("fam"),
            name=name,
            joinToken=self.new_join_token(),
        )
        self._session.add(
            FamilyRow(id=family.id, name=family.name, join_token=family.joinToken)
        )
        self._session.add(
            MemberRow(
                user_id=admin.id,
                family_id=family.id,
                name=admin.name,
                email=admin.email,
                role=Role.admin.value,
            )
        )
        self._session.flush()
        return family

    def add_member(
        self, family: Family, user: User, *, role: Role = Role.member
    ) -> Member:
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
        self._session.add(
            MemberRow(
                user_id=member.userId,
                family_id=member.familyId,
                name=member.name,
                email=member.email,
                role=member.role.value,
            )
        )
        self._session.flush()
        return member

    def rename_family(self, family_id: str, name: str) -> Family:
        row = self._session.get(FamilyRow, family_id)
        assert row is not None
        row.name = name
        self._session.flush()
        return self._family_from_row(row)

    def remove_member(self, family_id: str, user_id: str) -> bool:
        row = self._session.get(MemberRow, (user_id, family_id))
        if row is None:
            return False
        self._session.delete(row)
        self._session.flush()
        return True

    def get_commitment(self, commitment_id: str) -> Commitment | None:
        row = self._session.scalar(
            select(CommitmentRow)
            .where(CommitmentRow.id == commitment_id)
            .options(selectinload(CommitmentRow.history_events))
        )
        return None if row is None else self._commitment_from_row(row)

    def list_commitments(self, family_id: str) -> list[Commitment]:
        rows = self._session.scalars(
            select(CommitmentRow)
            .where(CommitmentRow.family_id == family_id)
            .options(selectinload(CommitmentRow.history_events))
        ).all()
        return [self._commitment_from_row(row) for row in rows]

    def append_history(
        self,
        commitment: Commitment,
        *,
        kind: HistoryEventKind,
        detail: str,
        by_user_id: str,
    ) -> None:
        event = HistoryEvent(
            id=self.new_id("h"),
            at=_utcnow(),
            byUserId=by_user_id,
            kind=kind,
            detail=detail,
        )
        commitment.history.append(event)
        self._persist_commitment(commitment, new_event=event)

    def create_commitment(
        self,
        family_id: str,
        input_data: CommitmentInput,
        *,
        by_user_id: str,
    ) -> Commitment:
        commitment = Commitment(
            id=self.new_id("c"),
            familyId=family_id,
            title=input_data.title.strip(),
            type=input_data.type,
            responsibleId=input_data.responsibleId,
            points=input_data.points,
            startDate=input_data.startDate,
            dueDate=input_data.dueDate,
            note=input_data.note,
            status=Status.backlog,
            startedOnce=False,
            createdAt=_utcnow(),
            confirmedAt=None,
            confirmedById=None,
            archivedAt=None,
            cancelledAt=None,
            history=[],
        )
        self.append_history(
            commitment,
            kind=HistoryEventKind.created,
            detail="Created in Backlog",
            by_user_id=by_user_id,
        )
        return commitment

    def points_totals(self, family_id: str) -> list[PointsTotal]:
        members = self.list_members(family_id)
        commitments = self._session.scalars(
            select(CommitmentRow).where(CommitmentRow.family_id == family_id)
        ).all()
        totals: list[PointsTotal] = []
        for member in members:
            total = sum(
                c.points
                for c in commitments
                if c.responsible_id == member.userId
                and c.status in (Status.confirmed.value, Status.archived.value)
            )
            totals.append(
                PointsTotal(userId=member.userId, name=member.name, total=total)
            )
        return totals

    def points_ledger(self, family_id: str) -> list[PointsEntry]:
        rows = self._session.scalars(
            select(CommitmentRow)
            .where(CommitmentRow.family_id == family_id)
            .options(selectinload(CommitmentRow.history_events))
        ).all()
        entries: list[PointsEntry] = []
        for row in rows:
            if row.status not in (Status.confirmed.value, Status.archived.value):
                continue
            confirmed_at = _ensure_utc(row.confirmed_at)
            if confirmed_at is None:
                for event in row.history_events:
                    if event.kind == HistoryEventKind.confirmed.value:
                        confirmed_at = _ensure_utc(event.at)
                        break
            if confirmed_at is None:
                confirmed_at = _ensure_utc(row.created_at) or _utcnow()
            entries.append(
                PointsEntry(
                    commitmentId=row.id,
                    userId=row.responsible_id,
                    title=row.title,
                    points=row.points,
                    confirmedAt=confirmed_at,
                )
            )
        entries.sort(key=lambda e: e.confirmedAt, reverse=True)
        return entries

    def list_history(self, family_id: str) -> list[HistoryItem]:
        rows = self._session.scalars(
            select(CommitmentRow).where(CommitmentRow.family_id == family_id)
        ).all()
        items: list[HistoryItem] = []
        for row in rows:
            if row.status not in (
                Status.archived.value,
                Status.cancelled.value,
                Status.confirmed.value,
            ):
                continue
            member = self.get_member(family_id, row.responsible_id)
            outcome = (
                _ensure_utc(row.archived_at)
                or _ensure_utc(row.cancelled_at)
                or _ensure_utc(row.confirmed_at)
                or _ensure_utc(row.created_at)
                or _utcnow()
            )
            items.append(
                HistoryItem(
                    commitmentId=row.id,
                    title=row.title,
                    type=CommitmentType(row.type),
                    responsibleId=row.responsible_id,
                    responsibleName=member.name if member else "Unknown",
                    status=HistoryOutcomeStatus(row.status),
                    outcomeDate=outcome,
                    points=row.points,
                )
            )
        items.sort(key=lambda i: i.outcomeDate, reverse=True)
        return items

    def _persist_commitment(
        self, commitment: Commitment, *, new_event: HistoryEvent | None = None
    ) -> None:
        row = self._session.get(CommitmentRow, commitment.id)
        if row is None:
            row = CommitmentRow(id=commitment.id, family_id=commitment.familyId)
            self._session.add(row)

        row.family_id = commitment.familyId
        row.title = commitment.title
        row.type = commitment.type.value
        row.responsible_id = commitment.responsibleId
        row.points = commitment.points
        row.status = commitment.status.value
        row.started_once = commitment.startedOnce
        row.created_at = commitment.createdAt
        row.start_date = commitment.startDate
        row.due_date = commitment.dueDate
        row.note = commitment.note
        row.confirmed_at = commitment.confirmedAt
        row.confirmed_by_id = commitment.confirmedById
        row.archived_at = commitment.archivedAt
        row.cancelled_at = commitment.cancelledAt

        if new_event is not None:
            self._session.add(
                HistoryEventRow(
                    id=new_event.id,
                    commitment_id=commitment.id,
                    at=new_event.at,
                    by_user_id=new_event.byUserId,
                    kind=new_event.kind.value,
                    detail=new_event.detail,
                )
            )
        self._session.flush()

    @staticmethod
    def _family_from_row(row: FamilyRow) -> Family:
        return Family(id=row.id, name=row.name, joinToken=row.join_token)

    @staticmethod
    def _member_from_row(row: MemberRow) -> Member:
        return Member(
            userId=row.user_id,
            familyId=row.family_id,
            name=row.name,
            email=row.email,
            role=Role(row.role),
        )

    @staticmethod
    def _commitment_from_row(row: CommitmentRow) -> Commitment:
        history = [
            HistoryEvent(
                id=event.id,
                at=_ensure_utc(event.at) or _utcnow(),
                byUserId=event.by_user_id,
                kind=HistoryEventKind(event.kind),
                detail=event.detail,
            )
            for event in row.history_events
        ]
        return Commitment(
            id=row.id,
            familyId=row.family_id,
            title=row.title,
            type=CommitmentType(row.type),
            responsibleId=row.responsible_id,
            points=row.points,
            status=Status(row.status),
            startedOnce=row.started_once,
            createdAt=_ensure_utc(row.created_at) or _utcnow(),
            history=history,
            startDate=_ensure_utc(row.start_date),
            dueDate=_ensure_utc(row.due_date),
            note=row.note,
            confirmedAt=_ensure_utc(row.confirmed_at),
            confirmedById=row.confirmed_by_id,
            archivedAt=_ensure_utc(row.archived_at),
            cancelledAt=_ensure_utc(row.cancelled_at),
        )
