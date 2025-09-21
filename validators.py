#!/usr/bin/env python3
"""
Validation functions for the Yandex Cloud User Creation CLI Tool
"""

import os
import re
import sys
import logging

logger = logging.getLogger(__name__)


def validate_userpool_id(userpool_id: str) -> None:
    """Validate user pool ID"""
    if not userpool_id:
        raise ValueError("User pool ID cannot be empty")
    
    if len(userpool_id) > 32:
        raise ValueError("User pool ID cannot be longer than 32 characters")
    
    if not re.match(r'^[a-zA-Z0-9]+$', userpool_id):
        raise ValueError("User pool ID must contain only letters and digits")


def validate_number_of_users(num_users: int) -> None:
    """Validate number of users"""
    if num_users <= 0:
        raise ValueError("Number of users must be greater than zero")
    
    if num_users > 100:
        raise ValueError("Number of users cannot be greater than 100")


def validate_domain(domain: str) -> None:
    """Validate domain name syntax"""
    if not domain:
        raise ValueError("Domain name cannot be empty")
    
    # Basic domain validation regex
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
    
    if not re.match(domain_pattern, domain):
        raise ValueError("Invalid domain name syntax")


def validate_created_users_file(created_users_file: str) -> None:
    """Validate created users file"""
    if not created_users_file:
        raise ValueError(f"Created users file {created_users_file} cannot be empty")

    # check that file is writable and the directory where it is supposed to exist is writable
    dir = os.path.dirname(created_users_file)
    if len(dir) == 0:
        dir = '.'
    if not os.access(dir, os.W_OK):
        raise ValueError(f"Dir {dir} with users file {created_users_file} is not writable")
    if os.path.exists(created_users_file) and not os.access(created_users_file, os.W_OK):
        raise ValueError(f"Created users file {created_users_file} is not writable")
    if os.path.exists(created_users_file):
        # as confirmation to proceed
        logger.info(f"Created users file {created_users_file} already exists. Do you want to proceed? (y/n)")
        if input() != 'y':
            sys.exit(1)


def validate_cloud_id(cloud_id: str) -> None:
    """Validate cloud ID"""
    if not cloud_id:
        raise ValueError("Cloud ID cannot be empty")
    
    if len(cloud_id) > 32:
        raise ValueError("Cloud ID cannot be longer than 32 characters")
    
    if not re.match(r'^[a-zA-Z0-9]+$', cloud_id):
        raise ValueError("Cloud ID must contain only letters and digits")
