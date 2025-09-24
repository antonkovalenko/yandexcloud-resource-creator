#!/usr/bin/env python3
"""
Mode handlers for the Yandex Cloud CLI tool.

Provides run_users_mode and run_ydb_mode entry points used by main.py.
"""

import time
import logging
import sys
import os
from typing import Tuple

from config import Constants
from exceptions import UserCreationError, ValidationError
from name_generator import NameGenerator
from operation_poller import OperationPoller
from user_creator import UserCreator
from utils import (
    parse_comma_separated_ids, parse_skip_folder_ids, safe_file_writer,
    generate_username, generate_phone_number, create_folder_objects_from_ids,
    has_ydb_storage_groups, has_dedicated_ydb_storage, OperationTimer, log_operation_progress
)
from validators import (
    validate_userpool_id, validate_number_of_users, validate_domain,
    validate_created_users_file, validate_cloud_id, validate_batch_size,
    validate_output_directory
)

logger = logging.getLogger(__name__)




def run_users_mode(args, user_creator: UserCreator) -> None:
    """Run user creation mode with improved error handling and utilities."""
    # Validate required parameters
    if not args.userpool_id:
        raise ValidationError("--userpool-id is required for users mode")
    if not args.num_users:
        raise ValidationError("--num-users is required for users mode")

    # Validate all parameters
    validate_userpool_id(args.userpool_id)
    validate_number_of_users(args.num_users)
    validate_domain(args.domain)
    validate_created_users_file(args.created_users_file, overwrite=True)
    validate_cloud_id(args.cloud_id)

    logger.info(
        f"Starting user creation: {args.num_users} users in pool {args.userpool_id}, cloud {args.cloud_id}"
    )

    name_generator = NameGenerator()
    created_count = 0

    with OperationTimer("user creation"):
        with safe_file_writer(args.created_users_file) as f:
            f.write("id,username,password\n")
            f.flush()

            for i in range(args.num_users):
                try:
                    log_operation_progress(i, args.num_users, "User creation")
                    
                    given_name, family_name = name_generator.generate_unique_name()
                    full_name = f"{given_name} {family_name}"
                    
                    username = generate_username(given_name, family_name, args.domain)
                    email = username
                    phone_number = generate_phone_number(i)
                    
                    password, generation_proof = user_creator.generate_password()
                    
                    user_id = user_creator.create_user(
                        userpool_id=args.userpool_id,
                        username=username,
                        full_name=full_name,
                        given_name=given_name,
                        family_name=family_name,
                        email=email,
                        phone_number=phone_number,
                        password=password,
                        generation_proof=generation_proof,
                    )
                    
                    # Create folder and grant access
                    try:
                        folder_id = user_creator.create_folder(
                            cloud_id=args.cloud_id,
                            folder_name=given_name.lower() + "-" + family_name.lower(),
                            description=f"Personal folder for user {full_name}",
                        )
                        
                        user_creator.grant_folder_access(
                            folder_id=folder_id,
                            user_id=user_id,
                            role_id='editor',
                        )
                        
                        user_creator.grant_cloud_access(
                            cloud_id=args.cloud_id,
                            user_id=user_id,
                            role_id='resource-manager.clouds.member',
                        )
                        
                        logger.info(f"Folder and access created for user {username}")
                        
                    except UserCreationError as e:
                        logger.error(f"Failed to create folder/access for user {username}: {e}")

                    # Write CSV line immediately so progress is not lost
                    f.write(f"{user_id},{username},{password}\n")
                    f.flush()
                    created_count += 1
                    
                    logger.info(f"Created user {i+1}/{args.num_users}: {username} ({full_name}) id: {user_id}")
                    
                except UserCreationError as e:
                    logger.error(f"Failed to create user {i+1}: {e}")
                    continue

    logger.info(f"User creation completed. Successfully created {created_count} users. Output: {args.created_users_file}")


def run_ydb_mode(args, user_creator: UserCreator) -> None:
    """Run YDB creation mode with improved utilities and error handling."""
    validate_cloud_id(args.cloud_id)

    logger.info(f"Starting YDB creation mode for cloud {args.cloud_id}")

    # Parse skip folder IDs
    skip_folder_ids = parse_skip_folder_ids(args.skip_folder_ids)
    if skip_folder_ids:
        logger.info(f"Will skip folders: {skip_folder_ids}")

    # Determine which folders to process
    if getattr(args, 'create_ydb_in_folders', None):
        folder_ids = parse_comma_separated_ids(args.create_ydb_in_folders)
        target_folders = create_folder_objects_from_ids(folder_ids)
        logger.info(f"Will create YDB only in specified folders: {folder_ids}")
    else:
        target_folders = user_creator.list_folders(args.cloud_id)

    created_databases = 0
    skipped_folders = 0
    pending_ops = []  # list of dicts: {folder_id, folder_name, operation_id}
    poller = OperationPoller(user_creator)

    with OperationTimer("YDB creation"):
        for folder in target_folders:
            folder_id = folder['id']
            folder_name = folder['name']

            if folder_id in skip_folder_ids:
                logger.info(f"Skipping folder {folder_name} (ID: {folder_id})")
                skipped_folders += 1
                continue

            try:
                # Skip if folder already has a dedicated YDB
                existing_dbs = user_creator.list_ydb_databases_in_folder(folder_id)
                has_existing_dedicated = any(has_dedicated_ydb_storage(db) for db in existing_dbs)
                
                if has_existing_dedicated:
                    logger.info(f"Folder {folder_name} (ID: {folder_id}) already has a dedicated YDB database. Skipping.")
                    skipped_folders += 1
                    continue

                # Check for existing VPC or create new one
                network_id, subnet_ids = user_creator.check_existing_vpc(folder_id)

                if network_id and subnet_ids:
                    logger.info(f"Using existing VPC {network_id} for folder {folder_name} (ID: {folder_id})")
                else:
                    logger.info(f"Creating new VPC for folder {folder_name} (ID: {folder_id})")
                    network_id, subnet_ids = user_creator.create_vpc_with_subnets(
                        folder_id=folder_id,
                        network_name=f"vpc-{folder_name}",
                        description=f"VPC network for folder {folder_name}",
                    )

                # Flow control: if we already have max concurrent ops in-flight, poll until one finishes
                while len(pending_ops) >= Constants.MAX_CONCURRENT_OPERATIONS:
                    created_databases += poller.poll_pending_operations(pending_ops, "create")

                # Start YDB create operation (non-blocking)
                op_id = user_creator.start_ydb_database(
                    folder_id=folder_id,
                    network_id=network_id,
                    subnet_ids=subnet_ids,
                    database_name=f"ydb-{folder_name}",
                    description=f"YDB database for folder {folder_name}",
                )

                pending_ops.append({
                    'folder_id': folder_id,
                    'folder_name': folder_name,
                    'operation_id': op_id,
                    'start_time': time.time(),
                })

            except UserCreationError as e:
                logger.error(f"Failed to start YDB for folder {folder_name} (ID: {folder_id}): {e}")
                continue

        # Finalize any remaining operations
        while pending_ops:
            created_now = poller.poll_pending_operations(pending_ops, "create")
            created_databases += created_now

    logger.info(f"YDB creation completed. Created {created_databases} databases, skipped {skipped_folders} folders")


def run_delete_ydb_mode(args, user_creator: UserCreator) -> None:
    """Run YDB deletion mode with improved utilities and error handling."""
    validate_cloud_id(args.cloud_id)

    logger.info(f"Starting YDB deletion mode for cloud {args.cloud_id}")

    # Resolve folders to process
    if getattr(args, 'folder_ids', None):
        folder_ids = parse_comma_separated_ids(args.folder_ids)
        folders = create_folder_objects_from_ids(folder_ids)
        logger.info(f"delete-ydb: using provided folder IDs: {folder_ids}")
    else:
        folders = user_creator.list_folders(args.cloud_id)
        logger.info(f"delete-ydb: listed {len(folders)} folders in cloud {args.cloud_id}")

    # Build skip set
    skip_set = parse_skip_folder_ids(getattr(args, 'skip_folder_ids', None))

    deleted_databases = 0
    pending_ops = []  # list of dicts: {folder_id, folder_name, database_id, operation_id}
    poller = OperationPoller(user_creator)

    # Collect all databases to delete
    databases_to_delete = []
    for folder in folders:
        folder_id = folder['id']
        folder_name = folder.get('name', folder_id)
        if folder_id in skip_set:
            logger.info(f"delete-ydb: skipping folder {folder_name} (ID: {folder_id})")
            continue
        try:
            # List YDB databases in the folder
            databases = user_creator.list_ydb_databases_in_folder(folder_id)
            logger.info(f"Found {len(databases)} YDB databases in folder {folder_name} (ID: {folder_id})")

            for db in databases:
                databases_to_delete.append({
                    'folder_id': folder_id,
                    'folder_name': folder_name,
                    'database_id': db['id'],
                    'database_name': db.get('name', db['id'])
                })

        except UserCreationError as e:
            logger.error(f"Failed to list YDB databases in folder {folder_id}: {e}")
            continue

    logger.info(f"Total databases to delete: {len(databases_to_delete)}")

    with OperationTimer("YDB deletion"):
        # Start deletion operations with concurrency control
        for db_info in databases_to_delete:
            folder_id = db_info['folder_id']
            folder_name = db_info['folder_name']
            database_id = db_info['database_id']
            database_name = db_info['database_name']
            
            try:
                # Flow control: if we already have max concurrent ops in-flight, poll until one finishes
                while len(pending_ops) >= Constants.MAX_CONCURRENT_OPERATIONS:
                    deleted_databases += poller.poll_pending_operations(pending_ops, "delete")
                
                # Start YDB delete operation (non-blocking)
                op_id = user_creator.start_ydb_database_deletion(database_id)
                
                pending_ops.append({
                    'folder_id': folder_id,
                    'folder_name': folder_name,
                    'database_id': database_id,
                    'database_name': database_name,
                    'operation_id': op_id,
                    'start_time': time.time(),
                })
                
            except UserCreationError as e:
                logger.error(f"Failed to start YDB deletion for database {database_name} in folder {folder_name} (ID: {folder_id}): {e}")
                continue
        
        # Finalize any remaining operations
        while pending_ops:
            deleted_now = poller.poll_pending_operations(pending_ops, "delete")
            deleted_databases += deleted_now
    
    logger.info(f"YDB deletion completed. Deleted {deleted_databases} databases")




def run_reset_password_mode(args, user_creator: UserCreator) -> None:
    """Run password reset mode with improved utilities and error handling."""
    # Validate inputs
    if not args.userpool_id:
        raise ValidationError("--userpool-id is required for reset-password mode")

    validate_userpool_id(args.userpool_id)
    validate_created_users_file(args.created_users_file, overwrite=True)

    # Build username map by listing users (used for output consistency)
    logger.info(f"Listing users from userpool {args.userpool_id} to build username map")
    users = user_creator.list_users_in_userpool(args.userpool_id)
    username_by_id = {u['id']: u.get('username', '') for u in users}

    # Decide target users
    if getattr(args, 'user_ids', None):
        target_user_ids = parse_comma_separated_ids(args.user_ids)
        logger.info(f"Resetting password for provided {len(target_user_ids)} user(s)")
    else:
        target_user_ids = list(username_by_id.keys())
        logger.info(f"Collected {len(target_user_ids)} user(s) to reset from userpool")

    successes = 0
    failures = 0

    with OperationTimer("password reset"):
        with safe_file_writer(args.created_users_file) as f:
            f.write("id,username,password\n")
            f.flush()

            for i, user_id in enumerate(target_user_ids):
                try:
                    log_operation_progress(i, len(target_user_ids), "Password reset")
                    
                    # Generate a new password
                    password, generation_proof = user_creator.generate_password()
                    # Set password for the user
                    user_creator.set_others_password(user_id, password, generation_proof)

                    username = username_by_id.get(user_id, '')
                    f.write(f"{user_id},{username},{password}\n")
                    f.flush()

                    successes += 1
                except UserCreationError as e:
                    logger.error(f"Failed to reset password for user {user_id}: {e}")
                    failures += 1

    logger.info(f"Password reset completed. Success: {successes}, Failed: {failures}")


def run_generate_load_mode(args, user_creator: UserCreator) -> None:
    """Run load generation mode with improved utilities and error handling."""
    # Validate inputs
    validate_cloud_id(args.cloud_id)
    validate_batch_size(args.batch_size)
    validate_output_directory(args.output_dir)

    # Resolve folders to process
    if getattr(args, 'folder_ids', None):
        folder_ids = parse_comma_separated_ids(args.folder_ids)
        folders = create_folder_objects_from_ids(folder_ids)
        logger.info(f"generate-load: using provided folder IDs: {folder_ids}")
    else:
        folders = user_creator.list_folders(args.cloud_id)
        logger.info(f"generate-load: listed {len(folders)} folders in cloud {args.cloud_id}")

    # Build skip set
    skip_set = parse_skip_folder_ids(getattr(args, 'skip_folder_ids', None))

    # Open init script; mixed/select will be split into batch files
    init_path = os.path.join(args.output_dir, 'init.bash')
    
    generated = 0
    batch_size = args.batch_size
    mixed_f = None
    batch_no = 1
    current_batch_count = 0
    batch_files = []

    with OperationTimer("load script generation"):
        with safe_file_writer(init_path) as init_f:
            init_f.write("#!/usr/bin/env bash\n")

            for folder in folders:
                folder_id = folder['id']
                folder_name = folder.get('name', folder_id)
                if folder_id in skip_set:
                    logger.info(f"generate-load: skipping folder {folder_name} (ID: {folder_id})")
                    continue

                # Find first YDB with storage groups
                try:
                    dbs = user_creator.list_ydb_databases_in_folder(folder_id)
                except UserCreationError as e:
                    logger.error(f"generate-load: failed to list YDB in folder {folder_id}: {e}")
                    continue

                target_db = None
                for db in dbs:
                    if has_ydb_storage_groups(db):
                        target_db = db
                        break

                if not target_db:
                    logger.info(f"generate-load: no YDB with storage groups found in folder {folder_id}")
                    continue

                db_id = target_db['id']
                endpoint = target_db.get('endpoint', '')

                # Generate commands
                init_cmd = (
                    f"ydb --use-metadata-credentials -e {endpoint} -d /ru-central1/{args.cloud_id}/{db_id} "
                    f"workload kv init --auto-partition 0 --max-partitions 1 --min-partitions 1 > init-{db_id} 2>&1"
                )
                mixed_cmd = (
                    f"ydb --use-metadata-credentials -e {endpoint} -d /ru-central1/{args.cloud_id}/{db_id} "
                    f"workload kv run mixed -t 100 --seconds {Constants.LOAD_DURATION_SECONDS} > mixed-{db_id} 2>&1 &"
                )
                select_cmd = (
                    f"ydb --use-metadata-credentials -e {endpoint} -d /ru-central1/{args.cloud_id}/{db_id} "
                    f"workload kv run select --threads 10 --seconds {Constants.LOAD_DURATION_SECONDS} --rows 1000 > mixed-{db_id} 2>&1 &"
                )

                init_f.write(init_cmd + "\n")

                # Rotate batch file if needed
                if mixed_f is None or current_batch_count >= batch_size:
                    # close previous batch file
                    if mixed_f is not None:
                        mixed_f.close()
                    mixed_path = os.path.join(args.output_dir, f"run-mixed-and-select-{batch_no}.bash")
                    mixed_f = open(mixed_path, 'w')
                    mixed_f.write("#!/usr/bin/env bash\n")
                    batch_files.append(mixed_path)
                    batch_no += 1
                    current_batch_count = 0

                mixed_f.write(mixed_cmd + "\n")
                mixed_f.write(select_cmd + "\n")
                generated += 1
                current_batch_count += 1

        # Close the last batch file
        if mixed_f is not None:
            mixed_f.close()

        # Make executable
        try:
            os.chmod(init_path, 0o755)
            for path in batch_files:
                try:
                    os.chmod(path, 0o755)
                except Exception as e:
                    logger.warning(f"Failed to make script executable: {path}: {e}")
        except Exception as e:
            logger.warning(f"Failed to make scripts executable: {e}")

    logger.info(f"generate-load: wrote init.bash and {len(batch_files)} mixed/select batch script(s) to {args.output_dir}. Databases targeted: {generated}")


