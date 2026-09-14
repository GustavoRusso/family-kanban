from datetime import datetime, timezone

from fastapi import APIRouter

from app.auth.deps import RequireSessionDep, StoreDep
from app.errors import AppError
from app.models.commitments import (
    BoardStatus,
    Commitment,
    CommitmentPatch,
    HistoryEventKind,
    MoveCommitmentRequest,
    Status,
)
from app.rules import (
    can_archive,
    can_cancel,
    can_confirm,
    can_edit,
    can_move,
    can_restore,
    can_unconfirm,
    check,
    validate_input,
)

router = APIRouter(prefix="/commitments")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _require_commitment(store, commitment_id: str) -> Commitment:
    commitment = store.get_commitment(commitment_id)
    if commitment is None:
        raise AppError("Commitment not found.", status_code=404)
    return commitment


def _require_commitment_member(store, commitment: Commitment, user_id: str) -> None:
    if store.get_family(commitment.familyId) is None:
        raise AppError("Family not found.", status_code=404)
    if store.get_member(commitment.familyId, user_id) is None:
        raise AppError("You are not a member of this family.", status_code=403)


def _apply_move(
    store,
    commitment: Commitment,
    to: BoardStatus,
    user_id: str,
) -> Commitment:
    check(can_move(commitment, to, user_id))
    if to == BoardStatus.confirmed:
        commitment.confirmedAt = _utcnow()
        commitment.confirmedById = user_id
        store.append_history(
            commitment,
            kind=HistoryEventKind.confirmed,
            detail="Confirmed — points awarded",
            by_user_id=user_id,
        )
    elif commitment.status == Status.confirmed and to == BoardStatus.doing:
        commitment.confirmedAt = None
        commitment.confirmedById = None
        store.append_history(
            commitment,
            kind=HistoryEventKind.unconfirmed,
            detail="Un-confirmed — points returned",
            by_user_id=user_id,
        )
    else:
        store.append_history(
            commitment,
            kind=HistoryEventKind.moved,
            detail=f"Moved {commitment.status.value} → {to.value}",
            by_user_id=user_id,
        )
    if to == BoardStatus.doing:
        commitment.startedOnce = True
    commitment.status = Status(to.value)
    return commitment


@router.patch("/{commitment_id}", response_model=Commitment)
def update_commitment(
    commitment_id: str,
    body: CommitmentPatch,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Commitment:
    session, _token = auth
    commitment = _require_commitment(store, commitment_id)
    _require_commitment_member(store, commitment, session.user.id)
    check(can_edit(commitment))

    patch = body.model_dump(exclude_unset=True)
    title = patch.get("title", commitment.title)
    points = patch.get("points", commitment.points)
    responsible_id = patch.get("responsibleId", commitment.responsibleId)
    check(
        validate_input(
            title=title if isinstance(title, str) else commitment.title,
            points=points,
            responsible_id=responsible_id,
        )
    )

    if "title" in patch and patch["title"] is not None:
        commitment.title = str(patch["title"]).strip()
    if "type" in patch and patch["type"] is not None:
        commitment.type = patch["type"]
    if "responsibleId" in patch and patch["responsibleId"] is not None:
        commitment.responsibleId = patch["responsibleId"]
    if "points" in patch and patch["points"] is not None:
        commitment.points = patch["points"]
    if "startDate" in patch:
        commitment.startDate = patch["startDate"]
    if "dueDate" in patch:
        commitment.dueDate = patch["dueDate"]
    if "note" in patch:
        commitment.note = patch["note"]

    store.append_history(
        commitment,
        kind=HistoryEventKind.updated,
        detail="Details updated",
        by_user_id=session.user.id,
    )
    return commitment


@router.post("/{commitment_id}/move", response_model=Commitment)
def move_commitment(
    commitment_id: str,
    body: MoveCommitmentRequest,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Commitment:
    session, _token = auth
    commitment = _require_commitment(store, commitment_id)
    _require_commitment_member(store, commitment, session.user.id)
    return _apply_move(store, commitment, body.to, session.user.id)


@router.post("/{commitment_id}/confirm", response_model=Commitment)
def confirm_commitment(
    commitment_id: str,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Commitment:
    session, _token = auth
    commitment = _require_commitment(store, commitment_id)
    _require_commitment_member(store, commitment, session.user.id)
    check(can_confirm(commitment, session.user.id))
    return _apply_move(store, commitment, BoardStatus.confirmed, session.user.id)


@router.post("/{commitment_id}/unconfirm", response_model=Commitment)
def unconfirm_commitment(
    commitment_id: str,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Commitment:
    session, _token = auth
    commitment = _require_commitment(store, commitment_id)
    _require_commitment_member(store, commitment, session.user.id)
    check(can_unconfirm(commitment, session.user.id))
    return _apply_move(store, commitment, BoardStatus.doing, session.user.id)


@router.post("/{commitment_id}/cancel", response_model=Commitment)
def cancel_commitment(
    commitment_id: str,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Commitment:
    session, _token = auth
    commitment = _require_commitment(store, commitment_id)
    _require_commitment_member(store, commitment, session.user.id)
    check(can_cancel(commitment, session.user.id))
    commitment.status = Status.cancelled
    commitment.cancelledAt = _utcnow()
    commitment.confirmedAt = None
    commitment.confirmedById = None
    store.append_history(
        commitment,
        kind=HistoryEventKind.cancelled,
        detail="Cancelled",
        by_user_id=session.user.id,
    )
    return commitment


@router.post("/{commitment_id}/restore", response_model=Commitment)
def restore_commitment(
    commitment_id: str,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Commitment:
    session, _token = auth
    commitment = _require_commitment(store, commitment_id)
    _require_commitment_member(store, commitment, session.user.id)
    check(can_restore(commitment, session.user.id))
    commitment.status = Status.backlog
    commitment.cancelledAt = None
    store.append_history(
        commitment,
        kind=HistoryEventKind.restored,
        detail="Restored to Backlog",
        by_user_id=session.user.id,
    )
    return commitment


@router.post("/{commitment_id}/archive", response_model=Commitment)
def archive_commitment(
    commitment_id: str,
    store: StoreDep,
    auth: RequireSessionDep,
) -> Commitment:
    session, _token = auth
    commitment = _require_commitment(store, commitment_id)
    _require_commitment_member(store, commitment, session.user.id)
    check(can_archive(commitment, session.user.id))
    commitment.status = Status.archived
    commitment.archivedAt = _utcnow()
    store.append_history(
        commitment,
        kind=HistoryEventKind.archived,
        detail="Archived",
        by_user_id=session.user.id,
    )
    return commitment
