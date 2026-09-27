from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _clean_name(value: str) -> str:
    cleaned = " ".join(value.split())
    if not cleaned:
        raise ValueError("Display name must not be empty")
    return cleaned


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)
    display_name: str = Field(min_length=1, max_length=80)

    _name = field_validator("display_name")(_clean_name)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=16, max_length=128)
    new_password: str = Field(min_length=1, max_length=256)


class EmailVerifyRequest(BaseModel):
    token: str = Field(min_length=16, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=1, max_length=256)


class UpdateProfileRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)

    _name = field_validator("display_name")(_clean_name)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str
    email_verified: bool
    created_at: datetime


class CsrfOut(BaseModel):
    csrf_token: str


class AcceptedOut(BaseModel):
    status: str
    message: str
