"""Health check routes."""

from flask import Blueprint, jsonify


def create_health_bp():
    health_bp = Blueprint("health", __name__)

    @health_bp.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint."""
        return jsonify({"status": "healthy", "service": "auth-service"}), 200

    return health_bp
