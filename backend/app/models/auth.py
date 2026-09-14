"""Auth-related OpenAPI schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    email: str
    name: str


class Session(BaseModel):
    user: User
    activeFamilyId: str | None


class AuthSuccess(BaseModel):
    user: User
    activeFamilyId: str | None
    accessToken: str


class RequestCodeRequest(BaseModel):
    email: str


class RequestCodeResponse(BaseModel):
    devCode: str | None = None


class VerifyCodeRequest(BaseModel):
    email: str
    code: str
