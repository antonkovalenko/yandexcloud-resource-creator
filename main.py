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


# Configure logging to stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
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
            # Randomly choose between LOTR and War and Peace names
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
    # Create base username (max 12 characters)
    base_username = f"{given_name.lower()}{family_name.lower()}"
    
    # Truncate if too long
    if len(base_username) > 12:
        base_username = base_username[:12]
    
    # Ensure it ends with a letter or digit
    if not base_username[-1].isalnum():
        base_username = base_username.rstrip('_-') + '1'
    
    return f"{base_username}@{domain}"


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Create users in Yandex Cloud",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--userpool-id',
        required=True,
        help='User pool ID (string of letters and digits, max 32 characters)'
    )
    
    parser.add_argument(
        '--num-users',
        type=int,
        required=True,
        help='Number of users to create (1-100)'
    )
    
    parser.add_argument(
        '--domain',
        required=False,
        default='ydbem.idp.yandexcloud.net',
        help='Domain name for user emails'
    )

    #add argument to specify filename for list of created users
    parser.add_argument(
        '--created-users-file',
        required=False,
        default='created_users.txt',
        help='Filename for list of created users'
    )

    # add argument to pass cloud-id. Cloud id is a string of letters and digits, can not be longer than 32 cannot be empty or ommitted
    parser.add_argument(
        '--cloud-id',
        required=False,
        default='b1gad4empjmov1cn3ahu',
        help='Cloud id to add users to'
    )
    
    args = parser.parse_args()
    
    # Validate IAM token
    iam_token = os.getenv('IAM_TOKEN')
    if not iam_token:
        logger.error("IAM_TOKEN environment variable is required")
        sys.exit(1)
    
    try:
        # Validate parameters
        validate_userpool_id(args.userpool_id)
        validate_number_of_users(args.num_users)
        validate_domain(args.domain)
        validate_created_users_file(args.created_users_file)
        validate_cloud_id(args.cloud_id)
        
        logger.info(f"Starting user creation: {args.num_users} users in pool {args.userpool_id}, cloud {args.cloud_id}")
        
        # Initialize components
        name_generator = NameGenerator()
        user_creator = UserCreator(iam_token)
        
        created_users = []
        
        # Create users
        for i in range(args.num_users):
            try:
                # Generate unique name
                given_name, family_name = name_generator.generate_unique_name()
                full_name = f"{given_name} {family_name}"
                
                # Generate username and email
                username = generate_username(given_name, family_name, args.domain)
                email = username  # Username is already in email format
                phone_number = f"+1555{i:07d}"  # Generate dummy phone number
                
                # Generate password
                password, generation_proof = user_creator.generate_password()
                
                # Create user
                user_id = user_creator.create_user(
                    userpool_id=args.userpool_id,
                    username=username,
                    full_name=full_name,
                    given_name=given_name,
                    family_name=family_name,
                    email=email,
                    phone_number=phone_number,
                    password=password,
                    generation_proof=generation_proof
                )
                
                # Create folder for the user
                try:
                    folder_id = user_creator.create_folder(
                        cloud_id=args.cloud_id,
                        folder_name=given_name.lower() + "-" + family_name.lower(),
                        description=f"Personal folder for user {full_name}"
                    )
                    
                    # Grant editor role to the user for their folder
                    user_creator.grant_folder_access(
                        folder_id=folder_id,
                        user_id=user_id,
                        role_id='editor'
                    )

                    # Grant resource-manager.clouds.member role to the user we have created to the cloud
                    user_creator.grant_cloud_access(
                        cloud_id=args.cloud_id,
                        user_id=user_id,
                        role_id='resource-manager.clouds.member'
                    )                    
                    
                    logger.info(f"Folder and access created for user {username}")
                                       
                except UserCreationError as e:
                    logger.error(f"Failed to create folder/access for user {username}: {e}")
                    # Continue with user creation even if folder creation fails
                    folder_id = None

                # Create virtual private network with 3 subnets in the just created folder
                network_id = None
                subnet_ids = []
                try:
                    network_id, subnet_ids = user_creator.create_vpc_with_subnets(
                        folder_id=folder_id,
                        network_name=f"vpc-" + given_name.lower() + "-" + family_name.lower(),
                        description=f"VPC network for user {username}"
                    )
                    logger.info(f"VPC network created for user {username}: {network_id}")
                    
                    # Create YDB database using the created network and subnets
                    try:
                        database_id = user_creator.create_ydb_database(
                            folder_id=folder_id,
                            network_id=network_id,
                            subnet_ids=subnet_ids,
                            database_name=f"ydb-" + given_name.lower() + "-" + family_name.lower(),
                            description=f"YDB database for user {username}"
                        )
                        logger.info(f"YDB database created for user {username}: {database_id}")
                        
                    except UserCreationError as e:
                        logger.error(f"Failed to create YDB database for user {username}: {e}")
                        # Continue with user creation even if YDB creation fails
                    
                except UserCreationError as e:
                    logger.error(f"Failed to create VPC for user {username}: {e}")
                    # Continue with user creation even if VPC creation fails

                created_users.append({
                    'id': user_id,
                    'username': username,
                    'full_name': full_name,
                    'password': password,
                    'network_id': network_id,
                    'subnet_ids': subnet_ids,
                    'database_id': database_id,
                    'folder_id': folder_id
                })
                
                logger.info(f"Created user {i+1}/{args.num_users}: {username} ({full_name}) id: {user_id}")
                 
                
            except UserCreationError as e:
                logger.error(f"Failed to create user {i+1}: {e}")
                continue
        
        logger.info(f"User creation completed. Successfully created {len(created_users)} users")
        
        # Write created users to file
        # use ready csv module to write list of dicts to file and add header with keys
        # handle the exception if file already exists or other error occurs and log the error
        try:
            with open(args.created_users_file, 'w') as f:
                writer = csv.DictWriter(f, created_users[0].keys())
                writer.writeheader()
                writer.writerows(created_users)
        except FileExistsError:
            logger.error(f"File {args.created_users_file} already exists")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to write created users to file: {e}")
            sys.exit(1)
        
        
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
