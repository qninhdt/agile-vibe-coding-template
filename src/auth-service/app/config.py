"""Configuration management for Auth Service."""

import os
from omegaconf import OmegaConf, DictConfig
from pathlib import Path


def load_config() -> DictConfig:
    config_path = Path(__file__).parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config: DictConfig = OmegaConf.load(config_path)

    # Merge environment variables into configuration.
    if database_url := os.getenv("DATABASE_URL"):
        config.database = {"url": database_url}
    else:
        config.database = {"url": None}

    # JWT configuration
    # private key and public key are optional
    if jwt_private_key := os.getenv("JWT_PRIVATE_KEY"):
        config.jwt.private_key = jwt_private_key
    else:
        config.jwt.private_key = ""

    if jwt_public_key := os.getenv("JWT_PUBLIC_KEY"):
        config.jwt.public_key = jwt_public_key
    else:
        config.jwt.public_key = ""

    # Redis configuration
    if redis_url := os.getenv("REDIS_URL"):
        config.redis = {"url": redis_url}
    else:
        config.redis = {"url": None}

        # Debug mode
    if debug := os.getenv("DEBUG"):
        config.debug = debug.lower() in ("true", "1", "yes")
    else:
        config.debug = False

    return config


config = load_config()
