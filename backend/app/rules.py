"""Pure domain rules for commitment lifecycle (port of frontend rules.ts)."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.commitments import BoardStatus, Commitment, Status


@dataclass(frozen=True)
class RuleCheck:
    ok: bool
    reason: str | None = None


_OK = RuleCheck(ok=True)


def _no(reason: str) -> RuleCheck:
    return RuleCheck(ok=False, reason=reason)


def is_on_board(c: Commitment) -> bool:
    return c.status not in (Status.archived, Status.cancelled)


def can_edit(c: Commitment) -> RuleCheck:
    if c.status in (Status.backlog, Status.ready):
        return _OK
    return _no("Commitments can only be edited while in Backlog or Ready.")


def can_move(c: Commitment, to: BoardStatus, user_id: str) -> RuleCheck:
    is_responsible = c.responsibleId == user_id
    if not is_on_board(c):
        return _no("This commitment is no longer on the board.")
    if c.status.value == to.value:
        return _no("Already in this column.")

    key = f"{c.status.value}->{to.value}"
    if key == "backlog->ready":
        if not is_responsible:
            return _no("Only the responsible person can pull this into Ready.")
        if not c.points or c.points < 1:
            return _no("Set at least 1 point before moving to Ready.")
        return _OK
    if key in ("ready->doing", "doing->done"):
        if not is_responsible:
            return _no("Only the responsible person can move this card.")
        return _OK
    if key == "done->confirmed":
        if is_responsible:
            return _no("Another family member needs to confirm this one.")
        return _OK
    if key == "confirmed->doing":
        if is_responsible:
            return _no("Another family member can un-confirm this one.")
        return _OK
    return _no("That move isn't part of the family flow.")


def can_confirm(c: Commitment, user_id: str) -> RuleCheck:
    if c.status != Status.done:
        return _no("Only Done commitments can be confirmed.")
    return can_move(c, BoardStatus.confirmed, user_id)


def can_unconfirm(c: Commitment, user_id: str) -> RuleCheck:
    if c.status != Status.confirmed:
        return _no("Only confirmed commitments can be un-confirmed.")
    return can_move(c, BoardStatus.doing, user_id)


def can_archive(c: Commitment, user_id: str) -> RuleCheck:
    if c.status != Status.confirmed:
        return _no("Only confirmed commitments can be archived.")
    if c.responsibleId != user_id:
        return _no("Only the responsible person can archive this one.")
    return _OK


def can_cancel(c: Commitment, user_id: str) -> RuleCheck:
    if not is_on_board(c):
        return _no("This commitment already left the board.")
    if c.responsibleId != user_id:
        return _no("Only the responsible person can cancel this one.")
    return _OK


def can_restore(c: Commitment, user_id: str) -> RuleCheck:
    if c.status != Status.cancelled:
        return _no("Only cancelled commitments can be restored.")
    if c.responsibleId != user_id:
        return _no("Only the responsible person can restore this one.")
    return _OK


def validate_input(*, title: str, points: int, responsible_id: str) -> RuleCheck:
    if not title.strip():
        return _no("Give the commitment a title.")
    if not responsible_id:
        return _no("Pick who is responsible.")
    if not isinstance(points, int) or isinstance(points, bool) or points < 1:
        return _no("Points must be a whole number of at least 1.")
    return _OK


def check(result: RuleCheck) -> None:
    from app.errors import AppError

    if not result.ok:
        raise AppError(result.reason or "Not allowed.")
