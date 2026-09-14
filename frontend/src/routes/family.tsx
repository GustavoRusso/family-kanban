import { createFileRoute } from "@tanstack/react-router";
import QRCode from "qrcode";
import { useEffect, useState } from "react";
import { useApp } from "@/app/app-provider";
import { Guard } from "@/components/guard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { services } from "@/services";

export const Route = createFileRoute("/family")({
  ssr: false,
  head: () => ({
    meta: [
      { title: "Your family — Family Kanban" },
      {
        name: "description",
        content:
          "Create a family, invite members with a QR code, and manage who shares your commitment board.",
      },
      { property: "og:title", content: "Your family — Family Kanban" },
      {
        property: "og:description",
        content: "Share a QR code so everyone joins the same family board.",
      },
    ],
  }),
  component: FamilyPage,
});

function FamilyPage() {
  return (
    <Guard needsFamily={false}>
      <FamilyView />
    </Guard>
  );
}

function FamilyView() {
  const { family, families, members, me, session, run } = useApp();
  const [newName, setNewName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [renameValue, setRenameValue] = useState("");
  const [qr, setQr] = useState<string | null>(null);

  useEffect(() => {
    setRenameValue(family?.name ?? "");
    if (!family) {
      setQr(null);
      return;
    }
    const origin = typeof window === "undefined" ? "" : window.location.origin;
    void QRCode.toDataURL(`${origin}/family?join=${family.joinToken}`, {
      width: 240,
      margin: 1,
    }).then(setQr);
  }, [family]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const token = new URLSearchParams(window.location.search).get("join");
    if (token && session) {
      setJoinCode(token);
    }
  }, [session]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold text-foreground">Your family</h1>
        <p className="text-sm text-muted-foreground">
          Create a family or join one by scanning its QR code.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-2xl border border-border bg-card p-5">
          <h2 className="font-display text-lg font-semibold text-card-foreground">
            Create a family
          </h2>
          <div className="mt-3 flex gap-2">
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="The Rivera Family"
            />
            <Button
              onClick={async () => {
                const created = await run(
                  () => services.families.create(newName),
                  "Family created.",
                );
                if (created) setNewName("");
              }}
            >
              Create
            </Button>
          </div>
        </section>

        <section className="rounded-2xl border border-border bg-card p-5">
          <h2 className="font-display text-lg font-semibold text-card-foreground">
            Join a family
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Scan the family's QR code, or type the code it contains.
          </p>
          <div className="mt-3 flex gap-2">
            <Input
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
              placeholder="RIVERA"
            />
            <Button
              variant="secondary"
              onClick={async () => {
                const joined = await run(
                  () => services.families.joinByToken(joinCode),
                  "You're in!",
                );
                if (joined) setJoinCode("");
              }}
            >
              Join
            </Button>
          </div>
        </section>
      </div>

      {families.length > 1 && (
        <section className="rounded-2xl border border-border bg-card p-5">
          <h2 className="font-display text-lg font-semibold text-card-foreground">
            Switch family
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {families.map((f) => (
              <Button
                key={f.id}
                variant={f.id === family?.id ? "default" : "secondary"}
                onClick={() => run(() => services.families.setActive(f.id), `Now on ${f.name}.`)}
              >
                {f.name}
              </Button>
            ))}
          </div>
        </section>
      )}

      {family && (
        <div className="grid gap-4 lg:grid-cols-2">
          <section className="rounded-2xl border border-border bg-card p-5">
            <h2 className="font-display text-lg font-semibold text-card-foreground">
              Invite with a QR code
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              New members sign in with their email first, then scan this code to join{" "}
              {family.name}.
            </p>
            {qr && (
              <img
                src={qr}
                alt={`QR code to join ${family.name}`}
                className="mt-4 rounded-xl border border-border bg-white p-2"
                width={240}
                height={240}
              />
            )}
            <p className="mt-3 text-sm text-muted-foreground">
              Join code: <strong className="text-card-foreground">{family.joinToken}</strong>
            </p>
          </section>

          <section className="rounded-2xl border border-border bg-card p-5">
            <h2 className="font-display text-lg font-semibold text-card-foreground">Members</h2>
            <ul className="mt-3 space-y-2">
              {members.map((m) => (
                <li
                  key={m.userId}
                  className="flex items-center justify-between gap-3 border-t border-border/70 pt-2 text-sm first:border-0 first:pt-0"
                >
                  <div>
                    <p className="font-medium text-card-foreground">{m.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {m.email} · {m.role}
                    </p>
                  </div>
                  {me?.role === "admin" && m.userId !== me.userId && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() =>
                        run(
                          () => services.families.removeMember(family.id, m.userId),
                          `${m.name} removed.`,
                        )
                      }
                    >
                      Remove
                    </Button>
                  )}
                </li>
              ))}
            </ul>

            {me?.role === "admin" && (
              <div className="mt-5 grid gap-1.5">
                <Label htmlFor="rename">Family name</Label>
                <div className="flex gap-2">
                  <Input
                    id="rename"
                    value={renameValue}
                    onChange={(e) => setRenameValue(e.target.value)}
                  />
                  <Button
                    variant="secondary"
                    onClick={() =>
                      run(
                        () => services.families.rename(family.id, renameValue),
                        "Family renamed.",
                      )
                    }
                  >
                    Save
                  </Button>
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
