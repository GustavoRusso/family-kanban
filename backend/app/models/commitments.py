"""Commitment-related OpenAPI schemas."""

from __future__ import annotations

from datetime import datetime

from enum import Enum

from pydantic import BaseModel


class CommitmentType(str, Enum):
    promise = "promise"
    request = "request"
    responsibility = "responsibility"
    consequence = "consequence"
    reward = "reward"


class BoardStatus(str, Enum):
    backlog = "backlog"
    ready = "ready"
    doing = "doing"
    done = "done"
    confirmed = "confirmed"


class Status(str, Enum):
    backlog = "backlog"
    ready = "ready"
    doing = "doing"
    done = "done"
    confirmed = "confirmed"
    archived = "archived"
    cancelled = "cancelled"


class HistoryEventKind(str, Enum):
    created = "created"
    updated = "updated"
    moved = "moved"
    confirmed = "confirmed"
    unconfirmed = "unconfirmed"
    cancelled = "cancelled"
    restored = "restored"
    archived = "archived"


class HistoryEvent(BaseModel):
    id: str
    at: datetime
    byUserId: str
    kind: HistoryEventKind
    detail: str


class Commitment(BaseModel):
    id: str
    familyId: str
    title: str
    type: CommitmentType
    responsibleId: str
    points: int
    status: Status
    startedOnce: bool
    createdAt: datetime
    history: list[HistoryEvent]
    startDate: datetime | None = None
    dueDate: datetime | None = None
    note: str | None = None
    confirmedAt: datetime | None = None
    confirmedById: str | None = None
    archivedAt: datetime | None = None
    cancelledAt: datetime | None = None


class CommitmentInput(BaseModel):
    title: str
    type: CommitmentType
    responsibleId: str
    points: int
    startDate: datetime | None = None
    dueDate: datetime | None = None
    note: str | None = None


class CommitmentPatch(BaseModel):
    title: str | None = None
    type: CommitmentType | None = None
    responsibleId: str | None = None
    points: int | None = None
    startDate: datetime | None = None
    dueDate: datetime | None = None
    note: str | None = None


class MoveCommitmentRequest(BaseModel):
    to: BoardStatus
