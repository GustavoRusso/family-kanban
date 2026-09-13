import { useEffect, useState } from "react";
import { useApp } from "@/app/app-provider";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { services } from "@/services";
import { COMMITMENT_TYPES, TYPE_LABELS, type Commitment, type CommitmentType } from "@/services";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editing: Commitment | null;
}

const toInput = (value?: string | null) => (value ? value.slice(0, 10) : "");
const toIso = (value: string) => (value ? new Date(`${value}T12:00:00`).toISOString() : null);

export function CommitmentDialog({ open, onOpenChange, editing }: Props) {
  const { members, family, session, run } = useApp();
  const [title, setTitle] = useState("");
  const [type, setType] = useState<CommitmentType>("promise");
  const [responsibleId, setResponsibleId] = useState("");
  const [points, setPoints] = useState("1");
  const [startDate, setStartDate] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [note, setNote] = useState("");

  useEffect(() => {
    if (!open) return;
    setTitle(editing?.title ?? "");
    setType(editing?.type ?? "promise");
    setResponsibleId(editing?.responsibleId ?? session?.user.id ?? members[0]?.userId ?? "");
    setPoints(String(editing?.points ?? 1));
    setStartDate(toInput(editing?.startDate));
    setDueDate(toInput(editing?.dueDate));
    setNote(editing?.note ?? "");
  }, [open, editing, members, session]);

  async function submit() {
    const payload = {
      title,
      type,
      responsibleId,
      points: Number(points),
      startDate: toIso(startDate),
      dueDate: toIso(dueDate),
      note: note.trim() || null,
    };
    const result = editing
      ? await run(() => services.commitments.update(editing.id, payload), "Commitment updated.")
      : await run(
          () => services.commitments.create(family!.id, payload),
          "Added to Backlog.",
        );
    if (result) onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-display">
            {editing ? "Edit commitment" : "New commitment"}
          </DialogTitle>
          <DialogDescription>
            Commitments start in Backlog and can be edited while in Backlog or Ready.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4">
          <div className="grid gap-1.5">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Walk the dog after school"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="grid gap-1.5">
              <Label>Type</Label>
              <Select value={type} onValueChange={(v) => setType(v as CommitmentType)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {COMMITMENT_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {TYPE_LABELS[t]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-1.5">
              <Label>Responsible</Label>
              <Select value={responsibleId} onValueChange={setResponsibleId}>
                <SelectTrigger>
                  <SelectValue placeholder="Pick a family member" />
                </SelectTrigger>
                <SelectContent>
                  {members.map((m) => (
                    <SelectItem key={m.userId} value={m.userId}>
                      {m.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="grid gap-1.5">
              <Label htmlFor="points">Points</Label>
              <Input
                id="points"
                type="number"
                min={1}
                step={1}
                value={points}
                onChange={(e) => setPoints(e.target.value)}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="start">Start date</Label>
              <Input
                id="start"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="due">Due date</Label>
              <Input
                id="due"
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </div>
          </div>

          <div className="grid gap-1.5">
            <Label htmlFor="note">Note</Label>
            <Textarea
              id="note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Why this matters, or any helpful context"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={submit}>{editing ? "Save changes" : "Add to Backlog"}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
