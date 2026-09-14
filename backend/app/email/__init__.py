"""Outbound email: login codes via Resend."""

from app.email.deps import EmailSenderDep, get_email_sender
from app.email.sender import EmailSender, RecordingEmailSender, ResendEmailSender

__all__ = [
    "EmailSender",
    "EmailSenderDep",
    "RecordingEmailSender",
    "ResendEmailSender",
    "get_email_sender",
]
