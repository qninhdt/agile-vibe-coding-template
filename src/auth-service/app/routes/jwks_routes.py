from flask import Blueprint, jsonify
import logging
from app.services.auth_service import AuthService


def create_jwks_bp(auth_service: AuthService):
    # JWKS endpoint should be at root level, not under auth prefix
    jwks_bp = Blueprint("jwks", __name__)
    logger = logging.getLogger(__name__)

    @jwks_bp.route("/.well-known/jwks.json", methods=["GET"])
    def jwks():
        """Get JSON Web Key Set for public key distribution."""
        try:
            # Get JWKS
            result = auth_service.get_jwks()

            return jsonify(result), 200

        except Exception as e:
            logger.error(f"Unexpected error in jwks: {str(e)}")
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

    return jwks_bp
