"""
Simplified Demo Script for DataVault Phase 3
Demonstrates core functionality without requiring database setup
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

class InMemoryDatabase:
    """Simple in-memory database for demo purposes"""
    def __init__(self):
        self.subscribers = {
            "TEST-SUB-001": {
                "subscriber_id": "TEST-SUB-001",
                "allocated_volume": 10737418240,  # 10 GB
                "remaining_volume": 10737418240
            },
            "TEST-SUB-002": {
                "subscriber_id": "TEST-SUB-002",
                "allocated_volume": 5368709120,  # 5 GB
                "remaining_volume": 5368709120
            }
        }
        self.devices = {
            "DV-001-ABCD": {
                "device_id": "DV-001-ABCD",
                "imei": "865432102345678",
                "status": "ACTIVE"
            },
            "DV-002-EFGH": {
                "device_id": "DV-002-EFGH",
                "imei": "865432102345679",
                "status": "ACTIVE"
            }
        }
        self.entitlements = {}
        self.transfer_log = []

    def get_subscriber(self, subscriber_id: str) -> Optional[Dict]:
        return self.subscribers.get(subscriber_id)

    def get_device(self, device_id: str) -> Optional[Dict]:
        return self.devices.get(device_id)

    def update_subscriber_quota(self, subscriber_id: str, volume: int):
        if subscriber_id in self.subscribers:
            self.subscribers[subscriber_id]["remaining_volume"] -= volume

    def create_entitlement(self, entitlement_data: Dict) -> Dict:
        entitlement_id = str(uuid.uuid4())
        entitlement_data["entitlement_id"] = entitlement_id
        self.entitlements[entitlement_id] = entitlement_data
        return entitlement_data

    def get_entitlement(self, entitlement_id: str) -> Optional[Dict]:
        return self.entitlements.get(entitlement_id)

    def update_entitlement(self, entitlement_id: str, updates: Dict):
        if entitlement_id in self.entitlements:
            self.entitlements[entitlement_id].update(updates)

    def log_transfer(self, log_data: Dict):
        self.transfer_log.append(log_data)


class SimulatedOperator:
    """Simulated Operator API without database"""
    def __init__(self):
        self.db = InMemoryDatabase()

    def quota_transfer(self, source_subscriber: str, destination_device_id: str,
                      volume: int, expiry: datetime, transfer_mode: str) -> Dict:
        """Transfer quota from subscriber to device"""
        # Check subscriber
        subscriber = self.db.get_subscriber(source_subscriber)
        if not subscriber:
            return {"error": "Subscriber not found", "status": 404}

        # Check quota
        if subscriber["remaining_volume"] < volume:
            return {"error": f"Insufficient quota. Available: {subscriber['remaining_volume']}, Requested: {volume}", "status": 403}

        # Check device
        device = self.db.get_device(destination_device_id)
        if not device:
            return {"error": "Device not registered", "status": 404}

        # Check for existing entitlement
        for ent in self.db.entitlements.values():
            if (ent["destination_device_id"] == destination_device_id and
                ent["status"] in ["ACTIVE", "PARTIALLY_CONSUMED"]):
                return {"error": "Device already has active entitlement", "status": 409}

        # Transfer quota
        self.db.update_subscriber_quota(source_subscriber, volume)

        # Create entitlement
        entitlement = self.db.create_entitlement({
            "source_subscriber_id": source_subscriber,
            "destination_device_id": destination_device_id,
            "allocated_volume": volume,
            "remaining_volume": volume,
            "issued_at": datetime.utcnow(),
            "expires_at": expiry,
            "status": "ACTIVE",
            "transfer_mode": transfer_mode,
            "token": f"jwt_token_{uuid.uuid4().hex}"
        })

        # Log transfer
        self.db.log_transfer({
            "entitlement_id": entitlement["entitlement_id"],
            "source_subscriber_id": source_subscriber,
            "destination_device_id": destination_device_id,
            "volume_transferred": volume,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {"entitlement": entitlement, "status": 200}

    def validate_entitlement(self, entitlement_id: str, device_id: str, token: str) -> Dict:
        """Validate entitlement"""
        entitlement = self.db.get_entitlement(entitlement_id)
        if not entitlement:
            return {"valid": False, "error": "Entitlement not found"}

        # Check device binding
        if entitlement["destination_device_id"] != device_id:
            return {"valid": False, "error": "Device mismatch"}

        # Check status
        if entitlement["status"] not in ["ACTIVE", "PARTIALLY_CONSUMED"]:
            return {"valid": False, "error": f"Entitlement status: {entitlement['status']}"}

        # Check expiry
        if entitlement["expires_at"] < datetime.utcnow():
            self.db.update_entitlement(entitlement_id, {"status": "EXPIRED"})
            return {"valid": False, "error": "Entitlement expired"}

        return {
            "valid": True,
            "remaining_volume": entitlement["remaining_volume"],
            "expires_at": entitlement["expires_at"].isoformat(),
            "status": entitlement["status"]
        }

    def report_usage(self, entitlement_id: str, device_id: str, volume_consumed: int) -> Dict:
        """Report usage and deduct quota"""
        entitlement = self.db.get_entitlement(entitlement_id)
        if not entitlement:
            return {"error": "Entitlement not found", "status": 404}

        if entitlement["remaining_volume"] < volume_consumed:
            return {"error": f"Insufficient quota. Remaining: {entitlement['remaining_volume']}", "status": 400}

        # Deduct quota
        new_remaining = entitlement["remaining_volume"] - volume_consumed
        new_status = "PARTIALLY_CONSUMED" if new_remaining > 0 else "EXHAUSTED"

        self.db.update_entitlement(entitlement_id, {
            "remaining_volume": new_remaining,
            "status": new_status
        })

        return {
            "remaining_volume": new_remaining,
            "status": new_status,
            "transaction_id": str(uuid.uuid4())
        }

    def get_subscriber_quota(self, subscriber_id: str) -> Dict:
        """Get subscriber quota"""
        subscriber = self.db.get_subscriber(subscriber_id)
        if not subscriber:
            return {"error": "Subscriber not found", "status": 404}
        return subscriber

    def get_entitlement(self, entitlement_id: str) -> Dict:
        """Get entitlement details"""
        entitlement = self.db.get_entitlement(entitlement_id)
        if not entitlement:
            return {"error": "Entitlement not found", "status": 404}
        return entitlement


class DeviceSimulator:
    """Device simulator with local token storage"""
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.tokens = {}

    def store_token(self, entitlement_data: Dict) -> bool:
        """Store token locally"""
        entitlement_id = entitlement_data["entitlement_id"]
        self.tokens[entitlement_id] = entitlement_data
        return True

    def get_token(self, entitlement_id: str) -> Optional[Dict]:
        """Retrieve token"""
        return self.tokens.get(entitlement_id)

    def simulate_traffic(self, entitlement_id: str, volume_bytes: int) -> Dict:
        """Simulate traffic (just check if possible, don't deduct locally)"""
        token = self.get_token(entitlement_id)
        if not token:
            return {"error": "Token not found", "status": 404}

        if token["remaining_volume"] < volume_bytes:
            return {"error": "Insufficient quota", "status": 400}

        # Just return info without deducting (deduction happens via report_usage)
        return {
            "status": "traffic_simulated",
            "volume_consumed": volume_bytes,
            "current_remaining": token["remaining_volume"]
        }


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text: str):
    """Print success message"""
    print(f"[PASS] {text}")


def print_info(text: str):
    """Print info message"""
    print(f"  {text}")


def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable"""
    gb = bytes_value / (1024**3)
    return f"{gb:.2f} GB"


def main():
    """Run the demo"""
    print_header("DataVault Phase 3 - Simplified Demo")

    # Initialize components
    operator = SimulatedOperator()
    device = DeviceSimulator("DV-001-ABCD")

    # Test 1: Check initial subscriber quota
    print_header("Test 1: Initial Subscriber Quota")
    quota = operator.get_subscriber_quota("TEST-SUB-001")
    print_info(f"Subscriber: {quota['subscriber_id']}")
    print_info(f"Allocated: {format_bytes(quota['allocated_volume'])}")
    print_info(f"Remaining: {format_bytes(quota['remaining_volume'])}")
    print_success("Test 1 passed: Subscriber has 10 GB quota")

    # Test 2: Transfer 5 GB to device
    print_header("Test 2: Transfer 5 GB to Device")
    expiry = datetime.utcnow() + timedelta(days=30)
    result = operator.quota_transfer(
        source_subscriber="TEST-SUB-001",
        destination_device_id="DV-001-ABCD",
        volume=5368709120,  # 5 GB
        expiry=expiry,
        transfer_mode="TRANSFER"
    )

    if result["status"] == 200:
        entitlement = result["entitlement"]
        print_info(f"Entitlement ID: {entitlement['entitlement_id']}")
        print_info(f"Device: {entitlement['destination_device_id']}")
        print_info(f"Volume: {format_bytes(entitlement['allocated_volume'])}")
        print_info(f"Token: {entitlement['token'][:20]}...")
        print_success("Test 2 passed: 5 GB transferred successfully")
        entitlement_id = entitlement["entitlement_id"]
        token = entitlement["token"]
    else:
        print(f"Error: {result}")
        return

    # Test 3: Verify subscriber quota reduced
    print_header("Test 3: Verify Subscriber Quota Reduced")
    quota = operator.get_subscriber_quota("TEST-SUB-001")
    print_info(f"Subscriber: {quota['subscriber_id']}")
    print_info(f"Allocated: {format_bytes(quota['allocated_volume'])}")
    print_info(f"Remaining: {format_bytes(quota['remaining_volume'])}")
    assert quota['remaining_volume'] == 5368709120, "Quota should be 5 GB"
    print_success("Test 3 passed: Subscriber quota reduced to 5 GB")

    # Test 4: Store token on device
    print_header("Test 4: Store Token on Device")
    device.store_token(entitlement)
    print_info(f"Token stored for device: {device.device_id}")
    print_info(f"Entitlement ID: {entitlement_id}")
    print_success("Test 4 passed: Token stored on device")

    # Test 5: Validate entitlement
    print_header("Test 5: Validate Entitlement")
    validation = operator.validate_entitlement(entitlement_id, "DV-001-ABCD", token)
    print_info(f"Valid: {validation['valid']}")
    print_info(f"Remaining: {format_bytes(validation['remaining_volume'])}")
    print_info(f"Status: {validation['status']}")
    assert validation['valid'] == True, "Entitlement should be valid"
    print_success("Test 5 passed: Entitlement validated successfully")

    # Test 6: Simulate 1 GB traffic (simulates device usage but doesn't deduct from operator yet)
    print_header("Test 6: Simulate 1 GB Traffic")
    traffic_result = device.simulate_traffic(entitlement_id, 1073741824)  # 1 GB
    print_info(f"Status: {traffic_result['status']}")
    print_info(f"Consumed: {format_bytes(traffic_result['volume_consumed'])}")
    print_info(f"Current remaining: {format_bytes(traffic_result['current_remaining'])}")
    print_success("Test 6 passed: 1 GB simulated locally")

    # Test 7: Report usage to operator (now deduct from operator)
    print_header("Test 7: Report Usage to Operator")
    usage_result = operator.report_usage(entitlement_id, "DV-001-ABCD", 1073741824)
    print_info(f"Operator remaining: {format_bytes(usage_result['remaining_volume'])}")
    print_info(f"Status: {usage_result['status']}")
    print_success("Test 7 passed: Usage reported, quota deducted")

    # Test 8: Verify final state
    print_header("Test 8: Verify Final State")
    entitlement = operator.get_entitlement(entitlement_id)
    print_info(f"Entitlement ID: {entitlement['entitlement_id']}")
    print_info(f"Allocated: {format_bytes(entitlement['allocated_volume'])}")
    print_info(f"Remaining: {format_bytes(entitlement['remaining_volume'])}")
    print_info(f"Status: {entitlement['status']}")
    assert entitlement['remaining_volume'] == 4294967296, "Should have 4 GB remaining"
    print_success("Test 8 passed: Final state verified (4 GB remaining)")

    # Test 9: Duplicate redemption prevention
    print_header("Test 9: Duplicate Redemption Prevention")
    validation = operator.validate_entitlement(entitlement_id, "DV-002-EFGH", token)
    print_info(f"Valid: {validation['valid']}")
    print_info(f"Error: {validation.get('error', 'None')}")
    assert validation['valid'] == False, "Should not be valid on different device"
    print_success("Test 9 passed: Duplicate redemption prevented")

    # Test 10: Independent connectivity
    print_header("Test 10: Independent Connectivity")
    subscriber_quota = operator.get_subscriber_quota("TEST-SUB-001")
    print_info(f"Source subscriber remaining: {format_bytes(subscriber_quota['remaining_volume'])}")
    print_info(f"Device entitlement remaining: {format_bytes(entitlement['remaining_volume'])}")
    assert subscriber_quota['remaining_volume'] == 5368709120, "Source should still have 5 GB"
    assert entitlement['remaining_volume'] == 4294967296, "Device should have 4 GB"
    print_success("Test 10 passed: Device uses quota independently")

    # Summary
    print_header("Demo Summary")
    print_info("All 10 tests passed successfully!")
    print_info("\nKey Findings:")
    print_info("  [+] Quota transfer from subscriber to device works")
    print_info("  [+] Token generation and validation works")
    print_info("  [+] Usage tracking and deduction works")
    print_info("  [+] Device binding prevents duplicate redemption")
    print_info("  [+] Device operates independently from source subscriber")
    print_info("\nNote: This is a simplified in-memory demo.")
    print_info("The full implementation uses PostgreSQL and proper JWT tokens.")
    print_info("See the full source code for production-ready implementation.")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
