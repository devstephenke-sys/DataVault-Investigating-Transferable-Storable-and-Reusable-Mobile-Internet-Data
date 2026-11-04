"""
Test configuration and fixtures for DataVault tests
"""
import pytest
import asyncio
import os

# Test configuration
OPERATOR_API_URL = os.getenv("OPERATOR_API_URL", "http://localhost:8001")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
DEVICE_SIMULATOR_URL = os.getenv("DEVICE_SIMULATOR_URL", "http://localhost:8002")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def api_urls():
    """Provide API URLs for tests"""
    return {
        "operator": OPERATOR_API_URL,
        "backend": BACKEND_API_URL,
        "device": DEVICE_SIMULATOR_URL
    }

@pytest.fixture
def sample_entitlement():
    """Provide a sample entitlement for testing"""
    return {
        "entitlement_id": "550e8400-e29b-41d4-a716-446655440000",
        "source_subscriber_id": "TEST-SUB-001",
        "destination_device_id": "DV-001-ABCD",
        "allocated_volume": 5368709120,  # 5 GB
        "remaining_volume": 5368709120,
        "issued_at": "2026-11-04T10:00:00Z",
        "expires_at": "2026-12-04T10:00:00Z",
        "status": "ACTIVE",
        "token": "sample_jwt_token"
    }
