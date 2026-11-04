"""
Security utilities for DataVault Backend
Handles JWT token validation and device authentication
"""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import uuid

class BackendJWTManager:
    """Manages JWT validation for backend services"""

    def __init__(self, operator_public_key: Optional[str] = None):
        """
        Initialize backend JWT manager with operator's public key

        Args:
            operator_public_key: PEM-encoded public key from operator
        """
        self.operator_public_key = operator_public_key
        self.algorithm = "RS256"

    def verify_operator_token(self, token: str) -> Dict:
        """
        Verify a token signed by the operator

        Args:
            token: JWT token string

        Returns:
            Decoded payload

        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
        """
        if not self.operator_public_key:
            raise ValueError("Operator public key not configured")

        payload = jwt.decode(token, self.operator_public_key, algorithms=[self.algorithm])
        return payload


class DeviceAuth:
    """Handles device authentication and binding"""

    def __init__(self, secret_key: str):
        """
        Initialize device auth with secret key

        Args:
            secret_key: Secret key for signing device tokens
        """
        self.secret_key = secret_key
        self.algorithm = "HS256"

    def generate_device_token(self, device_id: str, imei: str) -> str:
        """
        Generate an authentication token for a device

        Args:
            device_id: Device identifier
            imei: Device IMEI

        Returns:
            Device authentication token
        """
        payload = {
            "device_id": device_id,
            "imei": imei,
            "type": "device_auth",
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_device_token(self, token: str, expected_device_id: Optional[str] = None) -> Dict:
        """
        Verify device authentication token

        Args:
            token: Device authentication token
            expected_device_id: Optional expected device ID

        Returns:
            Decoded token payload

        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
            ValueError: Device ID mismatch
        """
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

        if payload.get("type") != "device_auth":
            raise ValueError("Invalid token type")

        if expected_device_id and payload.get("device_id") != expected_device_id:
            raise ValueError("Device ID mismatch")

        return payload
