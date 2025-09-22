#!/usr/bin/env python3
"""
Mode handlers for the Yandex Cloud CLI tool.

Provides run_users_mode and run_ydb_mode entry points used by main.py.
"""

import csv
import time
import logging
import random
import sys
from typing import Tuple

from user_creator import UserCreator, UserCreationError
from validators import (
    validate_userpool_id,
    validate_number_of_users,
    validate_domain,
    validate_created_users_file,
    validate_cloud_id,
)


logger = logging.getLogger(__name__)


class NameGenerator:
    """Generates names from Lord of the Rings and War and Peace characters"""

    LOTR_FIRST_NAMES = [
        "Aragorn", "Gandalf", "Frodo", "Samwise", "Pippin", "Merry", "Legolas",
        "Gimli", "Boromir", "Faramir", "Eowyn", "Arwen", "Galadriel", "Elrond",
        "Thranduil", "Bilbo", "Thorin", "Balin", "Dwalin", "Fili", "Kili",
        "Gloin", "Oin", "Ori", "Dori", "Nori", "Bifur", "Bofur", "Bombur",
        "Smaug", "Gollum", "Saruman", "Grima", "Theoden", "Eomer", "Haldir"
    ]

    WAR_AND_PEACE_FIRST_NAMES = [
        "Pierre", "Andrei", "Natasha", "Marya", "Nikolai", "Sonya", "Anatole",
        "Helene", "Vasily", "Anna", "Boris", "Dolokhov", "Kutuzov", "Bagration",
        "Denisov", "Rostov", "Kutuzov", "Napoleon", "Alexander", "Mikhail",
        "Vera", "Liza", "Petya", "Ilya", "Agafya", "Praskovya", "Dmitri",
        "Fyodor", "Ivan", "Sergei", "Vladimir", "Konstantin", "Pavel"
    ]

    LOTR_LAST_NAMES = [
        "Baggins", "Took", "Brandybuck", "Gamgee", "Strider", "Greyhame",
        "Greenleaf", "Oakenshield", "Ironfoot", "SonofThrain", "SonofGloin",
        "Evenstar", "Rivendell", "Lorien", "Mirkwood", "Gondor", "Rohan",
        "Rivendell", "Shire", "Mordor", "Isengard", "Helms", "Deep",
        "Woodland", "Erebor", "Moria", "Laketown", "Esgaroth", "Dale"
    ]

    WAR_AND_PEACE_LAST_NAMES = [
        "Bezukhov", "Bolkonsky", "Rostov", "Kuragin", "Drubetskoy", "Karagin",
        "Mamonov", "Berg", "Dolokhov", "Zherkov", "Denisov", "Kutuzov",
        "Bagration", "Napoleon", "Alexander", "Smirnov", "Ivanov", "Petrov",
        "Sokolov", "Popov", "Volkov", "Novikov", "Fedorov", "Morozov",
        "Volkov", "Alekseev", "Lebedev", "Semenov", "Egorov", "Pavlov",
        "Kozlov", "Stepanov", "Nikolaev", "Orlov", "Andreev", "Makarov",
        "Nikitin", "Zakharov", "Zaitsev", "Solovyov", "Borisov", "Yakovlev"
    ]

    def __init__(self):
        self.used_names = set()

    def generate_unique_name(self) -> Tuple[str, str]:
        """Generate a unique first and last name combination"""
        max_attempts = 1000
        for _ in range(max_attempts):
            if random.choice([True, False]):
                first_name = random.choice(self.LOTR_FIRST_NAMES)
                last_name = random.choice(self.LOTR_LAST_NAMES)
            else:
                first_name = random.choice(self.WAR_AND_PEACE_FIRST_NAMES)
                last_name = random.choice(self.WAR_AND_PEACE_LAST_NAMES)

            name_combination = f"{first_name} {last_name}"
            if name_combination not in self.used_names:
                self.used_names.add(name_combination)
                return first_name, last_name

        raise UserCreationError("Unable to generate unique name combination")


def generate_username(given_name: str, family_name: str, domain: str) -> str:
    """Generate username from given and family name"""
    base_username = f"{given_name.lower()}{family_name.lower()}"
    if len(base_username) > 12:
        base_username = base_username[:12]
    if not base_username[-1].isalnum():
        base_username = base_username.rstrip('_-') + '1'
    return f"{base_username}@{domain}"


def run_users_mode(args, user_creator: UserCreator) -> None:
    # Validate required parameters for users mode
    if not args.userpool_id:
        logger.error("--userpool-id is required for users mode")
        sys.exit(1)
    if not args.num_users:
        logger.error("--num-users is required for users mode")
        sys.exit(1)

    validate_userpool_id(args.userpool_id)
    validate_number_of_users(args.num_users)
    validate_domain(args.domain)
    validate_created_users_file(args.created_users_file)
    validate_cloud_id(args.cloud_id)

    logger.info(
        f"Starting user creation: {args.num_users} users in pool {args.userpool_id}, cloud {args.cloud_id}"
    )

    name_generator = NameGenerator()
    created_count = 0

    # Open file once, write header, then stream rows as users are created
    f = None
    try:
        f = open(args.created_users_file, 'w')
        f.write("id,username,password\n")
        f.flush()

        for i in range(args.num_users):
            try:
                given_name, family_name = name_generator.generate_unique_name()
                full_name = f"{given_name} {family_name}"
                
                username = generate_username(given_name, family_name, args.domain)
                email = username
                phone_number = f"+1555{i:07d}"
                
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
                
                folder_id = None
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
    except Exception as e:
        logger.error(f"Failed to open or write to file {args.created_users_file}: {e}")
        sys.exit(1)
    finally:
        if f is not None:
            try:
                f.close()
            except Exception:
                pass

    logger.info(f"User creation completed. Successfully created {created_count} users. Output: {args.created_users_file}")


def run_ydb_mode(args, user_creator: UserCreator) -> None:
    validate_cloud_id(args.cloud_id)

    logger.info(f"Starting YDB creation mode for cloud {args.cloud_id}")

    skip_folder_ids = set()
    if args.skip_folder_ids:
        skip_folder_ids = set(folder_id.strip() for folder_id in args.skip_folder_ids.split(','))
        logger.info(f"Will skip folders: {skip_folder_ids}")

    # Determine which folders to process
    target_folders = []
    if getattr(args, 'create_ydb_in_folders', None):
        ids = [fid.strip() for fid in args.create_ydb_in_folders.split(',') if fid.strip()]
        logger.info(f"Will create YDB only in specified folders: {ids}")
        # Build minimal folder objects from IDs; names unknown so set to ID
        target_folders = [{'id': fid, 'name': fid} for fid in ids]
    else:
        target_folders = user_creator.list_folders(args.cloud_id)

    created_databases = 0
    skipped_folders = 0
    max_concurrent = 5
    pending_ops = []  # list of dicts: {folder_id, folder_name, operation_id}

    for folder in target_folders:
        folder_id = folder['id']
        folder_name = folder['name']

        if folder_id in skip_folder_ids:
            logger.info(f"Skipping folder {folder_name} (ID: {folder_id})")
            skipped_folders += 1
            continue

        try:
            # Skip if folder already has a YDB with storageConfig.storageOptions.groupCount > 1
            existing_dbs = user_creator.list_ydb_databases_in_folder(folder_id)
            has_existing_dedicated = False
            for db in existing_dbs:
                opts = db.get('storageConfig', {}).get('storageOptions', [])
                for opt in opts:
                    try:
                        group_count = int(opt.get('groupCount', '0'))
                    except (TypeError, ValueError):
                        group_count = 0
                    if group_count > 1:
                        has_existing_dedicated = True
                        break
                if has_existing_dedicated:
                    break
            if has_existing_dedicated:
                logger.info(f"Folder {folder_name} (ID: {folder_id}) already has a dedicated YDB database (groupCount>1). Skipping.")
                skipped_folders += 1
                continue

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

            # Flow control: if we already have 5 in-flight ops, poll until one finishes
            while len(pending_ops) >= max_concurrent:
                _poll_pending_ops(user_creator, pending_ops)

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
            })

        except UserCreationError as e:
            logger.error(f"Failed to start YDB for folder {folder_name} (ID: {folder_id}): {e}")
            continue

    # Finalize any remaining operations
    while pending_ops:
        created_now = _poll_pending_ops(user_creator, pending_ops)
        created_databases += created_now

    logger.info(f"YDB creation completed. Created {created_databases} databases, skipped {skipped_folders} folders")


def _poll_pending_ops(user_creator: UserCreator, pending_ops: list) -> int:
    """Poll in-flight YDB create operations once, remove finished, return count of successes."""

    successes = 0
    still_pending = []
    for item in pending_ops:
        op_id = item['operation_id']
        folder_name = item['folder_name']
        try:
            data = user_creator.get_operation_status(op_id)
            done = data.get('done', False)
            if not done:
                # If operation reports intermediate error, stop it and log
                if 'error' in data and data['error']:
                    err = data['error']
                    logger.error(
                        f"YDB op {op_id} for folder {folder_name} has failures: "
                        f"status={err.get('code')}, message={err.get('message')}, details={err.get('details')}"
                    )
                else:
                    still_pending.append(item)
                continue

            # done == True
            if 'error' in data and data['error']:
                err = data['error']
                logger.error(
                    f"YDB op {op_id} for folder {folder_name} failed: "
                    f"status={err.get('code')}, message={err.get('message')}, details={err.get('details')}"
                )
            else:
                logger.info(f"YDB op {op_id} for folder {folder_name} completed successfully")
                successes += 1
        except UserCreationError as e:
            logger.error(f"Polling error for op {op_id} (folder {folder_name}): {e}")
            # drop this op from pending to avoid infinite loop
    # Gentle pacing between poll cycles
    if still_pending:
        time.sleep(2)
    pending_ops[:] = still_pending
    return successes


def run_reset_password_mode(args, user_creator: UserCreator) -> None:
    # Validate inputs
    if not args.userpool_id:
        logger.error("--userpool-id is required for reset-password mode")
        sys.exit(1)

    validate_userpool_id(args.userpool_id)
    validate_created_users_file(args.created_users_file)

    # Build username map by listing users (used for output consistency)
    logger.info(f"Listing users from userpool {args.userpool_id} to build username map")
    users = user_creator.list_users_in_userpool(args.userpool_id)
    username_by_id = {u['id']: u.get('username', '') for u in users}

    # Decide target users
    target_user_ids = []
    if getattr(args, 'user_ids', None):
        target_user_ids = [u.strip() for u in args.user_ids.split(',') if u.strip()]
        logger.info(f"Resetting password for provided {len(target_user_ids)} user(s)")
    else:
        target_user_ids = list(username_by_id.keys())
        logger.info(f"Collected {len(target_user_ids)} user(s) to reset from userpool")

    successes = 0
    failures = 0

    f = None
    try:
        # Open output file once and stream results line-by-line (same format as users mode)
        f = open(args.created_users_file, 'w')
        f.write("id,username,password\n")
        f.flush()

        for user_id in target_user_ids:
            try:
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
    except Exception as e:
        logger.error(f"Failed to open or write to file {args.created_users_file}: {e}")
        sys.exit(1)
    finally:
        if f is not None:
            try:
                f.close()
            except Exception:
                pass

    logger.info(f"Password reset completed. Success: {successes}, Failed: {failures}")


def _validate_output_dir(path: str) -> None:
    import os
    if not path:
        raise ValueError("output-dir cannot be empty")
    if not os.path.isdir(path):
        raise ValueError(f"output-dir {path} is not a directory")
    if not os.access(path, os.W_OK):
        raise ValueError(f"output-dir {path} is not writable")


def run_generate_load_mode(args, user_creator: UserCreator) -> None:
    # Validate inputs
    validate_cloud_id(args.cloud_id)
    if args.batch_size < 1 or args.batch_size > 32:
        logger.error("--batch-size must be between 1 and 32")
        sys.exit(1)
    try:
        _validate_output_dir(args.output_dir)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # Resolve folders to process
    if getattr(args, 'folder_ids', None):
        folder_ids = [fid.strip() for fid in args.folder_ids.split(',') if fid.strip()]
        folders = [{'id': fid, 'name': fid} for fid in folder_ids]
        logger.info(f"generate-load: using provided folder IDs: {folder_ids}")
    else:
        folders = user_creator.list_folders(args.cloud_id)
        logger.info(f"generate-load: listed {len(folders)} folders in cloud {args.cloud_id}")

    # Build skip set
    skip_set = set()
    if getattr(args, 'skip_folder_ids', None):
        skip_set = set(fid.strip() for fid in args.skip_folder_ids.split(',') if fid.strip())

    # Open output scripts
    import os
    init_path = os.path.join(args.output_dir, 'init.bash')
    mixed_path = os.path.join(args.output_dir, 'run-mixed-and-select.bash')
    try:
        init_f = open(init_path, 'w')
        mixed_f = open(mixed_path, 'w')
        init_f.write("#!/usr/bin/env bash\n")
        mixed_f.write("#!/usr/bin/env bash\n")
    except Exception as e:
        logger.error(f"Failed to open output scripts: {e}")
        sys.exit(1)

    generated = 0
    try:
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
                opts = db.get('storageConfig', {}).get('storageOptions', [])
                has_groups = False
                for opt in opts:
                    try:
                        group_count = int(opt.get('groupCount', '0'))
                    except (TypeError, ValueError):
                        group_count = 0
                    if group_count > 0:
                        has_groups = True
                        break
                if has_groups:
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
                f"workload kv init --auto-partition 0 --max-partitions 1 --min-partitions 1 > init-{db_id} 2>&1 &"
            )
            mixed_cmd = (
                f"ydb --use-metadata-credentials -e {endpoint} -d /ru-central1/{args.cloud_id}/{db_id} "
                f"workload kv run mixed -t 300 --seconds 3600 > mixed-{db_id} 2>&1 &"
            )
            select_cmd = (
                f"ydb --use-metadata-credentials -e {endpoint} -d /ru-central1/{args.cloud_id}/{db_id} "
                f"workload kv run select --threads 100 --seconds 3600 --rows 100 > mixed-{db_id} 2>&1 &"
            )

            init_f.write(init_cmd + "\n")
            mixed_f.write(mixed_cmd + "\n")
            mixed_f.write(select_cmd + "\n")
            generated += 1

    finally:
        try:
            init_f.close()
            mixed_f.close()
        except Exception:
            pass

    # Make executable
    try:
        os.chmod(init_path, 0o755)
        os.chmod(mixed_path, 0o755)
    except Exception as e:
        logger.warning(f"Failed to make scripts executable: {e}")

    logger.info(f"generate-load: wrote scripts to {args.output_dir}. Databases targeted: {generated}")


