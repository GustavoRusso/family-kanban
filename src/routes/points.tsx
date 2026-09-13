import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useApp } from "@/app/app-provider";
import { Guard } from "@/components/guard";
import { services, type PointsEntry, type PointsTotal } from "@/services";

export const Route = createFileRoute("/points")({
  ssr: false,
  head: () => ({
    meta: [
      { title: "Points — Family Kanban" },
      {
        name: "description",
        content:
          "Every family member's points total and the confirmed commitments behind them — a celebration, not a ranking.",
      },
      { property: "og:title", content: "Points — Family Kanban" },
      {
        property: "og:description",
        content: "Totals and per-commitment points earned, newest first.",
      },
    ],
  }),
  component: PointsPage,
});

function PointsPage() {
  return (
    <Guard>
      <PointsView />
    </Guard>
  );
}

function PointsView() {
  const { family, commitments } = useApp();
  const [totals, setTotals] = useState<PointsTotal[]>([]);
  const [ledger, setLedger] = useState<PointsEntry[]>([]);

  useEffect(() => {
    if (!family) return;
    void services.points.totals(family.id).then(setTotals);
    void services.points.ledger(family.id).then(setLedger);
  }, [family, commitments]);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="font-display text-3xl font-semibold text-foreground">Points</h1>
        <p className="text-sm text-muted-foreground">
          Each total stands on its own — this is a shared celebration, not a ranking.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {totals.map((person) => {
          const entries = ledger.filter((e) => e.userId === person.userId);
          return (
            <section key={person.userId} className="rounded-2xl border border-border bg-card p-4">
              <header className="flex items-baseline justify-between">
                <h2 className="font-display text-lg font-semibold text-card-foreground">
                  {person.name}
                </h2>
                <span className="font-display text-3xl font-bold text-primary">
                  {person.total}
                </span>
              </header>
              <ul className="mt-3 space-y-2">
                {entries.map((entry) => (
                  <li
                    key={entry.commitmentId}
                    className="flex items-start justify-between gap-3 border-t border-border/70 pt-2 text-sm"
                  >
                    <div>
                      <p className="font-medium text-card-foreground">{entry.title}</p>
                      <p className="text-xs text-muted-foreground">
                        confirmed {new Date(entry.confirmedAt).toLocaleDateString()}
                      </p>
                    </div>
                    <span className="shrink-0 font-semibold text-primary">+{entry.points}</span>
                  </li>
                ))}
                {entries.length === 0 && (
                  <li className="pt-2 text-sm text-muted-foreground">
                    No confirmed commitments yet.
                  </li>
                )}
              </ul>
            </section>
          );
        })}
      </div>
    </div>
  );
}
