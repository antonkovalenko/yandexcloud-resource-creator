#!/usr/bin/env python3
"""
UserCreator class for Yandex Cloud User Creation CLI Tool

This module handles user creation, folder creation, and access management
using the Yandex Cloud organization-manager and resource-manager APIs.
"""

import logging
import re
import requests
import sys
import time
from typing import Tuple


logger = logging.getLogger(__name__)


class UserCreationError(Exception):
    """Custom exception for user creation errors"""
    pass


class UserCreator:
    """Handles user creation, folder creation, and access management in Yandex Cloud"""
    # Availability zones used across VPC/subnet creation and checks
    ZONES = ["ru-central1-a", "ru-central1-b", "ru-central1-d"]
    MAX_POLL_RETRIES = 5
    VALID_OWN_PASSWORD = 'YdbAdmin$2025'
    MAX_CONCURRENT_OPERATIONS = 15
    def __init__(self, iam_token: str):
        self.iam_token = iam_token
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {iam_token}',
            'Content-Type': 'application/json'
        })
    
    def generate_password(self) -> Tuple[str, str]:
        """Generate password using Yandex Cloud API"""
        url = "https://organization-manager.api.cloud.yandex.net/organization-manager/v1/idp/users:generatePassword"
        
        try:
            response = self.session.post(url)
            response.raise_for_status()
            data = response.json()
            
            password = data['passwordSpec']['password']
            generation_proof = data['passwordSpec']['generationProof']
            
            logger.info("Password generated successfully")
            return password, generation_proof
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to generate password: {e}")
            raise UserCreationError(f"Password generation failed: {e}")
    # sample response 
    #     {
    #   "id": "string",
    #   "description": "string",
    #   "createdAt": "string",
    #   "createdBy": "string",
    #   "modifiedAt": "string",
    #   "done": "boolean",
    #   "metadata": {
    #     "userId": "string"
    #   },
    #   // Includes only one of the fields `error`, `response`
    #   "error": {
    #     "code": "integer",
    #     "message": "string",
    #     "details": [
    #       "object"
    #     ]
    #   },
    #   "response": {
    #     "id": "string",
    #     "userpoolId": "string",
    #     "status": "string",
    #     "username": "string",
    #     "fullName": "string",
    #     "givenName": "string",
    #     "familyName": "string",
    #     "email": "string",
    #     "phoneNumber": "string",
    #     "createdAt": "string",
    #     "updatedAt": "string",
    #     "externalId": "string"
    #   }
    #   // end of the list of possible fields
    # }

    def create_user(self, userpool_id: str, username: str, full_name: str, 
                   given_name: str, family_name: str, email: str, 
                   phone_number: str, password: str, generation_proof: str) -> dict:
        """Create a user using Yandex Cloud API"""
        url = "https://organization-manager.api.cloud.yandex.net/organization-manager/v1/idp/users"
        
        payload = {
            "userpoolId": userpool_id,
            "username": username,
            "fullName": full_name,
            "givenName": given_name,
            "familyName": family_name,
            "email": email,
            "phoneNumber": phone_number,
            "passwordSpec": {
                "password": password,
                "generationProof": generation_proof
            },
            "isActive": True
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Failed to create user {username}: {data['error']}")
                raise UserCreationError(f"User creation failed: {data['error']['message']}")
            
            # Get operation ID and poll until completion
            operation_id = data['id']
            operation_description = f"user creation for {username}"
            
            # Poll the operation until it's complete
            operation_response = self.poll_operation(operation_id, operation_description)
            # Extract user_id from the completed operation response
            user_id = operation_response['id']
            
            logger.info(f"User creation request submitted for {username}")
            return user_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create user {username}: {e} {response.text}")
            raise UserCreationError(f"User creation failed: {e}")
    
    def create_folder(self, cloud_id: str, folder_name: str, description: str = None) -> str:
        """Create a folder in Yandex Cloud"""
        url = "https://resource-manager.api.cloud.yandex.net/resource-manager/v1/folders"
        
        payload = {
            "cloudId": cloud_id,
            "name": folder_name,
            "description": description or f"Personal folder for user {folder_name}",
            "labels": {}
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            if 'error' in data:
                logger.error(f"Failed to create folder {folder_name}: {data['error']}")
                raise UserCreationError(f"Folder creation failed: {data['error']['message']}")
            
            # Get operation ID and poll until completion
            operation_id = data['id']
            operation_description = f"folder creation for {folder_name}"
            # Poll the operation until it's complete
            operation_response = self.poll_operation(operation_id, operation_description)            
            folder_id = operation_response['id']
            logger.info(f"Folder created successfully: {folder_name} (ID: {folder_id})")
            return folder_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create folder {folder_name}: {e} {response.text}")
            raise UserCreationError(f"Folder creation failed: {e}")
    
    def grant_folder_access(self, folder_id: str, user_id: str, role_id: str = 'editor') -> None:
        """Grant access to a folder for a user"""
        url = f"https://resource-manager.api.cloud.yandex.net/resource-manager/v1/folders/{folder_id}:setAccessBindings"
        
        payload = {
            "accessBindings": [
                {
                    "roleId": role_id,
                    "subject": {
                        "id": user_id,
                        "type": "userAccount"
                    }
                }
            ]
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Failed to grant access for user {user_id} to folder {folder_id}: {data['error']}")
                raise UserCreationError(f"Access grant failed: {data['error']['message']}")
            
            logger.info(f"Access granted successfully: user {user_id} -> role {role_id} -> folder {folder_id}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to grant access for user {user_id} to folder {folder_id}: {e} {response.text}")
            raise UserCreationError(f"Access grant failed: {e}")
    
    def grant_cloud_access(self, cloud_id: str, user_id: str, role_id: str = 'editor') -> None:
        """Grant access to a cloud for a user"""
        url = f"https://resource-manager.api.cloud.yandex.net/resource-manager/v1/clouds/{cloud_id}:updateAccessBindings"
        
        payload = {
            "accessBindingDeltas": [
                {
                    "action": "ADD",
                    "accessBinding": {
                        "roleId": role_id,
                        "subject": {
                            "id": user_id,
                            "type": "userAccount"
                        }
                    }
                }
            ]
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Failed to grant cloud access for user {user_id} to cloud {cloud_id}: {data['error']}")
                raise UserCreationError(f"Cloud access grant failed: {data['error']['message']}")
            
            # Get operation ID and poll until completion
            operation_id = data['id']
            operation_description = f"cloud access grant for user {user_id} to cloud {cloud_id}"
            
            # Poll the operation until it's complete
            self.poll_operation(operation_id, operation_description)
            
            logger.info(f"Cloud access granted successfully: user {user_id} -> role {role_id} -> cloud {cloud_id}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to grant cloud access for user {user_id} to cloud {cloud_id}: {e} {response.text}")
            raise UserCreationError(f"Cloud access grant failed: {e}")
    
    def create_vpc_with_subnets(self, folder_id: str, network_name: str = None, description: str = None) -> tuple:
        """Create a VPC network with 3 subnets in different zones"""
        if not network_name:
            network_name = f"vpc-network-{folder_id}"
        if not description:
            description = f"VPC network for folder {folder_id}"
        
        # Create the network first
        network_id = self._create_network(folder_id, network_name, description)
        
        # Create 3 subnets in different zones
        zones = self.ZONES
        subnet_ids = []
        
        for i, zone in enumerate(zones, 1):
            subnet_name = f"{network_name}-subnet-{zone}"
            subnet_description = f"Subnet in {zone} for {network_name}"
            cidr_block = f"192.168.{i}.0/24"  # 192.168.1.0/24, 192.168.2.0/24, 192.168.3.0/24
            
            subnet_id = self._create_subnet(
                folder_id=folder_id,
                network_id=network_id,
                zone_id=zone,
                name=subnet_name,
                description=subnet_description,
                cidr_block=cidr_block
            )
            subnet_ids.append(subnet_id)
        
        logger.info(f"VPC network created successfully: {network_name} (ID: {network_id}) with subnets: {subnet_ids}")
        return network_id, subnet_ids
    
    def _create_network(self, folder_id: str, name: str, description: str) -> str:
        """Create a VPC network"""
        url = "https://vpc.api.cloud.yandex.net/vpc/v1/networks"
        
        payload = {
            "folderId": folder_id,
            "name": name,
            "description": description,
            "labels": {}
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Failed to create network {name}: {data['error']}")
                raise UserCreationError(f"Network creation failed: {data['error']['message']}")
            
            # Get operation ID and poll until completion
            operation_id = data['id']
            operation_description = f"network creation for {name}"
            
            # Poll the operation until it's complete
            operation_response = self.poll_operation(operation_id, operation_description)
            
            network_id = operation_response['id']
            logger.info(f"Network created successfully: {name} (ID: {network_id})")
            return network_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create network {name}: {e} {response.text}")
            raise UserCreationError(f"Network creation failed: {e}")
    
    def _create_subnet(self, folder_id: str, network_id: str, zone_id: str, name: str, description: str, cidr_block: str) -> str:
        """Create a subnet in a specific zone"""
        url = "https://vpc.api.cloud.yandex.net/vpc/v1/subnets"
        
        payload = {
            "folderId": folder_id,
            "name": name,
            "description": description,
            "labels": {},
            "networkId": network_id,
            "zoneId": zone_id,
            "v4CidrBlocks": [cidr_block]
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Failed to create subnet {name}: {data['error']}")
                raise UserCreationError(f"Subnet creation failed: {data['error']['message']}")
            
            # Get operation ID and poll until completion
            operation_id = data['id']
            operation_description = f"subnet creation for {name} in {zone_id}"
            
            # Poll the operation until it's complete
            operation_response = self.poll_operation(operation_id, operation_description)
            
            subnet_id = operation_response['id']
            logger.info(f"Subnet created successfully: {name} (ID: {subnet_id}) in zone {zone_id} with CIDR {cidr_block}")
            return subnet_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create subnet {name}: {e} {response.text}")
            raise UserCreationError(f"Subnet creation failed: {e}")
    
    def create_ydb_database(self, folder_id: str, network_id: str, subnet_ids: list, database_name: str = None, description: str = None) -> str:
        """Create a YDB database with the specified configuration"""
        if not database_name:
            database_name = f"ydb-database-{folder_id}"
        if not description:
            description = f"YDB database for folder {folder_id}"
        
        # Validate resource name pattern: /|[a-zA-Z]([-_a-zA-Z0-9]{0,61}[a-zA-Z0-9])?/
        if not self._is_valid_ydb_resource_name(database_name):
            raise UserCreationError(f"Invalid database name '{database_name}'. Must match pattern /|[a-zA-Z]([-_a-zA-Z0-9]{{0,61}}[a-zA-Z0-9])?/")
        
        url = "https://ydb.api.cloud.yandex.net/ydb/v1/databases"
        
        payload = {
            "folderId": folder_id,
            "name": database_name,
            "description": description,
            "resourcePresetId": "small-m8",
            "storageConfig": {
                "storageOptions": [
                    {
                        "storageTypeId": "ssd",
                        "groupCount": "1"
                    }
                ]
            },
            "scalePolicy": {
                "fixedScale": {
                    "size": "1"
                }
            },
            "networkId": network_id,
            "subnetIds": subnet_ids,
            "dedicatedDatabase": {
                "resourcePresetId": "small-m8",
                "storageConfig": {
                    "storageOptions": [
                        {
                            "storageTypeId": "ssd",
                            "groupCount": "1"
                        }
                    ]
                },
                "scalePolicy": {
                    "fixedScale": {
                        "size": "1"
                    }
                },
                "networkId": network_id,
                "subnetIds": subnet_ids,
                "assignPublicIps": False
            },
            "assignPublicIps": False,
            "labels": {}
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Failed to create YDB database {database_name}: {data['error']}")
                raise UserCreationError(f"YDB database creation failed: {data['error']['message']}")
            
            # Get operation ID and poll until completion
            operation_id = data['id']
            operation_description = f"YDB database creation for {database_name}"
            
            # Poll the operation until it's complete
            operation_response = self.poll_operation(operation_id, operation_description)
            
            database_id = operation_response['id']
            logger.info(f"YDB database created successfully: {database_name} (ID: {database_id})")
            return database_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create YDB database {database_name}: {e} {response.text}")
            raise UserCreationError(f"YDB database creation failed: {e}")

    def start_ydb_database(self, folder_id: str, network_id: str, subnet_ids: list, database_name: str = None, description: str = None) -> str:
        """Start YDB database creation and return operation ID without waiting for completion"""
        if not database_name:
            database_name = f"ydb-database-{folder_id}"
        if not description:
            description = f"YDB database for folder {folder_id}"

        if not self._is_valid_ydb_resource_name(database_name):
            raise UserCreationError(f"Invalid database name '{database_name}'. Must match pattern /|[a-zA-Z]([-_a-zA-Z0-9]{0,61}[a-zA-Z0-9])?/")

        url = "https://ydb.api.cloud.yandex.net/ydb/v1/databases"

        payload = {
            "folderId": folder_id,
            "name": database_name,
            "description": description,
            "resourcePresetId": "small-m8",
            "storageConfig": {
                "storageOptions": [
                    {"storageTypeId": "ssd", "groupCount": "1"}
                ]
            },
            "scalePolicy": {"fixedScale": {"size": "1"}},
            "networkId": network_id,
            "subnetIds": subnet_ids,
            "dedicatedDatabase": {
                "resourcePresetId": "small-m8",
                "storageConfig": {"storageOptions": [{"storageTypeId": "ssd", "groupCount": "1"}]},
                "scalePolicy": {"fixedScale": {"size": "1"}},
                "networkId": network_id,
                "subnetIds": subnet_ids,
                "assignPublicIps": False,
            },
            "assignPublicIps": False,
            "labels": {},
        }

        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

            if 'error' in data:
                logger.error(f"Failed to start YDB database {database_name}: {data['error']}")
                raise UserCreationError(f"YDB database start failed: {data['error']['message']}")

            operation_id = data['id']
            logger.info(f"YDB create operation started for {database_name} (op: {operation_id})")
            return operation_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to start YDB database {database_name}: {e} {response.text}")
            raise UserCreationError(f"YDB database start failed: {e}")

    def start_ydb_database_deletion(self, database_id: str) -> str:
        """Start YDB database deletion and return operation ID without waiting for completion"""
        url = f"https://ydb.api.cloud.yandex.net/ydb/v1/databases/{database_id}"
        
        try:
            response = self.session.delete(url)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Failed to start YDB database deletion {database_id}: {data['error']}")
                raise UserCreationError(f"YDB database deletion start failed: {data['error']['message']}")
            
            operation_id = data['id']
            logger.info(f"YDB delete operation started for database {database_id} (op: {operation_id})")
            return operation_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to start YDB database deletion {database_id}: {e} {response.text if 'response' in locals() else ''}")
            raise UserCreationError(f"YDB database deletion start failed: {e}")

    def get_operation_status(self, operation_id: str) -> dict:
        """Fetch operation status once (non-blocking) and return the JSON."""
        url = f"https://operation.api.cloud.yandex.net/operations/{operation_id}"
        for attempt in range(1, self.MAX_POLL_RETRIES + 1):
            try:
                response = self.session.get(url)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt >= self.MAX_POLL_RETRIES:
                    logger.error(f"Failed to fetch operation status for {operation_id} after {attempt} attempts: {e}")
                    raise UserCreationError(f"Operation status fetch failed: {e}")
                delay = 2 ** (attempt - 1)
                logger.warning(
                    f"Fetch status retry {attempt}/{self.MAX_POLL_RETRIES} for op {operation_id} in {delay}s due to error: {e}"
                )
                time.sleep(delay)

    def list_users_in_userpool(self, userpool_id: str, page_size: int = 1000) -> list:
        """List users in a userpool, handling pagination."""
        url = "https://organization-manager.api.cloud.yandex.net/organization-manager/v1/idp/users"
        users = []
        page_token = None
        while True:
            params = {
                'userpoolId': userpool_id,
                'pageSize': str(page_size),
            }
            if page_token:
                params['pageToken'] = page_token
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if 'error' in data:
                    logger.error(f"Failed to list users in userpool {userpool_id}: {data['error']}")
                    raise UserCreationError(f"List users failed: {data['error']['message']}")
                batch = data.get('users', [])
                users.extend(batch)
                page_token = data.get('nextPageToken')
                if not page_token:
                    break
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to list users in userpool {userpool_id}: {e}")
                raise UserCreationError(f"List users failed: {e}")
        logger.info(f"Listed {len(users)} users in userpool {userpool_id}")
        return users

    def set_others_password(self, user_id: str, password: str, generation_proof: str) -> None:
        """Set password for a user as an administrator, with operation polling."""
        url = f"https://organization-manager.api.cloud.yandex.net/organization-manager/v1/idp/users/{user_id}:setOthersPassword"
        payload = {
            "passwordSpec": {
                "password": password,
                "generationProof": generation_proof,
            }
        }
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            if 'error' in data:
                logger.error(f"Failed to start setOthersPassword for user {user_id}: {data['error']}")
                raise UserCreationError(f"setOthersPassword failed: {data['error']['message']}")
            operation_id = data['id']
            op_desc = f"setOthersPassword for user {user_id}"
            self.poll_operation(operation_id, op_desc)
            logger.info(f"Password reset completed for user {user_id}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call setOthersPassword for user {user_id}: {e} {response.text if 'response' in locals() else ''}")
            raise UserCreationError(f"setOthersPassword request failed: {e}")
    
    def _is_valid_ydb_resource_name(self, name: str) -> bool:
        """Validate YDB resource name pattern: /|[a-zA-Z]([-_a-zA-Z0-9]{0,61}[a-zA-Z0-9])?/"""
        # Pattern: start with letter, then 0-61 chars of letters/numbers/dash/underscore, end with letter or number
        pattern = r'^[a-zA-Z]([-_a-zA-Z0-9]{0,61}[a-zA-Z0-9])?$'
        return bool(re.match(pattern, name))
    
    def list_folders(self, cloud_id: str) -> list:
        """List all folders in a cloud"""
        url = f"https://resource-manager.api.cloud.yandex.net/resource-manager/v1/folders"
        
        params = {
            'cloudId': cloud_id
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Failed to list folders in cloud {cloud_id}: {data['error']}")
                raise UserCreationError(f"Failed to list folders: {data['error']['message']}")
            
            folders = data.get('folders', [])
            logger.info(f"Found {len(folders)} folders in cloud {cloud_id}")
            return folders
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list folders in cloud {cloud_id}: {e}")
            raise UserCreationError(f"Failed to list folders: {e}")

    def list_ydb_databases_in_folder(self, folder_id: str, page_size: int = 1000) -> list:
        """List YDB databases in a folder (handles pagination)."""
        url = "https://ydb.api.cloud.yandex.net/ydb/v1/databases"
        databases = []
        page_token = None
        while True:
            params = {
                'folderId': folder_id,
                'pageSize': str(page_size),
            }
            if page_token:
                params['pageToken'] = page_token
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if 'error' in data:
                    logger.error(f"Failed to list YDB databases in folder {folder_id}: {data['error']}")
                    raise UserCreationError(f"List YDB databases failed: {data['error']['message']}")
                databases.extend(data.get('databases', []))
                page_token = data.get('nextPageToken')
                if not page_token:
                    break
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to list YDB databases in folder {folder_id}: {e}")
                raise UserCreationError(f"List YDB databases failed: {e}")
        logger.info(f"Listed {len(databases)} YDB databases in folder {folder_id}")
        return databases
    
    def list_networks(self, folder_id: str) -> list:
        """List all networks in a folder"""
        url = "https://vpc.api.cloud.yandex.net/vpc/v1/networks"
        #always return list with this only element enp405qc235ru1ci9vdj
        folder_id = 'b1gofk0fh5qlc1plb7oe'
        
        params = {
            'folderId': folder_id
        }
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Failed to list networks in folder {folder_id}: {data['error']}")
                raise UserCreationError(f"Failed to list networks: {data['error']['message']}")
            
            networks = data.get('networks', [])
            logger.info(f"Found {len(networks)} networks in folder {folder_id}")
            return networks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list networks in folder {folder_id}: {e}")
            raise UserCreationError(f"Failed to list networks: {e}")
    
    def list_subnets(self, network_id: str) -> list:
        """List all subnets in a network"""
        url = f"https://vpc.api.cloud.yandex.net/vpc/v1/networks/{network_id}/subnets"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                logger.error(f"Failed to list subnets for network {network_id}: {data['error']}")
                raise UserCreationError(f"Failed to list subnets: {data['error']['message']}")
            
            subnets = data.get('subnets', [])
            logger.info(f"Found {len(subnets)} subnets in network {network_id}")
            return subnets
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list subnets for network {network_id}: {e}")
            raise UserCreationError(f"Failed to list subnets: {e}")
    
    def check_existing_vpc(self, folder_id: str) -> tuple:
        """Check if folder has existing VPC with subnets in all required zones"""
        required_zones = self.ZONES
        
        try:
            # List networks in the folder
            networks = self.list_networks(folder_id)
            
            if not networks:
                logger.info(f"No networks found in folder {folder_id}")
                return None, []
            
            # Check each network for complete subnet coverage
            for network in networks:
                network_id = network['id']
                network_name = network['name']
                
                # Get subnets for this network
                subnets = self.list_subnets(network_id)
                
                if not subnets:
                    logger.info(f"Network {network_name} (ID: {network_id}) has no subnets")
                    continue
                
                # Check if we have subnets in all required zones
                subnet_zones = set()
                subnet_ids = []
                
                for subnet in subnets:
                    zone_id = subnet['zoneId']
                    subnet_zones.add(zone_id)
                    subnet_ids.append(subnet['id'])
                
                # Check if all required zones are covered
                if subnet_zones.issuperset(set(required_zones)):
                    logger.info(f"Found existing VPC {network_name} (ID: {network_id}) with subnets in all required zones: {subnet_zones}")
                    return network_id, subnet_ids
                else:
                    missing_zones = set(required_zones) - subnet_zones
                    logger.info(f"Network {network_name} (ID: {network_id}) missing subnets in zones: {missing_zones}")
            
            logger.info(f"No complete VPC found in folder {folder_id}")
            return None, []
            
        except UserCreationError:
            # Re-raise UserCreationError as-is
            raise
        except Exception as e:
            logger.error(f"Error checking existing VPC in folder {folder_id}: {e}")
            raise UserCreationError(f"Failed to check existing VPC: {e}")
    
    def poll_operation(self, operation_id: str, operation_description: str = "operation") -> dict:
        """Poll operation status until completion"""
        url = f"https://operation.api.cloud.yandex.net/operations/{operation_id}"
        
        logger.info(f"Starting polling for {operation_description} (ID: {operation_id})")
        start_time = time.time()
        
        while True:
            try:
                # GET with retries and backoff
                last_error = None
                for attempt in range(1, self.MAX_POLL_RETRIES + 1):
                    try:
                        response = self.session.get(url)
                        response.raise_for_status()
                        data = response.json()
                        break
                    except requests.exceptions.RequestException as e:
                        last_error = e
                        if attempt >= self.MAX_POLL_RETRIES:
                            raise
                        delay = 2 ** (attempt - 1)
                        logger.warning(
                            f"Poll retry {attempt}/{self.MAX_POLL_RETRIES} for {operation_description} (ID: {operation_id}) in {delay}s due to error: {e}"
                        )
                        time.sleep(delay)
                
                done = data.get('done', False)
                
                # Check if operation is done
                if done:
                    # Operation finished, check for errors
                    if 'error' in data and data['error']:
                        error = data['error']
                        elapsed_time = time.time() - start_time
                        logger.error(f"Operation {operation_id} failed after {elapsed_time:.2f}s: "
                                   f"status={error.get('code', 'unknown')}, "
                                   f"message='{error.get('message', 'no message')}', "
                                   f"details={error.get('details', {})}")
                        raise UserCreationError(f"Operation {operation_description} failed: {error.get('message', 'Unknown error')}")
                    else:
                        elapsed_time = time.time() - start_time
                        logger.info(f"Operation {operation_description} completed successfully (ID: {operation_id}) in {elapsed_time:.2f}s")
                        return data.get('response', {})
                else:
                    # Operation not done yet, check for errors
                    if 'error' in data and data['error']:
                        error = data['error']
                        elapsed_time = time.time() - start_time
                        logger.warning(f"Operation {operation_id} has failures during execution after {elapsed_time:.2f}s: "
                                     f"status={error.get('code', 'unknown')}, "
                                     f"message='{error.get('message', 'no message')}', "
                                     f"details={error.get('details', {})}")
                        raise UserCreationError(f"Operation {operation_description} failed during execution: {error.get('message', 'Unknown error')}")
                    
                    # Operation still in progress, wait and continue polling
                    logger.debug(f"Operation {operation_description} still in progress (ID: {operation_id})")
                    time.sleep(2)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to poll operation {operation_id}: {e}")
                raise UserCreationError(f"Failed to poll {operation_description}: {e}")
