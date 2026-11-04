# DataVault Phase 3: Proof of Concept Implementation

## Overview

This repository contains the Phase 3 implementation of DataVault - a portable mobile data entitlement and redemption system. This implementation builds on the Phase 2 engineering report and implements three distinct operating modes:

1. **Mode A: Simulated Operator** - Complete simulated operator environment with quota transfer, entitlement issuance, and redemption
2. **Mode B: Real Cellular Gateway** - Physical DataVault gateway with cellular modem and Wi-Fi hotspot
3. **Mode C: Real Operator Entitlement Adapter** - Production-ready adapter interface for future operator integration

## Project Structure

```
datavault-phase3/
├── mode_a_simulated_operator/     # Simulated operator implementation
│   ├── operator_api/              # Quota Transfer, Validation, Usage Reporting APIs
│   ├── operator_chf/              # Simulated Charging Function
│   └── database/                 # Operator database schema
├── mode_b_cellular_gateway/       # Physical gateway implementation
│   ├── device_agent/              # Device management agent
│   ├── networking/                # Wi-Fi hotspot, routing, firewall
│   └── modem_interface/           # Cellular modem integration
├── mode_c_operator_adapter/       # Operator integration interfaces
│   ├── interfaces/               # Abstract interfaces for operator APIs
│   └── adapters/                  # Mock implementations
├── backend/                       # DataVault backend services
│   ├── api/                       # FastAPI endpoints
│   ├── entitlement_engine/        # Core entitlement logic
│   ├── database/                  # DataVault database
│   └── security/                  # Authentication, JWT, device binding
├── device_simulator/              # Device simulation for testing
├── token_storage/                 # Token storage implementation
├── tests/                         # Automated acceptance tests
├── documentation/                 # Technical documentation
└── docker-compose.yml             # Container orchestration
```

## Technology Stack

- **Backend:** Python 3.12, FastAPI, PostgreSQL 15, Redis 7
- **Device:** Python 3.12, SQLite (local storage), Mock modem interface
- **Frontend:** React (dashboard simulator)
- **Infrastructure:** Docker, Docker Compose
- **Security:** JWT (RS256), device binding, audit logging

## Getting Started

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd datavault-phase3
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start infrastructure:
```bash
docker-compose up -d
```

5. Run database migrations:
```bash
python scripts/migrate.py
```

6. Start services:
```bash
# Simulated operator
python mode_a_simulated_operator/operator_api/main.py

# DataVault backend
python backend/api/main.py

# Device simulator
python device_simulator/main.py
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_mode_a_simulated_operator.py
pytest tests/test_mode_b_cellular_gateway.py
pytest tests/test_mode_c_operator_adapter.py

# Run with coverage
pytest --cov=. tests/
```

## Test Categories

### Mode A: Simulated Operator Tests
- Quota transfer from subscriber to device
- Entitlement token generation and validation
- Usage reporting and quota deduction
- Persistence across device restarts
- Duplicate prevention and double-spending protection

### Mode B: Real Cellular Network Tests
- Cellular modem connection
- Wi-Fi hotspot broadcasting
- Network routing and firewall
- Real traffic measurement
- Local usage enforcement

### Mode C: Real Transferred Entitlement Tests
- Attempt to redeem simulated entitlement on real network
- Document operator-side limitations
- Identify missing capabilities

## Documentation

- [Architecture Overview](documentation/architecture.md)
- [API Documentation](documentation/api.md)
- [Hardware Requirements](documentation/hardware.md)
- [Security Model](documentation/security.md)
- [Development Guide](documentation/development.md)

## Project Status

**Current Phase:** Phase 3 - Proof of Concept Implementation

**Progress:**
- [x] Project structure created
- [ ] Docker Compose environment
- [ ] Simulated operator implementation
- [ ] DataVault backend implementation
- [ ] Device simulator implementation
- [ ] Automated tests
- [ ] Linux gateway agent
- [ ] Hardware documentation
- [ ] Final engineering verdict

## License

Internal Use Only - DataVault Project

## Version

Phase 3.0.0 - November 2026
