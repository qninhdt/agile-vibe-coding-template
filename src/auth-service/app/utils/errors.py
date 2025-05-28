"""Error classes for Auth Service."""

from typing import Optional, Dict, Any


class AuthError(Exception):
    """Base authentication error."""

    def __init__(
        self, code: str, message: str, details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class ValidationError(AuthError):
    """Validation error for request data."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__("VALIDATION_FAILED", message, details)


class ConflictError(AuthError):
    """Conflict error for duplicate resources."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__("USER_ALREADY_EXISTS", message)


class InvalidCredentialsError(AuthError):
    """Invalid credentials error."""

    def __init__(self, message: str = "Invalid email/username or password"):
        super().__init__("INVALID_CREDENTIALS", message)


class AccountInactiveError(AuthError):
    """Account inactive error."""

    def __init__(self, message: str = "Account is inactive or suspended"):
        super().__init__("ACCOUNT_INACTIVE", message)


class RateLimitError(AuthError):
    """Rate limit exceeded error."""

    def __init__(self, message: str = "Too many requests. Please try again later"):
        super().__init__("RATE_LIMIT_EXCEEDED", message)


class InvalidTokenError(AuthError):
    """Invalid token error."""

    def __init__(self, message: str = "Token is invalid or expired"):
        super().__init__("INVALID_TOKEN", message)


class InvalidRefreshTokenError(AuthError):
    """Invalid refresh token error."""

    def __init__(self, message: str = "Refresh token is invalid or expired"):
        super().__init__("INVALID_REFRESH_TOKEN", message)
