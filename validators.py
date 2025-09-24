#!/usr/bin/env python3
"""
Validation functions for the Yandex Cloud User Creation CLI Tool
"""

import os
import re
import logging
from typing import Optional

from config import Constants
from exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_userpool_id(userpool_id: str) -> None:
    """Validate user pool ID"""
    if not userpool_id:
        raise ValidationError("User pool ID cannot be empty")
    
    if len(userpool_id) > Constants.MAX_USERPOOL_ID_LENGTH:
        raise ValidationError(f"User pool ID cannot be longer than {Constants.MAX_USERPOOL_ID_LENGTH} characters")
    
    if not re.match(r'^[a-zA-Z0-9]+$', userpool_id):
        raise ValidationError("User pool ID must contain only letters and digits")


def validate_number_of_users(num_users: int) -> None:
    """Validate number of users"""
    if num_users <= 0:
        raise ValidationError("Number of users must be greater than zero")
    
    if num_users > Constants.MAX_USERS_PER_BATCH:
        raise ValidationError(f"Number of users cannot be greater than {Constants.MAX_USERS_PER_BATCH}")


def validate_domain(domain: str) -> None:
    """Validate domain name syntax"""
    if not domain:
        raise ValidationError("Domain name cannot be empty")
    
    # Basic domain validation regex
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    
    if not re.match(domain_pattern, domain):
        raise ValidationError("Invalid domain name syntax")


def validate_created_users_file(created_users_file: str, overwrite: bool = False) -> None:
    """Validate created users file and check if it can be written to"""
    if not created_users_file:
        raise ValidationError("Created users file path cannot be empty")

    # Check that the directory is writable
    file_dir = os.path.dirname(created_users_file)
    if not file_dir:
        file_dir = '.'
    
    if not os.access(file_dir, os.W_OK):
        raise ValidationError(f"Directory {file_dir} is not writable")
    
    # Check if file exists and is writable
    if os.path.exists(created_users_file):
        if not os.access(created_users_file, os.W_OK):
            raise ValidationError(f"Created users file {created_users_file} is not writable")
        
        if not overwrite:
            logger.warning(f"Created users file {created_users_file} already exists and will be overwritten")


def validate_cloud_id(cloud_id: str) -> None:
    """Validate cloud ID"""
    if not cloud_id:
        raise ValidationError("Cloud ID cannot be empty")
    
    if len(cloud_id) > Constants.MAX_CLOUD_ID_LENGTH:
        raise ValidationError(f"Cloud ID cannot be longer than {Constants.MAX_CLOUD_ID_LENGTH} characters")
    
    if not re.match(r'^[a-zA-Z0-9]+$', cloud_id):
        raise ValidationError("Cloud ID must contain only letters and digits")


def validate_batch_size(batch_size: int) -> None:
    """Validate batch size parameter"""
    if batch_size < 1 or batch_size > 32:
        raise ValidationError("Batch size must be between 1 and 32")


def validate_output_directory(output_dir: str) -> None:
    """Validate output directory exists and is writable"""
    if not output_dir:
        raise ValidationError("Output directory cannot be empty")
    
    if not os.path.isdir(output_dir):
        raise ValidationError(f"Output directory {output_dir} is not a directory")
    
    if not os.access(output_dir, os.W_OK):
        raise ValidationError(f"Output directory {output_dir} is not writable")
