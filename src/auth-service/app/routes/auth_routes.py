"""Authentication routes."""

import logging
from flask import Blueprint, request, jsonify
from pydantic import ValidationError as PydanticValidationError

from app.services.auth_service import AuthService
from app.schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    LogoutRequest,
)
from werkzeug.exceptions import BadRequest
from app.utils.errors import AuthError


def create_auth_bp(auth_service: AuthService):
    logger = logging.getLogger(__name__)
    auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

    def get_client_ip():
        """Get client IP address from request."""
        if request.headers.get("X-Forwarded-For"):
            return request.headers.get("X-Forwarded-For").split(",")[0].strip()
        elif request.headers.get("X-Real-IP"):
            return request.headers.get("X-Real-IP")
        else:
            return request.remote_addr

    def get_device_info():
        """Get device information from request headers."""
        user_agent = request.headers.get("User-Agent", "")
        return user_agent[:500] if user_agent else None

    def handle_auth_error(error: AuthError):
        """Handle authentication errors and return proper response."""
        response_data = {"error": {"code": error.code, "message": error.message}}

        if error.details:
            response_data["error"]["details"] = error.details

        # Determine status code based on error type
        status_code = 400
        if error.code == "INVALID_CREDENTIALS":
            status_code = 401
        elif error.code == "ACCOUNT_INACTIVE":
            status_code = 403
        elif error.code == "USER_ALREADY_EXISTS":
            status_code = 409
        elif error.code == "RATE_LIMIT_EXCEEDED":
            status_code = 429

        return jsonify(response_data), status_code

    @auth_bp.route("/register", methods=["POST"])
    def register():
        """Register a new user."""
        try:
            # Validate request data
            request_data = RegisterRequest(**request.get_json())

            # Register user
            result = auth_service.register_user(request_data)

            return jsonify({"data": result}), 201

        except PydanticValidationError as e:
            # Extract validation errors
            details = {}
            for error in e.errors():
                field = error["loc"][-1]
                details[field] = error["msg"]

            error_response = {
                "error": {
                    "code": "VALIDATION_FAILED",
                    "message": "Registration validation failed",
                    "details": details,
                }
            }
            return jsonify(error_response), 400

        except AuthError as e:
            return handle_auth_error(e)

        except BadRequest as e:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_REQUEST",
                            "message": "Invalid request format",
                        }
                    }
                ),
                400,
            )

        except Exception as e:
            logger.error(f"Unexpected error in register: {str(e)}")
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "An unexpected error occurred",
                        }
                    }
                ),
                500,
            )

    @auth_bp.route("/login", methods=["POST"])
    def login():
        """Authenticate user and return tokens."""
        try:
            # Validate request data
            request_data = LoginRequest(**request.get_json())

            # Get client info
            ip_address = get_client_ip()
            device_info = get_device_info()

            # Login user
            result = auth_service.login_user(request_data, ip_address, device_info)

            return jsonify({"data": result}), 200

        except PydanticValidationError as e:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_REQUEST",
                            "message": "Invalid login request format",
                        }
                    }
                ),
                400,
            )

        except AuthError as e:
            return handle_auth_error(e)

        except BadRequest as e:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_REQUEST",
                            "message": "Invalid request format",
                        }
                    }
                ),
                400,
            )

        except Exception as e:
            logger.error(f"Unexpected error in login: {str(e)}")
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "An unexpected error occurred",
                            "details": str(e),
                        }
                    }
                ),
                500,
            )

    @auth_bp.route("/refresh", methods=["POST"])
    def refresh():
        """Refresh access and refresh tokens."""
        try:
            # Validate request data
            request_data = RefreshTokenRequest(**request.get_json())

            # Refresh tokens
            result = auth_service.refresh_tokens(request_data.refresh_token)

            return jsonify({"data": result}), 200

        except PydanticValidationError as e:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_REQUEST",
                            "message": "Invalid refresh token request format",
                        }
                    }
                ),
                400,
            )

        except AuthError as e:
            return handle_auth_error(e)

        except Exception as e:
            logger.error(f"Unexpected error in refresh: {str(e)}")
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "An unexpected error occurred",
                        }
                    }
                ),
                500,
            )

    @auth_bp.route("/logout", methods=["POST"])
    def logout():
        """Logout user by revoking refresh token."""
        try:
            # Validate request data
            request_data = LogoutRequest(**request.get_json())

            # Logout user
            auth_service.logout_user(request_data.refresh_token)

            return jsonify({"data": None}), 200

        except PydanticValidationError as e:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_REQUEST",
                            "message": "Invalid logout request format",
                        }
                    }
                ),
                400,
            )

        except AuthError as e:
            return handle_auth_error(e)

        except BadRequest as e:
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INVALID_REQUEST",
                            "message": "Invalid request format",
                        }
                    }
                ),
                400,
            )

        except Exception as e:
            logger.error(f"Unexpected error in logout: {str(e)}")
            return (
                jsonify(
                    {
                        "error": {
                            "code": "INTERNAL_ERROR",
                            "message": "An unexpected error occurred",
                        }
                    }
                ),
                500,
            )

    return auth_bp
