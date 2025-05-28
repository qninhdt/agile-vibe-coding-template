"""Configuration management for Auth Service."""

import os
import logging
from typing import Optional, Dict, Any
from omegaconf import OmegaConf, DictConfig
from pathlib import Path


class Config:
    """Configuration class for Auth Service."""

    def __init__(self):
        """Initialize configuration from YAML and environment variables."""
        self.config: DictConfig = self._load_config()
        self._merge_env_vars()

    def _load_config(self) -> DictConfig:
        """Load configuration from YAML file."""
        config_path = Path(__file__).parent / "config.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        return OmegaConf.load(config_path)

    def _merge_env_vars(self) -> None:
        """Merge environment variables into configuration."""
        # Database configuration
        if database_url := os.getenv("DATABASE_URL"):
            self.config.database = {"url": database_url}

        # JWT configuration
        if jwt_private_key := os.getenv("JWT_PRIVATE_KEY"):
            if "jwt" not in self.config:
                self.config.jwt = {}
            self.config.jwt.private_key = jwt_private_key

        if jwt_public_key := os.getenv("JWT_PUBLIC_KEY"):
            if "jwt" not in self.config:
                self.config.jwt = {}
            self.config.jwt.public_key = jwt_public_key

        if jwt_key_id := os.getenv("JWT_KEY_ID"):
            if "jwt" not in self.config:
                self.config.jwt = {}
            self.config.jwt.key_id = jwt_key_id

        if jwt_issuer := os.getenv("JWT_ISSUER"):
            if "jwt" not in self.config:
                self.config.jwt = {}
            self.config.jwt.issuer = jwt_issuer

        # Bcrypt rounds
        if bcrypt_rounds := os.getenv("BCRYPT_ROUNDS"):
            try:
                self.config.account.password.bcrypt_rounds = int(bcrypt_rounds)
            except (ValueError, AttributeError):
                logging.warning(f"Invalid BCRYPT_ROUNDS value: {bcrypt_rounds}")

        # Redis configuration
        if redis_url := os.getenv("REDIS_URL"):
            if "redis" not in self.config:
                self.config.redis = {}
            self.config.redis.url = redis_url

        # Debug mode
        if debug := os.getenv("DEBUG"):
            self.config.debug = debug.lower() in ("true", "1", "yes")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        try:
            return OmegaConf.select(self.config, key, default=default)
        except Exception:
            return default

    @property
    def database_url(self) -> Optional[str]:
        """Get database URL."""
        return self.get("database.url")

    @property
    def jwt_private_key(self) -> Optional[str]:
        """Get JWT private key."""
        return self.get("jwt.private_key")

    @property
    def jwt_public_key(self) -> Optional[str]:
        """Get JWT public key."""
        return self.get("jwt.public_key")

    @property
    def jwt_key_id(self) -> Optional[str]:
        """Get JWT key ID."""
        return self.get("jwt.key_id")

    @property
    def debug(self) -> bool:
        """Get debug mode."""
        return self.get("debug", False)


# Global configuration instance
config = Config()
