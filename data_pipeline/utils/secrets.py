"""
Secrets Manager - Secure credential handling for NZ Habitat Intelligence

Supports multiple backends:
1. AWS Secrets Manager (production)
2. Environment variables (development)
3. Local .env file (fallback)

Usage:
    from data_pipeline.utils.secrets import SecretsManager

    secrets = SecretsManager()
    api_key = secrets.get("API_KEY")
    db_password = secrets.get("DB_PASSWORD", required=True)
"""

import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class SecretsManager:
    """Secure credential manager with multiple backend support."""

    def __init__(
        self,
        backend: Optional[str] = None,
        aws_region: Optional[str] = None,
        secret_prefix: str = "nz-habitat/",
    ):
        """
        Initialize secrets manager.

        Args:
            backend: 'aws', 'env', or 'auto' (default: auto-detect)
            aws_region: AWS region for Secrets Manager
            secret_prefix: Prefix for AWS secret names
        """
        self.backend = backend or self._detect_backend()
        self.aws_region = aws_region or os.getenv("AWS_REGION", "ap-southeast-2")
        self.secret_prefix = secret_prefix
        self._cache: Dict[str, Any] = {}
        self._aws_client = None

        if self.backend == "aws":
            self._init_aws_client()

        logger.info(f"SecretsManager initialized with backend: {self.backend}")

    def _detect_backend(self) -> str:
        """Auto-detect secrets backend based on environment."""
        if os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ROLE_ARN"):
            return "aws"
        return "env"

    def _init_aws_client(self):
        """Initialize AWS Secrets Manager client."""
        try:
            import boto3

            self._aws_client = boto3.client(
                "secretsmanager",
                region_name=self.aws_region,
            )
            logger.info("AWS Secrets Manager client initialized")
        except ImportError:
            logger.warning("boto3 not installed, falling back to env backend")
            self.backend = "env"
        except Exception as e:
            logger.warning(f"Failed to initialize AWS client: {e}")
            self.backend = "env"

    def get(self, key: str, required: bool = False, default: Any = None) -> Any:
        """
        Retrieve a secret value.

        Args:
            key: Secret key name
            required: If True, raise error if not found
            default: Default value if not found

        Returns:
            Secret value or default

        Raises:
            ValueError: If required=True and secret not found
        """
        cache_key = key
        if cache_key in self._cache:
            return self._cache[cache_key]

        value = None

        if self.backend == "aws":
            value = self._get_from_aws(key)
        else:
            value = self._get_from_env(key)

        if value is None:
            if required:
                raise ValueError(f"Required secret '{key}' not found")
            value = default

        if value is not None:
            self._cache[cache_key] = value

        return value

    def _get_from_aws(self, key: str) -> Optional[str]:
        """Retrieve secret from AWS Secrets Manager."""
        if not self._aws_client:
            return None

        try:
            secret_name = f"{self.secret_prefix}{key}"
            response = self._aws_client.get_secret_value(SecretId=secret_name)

            secret_string = response.get("SecretString")
            if secret_string:
                try:
                    secret_dict = json.loads(secret_string)
                    return secret_dict
                except json.JSONDecodeError:
                    return secret_string

            return None
        except self._aws_client.exceptions.ResourceNotFoundException:
            logger.warning(f"AWS secret '{key}' not found")
            return None
        except Exception as e:
            logger.error(f"Error retrieving AWS secret '{key}': {e}")
            return None

    def _get_from_env(self, key: str) -> Optional[str]:
        """Retrieve secret from environment variables."""
        return os.getenv(key)

    def get_dict(self, key: str) -> Dict[str, Any]:
        """
        Retrieve a secret as a dictionary (for JSON secrets).

        Args:
            key: Secret key name

        Returns:
            Dictionary of secret values
        """
        value = self.get(key, default="{}")
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.warning(f"Secret '{key}' is not valid JSON")
                return {}
        return {}

    def get_required(self, key: str) -> Any:
        """
        Retrieve a required secret (raises error if not found).

        Args:
            key: Secret key name

        Returns:
            Secret value

        Raises:
            ValueError: If secret not found
        """
        return self.get(key, required=True)

    def refresh(self):
        """Clear the cache to force fresh retrieval."""
        self._cache.clear()
        logger.info("Secrets cache cleared")

    def list_cached(self) -> list:
        """List all cached secret keys (for debugging)."""
        return list(self._cache.keys())


# Module-level singleton
_secrets_manager: Optional[SecretsManager] = None


def get_secrets(backend: Optional[str] = None) -> SecretsManager:
    """
    Get or create the global secrets manager singleton.

    Args:
        backend: Override backend ('aws', 'env', or 'auto')

    Returns:
        SecretsManager instance
    """
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager(backend=backend)
    return _secrets_manager


def reset_secrets():
    """Reset the global secrets manager (for testing)."""
    global _secrets_manager
    _secrets_manager = None
