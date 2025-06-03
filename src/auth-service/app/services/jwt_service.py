"""Authentication utilities for JWT token management."""

import hashlib
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple, Optional

import bcrypt
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from omegaconf import DictConfig


logger = logging.getLogger(__name__)


class JWTService:
    """JWT token management with RSA keys."""

    def __init__(
        self,
        config: DictConfig,
    ):
        self.private_key = config.private_key
        self.public_key = config.public_key
        self.algorithm = config.algorithm
        self.issuer = config.issuer
        self.audience = config.audience
        self.access_token_ttl = (
            config.access_token_ttl_minutes * 60
        )  # Convert to seconds
        self.refresh_token_ttl = (
            config.refresh_token_ttl_days * 24 * 60 * 60
        )  # Convert to seconds
        self.key_size = config.key_size

        self.key_id = f"notepot-auth-service-key-{int(time.time())}"

        if not self.private_key or not self.public_key:
            logger.info(
                "JWT keys not found in environment variables. Generating new keys."
            )
            self._generate_rsa_keys()

    def _generate_rsa_keys(self) -> Tuple[str, str]:
        """Generate RSA key pair."""

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=self.key_size
        )
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

        self.private_key = private_pem.decode("utf-8")
        self.public_key = public_pem.decode("utf-8")

    def generate_access_token(self, user_id: str, username: str, email: str) -> str:
        """Generate JWT access token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "iss": self.issuer,
            "aud": self.audience,
            "exp": now + timedelta(seconds=self.access_token_ttl),
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
            "exp": now + timedelta(seconds=self.refresh_token_ttl),
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
        # Decode without verification first to get headers
        unverified = jwt.decode(token, options={"verify_signature": False})

        # Verify the token type
        if unverified.get("type") != token_type:
            raise jwt.InvalidTokenError(f"Token type is invalid")

        # Verify the token
        payload = jwt.decode(
            token,
            self.public_key,
            algorithms=[self.algorithm],
            issuer=self.issuer,
            audience=self.issuer if token_type == "refresh" else self.audience,
        )

        return payload

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


# TODO: refactor this code
class PasswordManager:
    """Password hashing and verification utilities."""

    def __init__(self, rounds: int):
        self.rounds = rounds

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
