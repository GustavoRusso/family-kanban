import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { toast } from "sonner";
import { services } from "@/services";
import type { Commitment, Family, Member, Session } from "@/services";

type Status = "loading" | "signed-out" | "no-family" | "ready";

interface AppValue {
  status: Status;
  session: Session | null;
  family: Family | null;
  families: Family[];
  members: Member[];
  commitments: Commitment[];
  me: Member | null;
  refresh: () => Promise<void>;
  run: <T>(fn: () => Promise<T>, successMessage?: string) => Promise<T | null>;
  memberName: (userId: string) => string;
}

const AppContext = createContext<AppValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [families, setFamilies] = useState<Family[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const current = await services.auth.currentSession();
    setSession(current);
    if (!current) {
      setFamilies([]);
      setMembers([]);
      setCommitments([]);
      setLoading(false);
      return;
    }
    const mine = await services.families.listMine();
    setFamilies(mine);
    if (current.activeFamilyId) {
      const [m, c] = await Promise.all([
        services.families.members(current.activeFamilyId),
        services.commitments.list(current.activeFamilyId),
      ]);
      setMembers(m);
      setCommitments(c);
    } else {
      setMembers([]);
      setCommitments([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const run = useCallback(
    async <T,>(fn: () => Promise<T>, successMessage?: string) => {
      try {
        const result = await fn();
        await refresh();
        if (successMessage) toast.success(successMessage);
        return result;
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "Something went wrong.");
        return null;
      }
    },
    [refresh],
  );

  const value = useMemo<AppValue>(() => {
    const family = families.find((f) => f.id === session?.activeFamilyId) ?? null;
    const status: Status = loading
      ? "loading"
      : !session
        ? "signed-out"
        : !family
          ? "no-family"
          : "ready";
    return {
      status,
      session,
      family,
      families,
      members,
      commitments,
      me: members.find((m) => m.userId === session?.user.id) ?? null,
      refresh,
      run,
      memberName: (userId: string) =>
        members.find((m) => m.userId === userId)?.name ?? "Someone",
    };
  }, [families, session, members, commitments, loading, refresh, run]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppValue {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside AppProvider");
  return ctx;
}
