"""FastAPI dependencies for outbound email."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.config import get_email_delivery
from app.email.sender import ConsoleEmailSender, EmailSender, ResendEmailSender


def get_email_sender() -> EmailSender:
    if get_email_delivery() == "console":
        return ConsoleEmailSender()
    return ResendEmailSender()


EmailSenderDep = Annotated[EmailSender, Depends(get_email_sender)]
