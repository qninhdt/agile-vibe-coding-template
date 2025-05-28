"""User model for authentication."""

from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel


class User(BaseModel):
    """User model for storing user authentication data."""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email_verified = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationship to refresh tokens
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )

    def to_public_dict(self) -> dict:
        """Convert to public dictionary (without sensitive data)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "username": self.username,
            "created_at": (
                self.created_at.isoformat() + "Z" if self.created_at else None
            ),
            "email_verified": self.email_verified,
        }
