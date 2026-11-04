"""
Configuration management for DataVault Backend
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class BackendSettings(BaseSettings):
    """Backend application settings"""

    # Database
    DATABASE_URL: str = "postgresql://datavault:datavault_backend_password@localhost:5437/datavault_backend"

    # Redis
    REDIS_URL: str = "redis://localhost:6381/1"

    # Operator API
    OPERATOR_API_URL: str = "http://localhost:8001"
    OPERATOR_PUBLIC_KEY: Optional[str] = None

    # JWT
    JWT_SECRET_KEY: str = "datavault_secret_key_change_in_production"

    # Security
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = BackendSettings()
