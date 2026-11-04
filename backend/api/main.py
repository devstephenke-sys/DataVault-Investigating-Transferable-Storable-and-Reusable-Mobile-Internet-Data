"""
DataVault Backend API
Manages entitlements, device registration, and operator integration
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import jwt
import asyncpg
from contextlib import asynccontextmanager
import os
import httpx
import json

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://datavault:datavault_backend_password@localhost:5433/datavault_backend")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")
OPERATOR_API_URL = os.getenv("OPERATOR_API_URL", "http://localhost:8001")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "datavault_secret_key_change_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")

security = HTTPBearer()

# Database connection pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    yield
    await db_pool.close()

app = FastAPI(
    title="DataVault Backend API",
    description="Backend services for DataVault entitlement management",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic models
class DeviceRegistration(BaseModel):
    device_id: str
    imei: Optional[str] = None
    serial_number: Optional[str] = None
    hardware_public_key: Optional[str] = None

class TransferRequest(BaseModel):
    source_subscriber: str
    destination_device_id: str
    volume: int
    expiry: datetime
    transfer_mode: str = "TRANSFER"

class Entitlement(BaseModel):
    entitlement_id: str
    source_subscriber_id: str
    destination_device_id: str
    allocated_volume: int
    remaining_volume: int
    issued_at: datetime
    expires_at: datetime
    status: str
    token: str

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

# Helper functions
async def get_db():
    return db_pool

async def call_operator_api(endpoint: str, method: str = "POST", data: dict = None):
    """Call the simulated operator API"""
    url = f"{OPERATOR_API_URL}{endpoint}"
    async with httpx.AsyncClient() as client:
        if method == "POST":
            response = await client.post(url, json=data, timeout=30.0)
        elif method == "GET":
            response = await client.get(url, timeout=30.0)
        return response.json()

# API Endpoints
@app.post("/api/v1/devices/register", status_code=201)
async def register_device(device: DeviceRegistration, db=Depends(get_db)):
    """
    Register a new DataVault device
    """
    async with db.acquire() as conn:
        # Check if device already exists
        existing = await conn.fetchrow(
            "SELECT device_id FROM devices WHERE device_id = $1",
            device.device_id
        )

        if existing:
            raise HTTPException(status_code=409, detail="Device already registered")

        # Register device
        await conn.execute(
            """INSERT INTO devices (device_id, imei, serial_number, hardware_public_key, status)
               VALUES ($1, $2, $3, $4, 'ACTIVE')""",
            device.device_id, device.imei, device.serial_number, device.hardware_public_key
        )

        return {
            "device_id": device.device_id,
            "status": "ACTIVE",
            "registered_at": datetime.utcnow()
        }

@app.get("/api/v1/devices/{device_id}")
async def get_device(device_id: str, db=Depends(get_db)):
    """
    Get device information
    """
    async with db.acquire() as conn:
        device = await conn.fetchrow(
            "SELECT * FROM devices WHERE device_id = $1",
            device_id
        )

        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        return {
            "device_id": device['device_id'],
            "imei": device['imei'],
            "serial_number": device['serial_number'],
            "status": device['status'],
            "registered_at": device['registered_at'],
            "last_heartbeat": device['last_heartbeat']
        }

@app.post("/api/v1/entitlement/transfer", response_model=Entitlement)
async def initiate_transfer(request: TransferRequest, db=Depends(get_db)):
    """
    Initiate quota transfer through operator API
    """
    # Call operator API
    operator_request = {
        "source_subscriber": request.source_subscriber,
        "destination_device_id": request.destination_device_id,
        "volume": request.volume,
        "expiry": request.expiry,
        "transfer_mode": request.transfer_mode,
        "authorization": "Bearer test_token"  # In production, this would be a real subscriber token
    }

    try:
        operator_response = await call_operator_api("/api/v1/quota/transfer", "POST", operator_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Operator API error: {str(e)}")

    # Cache entitlement locally
    async with db.acquire() as conn:
        await conn.execute(
            """INSERT INTO local_entitlements
               (entitlement_id, source_subscriber_id, destination_device_id,
                allocated_volume, remaining_volume, issued_at, expires_at,
                status, token, token_signature, device_binding)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)""",
            operator_response['entitlement_id'],
            request.source_subscriber,
            request.destination_device_id,
            operator_response['allocated_volume'],
            operator_response['remaining_volume'],
            operator_response['issued_at'],
            operator_response['expires_at'],
            operator_response['status'],
            operator_response['token'],
            "",  # token_signature
            json.dumps({"device_id": request.destination_device_id})
        )

    return Entitlement(**operator_response)

@app.post("/api/v1/entitlement/validate", response_model=ValidationResult)
async def validate_entitlement(request: ValidationRequest, db=Depends(get_db)):
    """
    Validate entitlement (locally cached and through operator)
    """
    async with db.acquire() as conn:
        # Check local cache
        local_entitlement = await conn.fetchrow(
            "SELECT * FROM local_entitlements WHERE entitlement_id = $1",
            request.entitlement_id
        )

        if not local_entitlement:
            # Validate through operator
            operator_request = {
                "entitlement_id": request.entitlement_id,
                "device_id": request.device_id,
                "token": request.token
            }

            try:
                operator_response = await call_operator_api("/api/v1/entitlement/validate", "POST", operator_request)
                return ValidationResult(**operator_response)
            except Exception as e:
                return ValidationResult(
                    valid=False,
                    error=f"Operator validation failed: {str(e)}"
                )

        # Local validation
        if local_entitlement['destination_device_id'] != request.device_id:
            return ValidationResult(
                valid=False,
                error="Device mismatch"
            )

        if local_entitlement['status'] not in ['ACTIVE', 'PARTIALLY_CONSUMED']:
            return ValidationResult(
                valid=False,
                error=f"Entitlement status: {local_entitlement['status']}",
                status=local_entitlement['status']
            )

        if local_entitlement['expires_at'] < datetime.utcnow():
            return ValidationResult(
                valid=False,
                error="Entitlement expired",
                status="EXPIRED"
            )

        return ValidationResult(
            valid=True,
            remaining_volume=local_entitlement['remaining_volume'],
            expires_at=local_entitlement['expires_at'],
            status=local_entitlement['status']
        )

@app.post("/api/v1/entitlement/report-usage")
async def report_usage(request: UsageReport, db=Depends(get_db)):
    """
    Report usage to both local cache and operator
    """
    async with db.acquire() as conn:
        # Get local entitlement
        entitlement = await conn.fetchrow(
            "SELECT * FROM local_entitlements WHERE entitlement_id = $1",
            request.entitlement_id
        )

        if not entitlement:
            raise HTTPException(status_code=404, detail="Entitlement not found")

        # Check quota
        if entitlement['remaining_volume'] < request.volume_consumed:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient quota. Remaining: {entitlement['remaining_volume']}"
            )

        # Record local usage
        await conn.execute(
            """INSERT INTO local_usage_records
               (entitlement_id, device_id, volume_consumed, measured_at, session_id, synced_to_operator)
               VALUES ($1, $2, $3, $4, $5, FALSE)""",
            request.entitlement_id, request.device_id,
            request.volume_consumed, request.reported_at, request.session_id
        )

        # Deduct from local cache
        new_remaining = entitlement['remaining_volume'] - request.volume_consumed
        new_status = 'PARTIALLY_CONSUMED' if new_remaining > 0 else 'EXHAUSTED'

        await conn.execute(
            """UPDATE local_entitlements
               SET remaining_volume = $1, status = $2, updated_at = NOW(), version = version + 1
               WHERE entitlement_id = $3""",
            new_remaining, new_status, request.entitlement_id
        )

        # Report to operator
        operator_request = {
            "entitlement_id": request.entitlement_id,
            "device_id": request.device_id,
            "volume_consumed": request.volume_consumed,
            "session_id": request.session_id,
            "reported_at": request.reported_at
        }

        try:
            operator_response = await call_operator_api("/api/v1/entitlement/report-usage", "POST", operator_request)

            # Mark as synced
            await conn.execute(
                "UPDATE local_usage_records SET synced_to_operator = TRUE WHERE entitlement_id = $1 AND session_id = $2",
                request.entitlement_id, request.session_id
            )

            return operator_response
        except Exception as e:
            # Return local result even if operator sync fails
            return {
                "remaining_volume": new_remaining,
                "transaction_id": str(uuid.uuid4()),
                "status": new_status,
                "warning": f"Operator sync failed: {str(e)}"
            }

@app.get("/api/v1/devices/{device_id}/entitlements")
async def get_device_entitlements(device_id: str, db=Depends(get_db)):
    """
    Get all entitlements for a device
    """
    async with db.acquire() as conn:
        entitlements = await conn.fetch(
            """SELECT * FROM local_entitlements
               WHERE destination_device_id = $1
               ORDER BY issued_at DESC""",
            device_id
        )

        return [
            {
                "entitlement_id": e['entitlement_id'],
                "source_subscriber_id": e['source_subscriber_id'],
                "allocated_volume": e['allocated_volume'],
                "remaining_volume": e['remaining_volume'],
                "issued_at": e['issued_at'],
                "expires_at": e['expires_at'],
                "status": e['status']
            }
            for e in entitlements
        ]

@app.post("/api/v1/devices/{device_id}/heartbeat")
async def device_heartbeat(device_id: str, heartbeat_data: dict, db=Depends(get_db)):
    """
    Receive device heartbeat
    """
    async with db.acquire() as conn:
        # Update device last seen
        await conn.execute(
            "UPDATE devices SET last_heartbeat = NOW() WHERE device_id = $1",
            device_id
        )

        # Record heartbeat
        await conn.execute(
            """INSERT INTO device_heartbeats
               (device_id, heartbeat_timestamp, cpu_usage, memory_usage, disk_usage, temperature, uptime_seconds)
               VALUES ($1, NOW(), $2, $3, $4, $5, $6)""",
            device_id,
            heartbeat_data.get('cpu_usage'),
            heartbeat_data.get('memory_usage'),
            heartbeat_data.get('disk_usage'),
            heartbeat_data.get('temperature'),
            heartbeat_data.get('uptime_seconds')
        )

        return {"status": "received"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "datavault-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
