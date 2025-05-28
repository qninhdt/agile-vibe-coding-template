"""Unit tests for JWTManager."""

import pytest
import jwt
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
import base64
import json

from app.utils.auth import JWTManager


class TestJWTManager:
    """Test cases for JWTManager."""

    def test_jwt_manager_initialization(self, jwt_manager):
        """Test JWT manager initialization."""
        assert jwt_manager.algorithm == "RS256"
        assert jwt_manager.issuer == "test-issuer"
        assert jwt_manager.audience == "test-audience"
        assert jwt_manager.access_token_ttl == 15
        assert jwt_manager.refresh_token_ttl == 30
        assert jwt_manager.private_key is not None
        assert jwt_manager.public_key is not None
        assert jwt_manager.key_id == "test-key-id"

    def test_generate_rsa_keys(self, mock_config, monkeypatch):
        """Test RSA key generation when keys are not provided."""
        # Mock config to return None for keys
        mock_config.jwt_private_key = None
        mock_config.jwt_public_key = None

        monkeypatch.setattr("app.utils.auth.config", mock_config)

        jwt_manager = JWTManager()

        assert jwt_manager.private_key is not None
        assert jwt_manager.public_key is not None
        assert "-----BEGIN PRIVATE KEY-----" in jwt_manager.private_key
        assert "-----BEGIN PUBLIC KEY-----" in jwt_manager.public_key

    def test_generate_access_token(self, jwt_manager):
        """Test access token generation."""
        user_id = "test-user-123"
        username = "testuser"
        email = "test@example.com"

        token = jwt_manager.generate_access_token(user_id, username, email)

        # Verify token is not empty
        assert token
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT has 3 parts

        # Decode and verify payload
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["email"] == email
        assert payload["type"] == "access"
        assert payload["iss"] == jwt_manager.issuer
        assert payload["aud"] == jwt_manager.audience
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_generate_refresh_token(self, jwt_manager):
        """Test refresh token generation."""
        user_id = "test-user-123"

        token = jwt_manager.generate_refresh_token(user_id)

        # Verify token is not empty
        assert token
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT has 3 parts

        # Decode and verify payload
        payload = jwt.decode(token, options={"verify_signature": False})
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert payload["iss"] == jwt_manager.issuer
        assert (
            payload["aud"] == jwt_manager.issuer
        )  # refresh tokens are for auth service only
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

        # Verify no user details in refresh token
        assert "username" not in payload
        assert "email" not in payload

    def test_access_token_expiration(self, jwt_manager):
        """Test access token expiration time."""
        user_id = "test-user-123"
        username = "testuser"
        email = "test@example.com"

        token = jwt_manager.generate_access_token(user_id, username, email)
        payload = jwt.decode(token, options={"verify_signature": False})

        # Calculate expected expiration (15 minutes from now)
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=15)
        actual_exp = datetime.fromtimestamp(payload["exp"], timezone.utc)

        # Allow 5 seconds tolerance
        assert abs((actual_exp - expected_exp).total_seconds()) < 5

    def test_refresh_token_expiration(self, jwt_manager):
        """Test refresh token expiration time."""
        user_id = "test-user-123"

        token = jwt_manager.generate_refresh_token(user_id)
        payload = jwt.decode(token, options={"verify_signature": False})

        # Calculate expected expiration (30 days from now)
        expected_exp = datetime.now(timezone.utc) + timedelta(days=30)
        actual_exp = datetime.fromtimestamp(payload["exp"], timezone.utc)

        # Allow 5 seconds tolerance
        assert abs((actual_exp - expected_exp).total_seconds()) < 5

    def test_validate_access_token_success(self, jwt_manager):
        """Test successful access token validation."""
        user_id = "test-user-123"
        username = "testuser"
        email = "test@example.com"

        token = jwt_manager.generate_access_token(user_id, username, email)
        payload = jwt_manager.validate_token(token, "access")

        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["email"] == email
        assert payload["type"] == "access"

    def test_validate_refresh_token_success(self, jwt_manager):
        """Test successful refresh token validation."""
        user_id = "test-user-123"

        token = jwt_manager.generate_refresh_token(user_id)
        payload = jwt_manager.validate_token(token, "refresh")

        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"

    def test_validate_token_wrong_type(self, jwt_manager):
        """Test token validation with wrong token type."""
        user_id = "test-user-123"
        username = "testuser"
        email = "test@example.com"

        access_token = jwt_manager.generate_access_token(user_id, username, email)

        with pytest.raises(jwt.InvalidTokenError) as exc_info:
            jwt_manager.validate_token(access_token, "refresh")

        assert "Invalid token type" in str(exc_info.value)

    def test_validate_expired_token(self, jwt_manager):
        """Test validation of expired token."""
        user_id = "test-user-123"

        # Create expired token
        expired_payload = {
            "sub": user_id,
            "iss": jwt_manager.issuer,
            "aud": jwt_manager.audience,
            "exp": datetime.utcnow() - timedelta(minutes=1),  # Expired 1 minute ago
            "iat": datetime.utcnow() - timedelta(minutes=16),
            "jti": "test-jti",
            "type": "access",
            "username": "testuser",
            "email": "test@example.com",
        }

        expired_token = jwt.encode(
            expired_payload,
            jwt_manager.private_key,
            algorithm=jwt_manager.algorithm,
            headers={"kid": jwt_manager.key_id},
        )

        with pytest.raises(jwt.InvalidTokenError) as exc_info:
            jwt_manager.validate_token(expired_token, "access")

        assert "Token has expired" in str(exc_info.value)

    def test_validate_token_invalid_signature(self, jwt_manager):
        """Test validation of token with invalid signature."""
        # Create token with wrong private key
        wrong_payload = {
            "sub": "test-user-123",
            "iss": jwt_manager.issuer,
            "aud": jwt_manager.audience,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
            "jti": "test-jti",
            "type": "access",
        }

        # Use a different key to sign
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        wrong_private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        wrong_private_pem = wrong_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        invalid_token = jwt.encode(
            wrong_payload,
            wrong_private_pem,
            algorithm=jwt_manager.algorithm,
        )

        with pytest.raises(jwt.InvalidTokenError):
            jwt_manager.validate_token(invalid_token, "access")

    def test_validate_token_wrong_issuer(self, jwt_manager):
        """Test validation of token with wrong issuer."""
        wrong_payload = {
            "sub": "test-user-123",
            "iss": "wrong-issuer",
            "aud": jwt_manager.audience,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
            "jti": "test-jti",
            "type": "access",
        }

        invalid_token = jwt.encode(
            wrong_payload,
            jwt_manager.private_key,
            algorithm=jwt_manager.algorithm,
        )

        with pytest.raises(jwt.InvalidTokenError):
            jwt_manager.validate_token(invalid_token, "access")

    def test_validate_token_wrong_audience(self, jwt_manager):
        """Test validation of token with wrong audience."""
        wrong_payload = {
            "sub": "test-user-123",
            "iss": jwt_manager.issuer,
            "aud": "wrong-audience",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
            "iat": datetime.now(timezone.utc),
            "jti": "test-jti",
            "type": "access",
        }

        invalid_token = jwt.encode(
            wrong_payload,
            jwt_manager.private_key,
            algorithm=jwt_manager.algorithm,
        )

        with pytest.raises(jwt.InvalidTokenError):
            jwt_manager.validate_token(invalid_token, "access")

    def test_get_jwks(self, jwt_manager):
        """Test JWKS generation."""
        jwks = jwt_manager.get_jwks()

        assert "keys" in jwks
        assert len(jwks["keys"]) == 1

        key = jwks["keys"][0]
        assert key["kty"] == "RSA"
        assert key["use"] == "sig"
        assert key["kid"] == jwt_manager.key_id
        assert key["alg"] == "RS256"
        assert "n" in key
        assert "e" in key

        # Verify the modulus and exponent are valid base64url encoded values
        assert isinstance(key["n"], str)
        assert isinstance(key["e"], str)
        assert len(key["n"]) > 0
        assert len(key["e"]) > 0

    def test_jwks_key_format(self, jwt_manager):
        """Test JWKS key format is correct."""
        jwks = jwt_manager.get_jwks()
        key = jwks["keys"][0]

        # Verify base64url encoding (should not contain +, /, or =)
        assert "+" not in key["n"]
        assert "/" not in key["n"]
        assert "=" not in key["n"]
        assert "+" not in key["e"]
        assert "/" not in key["e"]
        assert "=" not in key["e"]

    def test_hash_token(self, jwt_manager):
        """Test token hashing for storage."""
        token1 = "test.jwt.token"
        token2 = "different.jwt.token"

        hash1a = jwt_manager.hash_token(token1)
        hash1b = jwt_manager.hash_token(token1)
        hash2 = jwt_manager.hash_token(token2)

        # Same token should produce same hash
        assert hash1a == hash1b

        # Different tokens should produce different hashes
        assert hash1a != hash2

        # Hash should be hex string
        assert isinstance(hash1a, str)
        assert len(hash1a) == 64  # SHA-256 produces 64-character hex string

    def test_token_header_includes_kid(self, jwt_manager):
        """Test that generated tokens include key ID in header."""
        user_id = "test-user-123"
        username = "testuser"
        email = "test@example.com"

        access_token = jwt_manager.generate_access_token(user_id, username, email)
        refresh_token = jwt_manager.generate_refresh_token(user_id)

        # Decode headers without verification
        access_header = jwt.get_unverified_header(access_token)
        refresh_header = jwt.get_unverified_header(refresh_token)

        assert access_header["kid"] == jwt_manager.key_id
        assert refresh_header["kid"] == jwt_manager.key_id
        assert access_header["alg"] == "RS256"
        assert refresh_header["alg"] == "RS256"
        assert access_header["typ"] == "JWT"
        assert refresh_header["typ"] == "JWT"

    def test_unique_jti_values(self, jwt_manager):
        """Test that each token gets a unique JTI (JWT ID)."""
        user_id = "test-user-123"
        username = "testuser"
        email = "test@example.com"

        token1 = jwt_manager.generate_access_token(user_id, username, email)
        token2 = jwt_manager.generate_access_token(user_id, username, email)

        payload1 = jwt.decode(token1, options={"verify_signature": False})
        payload2 = jwt.decode(token2, options={"verify_signature": False})

        assert payload1["jti"] != payload2["jti"]

    def test_key_id_generation(self, mock_config, monkeypatch):
        """Test key ID generation when not provided."""
        mock_config.jwt_key_id = None
        monkeypatch.setattr("app.utils.auth.config", mock_config)

        with patch("time.time", return_value=1234567890):
            jwt_manager = JWTManager()
            assert jwt_manager.key_id == "auth-service-key-1234567890"

    def test_malformed_token_validation(self, jwt_manager):
        """Test validation of malformed tokens."""
        malformed_tokens = [
            "not.a.jwt",
            "invalid-token",
            "",
            "header.payload",  # Missing signature
            "too.many.parts.here.invalid",  # Too many parts
        ]

        for token in malformed_tokens:
            with pytest.raises(jwt.InvalidTokenError):
                jwt_manager.validate_token(token, "access")

    def test_jwks_multiple_calls_consistency(self, jwt_manager):
        """Test that JWKS returns consistent results across multiple calls."""
        jwks1 = jwt_manager.get_jwks()
        jwks2 = jwt_manager.get_jwks()

        assert jwks1 == jwks2

    def test_token_validation_with_real_signature(self, jwt_manager):
        """Test complete token validation flow with real signature verification."""
        user_id = "test-user-123"
        username = "testuser"
        email = "test@example.com"

        # Generate token
        token = jwt_manager.generate_access_token(user_id, username, email)

        # Validate token (this should verify signature, expiration, etc.)
        payload = jwt_manager.validate_token(token, "access")

        # Verify all claims
        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["email"] == email
        assert payload["type"] == "access"
        assert payload["iss"] == jwt_manager.issuer
        assert payload["aud"] == jwt_manager.audience

        # Verify expiration is in the future
        exp_time = datetime.fromtimestamp(payload["exp"], timezone.utc)
        assert exp_time > datetime.now(timezone.utc)

        # Verify issued time is in the past
        iat_time = datetime.fromtimestamp(payload["iat"], timezone.utc)
        assert iat_time <= datetime.now(timezone.utc)
