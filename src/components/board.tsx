import { Plus } from "lucide-react";
import { useMemo, useState } from "react";
import { useApp } from "@/app/app-provider";
import { CommitmentCard } from "@/components/commitment-card";
import { CommitmentDialog } from "@/components/commitment-dialog";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  BOARD_COLUMNS,
  COLUMN_LABELS,
  COMMITMENT_TYPES,
  TYPE_LABELS,
  WIP_LIMIT_DOING,
  isOnBoard,
  isPastDue,
  wipReminder,
  type BoardStatus,
  type Commitment,
  type CommitmentType,
} from "@/services";

interface Props {
  title: string;
  subtitle: string;
  /** Restrict the board to one person's commitments (My commitments view). */
  onlyUserId?: string | undefined;
}

export function Board({ title, subtitle, onlyUserId }: Props) {
  const { commitments, members, memberName } = useApp();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<Commitment | null>(null);
  const [memberFilter, setMemberFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [dueFilter, setDueFilter] = useState("all");
  const [swimlanes, setSwimlanes] = useState(false);

  const visible = useMemo(() => {
    return commitments.filter((c) => {
      if (!isOnBoard(c)) return false;
      if (onlyUserId && c.responsibleId !== onlyUserId) return false;
      if (memberFilter !== "all" && c.responsibleId !== memberFilter) return false;
      if (typeFilter !== "all" && c.type !== typeFilter) return false;
      if (dueFilter === "past-due" && !isPastDue(c)) return false;
      if (dueFilter === "has-due" && !c.dueDate) return false;
      return true;
    });
  }, [commitments, onlyUserId, memberFilter, typeFilter, dueFilter]);

  const reminders = members
    .map((m) => wipReminder(commitments, m.userId, m.name))
    .filter(Boolean) as string[];

  function openNew() {
    setEditing(null);
    setDialogOpen(true);
  }

  function openEdit(c: Commitment) {
    setEditing(c);
    setDialogOpen(true);
  }

  const lanes: Array<{ key: string; label: string | null; items: Commitment[] }> = swimlanes
    ? COMMITMENT_TYPES.map((t) => ({
        key: t,
        label: TYPE_LABELS[t],
        items: visible.filter((c) => c.type === (t as CommitmentType)),
      })).filter((lane) => lane.items.length > 0)
    : [{ key: "all", label: null, items: visible }];

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-semibold text-foreground">{title}</h1>
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        </div>
        <Button onClick={openNew}>
          <Plus className="size-4" /> New commitment
        </Button>
      </div>

      {reminders.map((reminder) => (
        <div
          key={reminder}
          className="rounded-xl border border-accent bg-accent/60 px-4 py-2.5 text-sm text-accent-foreground"
        >
          {reminder} (suggested limit: {WIP_LIMIT_DOING} in Doing)
        </div>
      ))}

      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-border bg-card px-4 py-3">
        {!onlyUserId && (
          <Select value={memberFilter} onValueChange={setMemberFilter}>
            <SelectTrigger className="w-44">
              <SelectValue placeholder="Everyone" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Everyone</SelectItem>
              {members.map((m) => (
                <SelectItem key={m.userId} value={m.userId}>
                  {m.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-44">
            <SelectValue placeholder="All types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All types</SelectItem>
            {COMMITMENT_TYPES.map((t) => (
              <SelectItem key={t} value={t}>
                {TYPE_LABELS[t]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={dueFilter} onValueChange={setDueFilter}>
          <SelectTrigger className="w-44">
            <SelectValue placeholder="Any date" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Any date</SelectItem>
            <SelectItem value="has-due">Has a due date</SelectItem>
            <SelectItem value="past-due">Past due</SelectItem>
          </SelectContent>
        </Select>
        <div className="flex items-center gap-2">
          <Switch id="swimlanes" checked={swimlanes} onCheckedChange={setSwimlanes} />
          <Label htmlFor="swimlanes" className="text-sm text-muted-foreground">
            Swimlanes by type
          </Label>
        </div>
      </div>

      <div className="space-y-6">
        {lanes.map((lane) => (
          <section key={lane.key} className="space-y-2">
            {lane.label && (
              <h2 className="font-display text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                {lane.label}
              </h2>
            )}
            <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-5">
              {BOARD_COLUMNS.map((column) => (
                <Column
                  key={column}
                  column={column}
                  items={lane.items.filter((c) => c.status === column)}
                  onEdit={openEdit}
                  memberName={memberName}
                />
              ))}
            </div>
          </section>
        ))}
        {visible.length === 0 && (
          <p className="rounded-xl border border-dashed border-border px-4 py-10 text-center text-sm text-muted-foreground">
            No commitments match this view yet.
          </p>
        )}
      </div>

      <CommitmentDialog open={dialogOpen} onOpenChange={setDialogOpen} editing={editing} />
    </div>
  );
}

function Column({
  column,
  items,
  onEdit,
}: {
  column: BoardStatus;
  items: Commitment[];
  onEdit: (c: Commitment) => void;
  memberName: (id: string) => string;
}) {
  return (
    <div className="rounded-2xl bg-secondary/60 p-3">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-foreground">
          {COLUMN_LABELS[column]}
        </h3>
        <span className="rounded-full bg-card px-2 py-0.5 text-xs text-muted-foreground">
          {items.length}
        </span>
      </div>
      <div className="space-y-2">
        {items.map((c) => (
          <CommitmentCard key={c.id} commitment={c} onEdit={onEdit} />
        ))}
        {items.length === 0 && (
          <p className="px-1 py-3 text-xs text-muted-foreground">Nothing here.</p>
        )}
      </div>
    </div>
  );
}
