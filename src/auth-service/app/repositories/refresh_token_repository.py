"""Refresh token repository for database operations."""

from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Repository for refresh token database operations."""

    def __init__(self, db_engine: Engine):
        self.db_engine = db_engine

    def create_refresh_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        device_info: Optional[str] = None,
    ) -> RefreshToken:
        """Create a new refresh token."""
        refresh_token = RefreshToken(
            user_id=UUID(user_id),
            token_hash=token_hash,
            expires_at=expires_at,
            device_info=device_info,
        )

        with Session(self.db_engine) as session:
            session.add(refresh_token)
            session.commit()
        return refresh_token

    def get_refresh_token_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash."""
        with Session(self.db_engine) as session:
            return (
                session.query(RefreshToken)
                .filter(
                    RefreshToken.token_hash == token_hash, RefreshToken.revoked == False
                )
                .first()
            )

    def revoke_refresh_token(self, token_hash: str) -> bool:
        """Revoke a refresh token."""
        with Session(self.db_engine) as session:
            token = (
                session.query(RefreshToken)
                .filter(RefreshToken.token_hash == token_hash)
                .first()
            )

            if token:
                token.revoked = True
                session.commit()
                return True

        return False

    def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all refresh tokens for a user."""
        with Session(self.db_engine) as session:
            updated = (
                session.query(RefreshToken)
                .filter(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
                .update({"revoked": True})
            )

            session.commit()
            return updated

    def cleanup_expired_tokens(self) -> int:
        """Clean up expired refresh tokens."""
        with Session(self.db_engine) as session:
            deleted = (
                session.query(RefreshToken)
                .filter(RefreshToken.expires_at < datetime.now(timezone.utc))
                .delete()
            )

            session.commit()
            return deleted

    def get_user_tokens(
        self, user_id: str, active_only: bool = True
    ) -> List[RefreshToken]:
        """Get all refresh tokens for a user."""
        with Session(self.db_engine) as session:
            query = session.query(RefreshToken).filter(RefreshToken.user_id == user_id)

        if active_only:
            query = query.filter(
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )

            return query.all()

    # TODO: Implement this
    def limit_user_sessions(self, user_id: str, max_sessions: int = 10) -> int:
        return 0
