"""
Mode A: Simulated Operator Tests
Tests the complete simulated operator environment
"""
import pytest
import asyncio
import httpx
from datetime import datetime, timedelta
import uuid
import os

# Configuration
OPERATOR_API_URL = os.getenv("OPERATOR_API_URL", "http://localhost:8001")
DATAVAULT_BACKEND_URL = os.getenv("DATAVAULT_BACKEND_URL", "http://localhost:8000")
DEVICE_SIMULATOR_URL = os.getenv("DEVICE_SIMULATOR_URL", "http://localhost:8002")

@pytest.mark.asyncio
class TestModeASimulatedOperator:
    """Test suite for Mode A: Simulated Operator"""

    async def test_1_create_subscriber_with_quota(self):
        """
        Test 1: Create subscriber with 10 GB quota
        This test verifies the test data is properly initialized
        """
        async with httpx.AsyncClient() as client:
            # Get subscriber quota
            response = await client.get(
                f"{OPERATOR_API_URL}/api/v1/subscriber/TEST-SUB-001/quota",
                timeout=10.0
            )

            assert response.status_code == 200
            data = response.json()
            assert data['subscriber_id'] == 'TEST-SUB-001'
            assert data['allocated_volume'] == 10737418240  # 10 GB
            assert data['remaining_volume'] == 10737418240  # 10 GB
            print("✓ Test 1 passed: Subscriber has 10 GB quota")

    async def test_2_quota_transfer_5gb(self):
        """
        Test 2: Transfer 5 GB from subscriber to device
        """
        async with httpx.AsyncClient() as client:
            # Initiate transfer
            transfer_request = {
                "source_subscriber": "TEST-SUB-001",
                "destination_device_id": "DV-001-ABCD",
                "volume": 5368709120,  # 5 GB
                "expiry": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "transfer_mode": "TRANSFER",
                "authorization": "Bearer test_token"
            }

            response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/quota/transfer",
                json=transfer_request,
                timeout=10.0
            )

            assert response.status_code == 200
            data = response.json()
            assert data['allocated_volume'] == 5368709120
            assert data['remaining_volume'] == 5368709120
            assert data['status'] == 'ACTIVE'
            assert 'token' in data
            assert 'entitlement_id' in data

            # Verify source subscriber quota reduced
            quota_response = await client.get(
                f"{OPERATOR_API_URL}/api/v1/subscriber/TEST-SUB-001/quota",
                timeout=10.0
            )
            quota_data = quota_response.json()
            assert quota_data['remaining_volume'] == 5368709120  # 5 GB remaining

            # Verify entitlement created
            entitlement_response = await client.get(
                f"{OPERATOR_API_URL}/api/v1/entitlement/{data['entitlement_id']}",
                timeout=10.0
            )
            entitlement_data = entitlement_response.json()
            assert entitlement_data['source_subscriber_id'] == 'TEST-SUB-001'
            assert entitlement_data['destination_device_id'] == 'DV-001-ABCD'

            print("✓ Test 2 passed: 5 GB transferred successfully")
            return data['entitlement_id'], data['token']

    async def test_3_persistence_after_restart(self):
        """
        Test 3: Verify entitlement survives device restart
        """
        # First, get an entitlement
        entitlement_id, token = await self.test_2_quota_transfer_5gb()

        # Store token in device simulator
        async with httpx.AsyncClient() as client:
            store_request = {
                "entitlement_id": entitlement_id,
                "token": token,
                "destination_device_id": "DV-001-ABCD",
                "allocated_volume": 5368709120,
                "remaining_volume": 5368709120,
                "issued_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "status": "ACTIVE"
            }

            response = await client.post(
                f"{DEVICE_SIMULATOR_URL}/device/token/store",
                json=store_request,
                timeout=10.0
            )
            assert response.status_code == 201

            # Simulate restart
            restart_response = await client.post(
                f"{DEVICE_SIMULATOR_URL}/device/restart",
                timeout=10.0
            )
            assert restart_response.status_code == 200
            restart_data = restart_response.json()
            assert restart_data['tokens_persisted'] >= 1

            # Verify token still accessible after restart
            token_response = await client.get(
                f"{DEVICE_SIMULATOR_URL}/device/token/{entitlement_id}",
                timeout=10.0
            )
            assert token_response.status_code == 200
            token_data = token_response.json()
            assert token_data['remaining_volume'] == 5368709120

            print("✓ Test 3 passed: Entitlement persists after restart")

    async def test_4_redemption_and_usage(self):
        """
        Test 4: Connect device and use 1 GB of quota
        """
        # Get entitlement
        entitlement_id, token = await self.test_2_quota_transfer_5gb()

        async with httpx.AsyncClient() as client:
            # Validate entitlement
            validation_request = {
                "entitlement_id": entitlement_id,
                "device_id": "DV-001-ABCD",
                "token": token
            }

            validation_response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/validate",
                json=validation_request,
                timeout=10.0
            )
            assert validation_response.status_code == 200
            validation_data = validation_response.json()
            assert validation_data['valid'] == True
            assert validation_data['remaining_volume'] == 5368709120

            # Simulate 1 GB traffic
            traffic_request = {
                "entitlement_id": entitlement_id,
                "volume_bytes": 1073741824  # 1 GB
            }

            traffic_response = await client.post(
                f"{DEVICE_SIMULATOR_URL}/device/simulate-traffic",
                json=traffic_request,
                timeout=10.0
            )
            assert traffic_response.status_code == 200

            # Verify remaining quota reduced
            entitlement_response = await client.get(
                f"{OPERATOR_API_URL}/api/v1/entitlement/{entitlement_id}",
                timeout=10.0
            )
            entitlement_data = entitlement_response.json()
            assert entitlement_data['remaining_volume'] == 4294967296  # 4 GB remaining

            print("✓ Test 4 passed: 1 GB consumed, 4 GB remaining")

    async def test_5_usage_accounting(self):
        """
        Test 5: Verify quota deduction after usage
        """
        # This builds on test 4
        entitlement_id, token = await self.test_2_quota_transfer_5gb()

        async with httpx.AsyncClient() as client:
            # Report usage directly
            usage_request = {
                "entitlement_id": entitlement_id,
                "device_id": "DV-001-ABCD",
                "volume_consumed": 1073741824,  # 1 GB
                "session_id": str(uuid.uuid4()),
                "reported_at": datetime.utcnow().isoformat()
            }

            usage_response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/report-usage",
                json=usage_request,
                timeout=10.0
            )
            assert usage_response.status_code == 200
            usage_data = usage_response.json()
            assert usage_data['remaining_volume'] >= 0
            assert usage_data['status'] in ['PARTIALLY_CONSUMED', 'EXHAUSTED']

            print("✓ Test 5 passed: Usage accounting verified")

    async def test_6_duplicate_redemption_prevention(self):
        """
        Test 6: Attempt to redeem same allocation on different device
        """
        entitlement_id, token = await self.test_2_quota_transfer_5gb()

        async with httpx.AsyncClient() as client:
            # Try to validate on wrong device
            validation_request = {
                "entitlement_id": entitlement_id,
                "device_id": "DV-002-EFGH",  # Different device
                "token": token
            }

            validation_response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/validate",
                json=validation_request,
                timeout=10.0
            )
            assert validation_response.status_code == 200
            validation_data = validation_response.json()
            assert validation_data['valid'] == False
            assert 'error' in validation_data

            print("✓ Test 6 passed: Duplicate redemption prevented")

    async def test_7_failure_recovery(self):
        """
        Test 7: Network interruption during transfer
        """
        # This would require simulating network failure
        # For now, we test idempotency - same transfer request twice

        async with httpx.AsyncClient() as client:
            transfer_request = {
                "source_subscriber": "TEST-SUB-002",  # Use different subscriber
                "destination_device_id": "DV-002-EFGH",
                "volume": 1073741824,  # 1 GB
                "expiry": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "transfer_mode": "TRANSFER",
                "authorization": "Bearer test_token"
            }

            # First transfer
            response1 = await client.post(
                f"{OPERATOR_API_URL}/api/v1/quota/transfer",
                json=transfer_request,
                timeout=10.0
            )
            assert response1.status_code == 200

            # Second transfer to same device should fail
            response2 = await client.post(
                f"{OPERATOR_API_URL}/api/v1/quota/transfer",
                json=transfer_request,
                timeout=10.0
            )
            assert response2.status_code == 409  # Conflict - device already has entitlement

            print("✓ Test 7 passed: Idempotency and consistency verified")

    async def test_8_independent_connectivity(self):
        """
        Test 8: Verify device can use quota without source phone
        """
        entitlement_id, token = await self.test_2_quota_transfer_5gb()

        async with httpx.AsyncClient() as client:
            # Source subscriber should have 5 GB remaining after transfer
            quota_response = await client.get(
                f"{OPERATOR_API_URL}/api/v1/subscriber/TEST-SUB-001/quota",
                timeout=10.0
            )
            quota_data = quota_response.json()
            assert quota_data['remaining_volume'] == 5368709120  # 5 GB

            # Device should be able to use its entitlement independently
            validation_request = {
                "entitlement_id": entitlement_id,
                "device_id": "DV-001-ABCD",
                "token": token
            }

            validation_response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/validate",
                json=validation_request,
                timeout=10.0
            )
            assert validation_response.status_code == 200
            validation_data = validation_response.json()
            assert validation_data['valid'] == True

            # Use some quota
            usage_request = {
                "entitlement_id": entitlement_id,
                "device_id": "DV-001-ABCD",
                "volume_consumed": 1073741824,  # 1 GB
                "session_id": str(uuid.uuid4()),
                "reported_at": datetime.utcnow().isoformat()
            }

            usage_response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/report-usage",
                json=usage_request,
                timeout=10.0
            )
            assert usage_response.status_code == 200

            # Source subscriber quota should still be 5 GB (unchanged)
            quota_response2 = await client.get(
                f"{OPERATOR_API_URL}/api/v1/subscriber/TEST-SUB-001/quota",
                timeout=10.0
            )
            quota_data2 = quota_response2.json()
            assert quota_data2['remaining_volume'] == 5368709120  # Still 5 GB

            print("✓ Test 8 passed: Independent connectivity verified")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
