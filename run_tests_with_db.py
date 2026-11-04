"""
Test DataVault with PostgreSQL databases
Tests the full system with real database connections
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
class TestWithPostgreSQL:
    """Test suite with PostgreSQL databases"""

    async def test_1_database_connection(self):
        """Test 1: Verify databases are accessible"""
        print("\n" + "=" * 70)
        print("Test 1: Database Connection")
        print("=" * 70)

        async with httpx.AsyncClient() as client:
            # Check operator API health
            response = await client.get(f"{OPERATOR_API_URL}/health", timeout=5.0)
            assert response.status_code == 200
            print(f"[PASS] Operator API health: {response.json()}")

            # Check backend API health
            response = await client.get(f"{DATAVAULT_BACKEND_URL}/health", timeout=5.0)
            assert response.status_code == 200
            print(f"[PASS] Backend API health: {response.json()}")

    async def test_2_initial_quota(self):
        """Test 2: Check initial subscriber quota from database"""
        print("\n" + "=" * 70)
        print("Test 2: Initial Subscriber Quota")
        print("=" * 70)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPERATOR_API_URL}/api/v1/subscriber/TEST-SUB-001/quota",
                timeout=10.0
            )

            assert response.status_code == 200
            data = response.json()
            assert data['subscriber_id'] == 'TEST-SUB-001'
            assert data['allocated_volume'] == 10737418240  # 10 GB
            assert data['remaining_volume'] == 10737418240  # 10 GB
            print(f"[PASS] Subscriber TEST-SUB-001 has 10 GB quota")

    async def test_3_quota_transfer(self):
        """Test 3: Transfer 5 GB from subscriber to device"""
        print("\n" + "=" * 70)
        print("Test 3: Quota Transfer")
        print("=" * 70)

        async with httpx.AsyncClient() as client:
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

            print(f"[PASS] 5 GB transferred successfully")
            print(f"  Entitlement ID: {data['entitlement_id']}")
            print(f"  Token: {data['token'][:30]}...")

            return data['entitlement_id'], data['token']

    async def test_4_validate_entitlement(self):
        """Test 4: Validate entitlement"""
        print("\n" + "=" * 70)
        print("Test 4: Validate Entitlement")
        print("=" * 70)

        entitlement_id, token = await self.test_3_quota_transfer()

        async with httpx.AsyncClient() as client:
            validation_request = {
                "entitlement_id": entitlement_id,
                "device_id": "DV-001-ABCD",
                "token": token
            }

            response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/validate",
                json=validation_request,
                timeout=10.0
            )

            assert response.status_code == 200
            data = response.json()
            assert data['valid'] == True
            assert data['remaining_volume'] == 5368709120

            print(f"[PASS] Entitlement validated successfully")
            print(f"  Valid: {data['valid']}")
            print(f"  Remaining: {data['remaining_volume']} bytes")

            return entitlement_id, token

    async def test_5_report_usage(self):
        """Test 5: Report usage and deduct quota"""
        print("\n" + "=" * 70)
        print("Test 5: Report Usage")
        print("=" * 70)

        entitlement_id, token = await self.test_4_validate_entitlement()

        async with httpx.AsyncClient() as client:
            usage_request = {
                "entitlement_id": entitlement_id,
                "device_id": "DV-001-ABCD",
                "volume_consumed": 1073741824,  # 1 GB
                "session_id": str(uuid.uuid4()),
                "reported_at": datetime.utcnow().isoformat()
            }

            response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/report-usage",
                json=usage_request,
                timeout=10.0
            )

            assert response.status_code == 200
            data = response.json()
            assert data['remaining_volume'] == 4294967296  # 4 GB remaining
            assert data['status'] == 'PARTIALLY_CONSUMED'

            print(f"[PASS] Usage reported successfully")
            print(f"  Remaining: {data['remaining_volume']} bytes")
            print(f"  Status: {data['status']}")

    async def test_6_verify_persistence(self):
        """Test 6: Verify data persists in database"""
        print("\n" + "=" * 70)
        print("Test 6: Database Persistence")
        print("=" * 70)

        entitlement_id, token = await self.test_3_quota_transfer()

        async with httpx.AsyncClient() as client:
            # Get entitlement after transfer
            response = await client.get(
                f"{OPERATOR_API_URL}/api/v1/entitlement/{entitlement_id}",
                timeout=10.0
            )

            assert response.status_code == 200
            data = response.json()
            assert data['entitlement_id'] == entitlement_id
            assert data['source_subscriber_id'] == 'TEST-SUB-001'
            assert data['destination_device_id'] == 'DV-001-ABCD'

            print(f"[PASS] Entitlement persisted in database")
            print(f"  Source: {data['source_subscriber_id']}")
            print(f"  Destination: {data['destination_device_id']}")

    async def test_7_duplicate_prevention(self):
        """Test 7: Prevent duplicate redemption"""
        print("\n" + "=" * 70)
        print("Test 7: Duplicate Redemption Prevention")
        print("=" * 70)

        entitlement_id, token = await self.test_3_quota_transfer()

        async with httpx.AsyncClient() as client:
            # Try to validate on wrong device
            validation_request = {
                "entitlement_id": entitlement_id,
                "device_id": "DV-002-EFGH",  # Different device
                "token": token
            }

            response = await client.post(
                f"{OPERATOR_API_URL}/api/v1/entitlement/validate",
                json=validation_request,
                timeout=10.0
            )

            assert response.status_code == 200
            data = response.json()
            assert data['valid'] == False
            assert 'error' in data

            print(f"[PASS] Duplicate redemption prevented")
            print(f"  Valid: {data['valid']}")
            print(f"  Error: {data['error']}")

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("DataVault PostgreSQL Integration Tests")
    print("=" * 70)
    print(f"\nOperator API: {OPERATOR_API_URL}")
    print(f"Backend API: {DATAVAULT_BACKEND_URL}")
    print(f"Device Simulator: {DEVICE_SIMULATOR_URL}")

    pytest.main([__file__, "-v", "-s"])
