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
3. When the container finishes setup, use Make from the repo root:

```sh
make install   # first time, or after dependency changes
make dev       # backend + frontend together (Ctrl+C stops both)
```

Or start them separately:

```sh
make frontend  # http://localhost:5173
make backend   # http://localhost:8000 — docs at /docs
```

Other useful targets: `make test`, `make test-frontend`, `make test-backend`, `make lint`. Run `make help` for the full list.

In dev, Vite proxies `/api` to `http://localhost:8000`, so the UI can call same-origin `/api/v1` without CORS. Optional `VITE_API_BASE_URL` in [`.env.example`](.env.example) overrides that base (empty = same-origin).

Requires [uv](https://docs.astral.sh/uv/) on `PATH`. In the DevContainer, `post-create` installs uv and runs `uv sync` when `backend/pyproject.toml` exists. The API persists with SQLAlchemy; `DATABASE_URL` in [`.env`](.env) selects the database (SQLite by default; Postgres later). Contract: [`openapi.yaml`](openapi.yaml).

The container includes Node 22, Python 3.12, and a PostgreSQL (`db`) service for when you switch `DATABASE_URL`. Shared config lives in [`.env`](.env) (from [`.env.example`](.env.example) on first setup). Layout: `frontend/`, `backend/`, and `openapi.yaml` at the repo root.

### Git over SSH (agent forwarding)

Keep `origin` as `git@github.com:...`. The Dev Container forwards your **WSL** `ssh-agent` automatically — do not copy private keys into the container.

In a **WSL** terminal (not inside the container):

```sh
# once per login / add to ~/.bash_profile or ~/.zprofile so it persists
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519   # or your GitHub key path
ssh-add -l                  # must list the key
```

Then rebuild or reopen the Dev Container so Cursor picks up `SSH_AUTH_SOCK`. Inside the container, `ssh-add -l` should show the same key, and `git push -u origin main` should work.

If the agent still is not forwarded, open the repo via **WSL** (not a Windows path) so Cursor uses the WSL agent instead of Windows OpenSSH.

### Host-only (frontend)

If you prefer not to use the DevContainer, you need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>/frontend
npm i
npm run dev
```

With Make and dependencies already installed: `make frontend` from the repo root.