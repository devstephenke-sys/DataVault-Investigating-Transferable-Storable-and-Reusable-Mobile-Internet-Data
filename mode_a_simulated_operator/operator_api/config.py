"""
Configuration management for DataVault
Uses environment variables with sensible defaults
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""

    # Database
    DATABASE_URL: str = "postgresql://datavault:datavault_operator_password@localhost:5436/datavault_operator"

    # JWT
    JWT_PRIVATE_KEY: Optional[str] = None
    JWT_PUBLIC_KEY: Optional[str] = None
    JWT_EXPIRY_HOURS: int = 720  # 30 days

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
settings = Settings()
