"""Application settings from environment."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Shared repo-root .env is the source of truth when present (overrides a stale
# compose-injected value after .env changes without a container rebuild).
_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env", override=True)

DEFAULT_DATABASE_URL = "sqlite:///./family_kanban.db"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL).strip() or DEFAULT_DATABASE_URL
