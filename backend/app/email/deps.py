"""FastAPI dependencies for outbound email."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.email.sender import EmailSender, ResendEmailSender


def get_email_sender() -> EmailSender:
    return ResendEmailSender()


EmailSenderDep = Annotated[EmailSender, Depends(get_email_sender)]
