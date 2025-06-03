"""Pydantic schemas for request/response validation."""

import re
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, Field
from app.config import config


class RegisterRequest(BaseModel):
    """User registration request schema."""

    email: EmailStr = Field(..., max_length=255)
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format and reserved words."""
        # Check alphanumeric and underscore only
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username must contain only alphanumeric characters and underscores"
            )

        # Check reserved words
        reserved_words = config.account.username.reserved_words
        if v.lower() in [word.lower() for word in reserved_words]:
            raise ValueError("Username is reserved and cannot be used")

        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")

        return v


class LoginRequest(BaseModel):
    """User login request schema."""

    identifier: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str = Field(..., min_length=1)


class LogoutRequest(BaseModel):
    """Logout request schema."""

    refresh_token: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """User response schema."""

    id: str
    email: str
    username: str
    created_at: Optional[str] = None
    email_verified: bool


class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


class LoginResponse(BaseModel):
    """Login response schema."""

    user: UserResponse
    tokens: TokenResponse


class ErrorDetail(BaseModel):
    """Error detail schema."""

    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: ErrorDetail


class SuccessResponse(BaseModel):
    """Success response schema."""

    data: dict
