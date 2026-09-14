import type {
  BoardStatus,
  Commitment,
  CommitmentInput,
  Family,
  HistoryItem,
  KanbanService,
  Member,
  PointsEntry,
  PointsTotal,
  Session,
  User,
} from "../types";
import { api, setAccessToken } from "./http";

interface AuthSuccess {
  user: User;
  activeFamilyId: string | null;
  accessToken: string;
}

export function createApiService(): KanbanService {
  return {
    auth: {
      async requestCode(email) {
        return api<{ devCode?: string | null }>("POST", "/auth/code", { email });
      },
      async verifyCode(email, code) {
        const result = await api<AuthSuccess>("POST", "/auth/verify", { email, code });
        setAccessToken(result.accessToken);
        return { user: result.user, activeFamilyId: result.activeFamilyId };
      },
      async currentSession() {
        return api<Session | null>("GET", "/auth/session");
      },
      async signOut() {
        try {
          await api<void>("POST", "/auth/sign-out");
        } finally {
          setAccessToken(null);
        }
      },
    },

    families: {
      async create(name) {
        return api<Family>("POST", "/families", { name });
      },
      async joinByToken(token) {
        return api<Family>("POST", "/families/join", { token });
      },
      async listMine() {
        return api<Family[]>("GET", "/families");
      },
      async setActive(familyId) {
        return api<Session>("POST", `/families/${encodeURIComponent(familyId)}/activate`);
      },
      async get(familyId) {
        return api<Family>("GET", `/families/${encodeURIComponent(familyId)}`);
      },
      async members(familyId) {
        return api<Member[]>("GET", `/families/${encodeURIComponent(familyId)}/members`);
      },
      async rename(familyId, name) {
        return api<Family>("PATCH", `/families/${encodeURIComponent(familyId)}`, { name });
      },
      async removeMember(familyId, userId) {
        await api<void>(
          "DELETE",
          `/families/${encodeURIComponent(familyId)}/members/${encodeURIComponent(userId)}`,
        );
      },
    },

    commitments: {
      async list(familyId) {
        return api<Commitment[]>(
          "GET",
          `/families/${encodeURIComponent(familyId)}/commitments`,
        );
      },
      async create(familyId, input) {
        return api<Commitment>(
          "POST",
          `/families/${encodeURIComponent(familyId)}/commitments`,
          input,
        );
      },
      async update(id, patch) {
        return api<Commitment>(
          "PATCH",
          `/commitments/${encodeURIComponent(id)}`,
          patch as Partial<CommitmentInput>,
        );
      },
      async move(id, to: BoardStatus) {
        return api<Commitment>("POST", `/commitments/${encodeURIComponent(id)}/move`, {
          to,
        });
      },
      async confirm(id) {
        return api<Commitment>("POST", `/commitments/${encodeURIComponent(id)}/confirm`);
      },
      async unconfirm(id) {
        return api<Commitment>("POST", `/commitments/${encodeURIComponent(id)}/unconfirm`);
      },
      async cancel(id) {
        return api<Commitment>("POST", `/commitments/${encodeURIComponent(id)}/cancel`);
      },
      async restore(id) {
        return api<Commitment>("POST", `/commitments/${encodeURIComponent(id)}/restore`);
      },
      async archive(id) {
        return api<Commitment>("POST", `/commitments/${encodeURIComponent(id)}/archive`);
      },
    },

    points: {
      async totals(familyId) {
        return api<PointsTotal[]>(
          "GET",
          `/families/${encodeURIComponent(familyId)}/points/totals`,
        );
      },
      async ledger(familyId) {
        return api<PointsEntry[]>(
          "GET",
          `/families/${encodeURIComponent(familyId)}/points/ledger`,
        );
      },
    },

    history: {
      async list(familyId) {
        return api<HistoryItem[]>("GET", `/families/${encodeURIComponent(familyId)}/history`);
      },
    },
  };
}
