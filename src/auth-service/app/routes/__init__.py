"""Route modules for Flask application."""

from .auth_routes import create_auth_bp
from .jwks_routes import create_jwks_bp
from .health_routes import create_health_bp

__all__ = ["create_auth_bp", "create_jwks_bp", "create_health_bp"]
