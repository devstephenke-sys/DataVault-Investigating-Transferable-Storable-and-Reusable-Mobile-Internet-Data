"""
Critical security tests for DataVault
Focus on security vulnerabilities that must be prevented
"""
import pytest
import asyncio
import httpx
from datetime import datetime, timedelta
import uuid
import os

OPERATOR_API_URL = os.getenv("OPERATOR_API_URL", "http://localhost:8001")
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

@pytest.mark.asyncio
class TestSecurityCritical:
    """Critical security tests - these must all pass"""

    async def test_empty_token_rejected_in_validation(self):
        """
        CRITICAL: Empty token must be rejected in validation
        This was a vulnerability in the original implementation
        """
        async with httpx.AsyncClient() as client:
            validation_request = {
                "entitlement_id": str(uuid.uuid4()),
                "device_id": "DV-001-ABCD",
                "token": ""  # CRITICAL: Empty token
            }

            response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/validate",
                json=validation_request,
                timeout=10.0
            )

            # Must reject empty token
            assert response.status_code == 200
            data = response.json()
            assert data['valid'] == False
            assert 'error' in data
            assert 'empty' in data['error'].lower() or 'required' in data['error'].lower()

    async def test_empty_token_rejected_in_usage_reporting(self):
        """
        CRITICAL: Empty token must be rejected in usage reporting
        This was a vulnerability in the original implementation
        """
        async with httpx.AsyncClient() as client:
            usage_request = {
                "entitlement_id": str(uuid.uuid4()),
                "device_id": "DV-001-ABCD",
                "volume_consumed": 1073741824,
                "session_id": str(uuid.uuid4()),
                "reported_at": datetime.utcnow().isoformat(),
                "token": ""  # CRITICAL: Empty token
            }

            response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/report-usage",
                json=usage_request,
                timeout=10.0
            )

            # Must reject empty token
            assert response.status_code == 400
            data = response.json()
            assert 'detail' in data
            assert 'token' in data['detail'].lower()

    async def test_none_token_rejected(self):
        """
        CRITICAL: None/null token must be rejected
        """
        async with httpx.AsyncClient() as client:
            validation_request = {
                "entitlement_id": str(uuid.uuid4()),
                "device_id": "DV-001-ABCD",
                "token": None  # CRITICAL: None token
            }

            response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/validate",
                json=validation_request,
                timeout=10.0
            )

            # Must reject None token
            assert response.status_code == 422  # Validation error

    async def test_token_signature_verified(self):
        """
        CRITICAL: Token signature must be verified
        Unsigned or tampered tokens must be rejected
        """
        async with httpx.AsyncClient() as client:
            # Attempt to use a fake token (not signed by operator)
            fake_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake_signature"

            validation_request = {
                "entitlement_id": str(uuid.uuid4()),
                "device_id": "DV-001-ABCD",
                "token": fake_token
            }

            response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/validate",
                json=validation_request,
                timeout=10.0
            )

            # Must reject invalid signature
            assert response.status_code == 200
            data = response.json()
            assert data['valid'] == False

    async def test_authorization_required_for_transfer(self):
        """
        CRITICAL: Authorization token must be required for transfer
        Cannot transfer without valid subscriber authorization
        """
        async with httpx.AsyncClient() as client:
            transfer_request = {
                "source_subscriber": "TEST-SUB-001",
                "destination_device_id": "DV-001-ABCD",
                "volume": 5368709120,
                "expiry": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "transfer_mode": "TRANSFER",
                "authorization": ""  # CRITICAL: Empty auth
            }

            response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/quota/transfer",
                json=transfer_request,
                timeout=10.0
            )

            # Must reject without authorization
            assert response.status_code == 401

    async def test_negative_quota_prevented(self):
        """
        CRITICAL: Negative quota must be prevented
        Cannot have negative remaining volume
        """
        async with httpx.AsyncClient() as client:
            # Try to report more usage than available
            usage_request = {
                "entitlement_id": str(uuid.uuid4()),
                "device_id": "DV-001-ABCD",
                "volume_consumed": 999999999999999,  # Extremely large
                "session_id": str(uuid.uuid4()),
                "reported_at": datetime.utcnow().isoformat(),
                "token": "some_token"
            }

            response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/report-usage",
                json=usage_request,
                timeout=10.0
            )

            # Must reject
            assert response.status_code in [400, 404]

    async def test_device_binding_enforced(self):
        """
        CRITICAL: Device binding must be enforced
        Cannot use entitlement on different device
        """
        async with httpx.AsyncClient() as client:
            validation_request = {
                "entitlement_id": str(uuid.uuid4()),
                "device_id": "DV-999-UNAUTHORIZED",  # Wrong device
                "token": "some_token"
            }

            response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/validate",
                json=validation_request,
                timeout=10.0
            )

            # Must reject device mismatch
            assert response.status_code == 200
            data = response.json()
            assert data['valid'] == False
            assert 'device' in data['error'].lower() or 'mismatch' in data['error'].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
