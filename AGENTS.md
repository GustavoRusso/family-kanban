# Agent operating instructions

This file is the single entry point for every coding agent.

Humans use [README.md](README.md) for a short product introduction.

Product specification: [\_docs/plan.md](_docs/plan.md).

## Development environments

Assume the **DevContainer** (see [`.devcontainer/`](.devcontainer/)) for agent coding: Node 22, Python 3.12, and the lightweight `compose.devcontainer.yml` workspace. Use `make dev` for reload-based development; its default database is SQLite through `DATABASE_URL`.

Humans can run the stable local environment with the default `compose.yaml`. It builds the API and frontend, runs PostgreSQL and migrations, and keeps data in a named volume. Use `just local-up`, `just local-down`, and `just local-reset`; set `LOCAL_PROJECT`, `LOCAL_API_PORT`, and `LOCAL_FRONTEND_PORT` per checkout so branches do not share data or host ports.

Layout:

- `frontend/` — web app
- `backend/` — Python API (FastAPI + SQLAlchemy)
- `openapi.yaml` — shared OpenAPI contract between front and back

Sign-in codes are emailed with Resend (`RESEND_API_KEY`, `EMAIL_FROM`). Setup: [`_docs/resend-setup.md`](_docs/resend-setup.md).

## Git renames

When you rename or move a tracked file, always use `git mv <old> <new>` (not a plain filesystem rename or delete+add). That keeps Git history linked to the new path. After `git mv`, update all references to the old path in the same change.

## Architecture

Centralize every backend call in the frontend services layer (`frontend/src/services/`). That layer talks to the real API over HTTP and must stay aligned with `openapi.yaml`.

On the backend, persist through `SqlAlchemyStore` (no in-memory mock store). Keep domain rules in sync between `frontend/src/services/rules.ts` and `backend/app/rules.py`. The stable local Compose environment is for human QA and integration checks; future CI and deployment Compose files may reuse its service topology but must keep environment-specific data, secrets, ports, and lifecycle separate.

Add tests.

For backend, use uv for dependency management. Useful commands:

```sh
cd backend
uv sync --group dev
uv add <PACKAGE-NAME>
uv run pytest
uv run uvicorn app.main:app --reload --port 8000
```
