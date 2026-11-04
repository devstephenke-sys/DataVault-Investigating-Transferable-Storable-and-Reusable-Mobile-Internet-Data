"""
Simulated Operator API
Implements Quota Transfer, Validation, and Usage Reporting APIs
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import asyncpg
from contextlib import asynccontextmanager
import os
import json

from config import settings
from security import get_jwt_manager, SubscriberAuth

# Configuration
DATABASE_URL = settings.DATABASE_URL
JWT_EXPIRY_HOURS = settings.JWT_EXPIRY_HOURS

security = HTTPBearer()

# Initialize security components
jwt_manager = get_jwt_manager()
subscriber_auth = SubscriberAuth(jwt_manager)

# Database connection pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
        print(f"Connected to database: {DATABASE_URL}")
        yield
    finally:
        if db_pool:
            await db_pool.close()
            print("Database connection closed")

app = FastAPI(
    title="Simulated Operator API",
    description="Quota Transfer, Validation, and Usage Reporting APIs for DataVault",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic models
class TransferRequest(BaseModel):
    source_subscriber: str = Field(..., description="Subscriber identifier (MSISDN or IMPI)")
    destination_device_id: str = Field(..., description="DataVault device identifier")
    volume: int = Field(..., description="Volume to transfer in bytes")
    expiry: datetime = Field(..., description="Entitlement expiry time")
    transfer_mode: str = Field(..., description="Transfer mode: TRANSFER or DELEGATE")
    authorization: str = Field(..., description="Bearer token for subscriber authorization")

class Entitlement(BaseModel):
    entitlement_id: str
    allocated_volume: int
    remaining_volume: int
    issued_at: datetime
    expires_at: datetime
    token: str
    status: str

class ValidationRequest(BaseModel):
    entitlement_id: str
    device_id: str
    token: str

class ValidationResult(BaseModel):
    valid: bool
    remaining_volume: Optional[int] = None
    expires_at: Optional[datetime] = None
    status: Optional[str] = None
    error: Optional[str] = None

class UsageReport(BaseModel):
    entitlement_id: str
    device_id: str
    volume_consumed: int
    session_id: str
    reported_at: datetime

class UsageReportResult(BaseModel):
    remaining_volume: int
    transaction_id: str
    status: str

# Helper functions
async def get_db():
    return db_pool

def generate_jwt_token(entitlement_data: dict) -> str:
    """Generate a signed JWT token for the entitlement"""
    payload = {
        "entitlement_id": entitlement_data["entitlement_id"],
        "source_subscriber_id": entitlement_data["source_subscriber_id"],
        "destination_device_id": entitlement_data["destination_device_id"],
        "allocated_volume": entitlement_data["allocated_volume"],
        "issued_at": entitlement_data["issued_at"].isoformat(),
        "expires_at": entitlement_data["expires_at"].isoformat(),
        "device_binding": entitlement_data["device_binding"],
        "nonce": str(uuid.uuid4())
    }
    token = jwt_manager.generate_token(payload, expires_in_hours=JWT_EXPIRY_HOURS)
    return token

def verify_jwt_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt_manager.verify_token(token)
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# API Endpoints
@app.post("/api/v1/quota/transfer", response_model=Entitlement, status_code=200)
async def quota_transfer(request: TransferRequest, db=Depends(get_db)):
    """
    Transfer quota from subscriber to device
    """
    # Verify subscriber authorization
    try:
        auth_payload = subscriber_auth.verify_auth_token(
            request.authorization,
            expected_subscriber_id=request.source_subscriber
        )
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Authorization failed: {str(e)}"
        )

    async with db.acquire() as conn:
        # Use transaction for atomic operation
        async with conn.transaction():
            # Check subscriber quota with row lock
            quota = await conn.fetchrow(
                "SELECT remaining_volume FROM quota_balances WHERE subscriber_id = $1 FOR UPDATE",
                request.source_subscriber
            )

            if not quota:
                raise HTTPException(status_code=404, detail="Subscriber not found")

            if quota['remaining_volume'] < request.volume:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient quota. Available: {quota['remaining_volume']}, Requested: {request.volume}"
                )

            # Check if device is registered
            device = await conn.fetchrow(
                "SELECT device_id FROM device_registrations WHERE device_id = $1 AND status = 'ACTIVE'",
                request.destination_device_id
            )

            if not device:
                raise HTTPException(status_code=404, detail="Device not registered or inactive")

            # Check if device already has active entitlement
            existing = await conn.fetchrow(
                """SELECT entitlement_id FROM entitlements
                   WHERE destination_device_id = $1 AND status IN ('ACTIVE', 'STORED', 'PARTIALLY_CONSUMED')
                   AND expires_at > NOW()
                   FOR UPDATE""",
                request.destination_device_id
            )

            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Device already has an active entitlement"
                )

            # Deduct from source subscriber
            await conn.execute(
                """UPDATE quota_balances
                   SET remaining_volume = remaining_volume - $1, last_updated = NOW()
                   WHERE subscriber_id = $2""",
                request.volume, request.source_subscriber
            )

            # Create entitlement
            entitlement_id = str(uuid.uuid4())
            device_binding = {
                "device_id": request.destination_device_id,
                "imei": "865432102345678",  # Would come from device registration
                "binding_type": "HARDWARE"
            }

            await conn.execute(
                """INSERT INTO entitlements
                   (entitlement_id, source_subscriber_id, destination_device_id,
                    allocated_volume, remaining_volume, issued_at, expires_at,
                    status, transfer_mode, device_binding, token_signature)
                   VALUES ($1, $2, $3, $4, $5, NOW(), $6, 'ACTIVE', $7, $8, '')""",
                entitlement_id, request.source_subscriber, request.destination_device_id,
                request.volume, request.volume, request.expiry, request.transfer_mode,
                json.dumps(device_binding)
            )

            # Generate JWT token
            entitlement_data = {
                "entitlement_id": entitlement_id,
                "source_subscriber_id": request.source_subscriber,
                "destination_device_id": request.destination_device_id,
                "allocated_volume": request.volume,
                "issued_at": datetime.utcnow(),
                "expires_at": request.expiry,
                "device_binding": device_binding
            }
            token = generate_jwt_token(entitlement_data)

            # Update token signature in database
            await conn.execute(
                "UPDATE entitlements SET token_signature = $1 WHERE entitlement_id = $2",
                token, entitlement_id
            )

            # Log transfer
            await conn.execute(
                """INSERT INTO transfer_audit_log
                   (entitlement_id, source_subscriber_id, destination_device_id,
                    volume_transferred, transfer_timestamp, initiated_by, approval_method)
                   VALUES ($1, $2, $3, $4, NOW(), $5, 'API')""",
                entitlement_id, request.source_subscriber, request.destination_device_id,
                request.volume, request.source_subscriber
            )

        # Fetch created entitlement
        entitlement = await conn.fetchrow(
            "SELECT * FROM entitlements WHERE entitlement_id = $1",
            entitlement_id
        )

        return Entitlement(
            entitlement_id=entitlement['entitlement_id'],
            allocated_volume=entitlement['allocated_volume'],
            remaining_volume=entitlement['remaining_volume'],
            issued_at=entitlement['issued_at'],
            expires_at=entitlement['expires_at'],
            token=token,
            status=entitlement['status']
        )

@app.post("/api/v1/entitlement/validate", response_model=ValidationResult)
async def validate_entitlement(request: ValidationRequest, db=Depends(get_db)):
    """
    Validate entitlement token
    """
    # Verify JWT token - THIS IS CRITICAL
    try:
        payload = verify_jwt_token(request.token)
    except HTTPException as e:
        return ValidationResult(
            valid=False,
            error=str(e.detail)
        )

    # Check device binding
    if payload['destination_device_id'] != request.device_id:
        return ValidationResult(
            valid=False,
            error="Device mismatch"
        )

    async with db.acquire() as conn:
        # Fetch entitlement from database
        entitlement = await conn.fetchrow(
            "SELECT * FROM entitlements WHERE entitlement_id = $1",
            request.entitlement_id
        )

        if not entitlement:
            return ValidationResult(
                valid=False,
                error="Entitlement not found"
            )

        # Check status
        if entitlement['status'] not in ['ACTIVE', 'PARTIALLY_CONSUMED']:
            return ValidationResult(
                valid=False,
                error=f"Entitlement status: {entitlement['status']}",
                status=entitlement['status']
            )

        # Check expiry
        if entitlement['expires_at'] < datetime.utcnow():
            # Update status to expired
            await conn.execute(
                "UPDATE entitlements SET status = 'EXPIRED' WHERE entitlement_id = $1",
                request.entitlement_id
            )
            return ValidationResult(
                valid=False,
                error="Entitlement expired",
                status="EXPIRED"
            )

        return ValidationResult(
            valid=True,
            remaining_volume=entitlement['remaining_volume'],
            expires_at=entitlement['expires_at'],
            status=entitlement['status']
        )

@app.post("/api/v1/entitlement/report-usage", response_model=UsageReportResult)
async def report_usage(request: UsageReport, db=Depends(get_db)):
    """
    Report usage for entitlement
    """
    # First validate the entitlement (this will verify the token)
    # We need to get the token first from the database
    async with db.acquire() as conn:
        entitlement = await conn.fetchrow(
            "SELECT * FROM entitlements WHERE entitlement_id = $1",
            request.entitlement_id
        )

        if not entitlement:
            raise HTTPException(status_code=404, detail="Entitlement not found")

        # Validate the token we have on file
        validation = await validate_entitlement(
            ValidationRequest(
                entitlement_id=request.entitlement_id,
                device_id=request.device_id,
                token=entitlement['token_signature']
            ),
            db
        )

        if not validation.valid:
            raise HTTPException(status_code=400, detail=validation.error)

        # Get current entitlement with row lock
        entitlement = await conn.fetchrow(
            "SELECT * FROM entitlements WHERE entitlement_id = $1 FOR UPDATE",
            request.entitlement_id
        )

        # Check if enough quota
        if entitlement['remaining_volume'] < request.volume_consumed:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient quota. Remaining: {entitlement['remaining_volume']}, Consumed: {request.volume_consumed}"
            )

        # Start transaction
        async with conn.transaction():
            # Check for duplicate usage report (idempotency)
            existing_report = await conn.fetchrow(
                """SELECT report_id FROM usage_reports
                   WHERE entitlement_id = $1 AND session_id = $2""",
                request.entitlement_id, request.session_id
            )

            if existing_report:
                # Deduplicate - return current state
                return UsageReportResult(
                    remaining_volume=entitlement['remaining_volume'],
                    transaction_id=str(existing_report['report_id']),
                    status=entitlement['status']
                )

            # Record usage
            await conn.execute(
                """INSERT INTO usage_reports
                   (entitlement_id, device_id, volume_consumed, reported_at, session_id)
                   VALUES ($1, $2, $3, $4, $5)""",
                request.entitlement_id, request.device_id,
                request.volume_consumed, request.reported_at, request.session_id
            )

            # Deduct from entitlement
            new_remaining = entitlement['remaining_volume'] - request.volume_consumed
            new_status = 'PARTIALLY_CONSUMED' if new_remaining > 0 else 'EXHAUSTED'

            await conn.execute(
                """UPDATE entitlements
                   SET remaining_volume = $1, status = $2, updated_at = NOW(), version = version + 1
                   WHERE entitlement_id = $3""",
                new_remaining, new_status, request.entitlement_id
            )

        return UsageReportResult(
            remaining_volume=new_remaining,
            transaction_id=str(uuid.uuid4()),
            status=new_status
        )

@app.get("/api/v1/subscriber/{subscriber_id}/quota")
async def get_subscriber_quota(subscriber_id: str, db=Depends(get_db)):
    """
    Get subscriber quota balance
    """
    async with db.acquire() as conn:
        quota = await conn.fetchrow(
            "SELECT * FROM quota_balances WHERE subscriber_id = $1",
            subscriber_id
        )

        if not quota:
            raise HTTPException(status_code=404, detail="Subscriber not found")

        return {
            "subscriber_id": quota['subscriber_id'],
            "allocated_volume": quota['allocated_volume'],
            "remaining_volume": quota['remaining_volume'],
            "last_updated": quota['last_updated']
        }

@app.get("/api/v1/entitlement/{entitlement_id}")
async def get_entitlement(entitlement_id: str, db=Depends(get_db)):
    """
    Get entitlement details
    """
    async with db.acquire() as conn:
        entitlement = await conn.fetchrow(
            "SELECT * FROM entitlements WHERE entitlement_id = $1",
            entitlement_id
        )

        if not entitlement:
            raise HTTPException(status_code=404, detail="Entitlement not found")

        return {
            "entitlement_id": entitlement['entitlement_id'],
            "source_subscriber_id": entitlement['source_subscriber_id'],
            "destination_device_id": entitlement['destination_device_id'],
            "allocated_volume": entitlement['allocated_volume'],
            "remaining_volume": entitlement['remaining_volume'],
            "issued_at": entitlement['issued_at'],
            "expires_at": entitlement['expires_at'],
            "status": entitlement['status'],
            "transfer_mode": entitlement['transfer_mode']
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "simulated-operator-api"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
