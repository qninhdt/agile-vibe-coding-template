"""Authentication service with business logic."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
import jwt

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.utils.errors import (
    ValidationError,
    ConflictError,
    InvalidCredentialsError,
    AccountInactiveError,
    InvalidRefreshTokenError,
)
from app.schemas import RegisterRequest, LoginRequest
from app.config import config
from app.services.rate_limiter import RateLimiter
from app.utils.auth import JWTManager, PasswordManager


logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for user management and JWT operations."""

    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        rate_limiter: RateLimiter,
        jwt_manager: JWTManager,
        password_manager: PasswordManager,
    ):
        self.user_repo = user_repo
        self.refresh_token_repo = refresh_token_repo
        self.rate_limiter = rate_limiter
        self.jwt_manager = jwt_manager
        self.password_manager = password_manager

    def register_user(self, request: RegisterRequest) -> Dict[str, Any]:
        """Register a new user."""
        # Validate password confirmation
        if request.password != request.confirm_password:
            raise ValidationError(
                "Password confirmation does not match",
                {"confirm_password": "Passwords do not match"},
            )

        # Check password complexity (already validated by Pydantic, but double-check)
        if (
            request.username.lower() in request.password.lower()
            or request.email.split("@")[0].lower() in request.password.lower()
        ):
            raise ValidationError("Password cannot contain username or email")

        # Hash password
        password_hash = self.password_manager.hash_password(request.password)

        # Create user
        user = self.user_repo.create_user(
            email=request.email, username=request.username, password_hash=password_hash
        )

        logger.info(f"User registered successfully: {user.email}")

        # Create tokens
        tokens = self.create_tokens(user)

        return {"user": user.to_public_dict(), "tokens": tokens}

    def login_user(
        self, request: LoginRequest, ip_address: str, device_info: Optional[str] = None
    ) -> Dict[str, Any]:
        """Authenticate user and return tokens."""
        try:
            # Check rate limits first
            self.rate_limiter.check_rate_limit(ip_address, request.identifier)

            # Find user by identifier
            user = self.user_repo.get_user_by_identifier(request.identifier)

            if not user:
                # Perform dummy bcrypt to prevent timing attacks

                # TODO: Try to understand this line and uncomment it
                # password_manager.dummy_verify()

                # Record failed attempt
                self.rate_limiter.record_attempt(ip_address, request.identifier)
                raise InvalidCredentialsError()

            # Check if account is active
            if not user.is_active:
                self.rate_limiter.record_attempt(
                    ip_address, request.identifier, str(user.id)
                )
                raise AccountInactiveError()

            # Verify password
            if not self.password_manager.verify_password(
                request.password, user.password_hash
            ):
                # Record failed attempt
                self.rate_limiter.record_attempt(
                    ip_address, request.identifier, str(user.id)
                )
                raise InvalidCredentialsError()

            # Clear rate limits on successful login
            self.rate_limiter.clear_user_rate_limits(str(user.id))

            # Generate tokens
            tokens = self.create_tokens(user)

            # Store refresh token hash
            token_hash = self.jwt_manager.hash_token(tokens["refresh_token"])
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=self.jwt_manager.refresh_token_ttl
            )

            self.refresh_token_repo.create_refresh_token(
                str(user.id), token_hash, expires_at, device_info
            )

            # Limit user sessions
            max_sessions = config.get("login.session.max_sessions_per_user", 10)
            revoked_count = self.refresh_token_repo.limit_user_sessions(
                str(user.id), max_sessions
            )

            if revoked_count > 0:
                logger.info(f"Revoked {revoked_count} sessions for user: {user.email}")

            logger.info(
                f"User logged in successfully: username={user.username}, ip_address={ip_address}, device_info={device_info}"
            )

            return {
                "user": user.to_public_dict(),
                "tokens": tokens,
            }

        except Exception as e:
            if not isinstance(e, (InvalidCredentialsError, AccountInactiveError)):
                # Record attempt for unexpected errors too
                self.rate_limiter.record_attempt(ip_address, request.identifier)
            raise

    def create_tokens(self, user: User) -> Dict[str, Any]:
        """Create access and refresh tokens."""
        access_token = self.jwt_manager.generate_access_token(
            str(user.id), user.username, user.email
        )
        refresh_token = self.jwt_manager.generate_refresh_token(str(user.id))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": self.jwt_manager.access_token_ttl * 60,
        }

    def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access and refresh tokens."""
        try:
            # Validate refresh token
            payload = self.jwt_manager.validate_token(refresh_token, "refresh")
            user_id = payload["sub"]

            # Check if token exists in database and is valid
            token_hash = self.jwt_manager.hash_token(refresh_token)
            stored_token = self.refresh_token_repo.get_refresh_token_by_hash(token_hash)

            if not stored_token or not stored_token.is_valid():
                raise InvalidRefreshTokenError()

            # Get user
            user = self.user_repo.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise InvalidRefreshTokenError("User account is inactive")

            # Revoke old refresh token
            self.refresh_token_repo.revoke_refresh_token(token_hash)

            # Generate new tokens
            new_access_token = self.jwt_manager.generate_access_token(
                str(user.id), user.username, user.email
            )
            new_refresh_token = self.jwt_manager.generate_refresh_token(str(user.id))

            # Store new refresh token
            new_token_hash = self.jwt_manager.hash_token(new_refresh_token)
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=self.jwt_manager.refresh_token_ttl
            )

            self.refresh_token_repo.create_refresh_token(
                str(user.id), new_token_hash, expires_at, stored_token.device_info
            )

            logger.info(f"Tokens refreshed for user: {user.email}")

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "Bearer",
                "expires_in": self.jwt_manager.access_token_ttl * 60,
            }

        except jwt.InvalidTokenError:
            raise InvalidRefreshTokenError()

    def logout_user(self, refresh_token: str) -> None:
        """Logout user by revoking refresh token."""
        try:
            # Validate refresh token format (but don't care if expired)
            payload = self.jwt_manager.validate_token(refresh_token, "refresh")
            user_id = payload["sub"]

            # Revoke the token
            token_hash = self.jwt_manager.hash_token(refresh_token)
            revoked = self.refresh_token_repo.revoke_refresh_token(token_hash)

            if revoked:
                logger.info(f"User logged out: {user_id}")
            else:
                logger.warning(f"Logout attempted with invalid token: {user_id}")

        except jwt.InvalidTokenError:
            # Still try to revoke in case token is malformed but exists in DB
            token_hash = self.jwt_manager.hash_token(refresh_token)
            self.refresh_token_repo.revoke_refresh_token(token_hash)

    def get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set for public key distribution."""
        return self.jwt_manager.get_jwks()

    def validate_access_token(self, token: str) -> Dict[str, Any]:
        """Validate access token and return user info."""
        try:
            payload = self.jwt_manager.validate_token(token, "access")

            # Check if user still exists and is active
            user = self.user_repo.get_user_by_id(payload["sub"])
            if not user or not user.is_active:
                raise jwt.InvalidTokenError("User account is inactive")

            return payload

        except jwt.InvalidTokenError:
            raise InvalidCredentialsError("Invalid or expired access token")
