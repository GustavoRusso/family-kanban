// Pure domain rules. Shared by the service implementation (enforcement)
// and the UI (enabling / disabling actions).

import type { BoardStatus, Commitment, CommitmentType } from "./types";

export const WIP_LIMIT_DOING = 2;

export const BOARD_COLUMNS: BoardStatus[] = [
  "backlog",
  "ready",
  "doing",
  "done",
  "confirmed",
];

export const COLUMN_LABELS: Record<BoardStatus, string> = {
  backlog: "Backlog",
  ready: "Ready",
  doing: "Doing",
  done: "Done",
  confirmed: "Confirmed",
};

export const COMMITMENT_TYPES: CommitmentType[] = [
  "promise",
  "request",
  "responsibility",
  "consequence",
  "reward",
];

export const TYPE_LABELS: Record<CommitmentType, string> = {
  promise: "Promise",
  request: "Request",
  responsibility: "Responsibility",
  consequence: "Consequence",
  reward: "Reward",
};

export interface RuleCheck {
  ok: boolean;
  reason?: string;
}

const ok: RuleCheck = { ok: true };
const no = (reason: string): RuleCheck => ({ ok: false, reason });

export function isOnBoard(c: Commitment): boolean {
  return c.status !== "archived" && c.status !== "cancelled";
}

/** Title, type, responsible person, dates, note and points are editable in Backlog/Ready only. */
export function canEdit(c: Commitment): RuleCheck {
  if (c.status === "backlog" || c.status === "ready") return ok;
  return no("Commitments can only be edited while in Backlog or Ready.");
}

export function canSetPoints(c: Commitment): RuleCheck {
  return canEdit(c).ok
    ? ok
    : no("Points stay fixed once the commitment enters Doing.");
}

export function canMove(
  c: Commitment,
  to: BoardStatus,
  userId: string,
): RuleCheck {
  const isResponsible = c.responsibleId === userId;
  if (!isOnBoard(c)) return no("This commitment is no longer on the board.");
  if (c.status === to) return no("Already in this column.");

  switch (`${c.status}->${to}`) {
    case "backlog->ready":
      if (!isResponsible)
        return no("Only the responsible person can pull this into Ready.");
      if (!c.points || c.points < 1)
        return no("Set at least 1 point before moving to Ready.");
      return ok;
    case "ready->doing":
    case "doing->done":
      if (!isResponsible)
        return no("Only the responsible person can move this card.");
      return ok;
    case "done->confirmed":
      if (isResponsible)
        return no("Another family member needs to confirm this one.");
      return ok;
    case "confirmed->doing":
      if (isResponsible)
        return no("Another family member can un-confirm this one.");
      return ok;
    default:
      return no("That move isn't part of the family flow.");
  }
}

export function canConfirm(c: Commitment, userId: string): RuleCheck {
  if (c.status !== "done") return no("Only Done commitments can be confirmed.");
  return canMove(c, "confirmed", userId);
}

export function canUnconfirm(c: Commitment, userId: string): RuleCheck {
  if (c.status !== "confirmed") return no("Only confirmed commitments can be un-confirmed.");
  return canMove(c, "doing", userId);
}

export function canArchive(c: Commitment, userId: string): RuleCheck {
  if (c.status !== "confirmed") return no("Only confirmed commitments can be archived.");
  if (c.responsibleId !== userId)
    return no("Only the responsible person can archive this one.");
  return ok;
}

export function canCancel(c: Commitment, userId: string): RuleCheck {
  if (!isOnBoard(c)) return no("This commitment already left the board.");
  if (c.responsibleId !== userId)
    return no("Only the responsible person can cancel this one.");
  return ok;
}

export function canRestore(c: Commitment, userId: string): RuleCheck {
  if (c.status !== "cancelled") return no("Only cancelled commitments can be restored.");
  if (c.responsibleId !== userId)
    return no("Only the responsible person can restore this one.");
  return ok;
}

/** Points are awarded while the commitment is confirmed or archived. */
export function hasAwardedPoints(c: Commitment): boolean {
  return c.status === "confirmed" || c.status === "archived";
}

export function isPastDue(c: Commitment, now: Date = new Date()): boolean {
  if (!c.dueDate) return false;
  if (!isOnBoard(c) || c.status === "confirmed") return false;
  return new Date(c.dueDate).getTime() < now.getTime();
}

export function isDueToday(c: Commitment, now: Date = new Date()): boolean {
  if (!c.dueDate) return false;
  const d = new Date(c.dueDate);
  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  );
}

export function doingCount(commitments: Commitment[], userId: string): number {
  return commitments.filter((c) => c.status === "doing" && c.responsibleId === userId)
    .length;
}

export function exceedsWipLimit(commitments: Commitment[], userId: string): boolean {
  return doingCount(commitments, userId) > WIP_LIMIT_DOING;
}

export function wipReminder(commitments: Commitment[], userId: string, name: string) {
  const count = doingCount(commitments, userId);
  if (count <= WIP_LIMIT_DOING) return null;
  return `${name} has ${count} cards in Doing — finishing one first usually feels better than starting another!`;
}

export function validateInput(input: {
  title: string;
  points: number;
  responsibleId: string;
}): RuleCheck {
  if (!input.title.trim()) return no("Give the commitment a title.");
  if (!input.responsibleId) return no("Pick who is responsible.");
  if (!Number.isInteger(input.points) || input.points < 1)
    return no("Points must be a whole number of at least 1.");
  return ok;
}
