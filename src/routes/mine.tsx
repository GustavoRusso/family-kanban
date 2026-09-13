import { createFileRoute } from "@tanstack/react-router";
import { useApp } from "@/app/app-provider";
import { Board } from "@/components/board";
import { Guard } from "@/components/guard";

export const Route = createFileRoute("/mine")({
  ssr: false,
  head: () => ({
    meta: [
      { title: "My commitments — Family Kanban" },
      {
        name: "description",
        content: "A focused view of the commitments you are responsible for in your family.",
      },
      { property: "og:title", content: "My commitments — Family Kanban" },
      {
        property: "og:description",
        content: "See only your own cards, from Backlog through Confirmed.",
      },
    ],
  }),
  component: MinePage,
});

function MinePage() {
  return (
    <Guard>
      <MineBoard />
    </Guard>
  );
}

function MineBoard() {
  const { session } = useApp();
  return (
    <Board
      title="My commitments"
      subtitle="Just your cards — keep Doing light and finish what you started."
      onlyUserId={session?.user.id}
    />
  );
}
