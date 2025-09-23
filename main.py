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
import time
from typing import List, Tuple

from validators import (
    validate_userpool_id,
    validate_number_of_users,
    validate_domain,
    validate_created_users_file,
    validate_cloud_id
)
from user_creator import UserCreator, UserCreationError
from modes import run_users_mode, run_ydb_mode, run_delete_ydb_mode, run_reset_password_mode, run_generate_load_mode


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
        choices=['users', 'create-ydb', 'delete-ydb', 'reset-password', 'generate-load'],
        required=True,
        help='Operation mode: "users", "create-ydb", "delete-ydb", "reset-password", or "generate-load"'
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
    
    # Reset-password mode arguments
    parser.add_argument(
        '--user-ids',
        required=False,
        default='',
        help='Comma-separated list of user IDs to reset password for (optional)'
    )
    
    # YDB mode specific arguments
    parser.add_argument(
        '--skip-folder-ids',
        required=False,
        default='',
        help='Comma-separated list of folder IDs to skip during YDB creation'
    )
    parser.add_argument(
        '--create-ydb-in-folders',
        required=False,
        default='',
        help='Comma-separated list of folder IDs to create YDB in (if provided, only these folders are processed)'
    )
    
    # Generate-load and delete-ydb mode arguments
    parser.add_argument(
        '--folder-ids',
        required=False,
        default='',
        help='Comma-separated list of folder IDs to target (required for delete-ydb mode, optional for generate-load mode)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        required=False,
        default=16,
        help='Parallel commands per batch (1-32) for generate-load mode'
    )
    parser.add_argument(
        '--output-dir',
        required=False,
        default='load',
        help='Existing writable directory to write bash scripts (generate-load mode)'
    )
    
    start_time = time.time()
    args = parser.parse_args()
    
    # Validate IAM token
    iam_token = os.getenv('IAM_TOKEN')
    if not iam_token:
        logger.error("IAM_TOKEN environment variable is required")
        elapsed = time.time() - start_time
        logger.info(f"Program run completed in {elapsed:.2f}s")
        sys.exit(1)
    
    try:
        # Initialize components
        user_creator = UserCreator(iam_token)

        if args.do == 'users':
            run_users_mode(args, user_creator)
        elif args.do == 'create-ydb':
            run_ydb_mode(args, user_creator)
        elif args.do == 'delete-ydb':
            run_delete_ydb_mode(args, user_creator)
        elif args.do == 'reset-password':
            run_reset_password_mode(args, user_creator)
        elif args.do == 'generate-load':
            run_generate_load_mode(args, user_creator)
        
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        #print message in exception with all the details of the exception
        logger.error(f"Unexpected error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Program run completed in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
