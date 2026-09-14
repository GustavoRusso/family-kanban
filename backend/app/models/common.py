"""Shared OpenAPI enums and error body."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    message: str = Field(description="Human-readable reason suitable for UI toasts")
