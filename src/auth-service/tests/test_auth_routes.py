"""Unit tests for authentication routes."""

import pytest
import json
from unittest.mock import Mock, patch

from app.utils.errors import (
    ValidationError,
    ConflictError,
    InvalidCredentialsError,
    AccountInactiveError,
    InvalidRefreshTokenError,
    AuthError,
)


class TestAuthRoutes:
    """Test cases for authentication routes."""

    def test_register_success(self, client, sample_user_data):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            data=json.dumps(sample_user_data),
            content_type="application/json",
        )

        print(response)

        assert response.status_code == 201
        data = json.loads(response.data)

        assert "data" in data
        assert "user" in data["data"]
        assert "tokens" in data["data"]

        user = data["data"]["user"]
        assert user["email"] == sample_user_data["email"]
        assert user["username"] == sample_user_data["username"]
        assert "id" in user
        assert "created_at" in user
        assert user["email_verified"] is False

        tokens = data["data"]["tokens"]
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "Bearer"
        assert tokens["expires_in"] == 900

    def test_register_validation_error(self, client):
        """Test registration with validation errors."""
        invalid_data = {
            "email": "invalid-email",
            "username": "ab",  # Too short
            "password": "weak",  # Too weak
            "confirm_password": "different",
        }

        response = client.post(
            "/api/v1/auth/register",
            data=json.dumps(invalid_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)

        assert "error" in data
        assert data["error"]["code"] == "VALIDATION_FAILED"
        assert "details" in data["error"]

    def test_register_duplicate_user(self, client, sample_user_data, auth_service):
        """Test registration with duplicate user."""

        response1 = client.post(
            "/api/v1/auth/register",
            data=json.dumps(sample_user_data),
            content_type="application/json",
        )

        # register the same user again
        response2 = client.post(
            "/api/v1/auth/register",
            data=json.dumps(sample_user_data),
            content_type="application/json",
        )

        assert response1.status_code == 201
        assert response2.status_code == 409

        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)

        assert data1["data"]["user"]["email"] == sample_user_data["email"]
        assert data2["error"]["code"] == "USER_ALREADY_EXISTS"

    def test_login_success_with_email(self, client, sample_user_data):
        """Test successful login with email."""

        # register the user first
        client.post(
            "/api/v1/auth/register",
            data=json.dumps(sample_user_data),
            content_type="application/json",
        )

        response = client.post(
            "/api/v1/auth/login",
            data=json.dumps(
                {
                    "identifier": sample_user_data["email"],
                    "password": sample_user_data["password"],
                }
            ),
            content_type="application/json",
            # fake ip address and device info
            headers={"X-Forwarded-For": "127.0.0.1", "User-Agent": "test"},
        )

        print(response.data)

        assert response.status_code == 200
        data = json.loads(response.data)

        assert "data" in data
        assert "user" in data["data"]
        assert "tokens" in data["data"]

        user = data["data"]["user"]
        assert user["email"] == sample_user_data["email"]
        assert user["username"] == sample_user_data["username"]
