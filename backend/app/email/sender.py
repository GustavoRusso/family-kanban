"""Email sender protocol and Resend / console implementations."""

from __future__ import annotations

import logging
from typing import Protocol

import resend

from app.config import get_email_from, get_login_code_ttl_minutes, get_resend_api_key
from app.errors import AppError

logger = logging.getLogger("app.email.sender")


class EmailSender(Protocol):
    def send_login_code(
        self, email: str, code: str, *, ttl_minutes: int | None = None
    ) -> None: ...


class RecordingEmailSender:
    """Test double that records sends and never hits the network."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, int]] = []

    def send_login_code(
        self, email: str, code: str, *, ttl_minutes: int | None = None
    ) -> None:
        minutes = ttl_minutes if ttl_minutes is not None else get_login_code_ttl_minutes()
        self.sent.append((email, code, minutes))

    def last_code_for(self, email: str) -> str | None:
        normalized = email.strip().lower()
        for sent_email, code, _ttl in reversed(self.sent):
            if sent_email == normalized:
                return code
        return None


class ConsoleEmailSender:
    """Local-dev sender: logs the code to the backend terminal (no network)."""

    def send_login_code(
        self, email: str, code: str, *, ttl_minutes: int | None = None
    ) -> None:
        minutes = ttl_minutes if ttl_minutes is not None else get_login_code_ttl_minutes()
        message = (
            f"EMAIL_DELIVERY=console — login code for {email} is {code} "
            f"(expires in {minutes} minute{'' if minutes == 1 else 's'})"
        )
        logging.getLogger().warning(message)
        logger.warning(message)


class ResendEmailSender:
    def send_login_code(
        self, email: str, code: str, *, ttl_minutes: int | None = None
    ) -> None:
        api_key = get_resend_api_key()
        from_addr = get_email_from()
        if not api_key or not from_addr:
            raise AppError(
                "Email is not configured. Set RESEND_API_KEY and EMAIL_FROM."
            )

        minutes = ttl_minutes if ttl_minutes is not None else get_login_code_ttl_minutes()
        expiry_line = (
            f"It expires in {minutes} minute{'s' if minutes != 1 else ''}, "
            "or when you use it or request a new one."
        )

        resend.api_key = api_key
        try:
            resend.Emails.send(
                {
                    "from": from_addr,
                    "to": [email],
                    "subject": "Your Family Kanban sign-in code",
                    "text": (
                        f"Your Family Kanban sign-in code is {code}.\n\n"
                        f"{expiry_line}\n"
                        "If you did not request this, you can ignore this email."
                    ),
                    "html": (
                        f"<p>Your Family Kanban sign-in code is "
                        f"<strong>{code}</strong>.</p>"
                        f"<p>{expiry_line}</p>"
                        "<p>If you did not request this, you can ignore this email.</p>"
                    ),
                }
            )
        except Exception as exc:  # noqa: BLE001 — surface Resend failures as AppError
            raise AppError(f"Couldn't send the sign-in email: {exc}") from exc
