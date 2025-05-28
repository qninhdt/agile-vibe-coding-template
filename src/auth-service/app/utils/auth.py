"""Authentication utilities for JWT token management."""

import hashlib
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple

import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import config


logger = logging.getLogger(__name__)


class JWTManager:
    """JWT token management with RSA keys."""

    def __init__(self):
        self.private_key, self.public_key = self._get_or_generate_keys()
        self.key_id = self._get_key_id()
        self.algorithm = config.get("jwt.algorithm", "RS256")
        self.issuer = config.get("jwt.issuer", "notepot_auth-service")
        self.audience = config.get("jwt.audience", "notepot-services")
        self.access_token_ttl = config.get("jwt.access_token_ttl_minutes", 15)
        self.refresh_token_ttl = config.get("jwt.refresh_token_ttl_days", 30)

    def _get_or_generate_keys(self) -> Tuple[str, str]:
        """Get keys from environment or generate new ones."""
        private_key = config.jwt_private_key
        public_key = config.jwt_public_key

        if not private_key or not public_key:
            logger.warning(
                "JWT keys not found in environment variables. Generating new keys."
            )
            return self._generate_rsa_keys()

        return private_key, public_key

    def _generate_rsa_keys(self) -> Tuple[str, str]:
        """Generate RSA key pair."""
        key_size = config.get("jwt.key_size", 2048)

        # Generate private key
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return private_pem.decode("utf-8"), public_pem.decode("utf-8")

    def _get_key_id(self) -> str:
        """Get or generate key ID."""
        key_id = config.jwt_key_id
        if not key_id:
            timestamp = int(time.time())
            key_id = f"auth-service-key-{timestamp}"
        return key_id

    def generate_access_token(self, user_id: str, username: str, email: str) -> str:
        """Generate JWT access token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "iss": self.issuer,
            "aud": self.audience,
            "exp": now + timedelta(minutes=self.access_token_ttl),
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "access",
            "username": username,
            "email": email,
        }

        return jwt.encode(
            payload,
            self.private_key,
            algorithm=self.algorithm,
            headers={"kid": self.key_id},
        )

    def generate_refresh_token(self, user_id: str) -> str:
        """Generate JWT refresh token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "iss": self.issuer,
            "aud": self.issuer,  # refresh tokens are for auth service only
            "exp": now + timedelta(days=self.refresh_token_ttl),
            "iat": now,
            "jti": str(uuid.uuid4()),
            "type": "refresh",
        }

        return jwt.encode(
            payload,
            self.private_key,
            algorithm=self.algorithm,
            headers={"kid": self.key_id},
        )

    def validate_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Validate JWT token and return payload."""
        try:
            # Decode without verification first to get headers
            unverified = jwt.decode(token, options={"verify_signature": False})

            # Verify the token type
            if unverified.get("type") != token_type:
                raise jwt.InvalidTokenError(
                    f"Invalid token type: expected {token_type}"
                )

            # Verify the token
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.issuer if token_type == "refresh" else self.audience,
            )

            return payload

        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")

    def get_jwks(self) -> Dict[str, Any]:
        """Get JSON Web Key Set for public key distribution."""
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        # Load public key
        public_key = serialization.load_pem_public_key(self.public_key.encode("utf-8"))

        # Get RSA numbers
        numbers = public_key.public_numbers()

        # Convert to base64url
        def int_to_base64url_uint(val):
            val_bytes = val.to_bytes((val.bit_length() + 7) // 8, "big")
            import base64

            return base64.urlsafe_b64encode(val_bytes).decode("ascii").rstrip("=")

        n = int_to_base64url_uint(numbers.n)
        e = int_to_base64url_uint(numbers.e)

        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "kid": self.key_id,
                    "alg": self.algorithm,
                    "n": n,
                    "e": e,
                }
            ]
        }

    def hash_token(self, token: str) -> str:
        """Hash token for secure storage."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()


class PasswordManager:
    """Password hashing and verification utilities."""

    def __init__(self):
        self.rounds = config.get("account.password.bcrypt_rounds", 12)

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def dummy_verify(self) -> None:
        """Perform dummy bcrypt operation to prevent timing attacks."""
        bcrypt.checkpw(b"dummy", b"$2b$12$dummy_hash_for_timing_protection")
