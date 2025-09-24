#!/usr/bin/env python3
"""
Custom exceptions for better error handling.
"""


class YandexCloudError(Exception):
    """Base exception for Yandex Cloud operations."""
    pass


class UserCreationError(YandexCloudError):
    """Exception raised during user creation operations."""
    pass


class ValidationError(YandexCloudError):
    """Exception raised during validation operations."""
    pass


class ConfigurationError(YandexCloudError):
    """Exception raised for configuration issues."""
    pass


class OperationError(YandexCloudError):
    """Exception raised during Yandex Cloud operations."""
    pass


class NetworkError(YandexCloudError):
    """Exception raised during network operations."""
    pass
