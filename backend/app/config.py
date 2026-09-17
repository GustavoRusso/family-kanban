"""Application settings from environment."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load the repository .env for local convenience without overriding values
# supplied by the process environment.
_REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_REPO_ROOT / ".env")

DEFAULT_DATABASE_URL = "sqlite:///./family_kanban.db"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL).strip() or DEFAULT_DATABASE_URL


def get_resend_api_key() -> str:
    return os.getenv("RESEND_API_KEY", "").strip()


def get_email_from() -> str:
    return os.getenv("EMAIL_FROM", "").strip()


def get_login_code_ttl_minutes() -> int:
    raw = os.getenv("LOGIN_CODE_TTL_MINUTES", "5").strip() or "5"
    try:
        minutes = int(raw)
    except ValueError:
        minutes = 5
    return max(1, minutes)


def get_email_delivery() -> str:
    """Outbound login-code channel: 'resend' (default) or 'console' (local only)."""
    raw = os.getenv("EMAIL_DELIVERY", "resend").strip().lower() or "resend"
    if raw == "console":
        return "console"
    return "resend"
