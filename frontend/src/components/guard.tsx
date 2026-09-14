import { useNavigate } from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";
import { useApp } from "@/app/app-provider";
import { AppShell } from "@/components/app-shell";

/** Client-side gate: signed-out people go to sign-in, family-less people to the family page. */
export function Guard({ children, needsFamily = true }: { children: ReactNode; needsFamily?: boolean }) {
  const { status } = useApp();
  const navigate = useNavigate();

  useEffect(() => {
    if (status === "signed-out") void navigate({ to: "/auth", replace: true });
    else if (status === "no-family" && needsFamily) void navigate({ to: "/family", replace: true });
  }, [status, needsFamily, navigate]);

  if (status === "loading" || status === "signed-out" || (status === "no-family" && needsFamily)) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-muted-foreground">
        Loading your family board…
      </div>
    );
  }

  return <AppShell>{children}</AppShell>;
}
