import { describe, expect, it } from "vitest";
import {
  canArchive,
  canCancel,
  canEdit,
  canMove,
  canRestore,
  canUnconfirm,
  doingCount,
  exceedsWipLimit,
  isPastDue,
  validateInput,
} from "../rules";
import type { Commitment, Status } from "../types";

const base = (overrides: Partial<Commitment> = {}): Commitment => ({
  id: "c1",
  familyId: "f1",
  title: "Walk the dog",
  type: "promise",
  responsibleId: "me",
  points: 2,
  startDate: null,
  dueDate: null,
  note: null,
  status: "backlog" as Status,
  startedOnce: false,
  createdAt: new Date("2026-01-01").toISOString(),
  confirmedAt: null,
  confirmedById: null,
  archivedAt: null,
  cancelledAt: null,
  history: [],
  ...overrides,
});

describe("move rules", () => {
  it("lets the responsible person pull Backlog → Ready when points are set", () => {
    expect(canMove(base(), "ready", "me").ok).toBe(true);
  });

  it("blocks Backlog → Ready for anyone else", () => {
    expect(canMove(base(), "ready", "other").ok).toBe(false);
  });

  it("blocks Backlog → Ready without points", () => {
    expect(canMove(base({ points: 0 }), "ready", "me").ok).toBe(false);
  });

  it("allows the responsible person through Ready → Doing → Done", () => {
    expect(canMove(base({ status: "ready" }), "doing", "me").ok).toBe(true);
    expect(canMove(base({ status: "doing" }), "done", "me").ok).toBe(true);
  });

  it("requires another member to confirm", () => {
    expect(canMove(base({ status: "done" }), "confirmed", "me").ok).toBe(false);
    expect(canMove(base({ status: "done" }), "confirmed", "other").ok).toBe(true);
  });

  it("rejects skipping columns", () => {
    expect(canMove(base(), "done", "me").ok).toBe(false);
  });
});

describe("edit and points rules", () => {
  it("allows editing in Backlog and Ready only", () => {
    expect(canEdit(base()).ok).toBe(true);
    expect(canEdit(base({ status: "ready" })).ok).toBe(true);
    expect(canEdit(base({ status: "doing" })).ok).toBe(false);
    expect(canEdit(base({ status: "confirmed" })).ok).toBe(false);
  });

  it("requires a whole number of points of at least 1", () => {
    expect(validateInput({ title: "x", points: 0, responsibleId: "me" }).ok).toBe(false);
    expect(validateInput({ title: "x", points: 1.5, responsibleId: "me" }).ok).toBe(false);
    expect(validateInput({ title: " ", points: 2, responsibleId: "me" }).ok).toBe(false);
    expect(validateInput({ title: "x", points: 2, responsibleId: "me" }).ok).toBe(true);
  });
});

describe("un-confirm, archive, cancel, restore", () => {
  const confirmed = base({ status: "confirmed" });

  it("lets another member un-confirm but not the responsible person", () => {
    expect(canUnconfirm(confirmed, "other").ok).toBe(true);
    expect(canUnconfirm(confirmed, "me").ok).toBe(false);
  });

  it("lets only the responsible person archive a confirmed card", () => {
    expect(canArchive(confirmed, "me").ok).toBe(true);
    expect(canArchive(confirmed, "other").ok).toBe(false);
    expect(canArchive(base({ status: "done" }), "me").ok).toBe(false);
  });

  it("lets only the responsible person cancel and restore", () => {
    expect(canCancel(base({ status: "doing" }), "me").ok).toBe(true);
    expect(canCancel(base({ status: "doing" }), "other").ok).toBe(false);
    expect(canRestore(base({ status: "cancelled" }), "me").ok).toBe(true);
    expect(canRestore(base({ status: "doing" }), "me").ok).toBe(false);
  });
});

describe("indicators and WIP", () => {
  const now = new Date("2026-02-10T12:00:00Z");

  it("flags past due cards still on the board", () => {
    expect(isPastDue(base({ dueDate: "2026-02-09T12:00:00Z", status: "doing" }), now)).toBe(true);
    expect(isPastDue(base({ dueDate: "2026-02-11T12:00:00Z", status: "doing" }), now)).toBe(false);
    expect(isPastDue(base({ dueDate: "2026-02-09T12:00:00Z", status: "confirmed" }), now)).toBe(
      false,
    );
  });

  it("counts Doing cards per person and warns above the soft limit", () => {
    const cards = [
      base({ id: "1", status: "doing" }),
      base({ id: "2", status: "doing" }),
      base({ id: "3", status: "doing" }),
      base({ id: "4", status: "doing", responsibleId: "other" }),
    ];
    expect(doingCount(cards, "me")).toBe(3);
    expect(exceedsWipLimit(cards, "me")).toBe(true);
    expect(exceedsWipLimit(cards, "other")).toBe(false);
  });
});
