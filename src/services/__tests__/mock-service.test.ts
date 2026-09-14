import { beforeEach, describe, expect, it } from "vitest";
import { createMockService } from "../mock/mock-service";
import { RuleError, type KanbanService } from "../types";

function svc(): KanbanService {
  return createMockService({ persistKey: null, latencyMs: 0, seed: false });
}

async function signIn(s: KanbanService, email: string) {
  const { devCode } = await s.auth.requestCode(email);
  return s.auth.verifyCode(email, devCode);
}

describe("auth", () => {
  let s: KanbanService;
  beforeEach(() => {
    s = svc();
  });

  it("auto-creates an account on first successful code verification", async () => {
    const session = await signIn(s, "Maya@Example.com ");
    expect(session.user.email).toBe("maya@example.com");
    expect(session.activeFamilyId).toBeNull();
  });

  it("rejects a wrong code", async () => {
    await s.auth.requestCode("leo@example.com");
    await expect(s.auth.verifyCode("leo@example.com", "000000")).rejects.toBeInstanceOf(RuleError);
  });

  it("signs the same email back into the same account", async () => {
    const first = await signIn(s, "maya@example.com");
    await s.auth.signOut();
    const second = await signIn(s, "maya@example.com");
    expect(second.user.id).toBe(first.user.id);
  });
});

describe("families", () => {
  it("creates a family with a join code and lets another account join it", async () => {
    const s = svc();
    await signIn(s, "maya@example.com");
    const family = await s.families.create("Rivera");
    await s.auth.signOut();

    await signIn(s, "leo@example.com");
    const joined = await s.families.joinByToken(family.joinToken.toLowerCase());
    expect(joined.id).toBe(family.id);
    const members = await s.families.members(family.id);
    expect(members).toHaveLength(2);
    expect(members[0]!.role).toBe("admin");
    expect(members[1]!.role).toBe("member");
  });
});

describe("commitment lifecycle", () => {
  let s: KanbanService;
  let familyId: string;
  let maya: string;
  let leo: string;

  beforeEach(async () => {
    s = svc();
    const m = await signIn(s, "maya@example.com");
    maya = m.user.id;
    const family = await s.families.create("Rivera");
    familyId = family.id;
    await s.auth.signOut();
    const l = await signIn(s, "leo@example.com");
    leo = l.user.id;
    await s.families.joinByToken(family.joinToken);
  });

  async function newCard(responsibleId = leo, points = 3) {
    return s.commitments.create(familyId, {
      title: "Fix the back door",
      type: "promise",
      responsibleId,
      points,
    });
  }

  it("creates commitments in Backlog", async () => {
    const c = await newCard();
    expect(c.status).toBe("backlog");
    expect(c.history[0]!.kind).toBe("created");
  });

  it("refuses points below 1", async () => {
    await expect(newCard(leo, 0)).rejects.toBeInstanceOf(RuleError);
  });

  it("runs the full flow and awards points on confirmation", async () => {
    let c = await newCard();
    c = await s.commitments.move(c.id, "ready");
    c = await s.commitments.move(c.id, "doing");
    c = await s.commitments.move(c.id, "done");
    await expect(s.commitments.confirm(c.id)).rejects.toBeInstanceOf(RuleError);

    await s.auth.signOut();
    await signIn(s, "maya@example.com");
    c = await s.commitments.confirm(c.id);
    expect(c.status).toBe("confirmed");
    expect(c.confirmedById).toBe(maya);

    const totals = await s.points.totals(familyId);
    expect(totals.find((t) => t.userId === leo)!.total).toBe(3);
  });

  it("returns points on un-confirm and awards them again on re-confirm", async () => {
    let c = await newCard();
    await s.commitments.move(c.id, "ready");
    await s.commitments.move(c.id, "doing");
    await s.commitments.move(c.id, "done");
    await s.auth.signOut();
    await signIn(s, "maya@example.com");
    await s.commitments.confirm(c.id);

    c = await s.commitments.unconfirm(c.id);
    expect(c.status).toBe("doing");
    let totals = await s.points.totals(familyId);
    expect(totals.find((t) => t.userId === leo)!.total).toBe(0);

    await s.auth.signOut();
    await signIn(s, "leo@example.com");
    await s.commitments.move(c.id, "done");
    await s.auth.signOut();
    await signIn(s, "maya@example.com");
    await s.commitments.confirm(c.id);
    totals = await s.points.totals(familyId);
    expect(totals.find((t) => t.userId === leo)!.total).toBe(3);
  });

  it("locks editing once the card is in Doing", async () => {
    const c = await newCard();
    await s.commitments.update(c.id, { points: 5, title: "Fix the door properly" });
    await s.commitments.move(c.id, "ready");
    await s.commitments.move(c.id, "doing");
    await expect(s.commitments.update(c.id, { points: 9 })).rejects.toBeInstanceOf(RuleError);
  });

  it("blocks Backlog → Ready when another member tries to pull", async () => {
    const c = await newCard(maya);
    await expect(s.commitments.move(c.id, "ready")).rejects.toBeInstanceOf(RuleError);
  });

  it("cancels, keeps history, and restores to Backlog with the same points", async () => {
    let c = await newCard();
    await s.commitments.move(c.id, "ready");
    c = await s.commitments.cancel(c.id);
    expect(c.status).toBe("cancelled");

    const history = await s.history.list(familyId);
    expect(history.some((h) => h.commitmentId === c.id && h.status === "cancelled")).toBe(true);

    c = await s.commitments.restore(c.id);
    expect(c.status).toBe("backlog");
    expect(c.points).toBe(3);
    expect(c.history.map((h) => h.kind)).toContain("cancelled");
  });

  it("removes awarded points when a confirmed commitment is cancelled", async () => {
    const c = await newCard();
    await s.commitments.move(c.id, "ready");
    await s.commitments.move(c.id, "doing");
    await s.commitments.move(c.id, "done");
    await s.auth.signOut();
    await signIn(s, "maya@example.com");
    await s.commitments.confirm(c.id);
    await s.auth.signOut();
    await signIn(s, "leo@example.com");
    await s.commitments.cancel(c.id);

    const totals = await s.points.totals(familyId);
    expect(totals.find((t) => t.userId === leo)!.total).toBe(0);
  });

  it("archives only after confirmation and keeps the points", async () => {
    const c = await newCard();
    await s.commitments.move(c.id, "ready");
    await s.commitments.move(c.id, "doing");
    await s.commitments.move(c.id, "done");
    await expect(s.commitments.archive(c.id)).rejects.toBeInstanceOf(RuleError);
    await s.auth.signOut();
    await signIn(s, "maya@example.com");
    await s.commitments.confirm(c.id);
    await expect(s.commitments.archive(c.id)).rejects.toBeInstanceOf(RuleError);
    await s.auth.signOut();
    await signIn(s, "leo@example.com");
    const archived = await s.commitments.archive(c.id);
    expect(archived.status).toBe("archived");
    const totals = await s.points.totals(familyId);
    expect(totals.find((t) => t.userId === leo)!.total).toBe(3);
  });

  it("lists the points ledger newest first", async () => {
    for (const title of ["A", "B"]) {
      const c = await s.commitments.create(familyId, {
        title,
        type: "request",
        responsibleId: leo,
        points: 1,
      });
      await s.commitments.move(c.id, "ready");
      await s.commitments.move(c.id, "doing");
      await s.commitments.move(c.id, "done");
      await s.auth.signOut();
      await signIn(s, "maya@example.com");
      await s.commitments.confirm(c.id);
      await s.auth.signOut();
      await signIn(s, "leo@example.com");
    }
    const ledger = await s.points.ledger(familyId);
    expect(ledger).toHaveLength(2);
    expect(ledger[0]!.confirmedAt >= ledger[1]!.confirmedAt).toBe(true);
  });
});
