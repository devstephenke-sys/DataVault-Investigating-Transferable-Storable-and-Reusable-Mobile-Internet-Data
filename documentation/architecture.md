# DataVault Phase 3 Architecture Documentation

## Overview

DataVault Phase 3 implements a three-mode architecture to investigate and demonstrate portable mobile data entitlement transfer and redemption capabilities.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MODE A: SIMULATED OPERATOR                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐           │
│  │ Mobile App   │────▶│ Operator API │────▶│ Operator CHF │           │
│  │ Simulator    │     │ (FastAPI)    │     │ (PostgreSQL) │           │
│  └──────────────┘     └──────────────┘     └──────────────┘           │
│                              │                                            │
│                              ▼                                            │
│                       ┌──────────────┐                                   │
│                       │ DataVault    │                                   │
│                       │ Backend      │                                   │
│                       │ (FastAPI)    │                                   │
│                       └──────────────┘                                   │
│                              │                                            │
│                              ▼                                            │
│                       ┌──────────────┐                                   │
│                       │ Device       │                                   │
│                       │ Simulator    │                                   │
│                       │ (Flask)      │                                   │
│                       └──────────────┘                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                       MODE B: REAL CELLULAR GATEWAY                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐           │
│  │ Client Phone │────▶│ DataVault    │────▶│ Cellular     │           │
│  │ (Wi-Fi)      │     │ Device       │     │ Modem        │           │
│  └──────────────┘     │ (Linux)      │     │ (4G/5G)      │           │
│                       └──────────────┘     └──────────────┘           │
│                              │                                            │
│                              ▼                                            │
│                       ┌──────────────┐                                   │
│                       │ Mobile       │                                   │
│                       │ Network      │                                   │
│                       └──────────────┘                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                   MODE C: OPERATOR ENTITLEMENT ADAPTER                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐           │
│  │ Abstract     │────▶│ Adapter      │────▶│ Real         │           │
│  │ Interface    │     │ Layer        │     │ Operator API │           │
│  └──────────────┘     └──────────────┘     └──────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Mode A: Simulated Operator

### Purpose
Demonstrate the complete software architecture and workflow without requiring real operator integration.

### Components

#### 1. Simulated Operator API (FastAPI)
- **Location:** `mode_a_simulated_operator/operator_api/`
- **Endpoints:**
  - `POST /api/v1/quota/transfer` - Transfer quota from subscriber to device
  - `POST /api/v1/entitlement/validate` - Validate entitlement token
  - `POST /api/v1/entitlement/report-usage` - Report usage and deduct quota
  - `GET /api/v1/subscriber/{id}/quota` - Get subscriber quota balance
  - `GET /api/v1/entitlement/{id}` - Get entitlement details

#### 2. Simulated Operator CHF (PostgreSQL)
- **Location:** `mode_a_simulated_operator/database/`
- **Tables:**
  - `subscribers` - Subscriber accounts
  - `quota_balances` - Data quota balances
  - `entitlements` - Portable entitlement records
  - `usage_reports` - Usage tracking
  - `transfer_audit_log` - Audit trail
  - `device_registrations` - Registered devices

#### 3. DataVault Backend (FastAPI)
- **Location:** `backend/api/`
- **Endpoints:**
  - `POST /api/v1/devices/register` - Register DataVault device
  - `GET /api/v1/devices/{id}` - Get device information
  - `POST /api/v1/entitlement/transfer` - Initiate quota transfer
  - `POST /api/v1/entitlement/validate` - Validate entitlement
  - `POST /api/v1/entitlement/report-usage` - Report usage
  - `GET /api/v1/devices/{id}/entitlements` - Get device entitlements
  - `POST /api/v1/devices/{id}/heartbeat` - Device heartbeat

#### 4. Device Simulator (Flask)
- **Location:** `device_simulator/`
- **Endpoints:**
  - `GET /device/status` - Device status
  - `POST /device/token/store` - Store entitlement token
  - `GET /device/token/{id}` - Retrieve token
  - `GET /device/tokens` - List all tokens
  - `POST /device/validate` - Validate token with backend
  - `POST /device/report-usage` - Report usage
  - `POST /device/simulate-traffic` - Simulate network traffic
  - `POST /device/restart` - Simulate device restart

### Data Flow

```
1. Mobile App initiates transfer
   ↓
2. Operator API validates subscriber quota
   ↓
3. Operator API deducts quota atomically
   ↓
4. Operator API creates entitlement record
   ↓
5. Operator API generates signed JWT token
   ↓
6. Mobile App receives token
   ↓
7. Mobile App transfers token to device
   ↓
8. Device stores token locally (SQLite)
   ↓
9. Device validates token with backend
   ↓
10. Device uses quota (simulated traffic)
    ↓
11. Device reports usage to backend
    ↓
12. Backend reports usage to operator
    ↓
13. Operator deducts from entitlement
```

## Mode B: Real Cellular Gateway

### Purpose
Implement a physical DataVault gateway with real cellular modem and Wi-Fi hotspot.

### Components

#### 1. Device Agent
- **Location:** `mode_b_cellular_gateway/device_agent/`
- **Responsibilities:**
  - Entitlement management
  - Token storage and validation
  - Usage tracking
  - Communication with backend

#### 2. Networking Layer
- **Location:** `mode_b_cellular_gateway/networking/`
- **Responsibilities:**
  - Wi-Fi hotspot management (hostapd)
  - Network routing (iptables/nftables)
  - Firewall configuration
  - DHCP server (dnsmasq)

#### 3. Modem Interface
- **Location:** `mode_b_cellular_gateway/modem_interface/`
- **Responsibilities:**
  - Cellular modem control (ModemManager)
  - SIM/eSIM management
  - Network connection management
  - Signal monitoring

### Hardware Requirements

**Minimum:**
- CPU: ARM Cortex-A53 or x86-64
- RAM: 2GB
- Storage: 16GB
- Cellular: 4G LTE modem with SIM slot
- Wi-Fi: 802.11ac
- Power: 5V/2A

**Recommended:**
- CPU: ARM Cortex-A72 or x86-64
- RAM: 4GB+
- Storage: 64GB+
- Cellular: 4G/5G modem with eSIM support
- Wi-Fi: 802.11ax (Wi-Fi 6)
- Power: Battery backup capability

### Software Stack

- **OS:** Linux (OpenWrt or Ubuntu Server)
- **Modem Manager:** ModemManager
- **Wi-Fi:** hostapd, dnsmasq
- **Firewall:** nftables
- **Language:** Python 3.12

## Mode C: Operator Entitlement Adapter

### Purpose
Design production-ready adapter interfaces for future operator integration.

### Components

#### 1. Abstract Interfaces
- **Location:** `mode_c_operator_adapter/interfaces/`
- **Interfaces:**
  - `IQuotaTransferAdapter` - Quota transfer operations
  - `IEntitlementValidationAdapter` - Entitlement validation
  - `IUsageReportingAdapter` - Usage reporting
  - `IAuthenticationAdapter` - Authentication

#### 2. Mock Implementations
- **Location:** `mode_c_operator_adapter/adapters/`
- **Implementations:**
  - `SimulatedOperatorAdapter` - Uses Mode A simulated operator
  - `SafaricomAdapter` - Mock Safaricom integration
  - `AirtelAdapter` - Mock Airtel integration

### Integration Pattern

```python
# Abstract interface
class IQuotaTransferAdapter:
    async def transfer_quota(self, request: TransferRequest) -> Entitlement:
        raise NotImplementedError

# Concrete implementation
class SafaricomAdapter(IQuotaTransferAdapter):
    async def transfer_quota(self, request: TransferRequest) -> Entitlement:
        # Call Safaricom API
        response = await self.client.post(
            self.api_endpoint,
            json=request.to_dict()
        )
        return Entitlement.from_dict(response.json())
```

## Security Architecture

### Authentication
- Subscriber: OAuth 2.0 authorization code flow
- Device: Mutual TLS with device certificates
- API: OAuth 2.0 client credentials

### Authorization
- Role-based access control (RBAC)
- Device binding (IMEI, hardware key)
- Transfer limits and cooling-off periods

### Data Protection
- TLS 1.3 for all network communication
- AES-256-GCM for data at rest
- JWT signed with RS256
- Hardware security module (HSM) for key storage

### Audit Logging
- All quota transfers logged
- All entitlement validations logged
- All usage reports logged
- Immutable audit trail

## Database Schema

### Operator Database
- Subscribers
- Quota balances
- Entitlements
- Usage reports
- Transfer audit log
- Device registrations
- Subscriber authorizations

### DataVault Backend Database
- Users
- Devices
- Local entitlements (cache)
- Local usage records
- Network interfaces
- Device heartbeats
- Audit logs
- Operator integrations

## Testing Strategy

### Mode A Tests
1. Create subscriber with 10 GB quota
2. Transfer 5 GB to device
3. Verify persistence after restart
4. Validate and use entitlement
5. Verify usage accounting
6. Prevent duplicate redemption
7. Test failure recovery
8. Verify independent connectivity

### Mode B Tests
1. Cellular modem connection
2. Wi-Fi hotspot broadcasting
3. Network routing
4. Real traffic measurement
5. Local usage enforcement

### Mode C Tests
1. Adapter interface compliance
2. Mock adapter functionality
3. Error handling
4. Rate limiting

## Deployment

### Development
```bash
docker-compose up -d
python mode_a_simulated_operator/operator_api/main.py
python backend/api/main.py
python device_simulator/main.py
```

### Production
- Kubernetes deployment
- PostgreSQL cluster
- Redis cluster
- Load balancer
- Monitoring (Prometheus, Grafana)
- Logging (ELK stack)

## Limitations

### Mode A
- No real operator integration
- Simulated cellular connection
- No hardware security

### Mode B
- Requires physical hardware
- Real SIM subscription required
- Operator integration still needed for quota transfer

### Mode C
- Only interfaces defined
- No real operator integration
- Mock implementations only
