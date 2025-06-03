import pytest
import uuid
from typing import Dict

from omegaconf import DictConfig
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.services.jwt_service import JWTService, PasswordManager
from app.services.rate_limiter import RateLimiter


@pytest.fixture(scope="session")
def test_rsa_keys():
    """Generates a new RSA key pair for testing."""
    private_key_obj = rsa.generate_private_key(
        public_exponent=65537, key_size=2048  # Use a common key size for tests
    )
    private_pem = private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_key_obj = private_key_obj.public_key()
    public_pem = public_key_obj.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


@pytest.fixture
def jwt_config(test_rsa_keys) -> DictConfig:
    """Provides a base DictConfig for JWTService."""
    private_key, public_key = test_rsa_keys
    return DictConfig(
        {
            "private_key": private_key,
            "public_key": public_key,
            "algorithm": "RS256",
            "issuer": "test_issuer",
            "audience": "test_audience",
            "access_token_ttl_minutes": 15,
            "refresh_token_ttl_days": 7,
            "key_size": 2048,
        }
    )


@pytest.fixture
def jwt_config_no_keys() -> DictConfig:
    """Provides a DictConfig without pre-set keys to test generation."""
    return DictConfig(
        {
            "private_key": None,
            "public_key": None,
            "algorithm": "RS256",
            "issuer": "test_gen_issuer",
            "audience": "test_gen_audience",
            "access_token_ttl_minutes": 1,  # shorter for testing
            "refresh_token_ttl_days": 1,  # shorter for testing
            "key_size": 2048,
        }
    )


@pytest.fixture
def jwt_service(jwt_config: DictConfig) -> JWTService:
    """Fixture for JWTService instance with pre-defined keys."""
    return JWTService(config=jwt_config)


@pytest.fixture
def jwt_service_generated_keys(jwt_config_no_keys: DictConfig) -> JWTService:
    """Fixture for JWTService instance that generates its own keys."""
    return JWTService(config=jwt_config_no_keys)


@pytest.fixture
def password_manager() -> PasswordManager:
    """Fixture for PasswordManager instance."""
    return PasswordManager(rounds=4)  # Use low rounds for faster tests


@pytest.fixture
def user_details() -> Dict[str, str]:
    return {
        "user_id": str(uuid.uuid4()),
        "username": "testuser",
        "email": "test@example.com",
    }


@pytest.fixture
def mock_cache_service():
    return MagicMock()


@pytest.fixture
def rate_limit_config_enabled():
    return DictConfig(
        {
            "enabled": True,
            "per_ip_requests": 10,
            "per_ip_window_minutes": 1,
            "per_identifier_attempts": 5,
            "per_identifier_window_minutes": 5,
            "per_account_attempts": 3,
            "per_account_window_minutes": 15,
        }
    )


@pytest.fixture
def rate_limit_config_disabled():
    return DictConfig(
        {
            "enabled": False,
            "per_ip_requests": 10,
            "per_ip_window_minutes": 1,
            "per_identifier_attempts": 5,
            "per_identifier_window_minutes": 5,
            "per_account_attempts": 3,
            "per_account_window_minutes": 15,
        }
    )


@pytest.fixture
def rate_limiter_enabled(rate_limit_config_enabled, mock_cache_service):
    return RateLimiter(rate_limit_config_enabled, mock_cache_service)


@pytest.fixture
def rate_limiter_disabled(rate_limit_config_disabled, mock_cache_service):
    return RateLimiter(rate_limit_config_disabled, mock_cache_service)
