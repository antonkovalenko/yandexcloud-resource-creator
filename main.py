#!/usr/bin/env python3
"""
Yandex Cloud User Creation CLI Tool - Improved Version

This tool creates users in Yandex Cloud using the organization-manager API.
"""

import argparse
import sys
import time
from typing import NoReturn

from config import Constants, get_environment_config
from exceptions import ValidationError, ConfigurationError, UserCreationError
from logging_config import setup_logging
from user_creator import UserCreator
from modes import (
    run_users_mode, run_ydb_mode, run_delete_ydb_mode, 
    run_reset_password_mode, run_generate_load_mode
)

logger = setup_logging()


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Yandex Cloud User and YDB Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Mode selection
    parser.add_argument(
        '--do',
        choices=['users', 'create-ydb', 'delete-ydb', 'reset-password', 'generate-load'],
        required=True,
        help='Operation mode'
    )
    
    # Common arguments
    parser.add_argument(
        '--cloud-id',
        default=Constants.DEFAULT_CLOUD_ID,
        help='Cloud ID'
    )
    parser.add_argument(
        '--domain',
        default=Constants.DEFAULT_DOMAIN,
        help='Domain name for user emails'
    )
    parser.add_argument(
        '--created-users-file',
        default=Constants.DEFAULT_CREATED_USERS_FILE,
        help='Filename for list of created users'
    )
    
    # User creation mode arguments
    parser.add_argument(
        '--userpool-id',
        help='User pool ID (required for users and reset-password modes)'
    )
    parser.add_argument(
        '--num-users',
        type=int,
        help='Number of users to create (required for users mode)'
    )
    
    # Reset-password mode arguments
    parser.add_argument(
        '--user-ids',
        help='Comma-separated list of user IDs to reset password for (optional)'
    )
    
    # YDB mode specific arguments
    parser.add_argument(
        '--skip-folder-ids',
        help='Comma-separated list of folder IDs to skip during operations'
    )
    parser.add_argument(
        '--create-ydb-in-folders',
        help='Comma-separated list of folder IDs to create YDB in (if provided, only these folders are processed)'
    )
    
    # Generate-load and delete-ydb mode arguments
    parser.add_argument(
        '--folder-ids',
        help='Comma-separated list of folder IDs to target (required for delete-ydb mode, optional for generate-load mode)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=Constants.DEFAULT_BATCH_SIZE,
        help=f'Parallel commands per batch (1-32) for generate-load mode (default: {Constants.DEFAULT_BATCH_SIZE})'
    )
    parser.add_argument(
        '--output-dir',
        default=Constants.DEFAULT_OUTPUT_DIR,
        help=f'Existing writable directory to write bash scripts (generate-load mode) (default: {Constants.DEFAULT_OUTPUT_DIR})'
    )
    
    return parser


def main() -> NoReturn:
    """Main function with improved structure and error handling."""
    start_time = time.time()
    
    try:
        # Parse arguments
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # Validate environment configuration
        try:
            env_config = get_environment_config()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        
        # Initialize components
        user_creator = UserCreator(env_config.iam_token)
        
        # Route to appropriate mode handler
        mode_handlers = {
            'users': run_users_mode,
            'create-ydb': run_ydb_mode,
            'delete-ydb': run_delete_ydb_mode,
            'reset-password': run_reset_password_mode,
            'generate-load': run_generate_load_mode,
        }
        
        handler = mode_handlers[args.do]
        handler(args, user_creator)
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except UserCreationError as e:
        logger.error(f"User creation error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        logger.debug(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Program completed in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
