# Family Kanban

**Family Kanban** helps a family see and keep the commitments they make to each other on a shared Kanban board.

## Development

Prefer the **DevContainer** so Node and Python are ready without host installs. Local development uses the SQLite default and the Alembic migration contract for schema changes.

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

Requires [uv](https://docs.astral.sh/uv/) on `PATH`. In the DevContainer, `post-create` installs uv and runs `uv sync` when `backend/pyproject.toml` exists. The API persists with SQLAlchemy and Alembic; `DATABASE_URL` in [`.env`](.env) selects the database (SQLite by default for local development; production uses PostgreSQL later). Contract: [`openapi.yaml`](openapi.yaml).

Sign-in codes are emailed with [Resend](https://resend.com). Set `RESEND_API_KEY` and `EMAIL_FROM` in [`.env`](.env) (see [`.env.example`](.env.example)). Full walkthrough: [`_docs/resend-setup.md`](_docs/resend-setup.md). For local work without Resend, set `EMAIL_DELIVERY=console` and read the code from the backend log (the API never returns it). Codes expire after 5 minutes by default (`LOGIN_CODE_TTL_MINUTES`).

The container includes Node 22 and Python 3.12. Shared config lives in [`.env`](.env) (from [`.env.example`](.env.example) on first setup). Layout: `frontend/`, `backend/`, and `openapi.yaml` at the repo root.

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
