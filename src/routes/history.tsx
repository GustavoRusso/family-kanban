import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useApp } from "@/app/app-provider";
import { CommitmentCard } from "@/components/commitment-card";
import { Guard } from "@/components/guard";
import { TYPE_LABELS, services, type HistoryItem } from "@/services";

export const Route = createFileRoute("/history")({
  ssr: false,
  head: () => ({
    meta: [
      { title: "History — Family Kanban" },
      {
        name: "description",
        content:
          "A lightweight record of confirmed, archived and cancelled family commitments, newest first.",
      },
      { property: "og:title", content: "History — Family Kanban" },
      {
        property: "og:description",
        content: "Look back at what the family finished, archived or let go.",
      },
    ],
  }),
  component: HistoryPage,
});

function HistoryPage() {
  return (
    <Guard>
      <HistoryView />
    </Guard>
  );
}

function HistoryView() {
  const { family, commitments } = useApp();
  const [items, setItems] = useState<HistoryItem[]>([]);

  useEffect(() => {
    if (!family) return;
    void services.history.list(family.id).then(setItems);
  }, [family, commitments]);

  const cancelled = commitments.filter((c) => c.status === "cancelled");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold text-foreground">History</h1>
        <p className="text-sm text-muted-foreground">
          Everything the family confirmed, archived or cancelled.
        </p>
      </div>

      {cancelled.length > 0 && (
        <section className="space-y-2">
          <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Cancelled — can be restored
          </h2>
          <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-4">
            {cancelled.map((c) => (
              <CommitmentCard key={c.id} commitment={c} onEdit={() => {}} />
            ))}
          </div>
        </section>
      )}

      <div className="overflow-hidden rounded-2xl border border-border bg-card">
        <table className="w-full text-left text-sm">
          <thead className="bg-secondary/60 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="px-4 py-2.5">Commitment</th>
              <th className="px-4 py-2.5">Type</th>
              <th className="px-4 py-2.5">Responsible</th>
              <th className="px-4 py-2.5">Status</th>
              <th className="px-4 py-2.5">Date</th>
              <th className="px-4 py-2.5 text-right">Points</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.commitmentId} className="border-t border-border/70">
                <td className="px-4 py-2.5 font-medium text-card-foreground">{item.title}</td>
                <td className="px-4 py-2.5 text-muted-foreground">{TYPE_LABELS[item.type]}</td>
                <td className="px-4 py-2.5 text-muted-foreground">{item.responsibleName}</td>
                <td className="px-4 py-2.5 capitalize text-muted-foreground">{item.status}</td>
                <td className="px-4 py-2.5 text-muted-foreground">
                  {new Date(item.outcomeDate).toLocaleDateString()}
                </td>
                <td className="px-4 py-2.5 text-right font-semibold text-primary">
                  {item.points}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  Nothing in history yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
