"""
Mobile App Simulator
Simulates a mobile app that initiates quota transfers
"""
import requests
import json
from datetime import datetime, timedelta
import os

# Configuration
DATAVAULT_BACKEND_URL = os.getenv("DATAVAULT_BACKEND_URL", "http://localhost:8000")

class MobileAppSimulator:
    """Simulates the DataVault mobile app"""

    def __init__(self, backend_url):
        self.backend_url = backend_url

    def initiate_transfer(self, subscriber_id, device_id, volume_gb, expiry_days=30):
        """
        Initiate a quota transfer from subscriber to device
        """
        # Convert GB to bytes
        volume_bytes = volume_gb * 1073741824

        transfer_request = {
            "source_subscriber": subscriber_id,
            "destination_device_id": device_id,
            "volume": volume_bytes,
            "expiry": (datetime.utcnow() + timedelta(days=expiry_days)).isoformat(),
            "transfer_mode": "TRANSFER"
        }

        try:
            response = requests.post(
                f"{self.backend_url}/api/v1/entitlement/transfer",
                json=transfer_request,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✓ Transfer successful!")
                print(f"  Entitlement ID: {data['entitlement_id']}")
                print(f"  Allocated: {data['allocated_volume'] / 1073741824:.2f} GB")
                print(f"  Token: {data['token'][:50]}...")
                return data
            else:
                print(f"✗ Transfer failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return None

        except Exception as e:
            print(f"✗ Transfer error: {str(e)}")
            return None

    def display_token(self, entitlement):
        """Display the entitlement token for transfer to device"""
        print("\n" + "="*60)
        print("ENTITLEMENT TOKEN")
        print("="*60)
        print(f"Entitlement ID: {entitlement['entitlement_id']}")
        print(f"Source Subscriber: {entitlement['source_subscriber_id']}")
        print(f"Destination Device: {entitlement['destination_device_id']}")
        print(f"Allocated Volume: {entitlement['allocated_volume'] / 1073741824:.2f} GB")
        print(f"Remaining Volume: {entitlement['remaining_volume'] / 1073741824:.2f} GB")
        print(f"Issued At: {entitlement['issued_at']}")
        print(f"Expires At: {entitlement['expires_at']}")
        print(f"Status: {entitlement['status']}")
        print(f"\nToken (copy this to device):")
        print(entitlement['token'])
        print("="*60 + "\n")

def main():
    """Main entry point for mobile app simulator"""
    app = MobileAppSimulator(DATAVAULT_BACKEND_URL)

    print("DataVault Mobile App Simulator")
    print("="*60)

    # Scenario 1: Transfer 5 GB from TEST-SUB-001 to DV-001-ABCD
    print("\nScenario 1: Transfer 5 GB from TEST-SUB-001 to DV-001-ABCD")
    entitlement = app.initiate_transfer("TEST-SUB-001", "DV-001-ABCD", 5)

    if entitlement:
        app.display_token(entitlement)

    # Scenario 2: Transfer 1 GB from TEST-SUB-002 to DV-002-EFGH
    print("\nScenario 2: Transfer 1 GB from TEST-SUB-002 to DV-002-EFGH")
    entitlement2 = app.initiate_transfer("TEST-SUB-002", "DV-002-EFGH", 1)

    if entitlement2:
        app.display_token(entitlement2)

if __name__ == "__main__":
    main()
