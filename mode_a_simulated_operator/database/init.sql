-- Simulated Operator Database Schema
-- This simulates the operator's CHF (Charging Function) database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Subscribers table (simulated operator subscriber accounts)
CREATE TABLE IF NOT EXISTS subscribers (
    subscriber_id VARCHAR(255) PRIMARY KEY,
    msisdn VARCHAR(20) UNIQUE NOT NULL,
    imsi VARCHAR(20) UNIQUE,
    name VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Quota balances table (subscriber data quotas)
CREATE TABLE IF NOT EXISTS quota_balances (
    balance_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscriber_id VARCHAR(255) NOT NULL,
    allocated_volume BIGINT NOT NULL DEFAULT 0,
    remaining_volume BIGINT NOT NULL DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_subscriber FOREIGN KEY (subscriber_id) REFERENCES subscribers(subscriber_id) ON DELETE CASCADE,
    CONSTRAINT non_negative_remaining CHECK (remaining_volume >= 0)
);

CREATE INDEX idx_quota_balances_subscriber ON quota_balances(subscriber_id);

-- Entitlements table (portable data entitlements issued by operator)
CREATE TABLE IF NOT EXISTS entitlements (
    entitlement_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_subscriber_id VARCHAR(255) NOT NULL,
    destination_device_id VARCHAR(255) NOT NULL,
    allocated_volume BIGINT NOT NULL,
    remaining_volume BIGINT NOT NULL,
    issued_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    transfer_mode VARCHAR(50) NOT NULL,
    token_signature TEXT NOT NULL,
    device_binding JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_source_subscriber FOREIGN KEY (source_subscriber_id) REFERENCES subscribers(subscriber_id) ON DELETE CASCADE,
    CONSTRAINT non_negative_remaining CHECK (remaining_volume >= 0),
    CONSTRAINT valid_status CHECK (status IN ('ACTIVE', 'EXHAUSTED', 'EXPIRED', 'REVOKED', 'TRANSFER_PENDING', 'STORED', 'PARTIALLY_CONSUMED'))
);

CREATE INDEX idx_entitlements_device ON entitlements(destination_device_id);
CREATE INDEX idx_entitlements_subscriber ON entitlements(source_subscriber_id);
CREATE INDEX idx_entitlements_status ON entitlements(status);
CREATE INDEX idx_entitlements_expires ON entitlements(expires_at);

-- Usage reports table (reported usage from devices)
CREATE TABLE IF NOT EXISTS usage_reports (
    report_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entitlement_id UUID NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    volume_consumed BIGINT NOT NULL,
    reported_at TIMESTAMP WITH TIME ZONE NOT NULL,
    session_id VARCHAR(255),
    cell_id VARCHAR(255),
    location_lat DECIMAL(10, 8),
    location_lon DECIMAL(11, 8),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_entitlement FOREIGN KEY (entitlement_id) REFERENCES entitlements(entitlement_id) ON DELETE CASCADE
);

CREATE INDEX idx_usage_reports_entitlement ON usage_reports(entitlement_id);
CREATE INDEX idx_usage_reports_device ON usage_reports(device_id);
CREATE INDEX idx_usage_reports_session ON usage_reports(session_id);

-- Transfer audit log
CREATE TABLE IF NOT EXISTS transfer_audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entitlement_id UUID NOT NULL,
    source_subscriber_id VARCHAR(255) NOT NULL,
    destination_device_id VARCHAR(255) NOT NULL,
    volume_transferred BIGINT NOT NULL,
    transfer_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    initiated_by VARCHAR(255) NOT NULL,
    approval_method VARCHAR(50) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_entitlement_audit FOREIGN KEY (entitlement_id) REFERENCES entitlements(entitlement_id) ON DELETE CASCADE
);

CREATE INDEX idx_audit_log_entitlement ON transfer_audit_log(entitlement_id);
CREATE INDEX idx_audit_log_subscriber ON transfer_audit_log(source_subscriber_id);
CREATE INDEX idx_audit_log_timestamp ON transfer_audit_log(transfer_timestamp);

-- Device registrations
CREATE TABLE IF NOT EXISTS device_registrations (
    device_id VARCHAR(255) PRIMARY KEY,
    imei VARCHAR(50) UNIQUE,
    serial_number VARCHAR(255),
    hardware_public_key TEXT,
    registered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE'
);

-- Subscriber authorizations
CREATE TABLE IF NOT EXISTS subscriber_authorizations (
    auth_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscriber_id VARCHAR(255) NOT NULL,
    authorized_device_id VARCHAR(255) NOT NULL,
    authorized_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_device FOREIGN KEY (authorized_device_id) REFERENCES device_registrations(device_id) ON DELETE CASCADE
);

-- Revocation log
CREATE TABLE IF NOT EXISTS revocation_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entitlement_id UUID,
    revoked_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    reason TEXT NOT NULL,
    revoked_by VARCHAR(255) NOT NULL,
    bulk_device_id VARCHAR(255),
    bulk_subscriber_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_revocation_entitlement ON revocation_log(entitlement_id);
CREATE INDEX idx_revocation_device ON revocation_log(bulk_device_id);
CREATE INDEX idx_revocation_subscriber ON revocation_log(bulk_subscriber_id);

-- Insert test data
INSERT INTO subscribers (subscriber_id, msisdn, imsi, name, status) VALUES
('TEST-SUB-001', '254712345678', '639012345678901', 'Test User 1', 'ACTIVE'),
('TEST-SUB-002', '254712345679', '639012345678902', 'Test User 2', 'ACTIVE');

INSERT INTO quota_balances (subscriber_id, allocated_volume, remaining_volume) VALUES
('TEST-SUB-001', 10737418240, 10737418240),  -- 10 GB
('TEST-SUB-002', 5368709120, 5368709120);    -- 5 GB

INSERT INTO device_registrations (device_id, imei, serial_number, status) VALUES
('DV-001-ABCD', '865432102345678', 'SN-001-ABCD', 'ACTIVE'),
('DV-002-EFGH', '865432102345679', 'SN-002-EFGH', 'ACTIVE');
