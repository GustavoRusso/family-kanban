// Domain types + the single service contract every backend call goes through.

export type CommitmentType =
  | "promise"
  | "request"
  | "responsibility"
  | "consequence"
  | "reward";

export type BoardStatus = "backlog" | "ready" | "doing" | "done" | "confirmed";
export type Status = BoardStatus | "archived" | "cancelled";

export type Role = "admin" | "member";

export interface User {
  id: string;
  email: string;
  name: string;
}

export interface Family {
  id: string;
  name: string;
  joinToken: string;
}

export interface Member {
  userId: string;
  familyId: string;
  name: string;
  email: string;
  role: Role;
}

export interface HistoryEvent {
  id: string;
  at: string;
  byUserId: string;
  kind:
    | "created"
    | "updated"
    | "moved"
    | "confirmed"
    | "unconfirmed"
    | "cancelled"
    | "restored"
    | "archived";
  detail: string;
}

export interface Commitment {
  id: string;
  familyId: string;
  title: string;
  type: CommitmentType;
  responsibleId: string;
  points: number;
  startDate?: string | null;
  dueDate?: string | null;
  note?: string | null;
  status: Status;
  /** Status the card returns to when restored is always backlog; kept for history clarity. */
  startedOnce: boolean;
  createdAt: string;
  confirmedAt?: string | null;
  confirmedById?: string | null;
  archivedAt?: string | null;
  cancelledAt?: string | null;
  history: HistoryEvent[];
}

export interface CommitmentInput {
  title: string;
  type: CommitmentType;
  responsibleId: string;
  points: number;
  startDate?: string | null;
  dueDate?: string | null;
  note?: string | null;
}

export interface Session {
  user: User;
  activeFamilyId: string | null;
}

export interface PointsTotal {
  userId: string;
  name: string;
  total: number;
}

export interface PointsEntry {
  commitmentId: string;
  userId: string;
  title: string;
  points: number;
  confirmedAt: string;
}

export interface HistoryItem {
  commitmentId: string;
  title: string;
  type: CommitmentType;
  responsibleId: string;
  responsibleName: string;
  status: Extract<Status, "archived" | "cancelled" | "confirmed">;
  outcomeDate: string;
  points: number;
}

export class RuleError extends Error {}

export interface KanbanService {
  auth: {
    /** Sends a one-time code. Returns the code in mock mode so it can be shown on screen. */
    requestCode(email: string): Promise<{ devCode: string }>;
    /** Verifies the code; auto-creates the account when the email is unknown. */
    verifyCode(email: string, code: string): Promise<Session>;
    currentSession(): Promise<Session | null>;
    signOut(): Promise<void>;
  };
  families: {
    create(name: string): Promise<Family>;
    joinByToken(token: string): Promise<Family>;
    listMine(): Promise<Family[]>;
    setActive(familyId: string): Promise<Session>;
    get(familyId: string): Promise<Family>;
    members(familyId: string): Promise<Member[]>;
    rename(familyId: string, name: string): Promise<Family>;
    removeMember(familyId: string, userId: string): Promise<void>;
  };
  commitments: {
    list(familyId: string): Promise<Commitment[]>;
    create(familyId: string, input: CommitmentInput): Promise<Commitment>;
    update(id: string, patch: Partial<CommitmentInput>): Promise<Commitment>;
    move(id: string, to: BoardStatus): Promise<Commitment>;
    confirm(id: string): Promise<Commitment>;
    unconfirm(id: string): Promise<Commitment>;
    cancel(id: string): Promise<Commitment>;
    restore(id: string): Promise<Commitment>;
    archive(id: string): Promise<Commitment>;
  };
  points: {
    totals(familyId: string): Promise<PointsTotal[]>;
    ledger(familyId: string): Promise<PointsEntry[]>;
  };
  history: {
    list(familyId: string): Promise<HistoryItem[]>;
  };
}
