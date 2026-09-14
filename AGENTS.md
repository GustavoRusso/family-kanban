# Agent operating instructions

This file is the single entry point for every coding agent.

Humans use [README.md](README.md) for a short product introduction.

Product specification: [\_docs/plan.md](_docs/plan.md).

## Development environment

Assume the **DevContainer** (see [`.devcontainer/`](.devcontainer/)): Node 22, Python 3.12, and SQLAlchemy via `DATABASE_URL` (SQLite by default; Postgres `db` compose service available for later). Shared env for DB, backend, and frontend lives in `.env` (from `.env.example`).

Planned layout:

- `frontend/` — web app
- `backend/` — Python API (SQLAlchemy)
- `openapi.yaml` — shared OpenAPI contract between front and back

## Git renames

When you rename or move a tracked file, always use `git mv <old> <new>` (not a plain filesystem rename or delete+add). That keeps Git history linked to the new path. After `git mv`, update all references to the old path in the same change.

## Architecture

Centralize every backend call in one services layer, and create a mock implementation of it so the whole app runs without a real backend. When the real API exists, the services layer should target the OpenAPI contract in `openapi.yaml`.

Add tests.

For backend, use uv for dependency management. Useful commands:

```sh
cd backend
uv sync --group dev
uv add <PACKAGE-NAME>
uv run pytest
uv run uvicorn app.main:app --reload --port 8000
```
