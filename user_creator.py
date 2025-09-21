#!/usr/bin/env python3
"""
UserCreator class for Yandex Cloud User Creation CLI Tool

This module handles user creation, folder creation, and access management
using the Yandex Cloud organization-manager and resource-manager APIs.
"""

import logging
import requests
import time
import sys
from typing import Tuple


logger = logging.getLogger(__name__)


class UserCreationError(Exception):
    """Custom exception for user creation errors"""
    pass


class UserCreator:
    """Handles user creation, folder creation, and access management in Yandex Cloud"""
    
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
            
            if folder_id is None:
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
    
    def poll_operation(self, operation_id: str, operation_description: str = "operation") -> dict:
        """Poll operation status until completion"""
        url = f"https://operation.api.cloud.yandex.net/operations/{operation_id}"
        
        logger.info(f"Starting polling for {operation_description} (ID: {operation_id})")
        
        while True:
            try:
                response = self.session.get(url)
                response.raise_for_status()
                data = response.json()
                
                done = data.get('done', False)
                
                # Check if operation is done
                if done:
                    # Operation finished, check for errors
                    if 'error' in data and data['error']:
                        error = data['error']
                        logger.error(f"Operation {operation_id} failed: "
                                   f"status={error.get('code', 'unknown')}, "
                                   f"message='{error.get('message', 'no message')}', "
                                   f"details={error.get('details', {})}")
                        raise UserCreationError(f"Operation {operation_description} failed: {error.get('message', 'Unknown error')}")
                    else:
                        logger.info(f"Operation {operation_description} completed successfully (ID: {operation_id})")
                        return data.get('response', {})
                else:
                    # Operation not done yet, check for errors
                    if 'error' in data and data['error']:
                        error = data['error']
                        logger.warning(f"Operation {operation_id} has failures during execution: "
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
