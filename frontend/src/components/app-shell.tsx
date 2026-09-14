import { Link, useNavigate, useRouterState } from "@tanstack/react-router";
import { LogOut, Users } from "lucide-react";
import type { ReactNode } from "react";
import { useApp } from "@/app/app-provider";
import { Button } from "@/components/ui/button";
import { services } from "@/services";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/", label: "Board" },
  { to: "/mine", label: "My commitments" },
  { to: "/points", label: "Points" },
  { to: "/history", label: "History" },
  { to: "/family", label: "Family" },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const { family, me, refresh } = useApp();
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  async function signOut() {
    await services.auth.signOut();
    await refresh();
    void navigate({ to: "/auth" });
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border/70 bg-card/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-4 px-4 py-3">
          <Link to="/" className="font-display text-xl font-semibold text-foreground">
            Family Kanban
          </Link>
          {family && (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">
              <Users className="size-3.5" /> {family.name}
            </span>
          )}
          <nav className="flex flex-1 flex-wrap items-center gap-1">
            {NAV.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  "rounded-full px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground",
                  pathname === item.to && "bg-primary text-primary-foreground hover:bg-primary",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          {me && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">{me.name}</span>
              <Button variant="ghost" size="icon" aria-label="Sign out" onClick={signOut}>
                <LogOut className="size-4" />
              </Button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
    </div>
  );
}
