import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import PASSWORD_RE

PHONE_RE = re.compile(r"^\+?[0-9]{9,15}$")


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = None
    district: str | None = Field(default=None, max_length=40)
    role: Literal["buyer", "seller"] = "buyer"  # admin can never be self-registered
    business_name: str | None = Field(default=None, min_length=2, max_length=120)

    @field_validator("password")
    @classmethod
    def strong(cls, v: str) -> str:
        if not PASSWORD_RE.match(v):
            raise ValueError("Password needs at least 10 characters with letters and digits")
        return v

    @field_validator("phone")
    @classmethod
    def phone_ok(cls, v):
        if v is None or v == "":
            return None
        v = v.replace(" ", "").replace("-", "")
        if not PHONE_RE.match(v):
            raise ValueError("Phone must be 9-15 digits, optional leading +")
        return v

    @field_validator("full_name")
    @classmethod
    def strip(cls, v: str) -> str:
        return v.strip()


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshIn(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=200)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str
    phone: str | None
    district: str | None
    role: str
    is_active: bool
    email_verified_at: datetime | None = None


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("password")
    @classmethod
    def strong(cls, v: str) -> str:
        if not PASSWORD_RE.match(v):
            raise ValueError("Password needs at least 10 characters with letters and digits")
        return v


class TokenIn(BaseModel):
    token: str = Field(min_length=20, max_length=200)
