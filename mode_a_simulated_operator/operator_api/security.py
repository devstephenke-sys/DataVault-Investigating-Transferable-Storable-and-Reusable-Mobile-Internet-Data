"""
Security utilities for DataVault
Handles JWT token generation, validation, and key management
"""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import uuid

class JWTManager:
    """Manages JWT tokens with RS256 asymmetric encryption"""

    def __init__(self, private_key: Optional[str] = None, public_key: Optional[str] = None):
        """
        Initialize JWT manager with RSA keys

        Args:
            private_key: PEM-encoded private key (optional, will generate if not provided)
            public_key: PEM-encoded public key (optional, will generate if not provided)
        """
        if private_key and public_key:
            self.private_key = private_key
            self.public_key = public_key
        else:
            # Generate new RSA key pair
            self.private_key, self.public_key = self._generate_rsa_key_pair()

        self.algorithm = "RS256"

    @staticmethod
    def _generate_rsa_key_pair() -> tuple[str, str]:
        """Generate RSA key pair for JWT signing"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Serialize private key
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        # Serialize public key
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        return private_pem, public_pem

    def generate_token(self, payload: Dict, expires_in_hours: int = 720) -> str:
        """
        Generate a signed JWT token

        Args:
            payload: Data to include in token
            expires_in_hours: Token expiry time in hours (default: 720 = 30 days)

        Returns:
            Signed JWT token string
        """
        # Add expiry and issued at
        payload['iat'] = datetime.utcnow()
        payload['exp'] = datetime.utcnow() + timedelta(hours=expires_in_hours)
        payload['jti'] = str(uuid.uuid4())  # Unique token ID

        token = jwt.encode(payload, self.private_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Dict:
        """
        Verify and decode a JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded payload

        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
        """
        payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm])
        return payload

    def decode_without_verification(self, token: str) -> Dict:
        """
        Decode token without verification (for debugging only)
        WARNING: Never use this in production for authorization decisions
        """
        return jwt.decode(token, options={"verify_signature": False})


class SubscriberAuth:
    """Handles subscriber authorization"""

    def __init__(self, jwt_manager: JWTManager):
        self.jwt_manager = jwt_manager

    def generate_auth_token(self, subscriber_id: str, device_id: Optional[str] = None) -> str:
        """
        Generate an authorization token for a subscriber

        Args:
            subscriber_id: Subscriber identifier
            device_id: Optional device identifier for binding

        Returns:
            Authorization token
        """
        payload = {
            "sub": subscriber_id,
            "type": "subscriber_auth",
            "device_binding": device_id if device_id else None
        }
        return self.jwt_manager.generate_token(payload, expires_in_hours=24)

    def verify_auth_token(self, token: str, expected_subscriber_id: Optional[str] = None) -> Dict:
        """
        Verify subscriber authorization token

        Args:
            token: Authorization token
            expected_subscriber_id: Optional expected subscriber ID

        Returns:
            Decoded token payload

        Raises:
            jwt.ExpiredSignatureError: Token has expired
            jwt.InvalidTokenError: Token is invalid
            ValueError: Subscriber ID mismatch
        """
        payload = self.jwt_manager.verify_token(token)

        if payload.get("type") != "subscriber_auth":
            raise ValueError("Invalid token type")

        if expected_subscriber_id and payload.get("sub") != expected_subscriber_id:
            raise ValueError("Subscriber ID mismatch")

        return payload


# Global JWT manager instance
_jwt_manager: Optional[JWTManager] = None

def get_jwt_manager() -> JWTManager:
    """Get or create global JWT manager instance"""
    global _jwt_manager
    if _jwt_manager is None:
        # Try to load keys from environment
        private_key = os.getenv("JWT_PRIVATE_KEY")
        public_key = os.getenv("JWT_PUBLIC_KEY")

        if private_key and public_key:
            _jwt_manager = JWTManager(private_key, public_key)
        else:
            # Generate new keys (should only happen in development)
            _jwt_manager = JWTManager()

            # Log warning in production
            if os.getenv("ENVIRONMENT") == "production":
                print("WARNING: Using auto-generated JWT keys in production. Set JWT_PRIVATE_KEY and JWT_PUBLIC_KEY environment variables.")

    return _jwt_manager
