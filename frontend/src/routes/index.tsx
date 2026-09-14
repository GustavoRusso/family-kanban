import { createFileRoute } from "@tanstack/react-router";
import { Board } from "@/components/board";
import { Guard } from "@/components/guard";

export const Route = createFileRoute("/")({
  ssr: false,
  head: () => ({
    meta: [
      { title: "Family Board — Family Kanban" },
      {
        name: "description",
        content:
          "A shared Kanban board where your family sees and keeps its promises, requests, responsibilities, consequences and rewards.",
      },
      { property: "og:title", content: "Family Board — Family Kanban" },
      {
        property: "og:description",
        content: "Pull work, respect WIP limits and celebrate points together as a family.",
      },
    ],
  }),
  component: BoardPage,
});

function BoardPage() {
  return (
    <Guard>
      <Board
        title="Family board"
        subtitle="Everything the family has agreed on — pull a card into Ready when you're set to start."
      />
    </Guard>
  );
}
