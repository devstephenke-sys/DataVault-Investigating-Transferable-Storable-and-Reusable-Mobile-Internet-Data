-- DataVault Backend Database Schema
-- This is DataVault's own database for managing entitlements and device state

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (DataVault system users)
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'USER',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Devices table (DataVault devices managed by this backend)
CREATE TABLE IF NOT EXISTS devices (
    device_id VARCHAR(255) PRIMARY KEY,
    imei VARCHAR(50) UNIQUE,
    serial_number VARCHAR(255),
    hardware_public_key TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Local entitlement cache (entitlements received from operator)
CREATE TABLE IF NOT EXISTS local_entitlements (
    entitlement_id UUID PRIMARY KEY,
    source_subscriber_id VARCHAR(255) NOT NULL,
    destination_device_id VARCHAR(255) NOT NULL,
    allocated_volume BIGINT NOT NULL,
    remaining_volume BIGINT NOT NULL,
    issued_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    token TEXT NOT NULL,
    token_signature TEXT NOT NULL,
    device_binding JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    synced_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_device FOREIGN KEY (destination_device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    CONSTRAINT non_negative_remaining CHECK (remaining_volume >= 0)
);

CREATE INDEX idx_local_entitlements_device ON local_entitlements(destination_device_id);
CREATE INDEX idx_local_entitlements_status ON local_entitlements(status);
CREATE INDEX idx_local_entitlements_expires ON local_entitlements(expires_at);

-- Local usage records (usage tracked by DataVault)
CREATE TABLE IF NOT EXISTS local_usage_records (
    record_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entitlement_id UUID NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    volume_consumed BIGINT NOT NULL,
    measured_at TIMESTAMP WITH TIME ZONE NOT NULL,
    session_id VARCHAR(255),
    synced_to_operator BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_entitlement FOREIGN KEY (entitlement_id) REFERENCES local_entitlements(entitlement_id) ON DELETE CASCADE
);

CREATE INDEX idx_local_usage_entitlement ON local_usage_records(entitlement_id);
CREATE INDEX idx_local_usage_device ON local_usage_records(device_id);
CREATE INDEX idx_local_usage_synced ON local_usage_records(synced_to_operator);

-- Network interfaces (for Mode B - cellular gateway)
CREATE TABLE IF NOT EXISTS network_interfaces (
    interface_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(255) NOT NULL,
    interface_name VARCHAR(50) NOT NULL,
    interface_type VARCHAR(50) NOT NULL,  -- CELLULAR, WIFI, ETHERNET
    ip_address INET,
    mac_address VARCHAR(17),
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    last_seen TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_network_device FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

-- Device heartbeats
CREATE TABLE IF NOT EXISTS device_heartbeats (
    heartbeat_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id VARCHAR(255) NOT NULL,
    heartbeat_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    cpu_usage DECIMAL(5,2),
    memory_usage DECIMAL(5,2),
    disk_usage DECIMAL(5,2),
    temperature DECIMAL(5,2),
    uptime_seconds BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_heartbeat_device FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE
);

CREATE INDEX idx_heartbeats_device ON device_heartbeats(device_id);
CREATE INDEX idx_heartbeats_timestamp ON device_heartbeats(heartbeat_timestamp);

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    device_id VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_device ON audit_logs(device_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(created_at);

-- Operator integrations (for Mode C)
CREATE TABLE IF NOT EXISTS operator_integrations (
    integration_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operator_name VARCHAR(255) NOT NULL,
    operator_code VARCHAR(50) UNIQUE NOT NULL,
    api_endpoint VARCHAR(255) NOT NULL,
    api_version VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    configuration JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert test device
INSERT INTO devices (device_id, imei, serial_number, status) VALUES
('DV-001-ABCD', '865432102345678', 'SN-001-ABCD', 'ACTIVE');
