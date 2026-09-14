import {
  AlarmClock,
  Archive,
  ArrowRight,
  CalendarDays,
  Check,
  Pencil,
  RotateCcw,
  Undo2,
  X,
} from "lucide-react";
import { useApp } from "@/app/app-provider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { services } from "@/services";
import {
  BOARD_COLUMNS,
  COLUMN_LABELS,
  TYPE_LABELS,
  canArchive,
  canCancel,
  canEdit,
  canMove,
  canRestore,
  canUnconfirm,
  isDueToday,
  isPastDue,
  type BoardStatus,
  type Commitment,
} from "@/services";

const TYPE_STYLES: Record<Commitment["type"], string> = {
  promise: "bg-type-promise/15 text-type-promise",
  request: "bg-type-request/15 text-type-request",
  responsibility: "bg-type-responsibility/15 text-type-responsibility",
  consequence: "bg-type-consequence/15 text-type-consequence",
  reward: "bg-type-reward/15 text-type-reward",
};

function formatDate(value: string) {
  return new Date(value).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function CommitmentCard({
  commitment,
  onEdit,
}: {
  commitment: Commitment;
  onEdit: (c: Commitment) => void;
}) {
  const { session, run, memberName } = useApp();
  const userId = session?.user.id ?? "";

  const nextStatus = (() => {
    const index = BOARD_COLUMNS.indexOf(commitment.status as BoardStatus);
    if (index < 0 || index >= BOARD_COLUMNS.length - 1) return null;
    return BOARD_COLUMNS[index + 1];
  })();

  const moveCheck = nextStatus ? canMove(commitment, nextStatus, userId) : { ok: false };
  const editCheck = canEdit(commitment);
  const unconfirmCheck = canUnconfirm(commitment, userId);
  const archiveCheck = canArchive(commitment, userId);
  const cancelCheck = canCancel(commitment, userId);
  const restoreCheck = canRestore(commitment, userId);

  const pastDue = isPastDue(commitment);
  const dueToday = !pastDue && isDueToday(commitment);

  return (
    <article className="rounded-xl border border-border bg-card p-3 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
            TYPE_STYLES[commitment.type],
          )}
        >
          {TYPE_LABELS[commitment.type]}
        </span>
        <span className="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-bold text-primary">
          {commitment.points} pt{commitment.points === 1 ? "" : "s"}
        </span>
      </div>

      <h3 className="mt-2 text-sm font-semibold leading-snug text-card-foreground">
        {commitment.title}
      </h3>
      <p className="mt-1 text-xs text-muted-foreground">{memberName(commitment.responsibleId)}</p>
      {commitment.note && (
        <p className="mt-1.5 text-xs italic text-muted-foreground">{commitment.note}</p>
      )}

      {(commitment.startDate || commitment.dueDate) && (
        <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-muted-foreground">
          {commitment.startDate && (
            <span className="inline-flex items-center gap-1">
              <CalendarDays className="size-3" /> starts {formatDate(commitment.startDate)}
            </span>
          )}
          {commitment.dueDate && (
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-1.5",
                pastDue && "bg-destructive/15 font-semibold text-destructive",
                dueToday && "bg-accent font-semibold text-accent-foreground",
              )}
            >
              <AlarmClock className="size-3" />
              {pastDue ? "past due " : dueToday ? "due today " : "due "}
              {formatDate(commitment.dueDate)}
            </span>
          )}
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-1.5">
        {nextStatus && (
          <Button
            size="sm"
            variant={nextStatus === "confirmed" ? "default" : "secondary"}
            disabled={!moveCheck.ok}
            title={moveCheck.ok ? undefined : moveCheck.reason}
            onClick={() =>
              run(
                () => services.commitments.move(commitment.id, nextStatus),
                nextStatus === "confirmed"
                  ? `Confirmed! ${commitment.points} point${commitment.points === 1 ? "" : "s"} to ${memberName(commitment.responsibleId)}.`
                  : `Moved to ${COLUMN_LABELS[nextStatus]}.`,
              )
            }
          >
            {nextStatus === "confirmed" ? (
              <Check className="size-3.5" />
            ) : (
              <ArrowRight className="size-3.5" />
            )}
            {nextStatus === "confirmed" ? "Confirm" : COLUMN_LABELS[nextStatus]}
          </Button>
        )}

        {commitment.status === "confirmed" && (
          <>
            <Button
              size="sm"
              variant="secondary"
              disabled={!archiveCheck.ok}
              title={archiveCheck.ok ? undefined : archiveCheck.reason}
              onClick={() =>
                run(() => services.commitments.archive(commitment.id), "Archived to history.")
              }
            >
              <Archive className="size-3.5" /> Archive
            </Button>
            <Button
              size="sm"
              variant="ghost"
              disabled={!unconfirmCheck.ok}
              title={unconfirmCheck.ok ? undefined : unconfirmCheck.reason}
              onClick={() =>
                run(
                  () => services.commitments.unconfirm(commitment.id),
                  "Un-confirmed — back to Doing.",
                )
              }
            >
              <Undo2 className="size-3.5" /> Un-confirm
            </Button>
          </>
        )}

        {editCheck.ok && (
          <Button size="sm" variant="ghost" onClick={() => onEdit(commitment)}>
            <Pencil className="size-3.5" /> Edit
          </Button>
        )}

        {commitment.status === "cancelled" ? (
          <Button
            size="sm"
            variant="secondary"
            disabled={!restoreCheck.ok}
            title={restoreCheck.ok ? undefined : restoreCheck.reason}
            onClick={() =>
              run(() => services.commitments.restore(commitment.id), "Restored to Backlog.")
            }
          >
            <RotateCcw className="size-3.5" /> Restore
          </Button>
        ) : (
          cancelCheck.ok && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => run(() => services.commitments.cancel(commitment.id), "Cancelled.")}
            >
              <X className="size-3.5" /> Cancel
            </Button>
          )
        )}
      </div>
    </article>
  );
}
