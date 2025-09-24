#!/usr/bin/env python3
"""
Centralized configuration and validation for Yandex Cloud CLI tool.
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Constants - make them clear and documented
class Constants:
    """Application constants."""
    # Load testing duration (10 hours in seconds)
    LOAD_DURATION_SECONDS = 36000
    
    # User limits and validation
    MAX_USERS_PER_BATCH = 100
    MAX_USERPOOL_ID_LENGTH = 32
    MAX_CLOUD_ID_LENGTH = 32
    
    # Operation limits
    MAX_CONCURRENT_OPERATIONS = 15
    MAX_POLL_RETRIES = 5
    
    # Default values
    DEFAULT_DOMAIN = 'ydbem.idp.yandexcloud.net'
    DEFAULT_CLOUD_ID = 'b1gad4empjmov1cn3ahu'
    DEFAULT_CREATED_USERS_FILE = 'created_users.txt'
    DEFAULT_OUTPUT_DIR = 'load'
    DEFAULT_BATCH_SIZE = 16
    
    # YDB configuration
    YDB_AVAILABILITY_ZONES = ["ru-central1-a", "ru-central1-b", "ru-central1-d"]
    YDB_RESOURCE_PRESET = "small-m8"
    YDB_STORAGE_TYPE = "ssd"
    YDB_GROUP_COUNT = "1"
    YDB_SCALE_SIZE = "1"
    
    # Network configuration
    VPC_CIDR_BLOCKS = ["192.168.1.0/24", "192.168.2.0/24", "192.168.3.0/24"]
    
    # Password configuration
    VALID_OWN_PASSWORD = 'YdbAdmin$2025'


@dataclass
class EnvironmentConfig:
    """Environment configuration validation."""
    iam_token: str
    
    @classmethod
    def from_env(cls) -> 'EnvironmentConfig':
        """Create configuration from environment variables."""
        iam_token = os.getenv('IAM_TOKEN')
        if not iam_token:
            raise ValueError("IAM_TOKEN environment variable is required for all operations")
        return cls(iam_token=iam_token)


def validate_required_env() -> EnvironmentConfig:
    """Validate all required environment variables."""
    return EnvironmentConfig.from_env()


def get_environment_config() -> EnvironmentConfig:
    """Get environment configuration with proper error handling."""
    try:
        return validate_required_env()
    except ValueError as e:
        logger.error(f"Environment configuration error: {e}")
        raise
