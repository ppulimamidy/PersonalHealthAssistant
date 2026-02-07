-- Create missing audit tables for auth service

-- Create enum types for audit
DO $$ BEGIN
    CREATE TYPE auditeventtype AS ENUM (
        'LOGIN_SUCCESS', 'LOGIN_FAILURE', 'LOGOUT', 'PASSWORD_CHANGE', 'PASSWORD_RESET',
        'ACCOUNT_LOCKED', 'ACCOUNT_UNLOCKED', 'MFA_ENABLED', 'MFA_DISABLED',
        'MFA_VERIFICATION_SUCCESS', 'MFA_VERIFICATION_FAILURE', 'MFA_DEVICE_ADDED',
        'MFA_DEVICE_REMOVED', 'BACKUP_CODE_USED', 'SESSION_CREATED', 'SESSION_REVOKED',
        'SESSION_EXPIRED', 'TOKEN_REFRESHED', 'TOKEN_REVOKED', 'USER_CREATED',
        'USER_UPDATED', 'USER_DELETED', 'USER_ACTIVATED', 'USER_DEACTIVATED',
        'ROLE_ASSIGNED', 'ROLE_REMOVED', 'PERMISSION_GRANTED', 'PERMISSION_REVOKED',
        'DATA_ACCESSED', 'DATA_CREATED', 'DATA_UPDATED', 'DATA_DELETED',
        'DATA_EXPORTED', 'DATA_IMPORTED', 'DATA_SHARED', 'CONSENT_GIVEN',
        'CONSENT_WITHDRAWN', 'CONSENT_UPDATED', 'SUSPICIOUS_ACTIVITY',
        'SECURITY_ALERT', 'BREACH_DETECTED', 'COMPLIANCE_VIOLATION',
        'SYSTEM_CONFIG_CHANGED', 'BACKUP_CREATED', 'MAINTENANCE_MODE', 'SYSTEM_ERROR'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE auditseverity AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE auditstatus AS ENUM ('PENDING', 'PROCESSED', 'REVIEWED', 'ESCALATED', 'RESOLVED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create auth_audit_logs table
CREATE TABLE IF NOT EXISTS auth.auth_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    event_type auditeventtype NOT NULL,
    event_timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    severity auditseverity DEFAULT 'LOW',
    status auditstatus DEFAULT 'PENDING',
    description TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    ip_address VARCHAR,
    user_agent TEXT,
    session_id UUID REFERENCES auth.sessions(id),
    device_id VARCHAR,
    location VARCHAR,
    timezone VARCHAR,
    isp VARCHAR,
    risk_score INTEGER DEFAULT 0,
    is_suspicious BOOLEAN DEFAULT FALSE,
    threat_indicators JSONB DEFAULT '[]',
    hipaa_relevant BOOLEAN DEFAULT FALSE,
    phi_accessed BOOLEAN DEFAULT FALSE,
    data_subject_id UUID,
    related_user_id UUID REFERENCES auth.users(id),
    related_session_id UUID REFERENCES auth.sessions(id),
    related_device_id UUID,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_event_type ON auth.auth_audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_event_timestamp ON auth.auth_audit_logs(event_timestamp);
CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_user_id ON auth.auth_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_severity ON auth.auth_audit_logs(severity);
CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_status ON auth.auth_audit_logs(status);
CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_ip_address ON auth.auth_audit_logs(ip_address);
CREATE INDEX IF NOT EXISTS idx_auth_audit_logs_session_id ON auth.auth_audit_logs(session_id);

-- Create trigger for updated_at
CREATE TRIGGER update_auth_audit_logs_updated_at
    BEFORE UPDATE ON auth.auth_audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION auth.update_updated_at_column();
