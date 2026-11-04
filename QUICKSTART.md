# DataVault Phase 3 - Quick Start Guide

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Git
- 8GB RAM minimum
- 20GB disk space

## Installation

### 1. Clone or Navigate to Repository

```bash
cd "C:\Users\DBTECH AFRICA\Desktop\Data Vault"
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Docker Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL for simulated operator (port 5432)
- PostgreSQL for DataVault backend (port 5433)
- Redis cache (port 6379)

### 5. Wait for Services to Initialize

```bash
# Check services are healthy
docker-compose ps
```

Wait until all services show "healthy" status (may take 10-20 seconds).

## Running the System

### Option 1: Run with Docker Compose (Recommended)

```bash
docker-compose up
```

This will start all services:
- Simulated Operator API (http://localhost:8001)
- DataVault Backend API (http://localhost:8000)
- Device Simulator (http://localhost:8002)

### Option 2: Run Services Manually

Open three separate terminal windows:

**Terminal 1 - Simulated Operator API:**
```bash
cd mode_a_simulated_operator/operator_api
python main.py
```

**Terminal 2 - DataVault Backend:**
```bash
cd backend/api
python main.py
```

**Terminal 3 - Device Simulator:**
```bash
cd device_simulator
python main.py
```

## Running Tests

### Run All Tests

```bash
python scripts/run_tests.py
```

### Run Mode A Tests Only

```bash
python -m pytest tests/test_mode_a_simulated_operator.py -v
```

### Run Specific Test

```bash
python -m pytest tests/test_mode_a_simulated_operator.py::TestModeASimulatedOperator::test_2_quota_transfer_5gb -v
```

## Using the Mobile App Simulator

```bash
cd mobile_app_simulator
python main.py
```

This will:
1. Transfer 5 GB from TEST-SUB-001 to DV-001-ABCD
2. Transfer 1 GB from TEST-SUB-002 to DV-002-EFGH
3. Display the entitlement tokens

## API Documentation

### Simulated Operator API (http://localhost:8001)

- **POST /api/v1/quota/transfer** - Transfer quota from subscriber to device
- **POST /api/v1/entitlement/validate** - Validate entitlement token
- **POST /api/v1/entitlement/report-usage** - Report usage and deduct quota
- **GET /api/v1/subscriber/{id}/quota** - Get subscriber quota balance
- **GET /api/v1/entitlement/{id}** - Get entitlement details
- **GET /health** - Health check

### DataVault Backend API (http://localhost:8000)

- **POST /api/v1/devices/register** - Register a device
- **GET /api/v1/devices/{id}** - Get device information
- **POST /api/v1/entitlement/transfer** - Initiate quota transfer
- **POST /api/v1/entitlement/validate** - Validate entitlement
- **POST /api/v1/entitlement/report-usage** - Report usage
- **GET /api/v1/devices/{id}/entitlements** - Get device entitlements
- **POST /api/v1/devices/{id}/heartbeat** - Device heartbeat
- **GET /health** - Health check

### Device Simulator API (http://localhost:8002)

- **GET /device/status** - Device status
- **POST /device/token/store** - Store entitlement token
- **GET /device/token/{id}** - Retrieve token
- **GET /device/tokens** - List all tokens
- **POST /device/validate** - Validate token with backend
- **POST /device/report-usage** - Report usage
- **POST /device/simulate-traffic** - Simulate network traffic
- **POST /device/restart** - Simulate device restart
- **GET /health** - Health check

## Example Workflow

### 1. Register a Device

```bash
curl -X POST http://localhost:8000/api/v1/devices/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "DV-001-ABCD",
    "imei": "865432102345678",
    "serial_number": "SN-001-ABCD"
  }'
```

### 2. Transfer Quota

```bash
curl -X POST http://localhost:8001/api/v1/quota/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "source_subscriber": "TEST-SUB-001",
    "destination_device_id": "DV-001-ABCD",
    "volume": 5368709120,
    "expiry": "2026-12-31T23:59:59Z",
    "transfer_mode": "TRANSFER",
    "authorization": "Bearer test_token"
  }'
```

### 3. Store Token on Device

```bash
curl -X POST http://localhost:8002/device/token/store \
  -H "Content-Type: application/json" \
  -d '{
    "entitlement_id": "<entitlement_id_from_step_2>",
    "token": "<token_from_step_2>",
    "destination_device_id": "DV-001-ABCD",
    "allocated_volume": 5368709120,
    "remaining_volume": 5368709120,
    "issued_at": "2026-11-04T10:00:00Z",
    "expires_at": "2026-12-31T23:59:59Z",
    "status": "ACTIVE"
  }'
```

### 4. Validate Entitlement

```bash
curl -X POST http://localhost:8001/api/v1/entitlement/validate \
  -H "Content-Type: application/json" \
  -d '{
    "entitlement_id": "<entitlement_id>",
    "device_id": "DV-001-ABCD",
    "token": "<token>"
  }'
```

### 5. Simulate Traffic

```bash
curl -X POST http://localhost:8002/device/simulate-traffic \
  -H "Content-Type: application/json" \
  -d '{
    "entitlement_id": "<entitlement_id>",
    "volume_bytes": 1073741824
  }'
```

### 6. Check Remaining Quota

```bash
curl http://localhost:8001/api/v1/entitlement/<entitlement_id>
```

## Stopping the System

```bash
docker-compose down
```

## Troubleshooting

### Database Connection Error

If you get a database connection error:
1. Check Docker services are running: `docker-compose ps`
2. Wait 10-20 seconds for databases to initialize
3. Check database logs: `docker-compose logs postgres-operator`

### Port Already in Use

If ports are already in use:
1. Check what's using the port: `netstat -ano | findstr :8000` (Windows)
2. Stop the conflicting service
3. Or change ports in docker-compose.yml

### Tests Fail

If tests fail:
1. Ensure all services are running
2. Check service health: `curl http://localhost:8001/health`
3. Check test logs for specific errors
4. Restart services: `docker-compose restart`

## Next Steps

1. Review the test results in `TEST_REPORT.md`
2. Read the engineering verdict in `DATAVAULT_PHASE3_ENGINEERING_VERDICT.md`
3. Review architecture documentation in `documentation/architecture.md`
4. Review hardware requirements in `documentation/hardware.md`
5. Decide on next steps based on verdict recommendations

## Support

For issues or questions:
1. Check documentation in `documentation/` directory
2. Review test scripts in `scripts/` directory
3. Examine source code for implementation details
