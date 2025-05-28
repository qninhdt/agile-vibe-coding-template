"""Main Flask application factory."""

import logging
import os
from flask import Flask
from flask_cors import CORS

from app.config import config
from app.routes import (
    create_auth_bp,
    create_jwks_bp,
    create_health_bp,
)
from app.services import AuthService, RateLimiter
from app.repositories import UserRepository, RefreshTokenRepository
from sqlalchemy import create_engine
from app.utils.auth import JWTManager, PasswordManager


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO if not config.debug else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Enable CORS
    CORS(app)

    # Initialize database
    try:
        db_engine = create_engine(config.database_url)

        logging.info("Database initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize database: {str(e)}")
        raise

    # Initialize repositories
    user_repo = UserRepository(db_engine)
    refresh_token_repo = RefreshTokenRepository(db_engine)
    rate_limiter = RateLimiter()
    jwt_manager = JWTManager()
    password_manager = PasswordManager()

    # Initialize services
    auth_service = AuthService(
        user_repo, refresh_token_repo, rate_limiter, jwt_manager, password_manager
    )

    # Initialize routes
    auth_bp = create_auth_bp(auth_service)
    jwks_bp = create_jwks_bp(auth_service)
    health_bp = create_health_bp()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(jwks_bp)
    app.register_blueprint(health_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": {"code": "NOT_FOUND", "message": "Resource not found"}}, 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return {
            "error": {"code": "METHOD_NOT_ALLOWED", "message": "Method not allowed"}
        }, 405

    @app.errorhandler(500)
    def internal_error(error):
        return {
            "error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}
        }, 500

    logging.info("Flask application created successfully")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=config.debug)
