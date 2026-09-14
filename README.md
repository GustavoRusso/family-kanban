# Family Kanban

**Family Kanban** helps a family see and keep the commitments they make to each other on a shared Kanban board.


## Build with Lovable

This project was built with [Lovable](https://lovable.dev).

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/bb2058ca-40a1-4c79-bf7b-738693d5d681).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer the **DevContainer** so Node, Python, and PostgreSQL are ready without host installs.

1. Open this repository in VS Code or Cursor.
2. Reopen in Container (Dev Containers).
3. When the container finishes setup:

```sh
cd frontend
npm run dev
```

The container includes Node 22, Python 3.12, and PostgreSQL (`db` service). Shared config for the DB (and later backend + frontend) lives in [`.env`](.env) (created from [`.env.example`](.env.example) on first setup). Planned layout: `frontend/`, `backend/`, and a shared `openapi.yaml` at the repo root.

### Host-only (frontend)

If you prefer not to use the DevContainer, you need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>/frontend
npm i
npm run dev
```
