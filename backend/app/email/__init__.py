"""Outbound email: login codes via Resend (or console for local)."""

from app.email.deps import EmailSenderDep, get_email_sender
from app.email.sender import (
    ConsoleEmailSender,
    EmailSender,
    RecordingEmailSender,
    ResendEmailSender,
)

__all__ = [
    "ConsoleEmailSender",
    "EmailSender",
    "EmailSenderDep",
    "RecordingEmailSender",
    "ResendEmailSender",
    "get_email_sender",
]
