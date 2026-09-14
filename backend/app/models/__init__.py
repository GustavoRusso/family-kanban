"""Pydantic models matching OpenAPI components."""

from app.models.auth import (
    AuthSuccess,
    RequestCodeRequest,
    RequestCodeResponse,
    Session,
    User,
    VerifyCodeRequest,
)
from app.models.commitments import (
    BoardStatus,
    Commitment,
    CommitmentInput,
    CommitmentPatch,
    CommitmentType,
    HistoryEvent,
    HistoryEventKind,
    MoveCommitmentRequest,
    Status,
)
from app.models.common import ErrorBody
from app.models.points import HistoryItem, PointsEntry, PointsTotal
from app.models.families import (
    CreateFamilyRequest,
    Family,
    JoinFamilyRequest,
    Member,
    RenameFamilyRequest,
    Role,
)

__all__ = [
    "AuthSuccess",
    "BoardStatus",
    "Commitment",
    "CommitmentInput",
    "CommitmentPatch",
    "CommitmentType",
    "CreateFamilyRequest",
    "ErrorBody",
    "Family",
    "HistoryEvent",
    "HistoryEventKind",
    "HistoryItem",
    "JoinFamilyRequest",
    "Member",
    "MoveCommitmentRequest",
    "PointsEntry",
    "PointsTotal",
    "RenameFamilyRequest",
    "RequestCodeRequest",
    "RequestCodeResponse",
    "Role",
    "Session",
    "Status",
    "User",
    "VerifyCodeRequest",
]
