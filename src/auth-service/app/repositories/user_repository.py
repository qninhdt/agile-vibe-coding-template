"""User repository for database operations."""

from typing import Optional
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.user import User
from app.utils.errors import ConflictError


class UserRepository:
    """Repository for user database operations."""

    def __init__(self, db_engine: Engine):
        self.db_engine = db_engine

    def create_user(self, email: str, username: str, password_hash: str) -> User:
        """Create a new user."""
        user = User(
            email=email.lower(),  # Store email in lowercase
            username=username,
            password_hash=password_hash,
        )

        try:
            with Session(self.db_engine) as session:
                session.add(user)
                session.commit()
                session.refresh(user)

                return user
        except IntegrityError:
            raise ConflictError("User with this email or username already exists")

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        with Session(self.db_engine) as session:
            return session.query(User).filter(User.email == email.lower()).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        with Session(self.db_engine) as session:
            return session.query(User).filter(User.username == username).first()

    def get_user_by_identifier(self, identifier: str) -> Optional[User]:
        """Get user by email or username."""
        # single query to get user by email or username
        with Session(self.db_engine) as session:
            return (
                session.query(User)
                .filter(or_(User.email == identifier, User.username == identifier))
                .first()
            )

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        with Session(self.db_engine) as session:
            return session.query(User).filter(User.id == user_id).first()

    def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        with Session(self.db_engine) as session:
            return (
                session.query(User).filter(User.email == email.lower()).first()
                is not None
            )

    def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        with Session(self.db_engine) as session:
            return (
                session.query(User).filter(User.username == username).first()
                is not None
            )
