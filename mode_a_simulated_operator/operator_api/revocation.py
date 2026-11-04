"""
Token revocation management for DataVault
Handles entitlement and token revocation
"""
from datetime import datetime
from typing import Optional
import asyncpg

class RevocationManager:
    """Manages token and entitlement revocation"""

    def __init__(self, db_pool):
        self.db_pool = db_pool

    async def revoke_entitlement(
        self,
        entitlement_id: str,
        reason: str,
        revoked_by: str
    ) -> bool:
        """
        Revoke an entitlement

        Args:
            entitlement_id: Entitlement ID to revoke
            reason: Reason for revocation
            revoked_by: Who is revoking the entitlement

        Returns:
            True if revoked successfully
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Update entitlement status
                result = await conn.execute(
                    """UPDATE entitlements
                       SET status = 'REVOKED',
                           updated_at = NOW(),
                           version = version + 1
                       WHERE entitlement_id = $1 AND status != 'REVOKED'""",
                    entitlement_id
                )

                if result == "UPDATE 0":
                    return False  # Already revoked or doesn't exist

                # Log revocation
                await conn.execute(
                    """INSERT INTO revocation_log
                       (entitlement_id, revoked_at, reason, revoked_by)
                       VALUES ($1, NOW(), $2, $3)""",
                    entitlement_id, reason, revoked_by
                )

                return True

    async def is_entitlement_revoked(self, entitlement_id: str) -> bool:
        """
        Check if an entitlement is revoked

        Args:
            entitlement_id: Entitlement ID to check

        Returns:
            True if revoked
        """
        async with self.db_pool.acquire() as conn:
            entitlement = await conn.fetchrow(
                "SELECT status FROM entitlements WHERE entitlement_id = $1",
                entitlement_id
            )

            if not entitlement:
                return True  # Doesn't exist, treat as revoked

            return entitlement['status'] == 'REVOKED'

    async def revoke_by_device(self, device_id: str, reason: str, revoked_by: str) -> int:
        """
        Revoke all entitlements for a device

        Args:
            device_id: Device ID
            reason: Reason for revocation
            revoked_by: Who is revoking

        Returns:
            Number of entitlements revoked
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Update all entitlements for the device
                result = await conn.execute(
                    """UPDATE entitlements
                       SET status = 'REVOKED',
                           updated_at = NOW(),
                           version = version + 1
                       WHERE destination_device_id = $1
                         AND status NOT IN ('REVOKED', 'EXHAUSTED', 'EXPIRED')""",
                    device_id
                )

                count = int(result.split()[1]) if result else 0

                if count > 0:
                    # Log bulk revocation
                    await conn.execute(
                        """INSERT INTO revocation_log
                           (entitlement_id, revoked_at, reason, revoked_by, bulk_device_id)
                           VALUES (gen_random_uuid(), NOW(), $1, $2, $3)""",
                        reason, revoked_by, device_id
                    )

                return count

    async def revoke_by_subscriber(self, subscriber_id: str, reason: str, revoked_by: str) -> int:
        """
        Revoke all entitlements from a subscriber

        Args:
            subscriber_id: Subscriber ID
            reason: Reason for revocation
            revoked_by: Who is revoking

        Returns:
            Number of entitlements revoked
        """
        async with self.db_pool.acquire() as conn:
            async with conn.transaction():
                # Update all entitlements from the subscriber
                result = await conn.execute(
                    """UPDATE entitlements
                       SET status = 'REVOKED',
                           updated_at = NOW(),
                           version = version + 1
                       WHERE source_subscriber_id = $1
                         AND status NOT IN ('REVOKED', 'EXHAUSTED', 'EXPIRED')""",
                    subscriber_id
                )

                count = int(result.split()[1]) if result else 0

                if count > 0:
                    # Log bulk revocation
                    await conn.execute(
                        """INSERT INTO revocation_log
                           (entitlement_id, revoked_at, reason, revoked_by, bulk_subscriber_id)
                           VALUES (gen_random_uuid(), NOW(), $1, $2, $3)""",
                        reason, revoked_by, subscriber_id
                    )

                return count

    async def get_revocation_history(self, entitlement_id: str) -> list:
        """
        Get revocation history for an entitlement

        Args:
            entitlement_id: Entitlement ID

        Returns:
            List of revocation events
        """
        async with self.db_pool.acquire() as conn:
            records = await conn.fetch(
                """SELECT * FROM revocation_log
                   WHERE entitlement_id = $1 OR bulk_device_id IN (
                       SELECT destination_device_id FROM entitlements WHERE entitlement_id = $1
                   ) OR bulk_subscriber_id IN (
                       SELECT source_subscriber_id FROM entitlements WHERE entitlement_id = $1
                   )
                   ORDER BY revoked_at DESC""",
                entitlement_id
            )

            return [
                {
                    "revoked_at": r['revoked_at'],
                    "reason": r['reason'],
                    "revoked_by": r['revoked_by']
                }
                for r in records
            ]
