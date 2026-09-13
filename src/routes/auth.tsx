import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useApp } from "@/app/app-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { services } from "@/services";

export const Route = createFileRoute("/auth")({
  ssr: false,
  head: () => ({
    meta: [
      { title: "Sign in — Family Kanban" },
      {
        name: "description",
        content:
          "Sign in to Family Kanban with your email and a one-time code. No passwords, no setup.",
      },
      { property: "og:title", content: "Sign in — Family Kanban" },
      {
        property: "og:description",
        content: "Passwordless sign-in for your family's shared commitment board.",
      },
    ],
  }),
  component: AuthPage,
});

function AuthPage() {
  const { status, refresh } = useApp();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [sentCode, setSentCode] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (status === "ready") void navigate({ to: "/", replace: true });
    else if (status === "no-family") void navigate({ to: "/family", replace: true });
  }, [status, navigate]);

  async function sendCode() {
    setBusy(true);
    try {
      const { devCode } = await services.auth.requestCode(email);
      setSentCode(devCode);
      toast.success("We sent you a one-time code.");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Couldn't send the code.");
    } finally {
      setBusy(false);
    }
  }

  async function verify() {
    setBusy(true);
    try {
      const session = await services.auth.verifyCode(email, code);
      await refresh();
      toast.success(`Welcome, ${session.user.name}!`);
      void navigate({ to: session.activeFamilyId ? "/" : "/family", replace: true });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "That code didn't work.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-md rounded-3xl border border-border bg-card p-8 shadow-sm">
        <h1 className="font-display text-3xl font-semibold text-foreground">Family Kanban</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          See and keep the promises, requests and responsibilities your family shares. Enter your
          email and we'll send a one-time code — new emails get an account automatically.
        </p>

        <div className="mt-6 grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              disabled={!!sentCode}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>

          {sentCode ? (
            <>
              <div className="grid gap-1.5">
                <Label htmlFor="code">One-time code</Label>
                <Input
                  id="code"
                  inputMode="numeric"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="6-digit code"
                />
                <p className="text-xs text-muted-foreground">
                  Demo mode — your code is <strong>{sentCode}</strong>.
                </p>
              </div>
              <Button onClick={verify} disabled={busy || code.length < 6}>
                Sign in
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setSentCode(null);
                  setCode("");
                }}
              >
                Use a different email
              </Button>
            </>
          ) : (
            <Button onClick={sendCode} disabled={busy || !email}>
              Send my code
            </Button>
          )}
        </div>

        <p className="mt-6 text-xs text-muted-foreground">
          Try the demo family with <strong>maya@example.com</strong>, <strong>leo@example.com</strong>{" "}
          or <strong>nina@example.com</strong>.
        </p>
      </div>
    </div>
  );
}
