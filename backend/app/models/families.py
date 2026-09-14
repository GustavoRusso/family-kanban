"""Family-related OpenAPI schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    admin = "admin"
    member = "member"


class Family(BaseModel):
    id: str
    name: str
    joinToken: str


class Member(BaseModel):
    userId: str
    familyId: str
    name: str
    email: str
    role: Role


class CreateFamilyRequest(BaseModel):
    name: str = Field(min_length=1)


class JoinFamilyRequest(BaseModel):
    token: str


class RenameFamilyRequest(BaseModel):
    name: str = Field(min_length=1)
