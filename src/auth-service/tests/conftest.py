"""Test configuration and fixtures."""

import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.utils.auth import JWTManager, PasswordManager
from app.services.rate_limiter import RateLimiter
from app.models.user import User
from app.models import Base
from app.config import Config as AppConfig


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock(spec=AppConfig)
    config.get.side_effect = lambda key, default=None: {
        "jwt.algorithm": "RS256",
        "jwt.issuer": "test-issuer",
        "jwt.audience": "test-audience",
        "jwt.access_token_ttl_minutes": 15,
        "jwt.refresh_token_ttl_days": 30,
        "jwt.key_size": 2048,
        "account.password.bcrypt_rounds": 4,  # Lower for testing speed
        "account.username.reserved_words": ["admin", "root"],
        "login.session.max_sessions_per_user": 10,
    }.get(key, default)

    config.jwt_private_key = None
    config.jwt_public_key = None
    config.jwt_key_id = "test-key-id"

    return config


@pytest.fixture
def test_database_url():
    """Create a temporary SQLite database file for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)  # Close the file descriptor, we only need the path

    database_url = f"sqlite:///{db_path}"

    yield database_url

    # Cleanup: remove the temporary database file
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def alembic_config():
    """Create Alembic configuration for testing."""
    # Get the directory of this file to locate alembic.ini
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_cfg = Config(os.path.join(current_dir, "alembic.ini"))

    # Override the script location to point to our migrations directory
    alembic_cfg.set_main_option(
        "script_location", os.path.join(current_dir, "migrations")
    )

    return alembic_cfg


@pytest.fixture
def in_memory_db(test_database_url, alembic_config):
    """Create database with Alembic migrations for testing."""
    # Override the database URL in alembic config for testing
    alembic_config.set_main_option("sqlalchemy.url", test_database_url)

    # Create the database engine
    engine = create_engine(test_database_url)

    # Run Alembic migrations to set up the schema
    try:
        command.upgrade(alembic_config, "head")
    except Exception as e:
        # If migrations fail, fall back to creating tables directly
        print(
            f"Warning: Alembic migration failed ({e}), falling back to metadata.create_all()"
        )
        Base.metadata.create_all(engine)

    return engine


@pytest.fixture
def user_repo(in_memory_db):
    """Create user repository for testing."""
    return UserRepository(in_memory_db)


@pytest.fixture
def refresh_token_repo(in_memory_db):
    """Create refresh token repository for testing."""
    return RefreshTokenRepository(in_memory_db)


@pytest.fixture
def mock_rate_limiter():
    """Mock rate limiter for testing."""
    rate_limiter = Mock(spec=RateLimiter)
    rate_limiter.check_rate_limit.return_value = None
    rate_limiter.record_attempt.return_value = None
    rate_limiter.clear_user_rate_limits.return_value = None
    return rate_limiter


@pytest.fixture
def jwt_manager(mock_config, monkeypatch):
    """Create JWT manager for testing."""
    # Mock config module
    monkeypatch.setattr("app.utils.auth.config", mock_config)
    return JWTManager()


@pytest.fixture
def password_manager(mock_config, monkeypatch):
    """Create password manager for testing."""
    # Mock config module
    monkeypatch.setattr("app.utils.auth.config", mock_config)
    return PasswordManager()


@pytest.fixture
def auth_service(
    user_repo, refresh_token_repo, mock_rate_limiter, jwt_manager, password_manager
):
    """Create auth service for testing."""
    return AuthService(
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
        rate_limiter=mock_rate_limiter,
        jwt_manager=jwt_manager,
        password_manager=password_manager,
    )


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "testcc@gmail.com",
        "username": "testusercc",
        "password": "TestPass123!",
        "confirm_password": "TestPass123!",
    }


@pytest.fixture
def created_user(user_repo, password_manager):
    """Create a user in the database for testing."""
    password_hash = password_manager.hash_password("TestPass123!")
    user = user_repo.create_user(
        email="testcc@example.com",
        username="testusercc",
        password_hash=password_hash,
    )
    return user


@pytest.fixture
def flask_app(auth_service, monkeypatch):
    """Create Flask app for testing."""
    from app.main import create_app
    from app.routes import create_auth_bp, create_jwks_bp, create_health_bp
    from flask import Flask

    app = Flask(__name__)
    app.config["TESTING"] = True

    # Mock the config and dependencies
    mock_db_engine = Mock()
    monkeypatch.setattr("app.main.create_engine", lambda url: mock_db_engine)
    monkeypatch.setattr(
        "app.main.UserRepository", lambda engine: auth_service.user_repo
    )
    monkeypatch.setattr(
        "app.main.RefreshTokenRepository",
        lambda engine: auth_service.refresh_token_repo,
    )
    monkeypatch.setattr("app.main.RateLimiter", lambda: auth_service.rate_limiter)
    monkeypatch.setattr("app.main.JWTManager", lambda: auth_service.jwt_manager)
    monkeypatch.setattr(
        "app.main.PasswordManager", lambda: auth_service.password_manager
    )
    monkeypatch.setattr("app.main.AuthService", lambda *args: auth_service)

    # Register blueprints
    auth_bp = create_auth_bp(auth_service)
    jwks_bp = create_jwks_bp(auth_service)
    health_bp = create_health_bp()

    app.register_blueprint(auth_bp)
    app.register_blueprint(jwks_bp)
    app.register_blueprint(health_bp)

    return app


@pytest.fixture
def client(flask_app):
    """Create test client."""
    return flask_app.test_client()
