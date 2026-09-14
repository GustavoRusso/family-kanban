// Mock implementation of the whole backend. In-memory, optionally persisted
// to localStorage, so the full app runs without any real backend.

import {
  RuleError,
  type BoardStatus,
  type Commitment,
  type CommitmentInput,
  type Family,
  type HistoryItem,
  type KanbanService,
  type Member,
  type PointsEntry,
  type PointsTotal,
  type Session,
  type User,
} from "../types";
import {
  canArchive,
  canCancel,
  canConfirm,
  canEdit,
  canMove,
  canRestore,
  canUnconfirm,
  validateInput,
} from "../rules";

interface Db {
  users: User[];
  families: Family[];
  members: Member[];
  commitments: Commitment[];
  codes: Record<string, string>;
  session: Session | null;
}

export interface MockOptions {
  persistKey?: string | null;
  latencyMs?: number;
  seed?: boolean;
  now?: () => Date;
}

const id = () => Math.random().toString(36).slice(2, 10);
const token = () => Math.random().toString(36).slice(2, 8).toUpperCase();

function emptyDb(): Db {
  return { users: [], families: [], members: [], commitments: [], codes: {}, session: null };
}

function seedDb(now: Date): Db {
  const db = emptyDb();
  const family: Family = { id: "fam-demo", name: "The Rivera Family", joinToken: "RIVERA" };
  db.families.push(family);

  const people: Array<[string, string, string, "admin" | "member"]> = [
    ["u-mom", "maya@example.com", "Maya", "admin"],
    ["u-dad", "leo@example.com", "Leo", "member"],
    ["u-kid", "nina@example.com", "Nina", "member"],
  ];
  for (const [uid, email, name, role] of people) {
    db.users.push({ id: uid, email, name });
    db.members.push({ userId: uid, familyId: family.id, name, email, role });
  }

  const day = 86_400_000;
  const iso = (offset: number) => new Date(now.getTime() + offset).toISOString();

  const make = (
    c: Partial<Commitment> & Pick<Commitment, "title" | "type" | "responsibleId" | "points" | "status">,
  ): Commitment => ({
    id: id(),
    familyId: family.id,
    startDate: null,
    dueDate: null,
    note: null,
    startedOnce: ["doing", "done", "confirmed", "archived"].includes(c.status),
    createdAt: iso(-3 * day),
    confirmedAt: null,
    confirmedById: null,
    archivedAt: null,
    cancelledAt: null,
    history: [
      { id: id(), at: iso(-3 * day), byUserId: "u-mom", kind: "created", detail: "Created" },
    ],
    ...c,
  });

  db.commitments.push(
    make({ title: "Walk the dog after school", type: "responsibility", responsibleId: "u-kid", points: 2, status: "doing", dueDate: iso(-1 * day) }),
    make({ title: "Fix the squeaky back door", type: "promise", responsibleId: "u-dad", points: 3, status: "ready" }),
    make({ title: "Plan Saturday movie night", type: "reward", responsibleId: "u-mom", points: 2, status: "backlog", note: "Everyone picks one snack." }),
    make({ title: "Tidy the shared bookshelf", type: "request", responsibleId: "u-kid", points: 1, status: "done" }),
    make({ title: "Help with grocery unpacking", type: "request", responsibleId: "u-dad", points: 1, status: "backlog", dueDate: iso(day) }),
    make({
      title: "Read 20 minutes before bed",
      type: "consequence",
      responsibleId: "u-kid",
      points: 2,
      status: "confirmed",
      confirmedAt: iso(-day),
      confirmedById: "u-mom",
    }),
  );
  return db;
}

export function createMockService(options: MockOptions = {}): KanbanService {
  const { persistKey = "family-kanban-db", latencyMs = 120, seed = true } = options;
  const now = options.now ?? (() => new Date());

  let db: Db = load();

  function load(): Db {
    if (persistKey && typeof localStorage !== "undefined") {
      const raw = localStorage.getItem(persistKey);
      if (raw) {
        try {
          return JSON.parse(raw) as Db;
        } catch {
          /* fall through to a fresh db */
        }
      }
    }
    return seed ? seedDb(now()) : emptyDb();
  }

  function save() {
    if (persistKey && typeof localStorage !== "undefined") {
      localStorage.setItem(persistKey, JSON.stringify(db));
    }
  }

  async function delay<T>(value: T): Promise<T> {
    if (latencyMs > 0) await new Promise((r) => setTimeout(r, latencyMs));
    save();
    return value;
  }

  function requireSession(): Session {
    if (!db.session) throw new RuleError("You need to sign in first.");
    return db.session;
  }

  function requireCommitment(cid: string): Commitment {
    const c = db.commitments.find((x) => x.id === cid);
    if (!c) throw new RuleError("Commitment not found.");
    return c;
  }

  function assertMember(familyId: string, userId: string) {
    if (!db.members.some((m) => m.familyId === familyId && m.userId === userId))
      throw new RuleError("You are not a member of this family.");
  }

  function check(result: { ok: boolean; reason?: string }) {
    if (!result.ok) throw new RuleError(result.reason ?? "Not allowed.");
  }

  function log(c: Commitment, kind: Commitment["history"][number]["kind"], detail: string, by: string) {
    c.history.push({ id: id(), at: now().toISOString(), byUserId: by, kind, detail });
  }

  function clone<T>(v: T): T {
    return JSON.parse(JSON.stringify(v)) as T;
  }

  return {
    auth: {
      async requestCode(email) {
        const normalized = email.trim().toLowerCase();
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(normalized))
          throw new RuleError("Enter a valid email address.");
        const code = String(Math.floor(100000 + Math.random() * 900000));
        db.codes[normalized] = code;
        return delay({ devCode: code });
      },
      async verifyCode(email, code) {
        const normalized = email.trim().toLowerCase();
        if (db.codes[normalized] !== code.trim())
          throw new RuleError("That code doesn't match. Try again.");
        delete db.codes[normalized];
        const existing = db.users.find((u) => u.email === normalized);
        const user: User = existing ?? {
          id: `u-${id()}`,
          email: normalized,
          name: normalized.split("@")[0] ?? normalized,
        };
        if (!existing) db.users.push(user);
        const families = db.members.filter((m) => m.userId === user.id);
        const session: Session = { user, activeFamilyId: families[0]?.familyId ?? null };
        db.session = session;
        return delay(clone(session));
      },
      async currentSession() {
        return delay(db.session ? clone(db.session) : null);
      },
      async signOut() {
        db.session = null;
        return delay(undefined);
      },
    },

    families: {
      async create(name) {
        const s = requireSession();
        const family: Family = { id: `fam-${id()}`, name: name.trim(), joinToken: token() };
        if (!family.name) throw new RuleError("Give your family a name.");
        db.families.push(family);
        db.members.push({
          userId: s.user.id,
          familyId: family.id,
          name: s.user.name,
          email: s.user.email,
          role: "admin",
        });
        db.session = { ...s, activeFamilyId: family.id };
        return delay(clone(family));
      },
      async joinByToken(joinToken) {
        const s = requireSession();
        const family = db.families.find(
          (f) => f.joinToken.toUpperCase() === joinToken.trim().toUpperCase(),
        );
        if (!family) throw new RuleError("We couldn't find a family for that code.");
        if (!db.members.some((m) => m.familyId === family.id && m.userId === s.user.id)) {
          db.members.push({
            userId: s.user.id,
            familyId: family.id,
            name: s.user.name,
            email: s.user.email,
            role: "member",
          });
        }
        db.session = { ...s, activeFamilyId: family.id };
        return delay(clone(family));
      },
      async listMine() {
        const s = requireSession();
        const ids = db.members.filter((m) => m.userId === s.user.id).map((m) => m.familyId);
        return delay(clone(db.families.filter((f) => ids.includes(f.id))));
      },
      async setActive(familyId) {
        const s = requireSession();
        assertMember(familyId, s.user.id);
        db.session = { ...s, activeFamilyId: familyId };
        return delay(clone(db.session));
      },
      async get(familyId) {
        const f = db.families.find((x) => x.id === familyId);
        if (!f) throw new RuleError("Family not found.");
        return delay(clone(f));
      },
      async members(familyId) {
        return delay(clone(db.members.filter((m) => m.familyId === familyId)));
      },
      async rename(familyId, name) {
        const s = requireSession();
        const me = db.members.find((m) => m.familyId === familyId && m.userId === s.user.id);
        if (me?.role !== "admin") throw new RuleError("Only an admin can rename the family.");
        const f = db.families.find((x) => x.id === familyId)!;
        f.name = name.trim() || f.name;
        return delay(clone(f));
      },
      async removeMember(familyId, userId) {
        const s = requireSession();
        const me = db.members.find((m) => m.familyId === familyId && m.userId === s.user.id);
        if (me?.role !== "admin") throw new RuleError("Only an admin can remove members.");
        db.members = db.members.filter(
          (m) => !(m.familyId === familyId && m.userId === userId),
        );
        return delay(undefined);
      },
    },

    commitments: {
      async list(familyId) {
        return delay(clone(db.commitments.filter((c) => c.familyId === familyId)));
      },
      async create(familyId, input) {
        const s = requireSession();
        assertMember(familyId, s.user.id);
        check(validateInput(input));
        const c: Commitment = {
          id: `c-${id()}`,
          familyId,
          title: input.title.trim(),
          type: input.type,
          responsibleId: input.responsibleId,
          points: input.points,
          startDate: input.startDate ?? null,
          dueDate: input.dueDate ?? null,
          note: input.note ?? null,
          status: "backlog",
          startedOnce: false,
          createdAt: now().toISOString(),
          confirmedAt: null,
          confirmedById: null,
          archivedAt: null,
          cancelledAt: null,
          history: [],
        };
        log(c, "created", "Created in Backlog", s.user.id);
        db.commitments.push(c);
        return delay(clone(c));
      },
      async update(cid, patch) {
        const s = requireSession();
        const c = requireCommitment(cid);
        assertMember(c.familyId, s.user.id);
        check(canEdit(c));
        const next = { ...c, ...patch };
        check(
          validateInput({
            title: next.title,
            points: next.points,
            responsibleId: next.responsibleId,
          }),
        );
        Object.assign(c, patch, { title: next.title.trim() });
        log(c, "updated", "Details updated", s.user.id);
        return delay(clone(c));
      },
      async move(cid, to: BoardStatus) {
        const s = requireSession();
        const c = requireCommitment(cid);
        assertMember(c.familyId, s.user.id);
        check(canMove(c, to, s.user.id));
        if (to === "confirmed") {
          c.confirmedAt = now().toISOString();
          c.confirmedById = s.user.id;
          log(c, "confirmed", "Confirmed — points awarded", s.user.id);
        } else if (c.status === "confirmed" && to === "doing") {
          c.confirmedAt = null;
          c.confirmedById = null;
          log(c, "unconfirmed", "Un-confirmed — points returned", s.user.id);
        } else {
          log(c, "moved", `Moved ${c.status} → ${to}`, s.user.id);
        }
        if (to === "doing") c.startedOnce = true;
        c.status = to;
        return delay(clone(c));
      },
      async confirm(cid) {
        const s = requireSession();
        const c = requireCommitment(cid);
        check(canConfirm(c, s.user.id));
        return this.move(cid, "confirmed");
      },
      async unconfirm(cid) {
        const s = requireSession();
        const c = requireCommitment(cid);
        check(canUnconfirm(c, s.user.id));
        return this.move(cid, "doing");
      },
      async cancel(cid) {
        const s = requireSession();
        const c = requireCommitment(cid);
        check(canCancel(c, s.user.id));
        c.status = "cancelled";
        c.cancelledAt = now().toISOString();
        c.confirmedAt = null;
        c.confirmedById = null;
        log(c, "cancelled", "Cancelled", s.user.id);
        return delay(clone(c));
      },
      async restore(cid) {
        const s = requireSession();
        const c = requireCommitment(cid);
        check(canRestore(c, s.user.id));
        c.status = "backlog";
        c.cancelledAt = null;
        log(c, "restored", "Restored to Backlog", s.user.id);
        return delay(clone(c));
      },
      async archive(cid) {
        const s = requireSession();
        const c = requireCommitment(cid);
        check(canArchive(c, s.user.id));
        c.status = "archived";
        c.archivedAt = now().toISOString();
        log(c, "archived", "Archived", s.user.id);
        return delay(clone(c));
      },
    },

    points: {
      async totals(familyId) {
        const members = db.members.filter((m) => m.familyId === familyId);
        const totals: PointsTotal[] = members.map((m) => ({
          userId: m.userId,
          name: m.name,
          total: db.commitments
            .filter(
              (c) =>
                c.familyId === familyId &&
                c.responsibleId === m.userId &&
                (c.status === "confirmed" || c.status === "archived"),
            )
            .reduce((sum, c) => sum + c.points, 0),
        }));
        return delay(totals);
      },
      async ledger(familyId) {
        const entries: PointsEntry[] = db.commitments
          .filter(
            (c) =>
              c.familyId === familyId &&
              (c.status === "confirmed" || c.status === "archived"),
          )
          .map((c) => ({
            commitmentId: c.id,
            userId: c.responsibleId,
            title: c.title,
            points: c.points,
            confirmedAt:
              c.confirmedAt ??
              c.history.find((h) => h.kind === "confirmed")?.at ??
              c.createdAt,
          }))
          .sort((a, b) => b.confirmedAt.localeCompare(a.confirmedAt));
        return delay(entries);
      },
    },

    history: {
      async list(familyId) {
        const items: HistoryItem[] = db.commitments
          .filter(
            (c) =>
              c.familyId === familyId &&
              (c.status === "archived" || c.status === "cancelled" || c.status === "confirmed"),
          )
          .map((c) => ({
            commitmentId: c.id,
            title: c.title,
            type: c.type,
            responsibleId: c.responsibleId,
            responsibleName:
              db.members.find((m) => m.userId === c.responsibleId && m.familyId === familyId)
                ?.name ?? "Unknown",
            status: c.status as HistoryItem["status"],
            outcomeDate: c.archivedAt ?? c.cancelledAt ?? c.confirmedAt ?? c.createdAt,
            points: c.points,
          }))
          .sort((a, b) => b.outcomeDate.localeCompare(a.outcomeDate));
        return delay(items);
      },
    },
  };
}
