#!/usr/bin/env python3
"""
Yandex Cloud User Creation CLI Tool

This tool creates users in Yandex Cloud using the organization-manager API.
"""

import argparse
import logging
import os
import random
import sys
import traceback
import csv
from typing import List, Tuple

from validators import (
    validate_userpool_id,
    validate_number_of_users,
    validate_domain,
    validate_created_users_file,
    validate_cloud_id
)
from user_creator import UserCreator, UserCreationError
from modes import run_users_mode, run_ydb_mode


# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


 


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Yandex Cloud User and YDB Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Mode selection
    parser.add_argument(
        '--do',
        choices=['users', 'ydb'],
        required=True,
        help='Operation mode: "users" for user creation, "ydb" for YDB database creation'
    )
    
    # User creation mode arguments
    parser.add_argument(
        '--userpool-id',
        help='User pool ID (string of letters and digits, max 32 characters) - required for users mode'
    )
    
    parser.add_argument(
        '--num-users',
        type=int,
        help='Number of users to create (1-100) - required for users mode'
    )
    
    parser.add_argument(
        '--domain',
        required=False,
        default='ydbem.idp.yandexcloud.net',
        help='Domain name for user emails'
    )

    parser.add_argument(
        '--created-users-file',
        required=False,
        default='created_users.txt',
        help='Filename for list of created users'
    )

    # Cloud and YDB mode arguments
    parser.add_argument(
        '--cloud-id',
        required=False,
        default='b1gad4empjmov1cn3ahu',
        help='Cloud id - required for both modes'
    )
    
    # YDB mode specific arguments
    parser.add_argument(
        '--skip-folder-ids',
        required=False,
        default='',
        help='Comma-separated list of folder IDs to skip during YDB creation'
    )
    
    args = parser.parse_args()
    
    # Validate IAM token
    iam_token = os.getenv('IAM_TOKEN')
    if not iam_token:
        logger.error("IAM_TOKEN environment variable is required")
        sys.exit(1)
    
    try:
        # Initialize components
        user_creator = UserCreator(iam_token)

        if args.do == 'users':
            run_users_mode(args, user_creator)
        elif args.do == 'ydb':
            run_ydb_mode(args, user_creator)
        
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        #print message in exception with all the details of the exception
        logger.error(f"Unexpected error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
