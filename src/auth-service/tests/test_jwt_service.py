from app.services.jwt_service import JWTService
from omegaconf import DictConfig
from typing import Dict
import jwt
import pytest
import time
from datetime import datetime, timedelta, timezone
import uuid
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def test_init_with_provided_keys(jwt_config: DictConfig):
    service = JWTService(jwt_config)
    assert service.private_key == jwt_config.private_key
    assert service.public_key == jwt_config.public_key
    assert service.algorithm == jwt_config.algorithm
    assert service.issuer == jwt_config.issuer
    assert service.audience == jwt_config.audience
    assert service.access_token_ttl == jwt_config.access_token_ttl_minutes * 60
    assert service.refresh_token_ttl == jwt_config.refresh_token_ttl_days * 24 * 60 * 60
    assert "notepot-auth-service-key-" in service.key_id


def test_init_generates_keys_if_not_provided(jwt_config_no_keys: DictConfig):
    service = JWTService(jwt_config_no_keys)
    assert service.private_key is not None
    assert service.public_key is not None
    assert "BEGIN PRIVATE KEY" in service.private_key  # PKCS1 for rsa module
    assert "BEGIN PUBLIC KEY" in service.public_key

    # Check if keys are valid PEM
    try:
        serialization.load_pem_private_key(service.private_key.encode(), password=None)
        serialization.load_pem_public_key(service.public_key.encode())
    except ValueError:
        pytest.fail("Generated keys are not valid PEM format.")


def test_generate_access_token(jwt_service: JWTService, user_details: Dict[str, str]):
    token = jwt_service.generate_access_token(
        user_details["user_id"], user_details["username"], user_details["email"]
    )
    assert isinstance(token, str)

    decoded_payload = jwt.decode(
        token,
        jwt_service.public_key,
        algorithms=[jwt_service.algorithm],
        audience=jwt_service.audience,
        issuer=jwt_service.issuer,
    )

    assert decoded_payload["sub"] == user_details["user_id"]
    assert decoded_payload["username"] == user_details["username"]
    assert decoded_payload["email"] == user_details["email"]
    assert decoded_payload["iss"] == jwt_service.issuer
    assert decoded_payload["aud"] == jwt_service.audience
    assert decoded_payload["type"] == "access"
    assert "jti" in decoded_payload
    assert "exp" in decoded_payload
    assert "iat" in decoded_payload
    assert (
        decoded_payload["exp"] == decoded_payload["iat"] + jwt_service.access_token_ttl
    )

    unverified_headers = jwt.get_unverified_header(token)
    assert unverified_headers["kid"] == jwt_service.key_id


def test_generate_refresh_token(jwt_service: JWTService, user_details: Dict[str, str]):
    token = jwt_service.generate_refresh_token(user_details["user_id"])
    assert isinstance(token, str)

    decoded_payload = jwt.decode(
        token,
        jwt_service.public_key,
        algorithms=[jwt_service.algorithm],
        audience=jwt_service.issuer,  # Refresh token audience is issuer
        issuer=jwt_service.issuer,
    )

    assert decoded_payload["sub"] == user_details["user_id"]
    assert decoded_payload["iss"] == jwt_service.issuer
    assert decoded_payload["aud"] == jwt_service.issuer  # Important check
    assert decoded_payload["type"] == "refresh"
    assert "jti" in decoded_payload
    assert "exp" in decoded_payload
    assert "iat" in decoded_payload
    assert (
        decoded_payload["exp"] == decoded_payload["iat"] + jwt_service.refresh_token_ttl
    )

    unverified_headers = jwt.get_unverified_header(token)
    assert unverified_headers["kid"] == jwt_service.key_id


def test_validate_access_token_valid(
    jwt_service: JWTService, user_details: Dict[str, str]
):
    token = jwt_service.generate_access_token(
        user_details["user_id"], user_details["username"], user_details["email"]
    )
    payload = jwt_service.validate_token(token, token_type="access")
    assert payload["sub"] == user_details["user_id"]
    assert payload["username"] == user_details["username"]
    assert payload["type"] == "access"


def test_validate_refresh_token_valid(
    jwt_service: JWTService, user_details: Dict[str, str]
):
    token = jwt_service.generate_refresh_token(user_details["user_id"])
    payload = jwt_service.validate_token(token, token_type="refresh")
    assert payload["sub"] == user_details["user_id"]
    assert payload["type"] == "refresh"
    assert payload["aud"] == jwt_service.issuer  # Check audience for refresh token


def test_validate_token_expired(jwt_config: DictConfig, user_details: Dict[str, str]):
    # Create a service with a very short TTL for access token
    short_ttl_config = jwt_config.copy()
    short_ttl_config.access_token_ttl_minutes = 0.5 / 60  # 0.5 second
    service = JWTService(short_ttl_config)

    token = service.generate_access_token(
        user_details["user_id"], user_details["username"], user_details["email"]
    )
    time.sleep(1)  # Wait for token to expire

    with pytest.raises(jwt.InvalidTokenError):
        service.validate_token(token, token_type="access")


def test_validate_token_invalid_signature(
    jwt_service: JWTService,
    jwt_config_no_keys: DictConfig,
    user_details: Dict[str, str],
):
    # generate an acesss token generated by different service
    other_service_jwt_service = JWTService(jwt_config_no_keys)
    other_service_access_token = other_service_jwt_service.generate_access_token(
        user_details["user_id"], user_details["username"], user_details["email"]
    )

    with pytest.raises(jwt.InvalidTokenError):
        jwt_service.validate_token(other_service_access_token, token_type="access")


def test_validate_token_wrong_type(
    jwt_service: JWTService, user_details: Dict[str, str]
):
    access_token = jwt_service.generate_access_token(
        user_details["user_id"], user_details["username"], user_details["email"]
    )
    with pytest.raises(jwt.InvalidTokenError):
        jwt_service.validate_token(access_token, token_type="refresh")

    refresh_token = jwt_service.generate_refresh_token(user_details["user_id"])
    with pytest.raises(jwt.InvalidTokenError):
        jwt_service.validate_token(refresh_token, token_type="access")


def test_validate_token_wrong_issuer(
    jwt_service: JWTService, user_details: Dict[str, str]
):
    token = jwt.encode(
        {
            "sub": user_details["user_id"],
            "iss": "wrong_issuer",
            "aud": jwt_service.audience,
            "exp": datetime.now(timezone.utc)
            + timedelta(seconds=jwt_service.access_token_ttl),
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "username": user_details["username"],
            "email": user_details["email"],
        },
        jwt_service.private_key,
        algorithm=jwt_service.algorithm,
    )
    with pytest.raises(jwt.InvalidTokenError):
        jwt_service.validate_token(token, token_type="access")


def test_validate_token_wrong_audience(
    jwt_service: JWTService, user_details: Dict[str, str]
):
    token = jwt.encode(
        {
            "sub": user_details["user_id"],
            "iss": jwt_service.issuer,
            "aud": "wrong_audience",
            "exp": datetime.now(timezone.utc)
            + timedelta(seconds=jwt_service.access_token_ttl),
            "iat": datetime.now(timezone.utc),
            "jti": str(uuid.uuid4()),
            "type": "access",
            "username": user_details["username"],
            "email": user_details["email"],
        },
        jwt_service.private_key,
        algorithm=jwt_service.algorithm,
    )

    with pytest.raises(jwt.InvalidTokenError):
        jwt_service.validate_token(token, token_type="access")


def test_get_jwks(jwt_service: JWTService):
    jwks = jwt_service.get_jwks()
    assert "keys" in jwks
    assert len(jwks["keys"]) == 1
    key_info = jwks["keys"][0]

    assert key_info["kty"] == "RSA"
    assert key_info["use"] == "sig"
    assert key_info["kid"] == jwt_service.key_id
    assert key_info["alg"] == jwt_service.algorithm
    assert "n" in key_info  # RSA modulus
    assert "e" in key_info  # RSA public exponent

    # Basic check for base64url encoding (no padding, URL-safe characters)
    assert "=" not in key_info["n"]
    assert "=" not in key_info["e"]
    assert "+" not in key_info["n"]
    assert "/" not in key_info["n"]


def test_hash_token(jwt_service: JWTService):
    token_to_hash = "some_jwt_token_string"
    hashed_token = jwt_service.hash_token(token_to_hash)

    assert isinstance(hashed_token, str)
    assert len(hashed_token) == 64  # SHA256 produces 64 hex characters

    # Test idempotency
    assert jwt_service.hash_token(token_to_hash) == hashed_token

    # Different token, different hash
    assert jwt_service.hash_token("another_token") != hashed_token
