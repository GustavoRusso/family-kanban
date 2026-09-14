"""Points and history OpenAPI schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.commitments import CommitmentType


class HistoryOutcomeStatus(str, Enum):
    archived = "archived"
    cancelled = "cancelled"
    confirmed = "confirmed"


class PointsTotal(BaseModel):
    userId: str
    name: str
    total: int = Field(ge=0)


class PointsEntry(BaseModel):
    commitmentId: str
    userId: str
    title: str
    points: int = Field(ge=1)
    confirmedAt: datetime


class HistoryItem(BaseModel):
    commitmentId: str
    title: str
    type: CommitmentType
    responsibleId: str
    responsibleName: str
    status: HistoryOutcomeStatus
    outcomeDate: datetime
    points: int = Field(ge=1)
