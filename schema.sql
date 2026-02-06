-- Personal Health Assistant Database Schema
-- Schema separation for microservices architecture

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas for each service
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS user_profile;
CREATE SCHEMA IF NOT EXISTS health_tracking;
CREATE SCHEMA IF NOT EXISTS device_data;
CREATE SCHEMA IF NOT EXISTS medical_records;
CREATE SCHEMA IF NOT EXISTS nutrition;

-- Set search path
SET search_path TO auth, user_profile, health_tracking, device_data, medical_records, nutrition, public;

-- ============================================================================
-- AUTH SCHEMA
-- ============================================================================

-- Users table (auth service)
CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supabase_user_id VARCHAR UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR UNIQUE,
    password_hash VARCHAR(255),
    auth0_user_id VARCHAR,
    mfa_status VARCHAR DEFAULT 'disabled' NOT NULL,
    mfa_secret VARCHAR,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth TIMESTAMP,
    gender VARCHAR(20),
    user_type VARCHAR NOT NULL,
    status VARCHAR DEFAULT 'pending_verification' NOT NULL,
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false,
    hipaa_consent_given BOOLEAN DEFAULT false,
    hipaa_consent_date TIMESTAMP,
    data_processing_consent BOOLEAN DEFAULT false,
    marketing_consent BOOLEAN DEFAULT false,
    failed_login_attempts INTEGER DEFAULT 0,
    last_failed_login TIMESTAMP,
    account_locked_until TIMESTAMP,
    password_changed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    user_metadata JSON DEFAULT '{}'
);

-- User roles
CREATE TABLE auth.roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User role assignments
CREATE TABLE auth.user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID REFERENCES auth.users(id),
    UNIQUE(user_id, role_id)
);

-- User sessions
CREATE TABLE auth.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    refresh_token_hash VARCHAR(255),
    device_info JSONB,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MFA settings
CREATE TABLE auth.mfa_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    mfa_type VARCHAR(20) NOT NULL, -- 'totp', 'sms', 'email'
    secret_key VARCHAR(255),
    backup_codes JSONB,
    is_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Password reset tokens
CREATE TABLE auth.password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email verification tokens
CREATE TABLE auth.email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log
CREATE TABLE auth.audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Consent records
CREATE TABLE auth.consent_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    consent_type VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    granted BOOLEAN NOT NULL,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- ============================================================================
-- USER PROFILE SCHEMA
-- ============================================================================

-- User profiles
CREATE TABLE user_profile.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    avatar_url VARCHAR(500),
    bio TEXT,
    location VARCHAR(200),
    timezone VARCHAR(50),
    language VARCHAR(10) DEFAULT 'en',
    date_format VARCHAR(20) DEFAULT 'YYYY-MM-DD',
    time_format VARCHAR(10) DEFAULT '24h',
    weight_unit VARCHAR(10) DEFAULT 'kg',
    height_unit VARCHAR(10) DEFAULT 'cm',
    temperature_unit VARCHAR(10) DEFAULT 'celsius',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Health attributes
CREATE TABLE user_profile.health_attributes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    height_cm DECIMAL(5,2),
    weight_kg DECIMAL(5,2),
    bmi DECIMAL(4,2),
    blood_type VARCHAR(5),
    allergies JSONB,
    medications JSONB,
    medical_conditions JSONB,
    emergency_contacts JSONB,
    insurance_info JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- User preferences
CREATE TABLE user_profile.preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    notification_settings JSONB,
    privacy_settings JSONB,
    health_goals JSONB,
    dietary_preferences JSONB,
    activity_preferences JSONB,
    sleep_preferences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Privacy settings
CREATE TABLE user_profile.privacy_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    profile_visibility VARCHAR(20) DEFAULT 'private',
    health_data_sharing JSONB,
    data_retention_policy JSONB,
    third_party_sharing BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- ============================================================================
-- HEALTH TRACKING SCHEMA
-- ============================================================================

-- Health metrics
CREATE TABLE health_tracking.health_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    metric_type VARCHAR(50) NOT NULL,
    value DECIMAL(10,4) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(100),
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Health goals
CREATE TABLE health_tracking.health_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    metric_type VARCHAR(50) NOT NULL,
    goal_type VARCHAR(20) NOT NULL DEFAULT 'target',
    target_value DECIMAL(10,4),
    current_value DECIMAL(10,4),
    unit VARCHAR(20) NOT NULL,
    frequency VARCHAR(20) NOT NULL DEFAULT 'once',
    start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    target_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    progress DECIMAL(5,2),
    goal_metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Health insights
CREATE TABLE health_tracking.health_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    insight_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    summary TEXT,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(20) NOT NULL DEFAULT 'new',
    confidence DECIMAL(3,2),
    actionable BOOLEAN DEFAULT true,
    action_taken BOOLEAN DEFAULT false,
    related_metrics JSONB,
    related_goals JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    acted_upon_at TIMESTAMP
);

-- Vital signs
CREATE TABLE health_tracking.vital_signs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    vital_sign_type VARCHAR(50) NOT NULL,
    measurement_method VARCHAR(50) NOT NULL,
    measurement_location VARCHAR(100),
    systolic DECIMAL CHECK (systolic >= 0),
    diastolic DECIMAL CHECK (diastolic >= 0),
    mean_arterial_pressure DECIMAL,
    heart_rate DECIMAL CHECK (heart_rate >= 0),
    heart_rate_variability DECIMAL,
    irregular_heartbeat_detected VARCHAR(10),
    temperature DECIMAL CHECK (temperature >= 0),
    temperature_method VARCHAR(50),
    oxygen_saturation DECIMAL CHECK (oxygen_saturation >= 0 AND oxygen_saturation <= 100),
    perfusion_index DECIMAL,
    respiratory_rate DECIMAL CHECK (respiratory_rate >= 0),
    respiratory_pattern VARCHAR(50),
    blood_glucose DECIMAL CHECK (blood_glucose >= 0),
    glucose_unit VARCHAR(10),
    glucose_context VARCHAR(50),
    weight DECIMAL CHECK (weight >= 0),
    height DECIMAL CHECK (height >= 0),
    bmi DECIMAL CHECK (bmi >= 0),
    waist_circumference DECIMAL CHECK (waist_circumference >= 0),
    body_fat_percentage DECIMAL CHECK (body_fat_percentage >= 0 AND body_fat_percentage <= 100),
    muscle_mass DECIMAL CHECK (muscle_mass >= 0),
    bone_density DECIMAL CHECK (bone_density >= 0),
    skin_temperature DECIMAL CHECK (skin_temperature >= 0),
    blood_alcohol_content DECIMAL CHECK (blood_alcohol_content >= 0 AND blood_alcohol_content <= 1),
    carbon_monoxide DECIMAL CHECK (carbon_monoxide >= 0),
    lung_capacity DECIMAL CHECK (lung_capacity >= 0),
    eye_pressure DECIMAL CHECK (eye_pressure >= 0),
    hearing_level DECIMAL CHECK (hearing_level >= 0),
    device_id VARCHAR(100),
    device_model VARCHAR(100),
    measurement_notes TEXT,
    measurement_quality VARCHAR(20),
    measurement_duration DECIMAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    vital_sign_metadata JSONB DEFAULT '{}'
);

-- Symptoms
CREATE TABLE health_tracking.symptoms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    symptom_name VARCHAR(200) NOT NULL,
    symptom_category VARCHAR(50) NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL,
    severity_level DECIMAL(3,1) NOT NULL CHECK (severity_level >= 1 AND severity_level <= 10),
    impact_on_daily_activities VARCHAR(20),
    frequency VARCHAR(20),
    frequency_count DECIMAL,
    frequency_period VARCHAR(20),
    duration VARCHAR(20),
    duration_hours DECIMAL CHECK (duration_hours >= 0),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    body_location VARCHAR(200),
    body_side VARCHAR(20),
    radiation VARCHAR(200),
    quality VARCHAR(100),
    triggers VARCHAR[],
    context TEXT,
    associated_symptoms VARCHAR[],
    relief_factors VARCHAR[],
    aggravating_factors VARCHAR[],
    related_conditions VARCHAR[],
    medications_taken VARCHAR[],
    treatments_tried VARCHAR[],
    sleep_impact VARCHAR(20),
    work_impact VARCHAR(20),
    social_impact VARCHAR(20),
    emotional_impact VARCHAR(20),
    is_recurring BOOLEAN DEFAULT false,
    recurrence_pattern VARCHAR(100),
    last_occurrence TIMESTAMP,
    next_expected TIMESTAMP,
    requires_medical_attention BOOLEAN DEFAULT false,
    medical_attention_urgency VARCHAR(20),
    medical_attention_received BOOLEAN DEFAULT false,
    medical_attention_date TIMESTAMP,
    medical_attention_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    symptom_metadata JSONB DEFAULT '{}'
);

-- Devices
CREATE TABLE health_tracking.devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    device_name VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(255),
    model VARCHAR(255),
    serial_number VARCHAR(255) UNIQUE,
    firmware_version VARCHAR(100),
    device_status VARCHAR(20),
    last_sync TIMESTAMP,
    battery_level INTEGER,
    is_connected BOOLEAN,
    connection_method VARCHAR(50),
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerts
CREATE TABLE health_tracking.alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20),
    status VARCHAR(20),
    is_read BOOLEAN DEFAULT false,
    is_actionable BOOLEAN DEFAULT true,
    action_taken TEXT,
    action_taken_at TIMESTAMP,
    scheduled_for TIMESTAMP,
    expires_at TIMESTAMP,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DEVICE DATA SCHEMA
-- ============================================================================

-- Devices table (device data service)
CREATE TABLE device_data.devices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    device_type VARCHAR(50) NOT NULL,
    manufacturer VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    serial_number VARCHAR(255) UNIQUE,
    mac_address VARCHAR(17) UNIQUE,
    connection_type VARCHAR(50) NOT NULL,
    connection_id VARCHAR(255),
    api_key VARCHAR(500),
    api_secret VARCHAR(500),
    status VARCHAR(50) DEFAULT 'inactive',
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    supported_metrics JSONB DEFAULT '[]',
    firmware_version VARCHAR(100),
    battery_level INTEGER,
    metadata JSONB DEFAULT '{}',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,
    last_used_at TIMESTAMP
);

-- Device data points table
CREATE TABLE device_data.device_data_points (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES device_data.devices(id) ON DELETE CASCADE,
    data_type VARCHAR(50) NOT NULL,
    source VARCHAR(50) DEFAULT 'device_sync',
    value NUMERIC(10, 4) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    raw_value TEXT,
    quality VARCHAR(20) DEFAULT 'unknown',
    is_validated BOOLEAN DEFAULT FALSE,
    validation_score NUMERIC(3, 2),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    is_processed BOOLEAN DEFAULT FALSE,
    is_anomaly BOOLEAN,
    anomaly_score NUMERIC(3, 2)
);

-- Device sync logs table
CREATE TABLE device_data.device_sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES device_data.devices(id) ON DELETE CASCADE,
    sync_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    data_points_synced INTEGER DEFAULT 0,
    sync_duration NUMERIC(5, 2),
    errors JSONB DEFAULT '[]',
    warnings JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Device health checks table
CREATE TABLE device_data.device_health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES device_data.devices(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    battery_level INTEGER,
    connection_quality VARCHAR(20),
    last_sync_status VARCHAR(50),
    error_message TEXT,
    firmware_version VARCHAR(100),
    sync_latency NUMERIC(5, 2),
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Device data types table (reference table for supported data types)
CREATE TABLE device_data.device_data_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    unit VARCHAR(50) NOT NULL,
    description TEXT,
    data_type VARCHAR(50) NOT NULL, -- numeric, text, boolean, etc.
    min_value NUMERIC(10, 4),
    max_value NUMERIC(10, 4),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Auth indexes
CREATE INDEX idx_auth_users_email ON auth.users(email);
CREATE INDEX idx_auth_users_username ON auth.users(supabase_user_id);
CREATE INDEX idx_auth_users_created_at ON auth.users(created_at);
CREATE INDEX idx_auth_sessions_user_id ON auth.sessions(user_id);
CREATE INDEX idx_auth_sessions_token_hash ON auth.sessions(token_hash);
CREATE INDEX idx_auth_sessions_expires_at ON auth.sessions(expires_at);
CREATE INDEX idx_auth_user_roles_user_id ON auth.user_roles(user_id);
CREATE INDEX idx_auth_audit_log_user_id ON auth.audit_log(user_id);
CREATE INDEX idx_auth_audit_log_created_at ON auth.audit_log(created_at);
CREATE INDEX idx_auth_consent_records_user_id ON auth.consent_records(user_id);

-- User profile indexes
CREATE INDEX idx_user_profile_profiles_user_id ON user_profile.profiles(user_id);
CREATE INDEX idx_user_profile_health_attributes_user_id ON user_profile.health_attributes(user_id);
CREATE INDEX idx_user_profile_preferences_user_id ON user_profile.preferences(user_id);
CREATE INDEX idx_user_profile_privacy_settings_user_id ON user_profile.privacy_settings(user_id);

-- Health tracking indexes
CREATE INDEX idx_health_tracking_metrics_user_id ON health_tracking.health_metrics(user_id);
CREATE INDEX idx_health_tracking_metrics_type ON health_tracking.health_metrics(metric_type);
CREATE INDEX idx_health_tracking_metrics_timestamp ON health_tracking.health_metrics(timestamp);
CREATE INDEX idx_health_tracking_metrics_user_timestamp ON health_tracking.health_metrics(user_id, timestamp);
CREATE INDEX idx_health_tracking_metrics_type_timestamp ON health_tracking.health_metrics(metric_type, timestamp);
CREATE INDEX idx_health_tracking_goals_user_id ON health_tracking.health_goals(user_id);
CREATE INDEX idx_health_tracking_goals_status ON health_tracking.health_goals(status);
CREATE INDEX idx_health_tracking_goals_user_status ON health_tracking.health_goals(user_id, status);
CREATE INDEX idx_health_tracking_insights_user_id ON health_tracking.health_insights(user_id);
CREATE INDEX idx_health_tracking_insights_type ON health_tracking.health_insights(insight_type);
CREATE INDEX idx_health_tracking_insights_status ON health_tracking.health_insights(status);
CREATE INDEX idx_health_tracking_insights_user_status ON health_tracking.health_insights(user_id, status);
CREATE INDEX idx_health_tracking_insights_type_created ON health_tracking.health_insights(insight_type, created_at);

-- Indexes for new health_tracking tables
CREATE INDEX idx_health_tracking_vital_signs_user_created ON health_tracking.vital_signs(user_id, created_at);
CREATE INDEX idx_health_tracking_vital_signs_type_created ON health_tracking.vital_signs(vital_sign_type, created_at);
CREATE INDEX idx_health_tracking_symptoms_user_created ON health_tracking.symptoms(user_id, created_at);
CREATE INDEX idx_health_tracking_symptoms_category_created ON health_tracking.symptoms(symptom_category, created_at);
CREATE INDEX idx_health_tracking_symptoms_severity_created ON health_tracking.symptoms(severity, created_at);
CREATE INDEX idx_health_tracking_devices_user_id ON health_tracking.devices(user_id);
CREATE INDEX idx_health_tracking_devices_serial_number ON health_tracking.devices(serial_number);
CREATE INDEX idx_health_tracking_devices_type ON health_tracking.devices(device_type);
CREATE INDEX idx_health_tracking_alerts_user_id ON health_tracking.alerts(user_id);
CREATE INDEX idx_health_tracking_alerts_status ON health_tracking.alerts(status);
CREATE INDEX idx_health_tracking_alerts_severity ON health_tracking.alerts(severity);
CREATE INDEX idx_health_tracking_alerts_created_at ON health_tracking.alerts(created_at);

-- Device data indexes
CREATE INDEX idx_device_data_devices_user_id ON device_data.devices(user_id);
CREATE INDEX idx_device_data_devices_status ON device_data.devices(status);
CREATE INDEX idx_device_data_devices_type ON device_data.devices(device_type);
CREATE INDEX idx_device_data_devices_serial ON device_data.devices(serial_number);
CREATE INDEX idx_device_data_devices_mac ON device_data.devices(mac_address);

CREATE INDEX idx_device_data_points_user_id ON device_data.device_data_points(user_id);
CREATE INDEX idx_device_data_points_device_id ON device_data.device_data_points(device_id);
CREATE INDEX idx_device_data_points_timestamp ON device_data.device_data_points(timestamp);
CREATE INDEX idx_device_data_points_data_type ON device_data.device_data_points(data_type);
CREATE INDEX idx_device_data_points_quality ON device_data.device_data_points(quality);
CREATE INDEX idx_device_data_points_anomaly ON device_data.device_data_points(is_anomaly);
CREATE INDEX idx_device_data_points_user_timestamp ON device_data.device_data_points(user_id, timestamp);
CREATE INDEX idx_device_data_points_device_timestamp ON device_data.device_data_points(device_id, timestamp);
CREATE INDEX idx_device_data_points_type_timestamp ON device_data.device_data_points(data_type, timestamp);

CREATE INDEX idx_device_sync_logs_device_id ON device_data.device_sync_logs(device_id);
CREATE INDEX idx_device_sync_logs_status ON device_data.device_sync_logs(status);
CREATE INDEX idx_device_sync_logs_started_at ON device_data.device_sync_logs(started_at);

CREATE INDEX idx_device_health_checks_device_id ON device_data.device_health_checks(device_id);
CREATE INDEX idx_device_health_checks_status ON device_data.device_health_checks(status);
CREATE INDEX idx_device_health_checks_checked_at ON device_data.device_health_checks(checked_at);

CREATE INDEX idx_device_data_types_name ON device_data.device_data_types(name);
CREATE INDEX idx_device_data_types_category ON device_data.device_data_types(category);
CREATE INDEX idx_device_data_types_active ON device_data.device_data_types(is_active);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all tables
CREATE TRIGGER update_auth_users_updated_at BEFORE UPDATE ON auth.users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_auth_roles_updated_at BEFORE UPDATE ON auth.roles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_auth_sessions_updated_at BEFORE UPDATE ON auth.sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_auth_mfa_settings_updated_at BEFORE UPDATE ON auth.mfa_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profile_profiles_updated_at BEFORE UPDATE ON user_profile.profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_profile_health_attributes_updated_at BEFORE UPDATE ON user_profile.health_attributes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_profile_preferences_updated_at BEFORE UPDATE ON user_profile.preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_profile_privacy_settings_updated_at BEFORE UPDATE ON user_profile.privacy_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_health_tracking_health_metrics_updated_at BEFORE UPDATE ON health_tracking.health_metrics FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_health_tracking_health_goals_updated_at BEFORE UPDATE ON health_tracking.health_goals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_health_tracking_health_insights_updated_at BEFORE UPDATE ON health_tracking.health_insights FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_health_tracking_vital_signs_updated_at BEFORE UPDATE ON health_tracking.vital_signs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_health_tracking_symptoms_updated_at BEFORE UPDATE ON health_tracking.symptoms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_health_tracking_devices_updated_at BEFORE UPDATE ON health_tracking.devices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_health_tracking_alerts_updated_at BEFORE UPDATE ON health_tracking.alerts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Device data triggers
CREATE TRIGGER update_device_data_devices_updated_at BEFORE UPDATE ON device_data.devices FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_device_data_points_updated_at BEFORE UPDATE ON device_data.device_data_points FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_device_data_types_updated_at BEFORE UPDATE ON device_data.device_data_types FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Insert default roles
INSERT INTO auth.roles (name, description, permissions) VALUES
('admin', 'Administrator with full access', '{"all": true}'),
('user', 'Standard user', '{"read_own": true, "write_own": true}'),
('healthcare_provider', 'Healthcare provider with patient access', '{"read_patients": true, "write_patients": true}'),
('researcher', 'Researcher with anonymized data access', '{"read_anonymized": true}');

-- Insert default user (for testing)
INSERT INTO auth.users (supabase_user_id, email, first_name, last_name, user_type, status, email_verified) VALUES
('admin-uuid-123', 'admin@healthassistant.com', 'Admin', 'User', 'admin', 'active', true);

-- Assign admin role to default user
INSERT INTO auth.user_roles (user_id, role_id, assigned_by) 
SELECT u.id, r.id, u.id 
FROM auth.users u, auth.roles r 
WHERE u.email = 'admin@healthassistant.com' AND r.name = 'admin';

-- Insert default device data types
INSERT INTO device_data.device_data_types (name, category, unit, description, data_type, min_value, max_value) VALUES
('heart_rate', 'cardiovascular', 'bpm', 'Heart rate in beats per minute', 'numeric', 40, 200),
('blood_pressure_systolic', 'cardiovascular', 'mmHg', 'Systolic blood pressure', 'numeric', 70, 200),
('blood_pressure_diastolic', 'cardiovascular', 'mmHg', 'Diastolic blood pressure', 'numeric', 40, 130),
('blood_oxygen', 'respiratory', '%', 'Blood oxygen saturation', 'numeric', 70, 100),
('respiratory_rate', 'respiratory', 'breaths/min', 'Breathing rate per minute', 'numeric', 8, 40),
('temperature', 'vital_signs', '°C', 'Body temperature', 'numeric', 35, 42),
('weight', 'body_composition', 'kg', 'Body weight', 'numeric', 20, 300),
('body_fat_percentage', 'body_composition', '%', 'Body fat percentage', 'numeric', 5, 50),
('muscle_mass', 'body_composition', 'kg', 'Muscle mass', 'numeric', 10, 100),
('steps', 'activity', 'count', 'Daily step count', 'numeric', 0, 50000),
('calories_burned', 'activity', 'kcal', 'Calories burned', 'numeric', 0, 5000),
('distance', 'activity', 'km', 'Distance traveled', 'numeric', 0, 100),
('sleep_duration', 'sleep', 'hours', 'Sleep duration', 'numeric', 0, 24),
('sleep_quality', 'sleep', 'score', 'Sleep quality score', 'numeric', 0, 100),
('glucose', 'metabolic', 'mg/dL', 'Blood glucose level', 'numeric', 40, 400),
('hydration', 'hydration', 'ml', 'Water intake', 'numeric', 0, 5000),
('stress_level', 'wellness', 'score', 'Stress level score', 'numeric', 0, 100),
('mood', 'wellness', 'score', 'Mood score', 'numeric', 0, 100);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.mfa_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.audit_log ENABLE ROW LEVEL SECURITY;

ALTER TABLE user_profile.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profile.health_attributes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profile.preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profile.privacy_settings ENABLE ROW LEVEL SECURITY;

ALTER TABLE health_tracking.health_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_tracking.health_goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_tracking.health_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_tracking.vital_signs ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_tracking.symptoms ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_tracking.devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_tracking.alerts ENABLE ROW LEVEL SECURITY;

ALTER TABLE device_data.devices ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_data.device_data_points ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_data.device_sync_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_data.device_health_checks ENABLE ROW LEVEL SECURITY;
ALTER TABLE device_data.device_data_types ENABLE ROW LEVEL SECURITY;

-- Medical Records RLS
ALTER TABLE medical_records.lab_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_records.imaging_studies ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_records.medical_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_records.biomarkers ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_records.document_processing ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_records.ehr_integration_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_records.clinical_nlp_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_records.document_agent_processing ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_records.access_audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_records.record_consents ENABLE ROW LEVEL SECURITY;

-- RLS Policies will be created by each service based on their specific requirements
-- This provides a foundation for secure multi-tenant data access

-- ============================================================================
-- VIEWS
-- ============================================================================

-- User summary view
CREATE VIEW user_profile.user_summary AS
SELECT 
    u.id,
    u.email,
    u.supabase_user_id,
    u.first_name,
    u.last_name,
    u.status,
    u.created_at,
    p.avatar_url,
    p.location,
    ha.height_cm,
    ha.weight_kg,
    ha.bmi,
    ha.blood_type
FROM auth.users u
LEFT JOIN user_profile.profiles p ON u.id = p.user_id
LEFT JOIN user_profile.health_attributes ha ON u.id = ha.user_id;

-- Health metrics summary view
CREATE VIEW health_tracking.metrics_summary AS
SELECT 
    user_id,
    metric_type,
    COUNT(*) as total_measurements,
    AVG(value) as average_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    MIN(timestamp) as first_measurement,
    MAX(timestamp) as last_measurement
FROM health_tracking.health_metrics
GROUP BY user_id, metric_type;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to calculate BMI
CREATE OR REPLACE FUNCTION health_tracking.calculate_bmi(height_cm DECIMAL, weight_kg DECIMAL)
RETURNS DECIMAL AS $$
BEGIN
    IF height_cm IS NULL OR weight_kg IS NULL OR height_cm <= 0 THEN
        RETURN NULL;
    END IF;
    
    RETURN ROUND((weight_kg / POWER(height_cm / 100, 2))::DECIMAL, 2);
END;
$$ LANGUAGE plpgsql;

-- Function to get user health score
CREATE OR REPLACE FUNCTION health_tracking.get_health_score(user_uuid UUID)
RETURNS DECIMAL AS $$
DECLARE
    score DECIMAL := 0;
    weight_score DECIMAL := 0;
    activity_score DECIMAL := 0;
    sleep_score DECIMAL := 0;
    latest_weight DECIMAL;
    latest_steps DECIMAL;
    latest_sleep DECIMAL;
BEGIN
    -- Get latest weight
    SELECT value INTO latest_weight
    FROM health_tracking.health_metrics
    WHERE user_id = user_uuid AND metric_type = 'weight'
    ORDER BY timestamp DESC LIMIT 1;
    
    -- Get latest steps (last 7 days average)
    SELECT AVG(value) INTO latest_steps
    FROM health_tracking.health_metrics
    WHERE user_id = user_uuid 
    AND metric_type = 'steps'
    AND timestamp >= CURRENT_DATE - INTERVAL '7 days';
    
    -- Get latest sleep duration (last 7 days average)
    SELECT AVG(value) INTO latest_sleep
    FROM health_tracking.health_metrics
    WHERE user_id = user_uuid 
    AND metric_type = 'sleep_duration'
    AND timestamp >= CURRENT_DATE - INTERVAL '7 days';
    
    -- Calculate weight score (assuming ideal BMI range 18.5-25)
    IF latest_weight IS NOT NULL THEN
        -- This is a simplified calculation - in practice you'd use height to calculate BMI
        weight_score := CASE 
            WHEN latest_weight BETWEEN 50 AND 100 THEN 25
            ELSE 10
        END;
    END IF;
    
    -- Calculate activity score
    IF latest_steps IS NOT NULL THEN
        activity_score := CASE 
            WHEN latest_steps >= 10000 THEN 25
            WHEN latest_steps >= 8000 THEN 20
            WHEN latest_steps >= 6000 THEN 15
            WHEN latest_steps >= 4000 THEN 10
            ELSE 5
        END;
    END IF;
    
    -- Calculate sleep score
    IF latest_sleep IS NOT NULL THEN
        sleep_score := CASE 
            WHEN latest_sleep BETWEEN 7 AND 9 THEN 25
            WHEN latest_sleep BETWEEN 6 AND 10 THEN 20
            WHEN latest_sleep BETWEEN 5 AND 11 THEN 15
            ELSE 10
        END;
    END IF;
    
    score := weight_score + activity_score + sleep_score;
    
    RETURN score;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON SCHEMA auth IS 'Authentication and authorization service schema';
COMMENT ON SCHEMA user_profile IS 'User profile and preferences service schema';
COMMENT ON SCHEMA health_tracking IS 'Health metrics and insights service schema';

COMMENT ON TABLE auth.users IS 'Core user accounts for the health assistant platform';
COMMENT ON TABLE auth.roles IS 'User roles and permissions';
COMMENT ON TABLE auth.sessions IS 'User session management';
COMMENT ON TABLE auth.audit_log IS 'Audit trail for security and compliance';

COMMENT ON TABLE user_profile.profiles IS 'User profile information';
COMMENT ON TABLE user_profile.health_attributes IS 'Core health attributes and medical information';
COMMENT ON TABLE user_profile.preferences IS 'User preferences and settings';
COMMENT ON TABLE user_profile.privacy_settings IS 'Privacy and data sharing preferences';

COMMENT ON TABLE health_tracking.health_metrics IS 'Health measurements and data points';
COMMENT ON TABLE health_tracking.health_goals IS 'User health goals and targets';
COMMENT ON TABLE health_tracking.health_insights IS 'AI-generated health insights and recommendations';

COMMENT ON SCHEMA medical_records IS 'Medical records and clinical data service schema';

COMMENT ON TABLE medical_records.lab_results IS 'Laboratory test results and clinical chemistry data';
COMMENT ON TABLE medical_records.imaging_studies IS 'Medical imaging studies and radiology reports';
COMMENT ON TABLE medical_records.medical_reports IS 'Clinical notes, discharge summaries, and medical reports';
COMMENT ON TABLE medical_records.biomarkers IS 'Specialized biomarkers and advanced laboratory tests';
COMMENT ON TABLE medical_records.document_processing IS 'OCR and document processing results';
COMMENT ON TABLE medical_records.ehr_integration_logs IS 'EHR integration and FHIR synchronization logs';
COMMENT ON TABLE medical_records.clinical_nlp_results IS 'Clinical NLP processing and AI analysis results';
COMMENT ON TABLE medical_records.document_agent_processing IS 'Document triage and agent processing results';
COMMENT ON TABLE medical_records.access_audit IS 'Medical records access audit trail for compliance';
COMMENT ON TABLE medical_records.record_consents IS 'Patient consent management for medical records';

-- ============================================================================
-- MEDICAL RECORDS INDEXES
-- ============================================================================

-- Lab Results Indexes
CREATE INDEX idx_medical_records_lab_results_patient_id ON medical_records.lab_results(patient_id);
CREATE INDEX idx_medical_records_lab_results_test_name ON medical_records.lab_results(test_name);
CREATE INDEX idx_medical_records_lab_results_test_date ON medical_records.lab_results(test_date);
CREATE INDEX idx_medical_records_lab_results_abnormal ON medical_records.lab_results(abnormal);
CREATE INDEX idx_medical_records_lab_results_critical ON medical_records.lab_results(critical);
CREATE INDEX idx_medical_records_lab_results_source ON medical_records.lab_results(source);
CREATE INDEX idx_medical_records_lab_results_external_id ON medical_records.lab_results(external_id);
CREATE INDEX idx_medical_records_lab_results_patient_date ON medical_records.lab_results(patient_id, test_date);

-- Imaging Studies Indexes
CREATE INDEX idx_medical_records_imaging_studies_patient_id ON medical_records.imaging_studies(patient_id);
CREATE INDEX idx_medical_records_imaging_studies_modality ON medical_records.imaging_studies(modality);
CREATE INDEX idx_medical_records_imaging_studies_study_date ON medical_records.imaging_studies(study_date);
CREATE INDEX idx_medical_records_imaging_studies_body_part ON medical_records.imaging_studies(body_part);
CREATE INDEX idx_medical_records_imaging_studies_status ON medical_records.imaging_studies(status);
CREATE INDEX idx_medical_records_imaging_studies_source ON medical_records.imaging_studies(source);
CREATE INDEX idx_medical_records_imaging_studies_external_id ON medical_records.imaging_studies(external_id);
CREATE INDEX idx_medical_records_imaging_studies_patient_date ON medical_records.imaging_studies(patient_id, study_date);

-- Medical Reports Indexes
CREATE INDEX idx_medical_records_medical_reports_patient_id ON medical_records.medical_reports(patient_id);
CREATE INDEX idx_medical_records_medical_reports_report_type ON medical_records.medical_reports(report_type);
CREATE INDEX idx_medical_records_medical_reports_report_date ON medical_records.medical_reports(report_date);
CREATE INDEX idx_medical_records_medical_reports_author ON medical_records.medical_reports(author);
CREATE INDEX idx_medical_records_medical_reports_status ON medical_records.medical_reports(status);
CREATE INDEX idx_medical_records_medical_reports_source ON medical_records.medical_reports(source);
CREATE INDEX idx_medical_records_medical_reports_external_id ON medical_records.medical_reports(external_id);
CREATE INDEX idx_medical_records_medical_reports_ocr_processed ON medical_records.medical_reports(ocr_processed);
CREATE INDEX idx_medical_records_medical_reports_patient_date ON medical_records.medical_reports(patient_id, report_date);
CREATE INDEX idx_medical_records_medical_reports_tags ON medical_records.medical_reports USING GIN(tags);

-- Biomarkers Indexes
CREATE INDEX idx_medical_records_biomarkers_patient_id ON medical_records.biomarkers(patient_id);
CREATE INDEX idx_medical_records_biomarkers_name ON medical_records.biomarkers(biomarker_name);
CREATE INDEX idx_medical_records_biomarkers_test_date ON medical_records.biomarkers(test_date);
CREATE INDEX idx_medical_records_biomarkers_abnormal ON medical_records.biomarkers(abnormal);
CREATE INDEX idx_medical_records_biomarkers_critical ON medical_records.biomarkers(critical);
CREATE INDEX idx_medical_records_biomarkers_source ON medical_records.biomarkers(source);
CREATE INDEX idx_medical_records_biomarkers_patient_date ON medical_records.biomarkers(patient_id, test_date);

-- Document Processing Indexes
CREATE INDEX idx_medical_records_document_processing_document_id ON medical_records.document_processing(document_id);
CREATE INDEX idx_medical_records_document_processing_type ON medical_records.document_processing(processing_type);
CREATE INDEX idx_medical_records_document_processing_status ON medical_records.document_processing(status);
CREATE INDEX idx_medical_records_document_processing_created_at ON medical_records.document_processing(created_at);

-- EHR Integration Logs Indexes
CREATE INDEX idx_medical_records_ehr_integration_logs_patient_id ON medical_records.ehr_integration_logs(patient_id);
CREATE INDEX idx_medical_records_ehr_integration_logs_type ON medical_records.ehr_integration_logs(integration_type);
CREATE INDEX idx_medical_records_ehr_integration_logs_operation ON medical_records.ehr_integration_logs(operation_type);
CREATE INDEX idx_medical_records_ehr_integration_logs_status ON medical_records.ehr_integration_logs(status);
CREATE INDEX idx_medical_records_ehr_integration_logs_created_at ON medical_records.ehr_integration_logs(created_at);

-- Clinical NLP Results Indexes
CREATE INDEX idx_medical_records_clinical_nlp_results_document_id ON medical_records.clinical_nlp_results(document_id);
CREATE INDEX idx_medical_records_clinical_nlp_results_model ON medical_records.clinical_nlp_results(nlp_model);
CREATE INDEX idx_medical_records_clinical_nlp_results_type ON medical_records.clinical_nlp_results(processing_type);
CREATE INDEX idx_medical_records_clinical_nlp_results_status ON medical_records.clinical_nlp_results(status);
CREATE INDEX idx_medical_records_clinical_nlp_results_created_at ON medical_records.clinical_nlp_results(created_at);

-- Document Agent Processing Indexes
CREATE INDEX idx_medical_records_document_agent_processing_document_id ON medical_records.document_agent_processing(document_id);
CREATE INDEX idx_medical_records_document_agent_processing_type ON medical_records.document_agent_processing(document_type);
CREATE INDEX idx_medical_records_document_agent_processing_status ON medical_records.document_agent_processing(processing_status);
CREATE INDEX idx_medical_records_document_agent_processing_priority ON medical_records.document_agent_processing(priority_score);
CREATE INDEX idx_medical_records_document_agent_processing_urgency ON medical_records.document_agent_processing(urgency_level);
CREATE INDEX idx_medical_records_document_agent_processing_category ON medical_records.document_agent_processing(document_category);
CREATE INDEX idx_medical_records_document_agent_processing_tags ON medical_records.document_agent_processing USING GIN(tags);
CREATE INDEX idx_medical_records_document_agent_processing_assigned_to ON medical_records.document_agent_processing(assigned_to);

-- Access Audit Indexes
CREATE INDEX idx_medical_records_access_audit_user_id ON medical_records.access_audit(user_id);
CREATE INDEX idx_medical_records_access_audit_record_id ON medical_records.access_audit(record_id);
CREATE INDEX idx_medical_records_access_audit_action ON medical_records.access_audit(action);
CREATE INDEX idx_medical_records_access_audit_created_at ON medical_records.access_audit(created_at);

-- Record Consents Indexes
CREATE INDEX idx_medical_records_record_consents_patient_id ON medical_records.record_consents(patient_id);
CREATE INDEX idx_medical_records_record_consents_record_id ON medical_records.record_consents(record_id);
CREATE INDEX idx_medical_records_record_consents_type ON medical_records.record_consents(consent_type);
CREATE INDEX idx_medical_records_record_consents_status ON medical_records.record_consents(consent_status);
CREATE INDEX idx_medical_records_record_consents_granted_at ON medical_records.record_consents(granted_at);

-- ============================================================================
-- MEDICAL RECORDS TRIGGERS
-- ============================================================================

CREATE TRIGGER update_medical_records_lab_results_updated_at BEFORE UPDATE ON medical_records.lab_results FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_records_imaging_studies_updated_at BEFORE UPDATE ON medical_records.imaging_studies FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_records_medical_reports_updated_at BEFORE UPDATE ON medical_records.medical_reports FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_records_biomarkers_updated_at BEFORE UPDATE ON medical_records.biomarkers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_records_document_processing_updated_at BEFORE UPDATE ON medical_records.document_processing FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_records_ehr_integration_logs_updated_at BEFORE UPDATE ON medical_records.ehr_integration_logs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_records_clinical_nlp_results_updated_at BEFORE UPDATE ON medical_records.clinical_nlp_results FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_records_document_agent_processing_updated_at BEFORE UPDATE ON medical_records.document_agent_processing FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_medical_records_record_consents_updated_at BEFORE UPDATE ON medical_records.record_consents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- MEDICAL RECORDS VIEWS
-- ============================================================================

-- Medical Records Summary View
CREATE VIEW medical_records.patient_records_summary AS
SELECT 
    patient_id,
    COUNT(DISTINCT lr.id) as lab_results_count,
    COUNT(DISTINCT im.id) as imaging_studies_count,
    COUNT(DISTINCT mr.id) as medical_reports_count,
    COUNT(DISTINCT bm.id) as biomarkers_count,
    MAX(lr.test_date) as latest_lab_date,
    MAX(im.study_date) as latest_imaging_date,
    MAX(mr.report_date) as latest_report_date,
    MAX(bm.test_date) as latest_biomarker_date,
    COUNT(CASE WHEN lr.abnormal = true THEN 1 END) as abnormal_labs_count,
    COUNT(CASE WHEN lr.critical = true THEN 1 END) as critical_labs_count,
    COUNT(CASE WHEN bm.abnormal = true THEN 1 END) as abnormal_biomarkers_count
FROM auth.users u
LEFT JOIN medical_records.lab_results lr ON u.id = lr.patient_id
LEFT JOIN medical_records.imaging_studies im ON u.id = im.patient_id
LEFT JOIN medical_records.medical_reports mr ON u.id = mr.patient_id
LEFT JOIN medical_records.biomarkers bm ON u.id = bm.patient_id
GROUP BY patient_id;

-- Abnormal Results Alert View
CREATE VIEW medical_records.abnormal_results_alert AS
SELECT 
    'lab_result' as record_type,
    id,
    patient_id,
    test_name as record_name,
    test_date as record_date,
    abnormal,
    critical,
    'Lab result outside normal range' as alert_message
FROM medical_records.lab_results
WHERE abnormal = true OR critical = true

UNION ALL

SELECT 
    'biomarker' as record_type,
    id,
    patient_id,
    biomarker_name as record_name,
    test_date as record_date,
    abnormal,
    critical,
    'Biomarker outside normal range' as alert_message
FROM medical_records.biomarkers
WHERE abnormal = true OR critical = true;

-- ============================================================================
-- MEDICAL RECORDS FUNCTIONS
-- ============================================================================

-- Function to calculate age-adjusted reference ranges
CREATE OR REPLACE FUNCTION medical_records.calculate_age_adjusted_reference_range(
    test_code VARCHAR,
    patient_age_years INTEGER,
    patient_gender VARCHAR DEFAULT NULL
)
RETURNS TABLE(low_value DECIMAL, high_value DECIMAL, unit VARCHAR) AS $$
BEGIN
    -- This is a simplified implementation
    -- In practice, you would have a comprehensive reference range database
    RETURN QUERY
    SELECT 
        CASE 
            WHEN test_code = 'GLU' AND patient_age_years >= 18 THEN 70.0
            WHEN test_code = 'GLU' AND patient_age_years < 18 THEN 60.0
            WHEN test_code = 'CRE' AND patient_gender = 'male' THEN 0.7
            WHEN test_code = 'CRE' AND patient_gender = 'female' THEN 0.5
            ELSE 0.0
        END as low_value,
        CASE 
            WHEN test_code = 'GLU' AND patient_age_years >= 18 THEN 100.0
            WHEN test_code = 'GLU' AND patient_age_years < 18 THEN 90.0
            WHEN test_code = 'CRE' AND patient_gender = 'male' THEN 1.3
            WHEN test_code = 'CRE' AND patient_gender = 'female' THEN 1.1
            ELSE 999.0
        END as high_value,
        CASE 
            WHEN test_code = 'GLU' THEN 'mg/dL'
            WHEN test_code = 'CRE' THEN 'mg/dL'
            ELSE 'units'
        END as unit;
END;
$$ LANGUAGE plpgsql;

-- Function to get patient's medical history summary
CREATE OR REPLACE FUNCTION medical_records.get_patient_medical_summary(patient_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    summary JSONB;
BEGIN
    SELECT jsonb_build_object(
        'patient_id', patient_uuid,
        'lab_results_count', (SELECT COUNT(*) FROM medical_records.lab_results WHERE patient_id = patient_uuid),
        'imaging_studies_count', (SELECT COUNT(*) FROM medical_records.imaging_studies WHERE patient_id = patient_uuid),
        'medical_reports_count', (SELECT COUNT(*) FROM medical_records.medical_reports WHERE patient_id = patient_uuid),
        'abnormal_results_count', (
            SELECT COUNT(*) FROM medical_records.lab_results 
            WHERE patient_id = patient_uuid AND (abnormal = true OR critical = true)
        ),
        'latest_lab_date', (SELECT MAX(test_date) FROM medical_records.lab_results WHERE patient_id = patient_uuid),
        'latest_imaging_date', (SELECT MAX(study_date) FROM medical_records.imaging_studies WHERE patient_id = patient_uuid),
        'latest_report_date', (SELECT MAX(report_date) FROM medical_records.medical_reports WHERE patient_id = patient_uuid)
    ) INTO summary;
    
    RETURN summary;
END;
$$ LANGUAGE plpgsql; 

-- ============================================================================
-- NUTRITION SCHEMA
-- ============================================================================

-- Food Recognition Results Table
CREATE TABLE nutrition.food_recognition_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL,
    recognition_id VARCHAR(100) UNIQUE NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Image metadata
    image_format VARCHAR(10),
    image_size_bytes INTEGER,
    image_hash VARCHAR(64),
    
    -- Recognition metadata
    models_used JSONB,
    processing_time_ms INTEGER,
    confidence_threshold FLOAT DEFAULT 0.5,
    
    -- Recognition results
    recognized_foods JSONB NOT NULL,
    total_foods_detected INTEGER DEFAULT 0,
    average_confidence FLOAT,
    
    -- User metadata
    meal_type VARCHAR(20),
    cuisine_hint VARCHAR(50),
    region_hint VARCHAR(50),
    dietary_restrictions JSONB,
    preferred_units VARCHAR(10) DEFAULT 'metric',
    
    -- Status and feedback
    is_corrected BOOLEAN DEFAULT FALSE,
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT
);

-- User Corrections Table
CREATE TABLE nutrition.user_corrections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recognition_result_id UUID NOT NULL REFERENCES nutrition.food_recognition_results(id) ON DELETE CASCADE,
    user_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Correction data
    original_food_name VARCHAR(100) NOT NULL,
    corrected_food_name VARCHAR(100),
    original_portion_g FLOAT,
    corrected_portion_g FLOAT,
    original_confidence FLOAT,
    user_confidence FLOAT DEFAULT 1.0,
    
    -- Correction metadata
    correction_type VARCHAR(20) NOT NULL,
    correction_reason TEXT
);

-- Meal Logs Table
CREATE TABLE nutrition.meal_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL,
    recognition_result_id UUID REFERENCES nutrition.food_recognition_results(id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Meal metadata
    meal_type VARCHAR(20) NOT NULL,
    meal_name VARCHAR(100),
    meal_description TEXT,
    
    -- Food items
    food_items JSONB NOT NULL,
    
    -- Nutrition totals
    total_calories FLOAT NOT NULL,
    total_protein_g FLOAT NOT NULL,
    total_carbs_g FLOAT NOT NULL,
    total_fat_g FLOAT NOT NULL,
    total_fiber_g FLOAT NOT NULL,
    total_sodium_mg FLOAT NOT NULL,
    total_sugar_g FLOAT NOT NULL,
    micronutrients JSONB,
    
    -- User input
    user_notes TEXT,
    mood_before VARCHAR(20),
    mood_after VARCHAR(20),
    
    -- Integration flags
    synced_to_health_tracking BOOLEAN DEFAULT FALSE,
    synced_to_medical_analysis BOOLEAN DEFAULT FALSE
);

-- Nutrition Goals Table
CREATE TABLE nutrition.nutrition_goals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Goal metadata
    goal_name VARCHAR(100) NOT NULL,
    goal_type VARCHAR(30) NOT NULL,
    goal_description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Target values
    target_calories FLOAT,
    target_protein_g FLOAT,
    target_carbs_g FLOAT,
    target_fat_g FLOAT,
    target_fiber_g FLOAT,
    target_sodium_mg FLOAT,
    
    -- Goal settings
    start_date TIMESTAMP WITH TIME ZONE,
    target_date TIMESTAMP WITH TIME ZONE,
    progress_percentage FLOAT DEFAULT 0.0
);

-- Food Database Table (for caching)
CREATE TABLE nutrition.food_database (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    food_name VARCHAR(200) NOT NULL,
    food_category VARCHAR(50),
    source VARCHAR(20) NOT NULL,
    
    -- Nutrition data (per 100g)
    calories_per_100g FLOAT NOT NULL,
    protein_g_per_100g FLOAT NOT NULL,
    carbs_g_per_100g FLOAT NOT NULL,
    fat_g_per_100g FLOAT NOT NULL,
    fiber_g_per_100g FLOAT NOT NULL,
    sodium_mg_per_100g FLOAT NOT NULL,
    sugar_g_per_100g FLOAT NOT NULL,
    micronutrients JSONB,
    
    -- Metadata
    brand_name VARCHAR(100),
    barcode VARCHAR(50),
    serving_size_g FLOAT,
    serving_description VARCHAR(100),
    
    -- Caching
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_accessed TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0
);

-- Model Performance Table
CREATE TABLE nutrition.model_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Performance metrics
    accuracy FLOAT,
    processing_time_ms FLOAT,
    success_rate FLOAT,
    error_rate FLOAT,
    
    -- Usage statistics
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    
    -- User feedback
    user_satisfaction_score FLOAT,
    correction_rate FLOAT
);

-- User Preferences Table
CREATE TABLE nutrition.user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Dietary preferences
    dietary_restrictions JSONB,
    allergies JSONB,
    preferred_cuisines JSONB,
    disliked_foods JSONB,
    
    -- Measurement preferences
    preferred_units VARCHAR(10) DEFAULT 'metric',
    calorie_goal FLOAT,
    protein_goal_g FLOAT,
    carb_goal_g FLOAT,
    fat_goal_g FLOAT,
    
    -- Notification preferences
    enable_nutrition_alerts BOOLEAN DEFAULT TRUE,
    enable_meal_reminders BOOLEAN DEFAULT TRUE,
    alert_thresholds JSONB,
    
    -- Recognition preferences
    preferred_recognition_models JSONB,
    confidence_threshold FLOAT DEFAULT 0.7,
    enable_portion_estimation BOOLEAN DEFAULT TRUE
);

-- ============================================================================
-- NUTRITION INDEXES
-- ============================================================================

-- Food Recognition Results Indexes
CREATE INDEX idx_nutrition_food_recognition_user_timestamp ON nutrition.food_recognition_results(user_id, timestamp);
CREATE INDEX idx_nutrition_food_recognition_recognition_id ON nutrition.food_recognition_results(recognition_id);
CREATE INDEX idx_nutrition_food_recognition_meal_type ON nutrition.food_recognition_results(meal_type);
CREATE INDEX idx_nutrition_food_recognition_is_corrected ON nutrition.food_recognition_results(is_corrected);

-- User Corrections Indexes
CREATE INDEX idx_nutrition_user_corrections_user_timestamp ON nutrition.user_corrections(user_id, timestamp);
CREATE INDEX idx_nutrition_user_corrections_recognition_result ON nutrition.user_corrections(recognition_result_id);
CREATE INDEX idx_nutrition_user_corrections_type ON nutrition.user_corrections(correction_type);

-- Meal Logs Indexes
CREATE INDEX idx_nutrition_meal_logs_user_meal_date ON nutrition.meal_logs(user_id, timestamp);
CREATE INDEX idx_nutrition_meal_logs_meal_type ON nutrition.meal_logs(meal_type);
CREATE INDEX idx_nutrition_meal_logs_recognition_result ON nutrition.meal_logs(recognition_result_id);
CREATE INDEX idx_nutrition_meal_logs_synced_flags ON nutrition.meal_logs(synced_to_health_tracking, synced_to_medical_analysis);

-- Nutrition Goals Indexes
CREATE INDEX idx_nutrition_goals_user_active ON nutrition.nutrition_goals(user_id, is_active);
CREATE INDEX idx_nutrition_goals_type ON nutrition.nutrition_goals(goal_type);
CREATE INDEX idx_nutrition_goals_dates ON nutrition.nutrition_goals(start_date, target_date);

-- Food Database Indexes
CREATE INDEX idx_nutrition_food_database_name_category ON nutrition.food_database(food_name, food_category);
CREATE INDEX idx_nutrition_food_database_source ON nutrition.food_database(source);
CREATE INDEX idx_nutrition_food_database_barcode ON nutrition.food_database(barcode);
CREATE INDEX idx_nutrition_food_database_access_count ON nutrition.food_database(access_count DESC);
CREATE INDEX idx_nutrition_food_database_last_accessed ON nutrition.food_database(last_accessed DESC);

-- Model Performance Indexes
CREATE INDEX idx_nutrition_model_performance_model_timestamp ON nutrition.model_performance(model_name, timestamp);
CREATE INDEX idx_nutrition_model_performance_accuracy ON nutrition.model_performance(model_name, accuracy);
CREATE INDEX idx_nutrition_model_performance_processing_time ON nutrition.model_performance(model_name, processing_time_ms);

-- User Preferences Indexes
CREATE INDEX idx_nutrition_user_preferences_user_id ON nutrition.user_preferences(user_id);

-- ============================================================================
-- NUTRITION TRIGGERS
-- ============================================================================

CREATE TRIGGER update_nutrition_goals_updated_at 
    BEFORE UPDATE ON nutrition.nutrition_goals 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nutrition_food_database_updated_at 
    BEFORE UPDATE ON nutrition.food_database 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nutrition_user_preferences_updated_at 
    BEFORE UPDATE ON nutrition.user_preferences 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- NUTRITION VIEWS
-- ============================================================================

-- Daily Nutrition Summary View
CREATE VIEW nutrition.daily_nutrition_summary AS
SELECT 
    user_id,
    DATE(timestamp) as date,
    COUNT(*) as meal_count,
    SUM(total_calories) as total_calories,
    SUM(total_protein_g) as total_protein_g,
    SUM(total_carbs_g) as total_carbs_g,
    SUM(total_fat_g) as total_fat_g,
    SUM(total_fiber_g) as total_fiber_g,
    SUM(total_sodium_mg) as total_sodium_mg,
    SUM(total_sugar_g) as total_sugar_g
FROM nutrition.meal_logs
GROUP BY user_id, DATE(timestamp);

-- Model Performance Summary View
CREATE VIEW nutrition.model_performance_summary AS
SELECT 
    model_name,
    DATE(timestamp) as date,
    COUNT(*) as total_requests,
    AVG(accuracy) as avg_accuracy,
    AVG(processing_time_ms) as avg_processing_time_ms,
    AVG(success_rate) as avg_success_rate,
    AVG(user_satisfaction_score) as avg_satisfaction
FROM nutrition.model_performance
GROUP BY model_name, DATE(timestamp);

-- User Recognition Statistics View
CREATE VIEW nutrition.user_recognition_stats AS
SELECT 
    user_id,
    COUNT(*) as total_recognitions,
    AVG(average_confidence) as avg_confidence,
    COUNT(CASE WHEN is_corrected THEN 1 END) as corrected_count,
    COUNT(CASE WHEN user_rating IS NOT NULL THEN 1 END) as rated_count,
    AVG(user_rating) as avg_rating
FROM nutrition.food_recognition_results
GROUP BY user_id;

-- ============================================================================
-- NUTRITION FUNCTIONS
-- ============================================================================

-- Function to calculate nutrition score
CREATE OR REPLACE FUNCTION nutrition.calculate_nutrition_score(
    user_uuid VARCHAR,
    date_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_DATE,
    date_to TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_DATE
)
RETURNS JSONB AS $$
DECLARE
    score JSONB;
    daily_avg JSONB;
BEGIN
    -- Get daily averages for the period
    SELECT jsonb_build_object(
        'avg_calories', AVG(total_calories),
        'avg_protein_g', AVG(total_protein_g),
        'avg_carbs_g', AVG(total_carbs_g),
        'avg_fat_g', AVG(total_fat_g),
        'avg_fiber_g', AVG(total_fiber_g),
        'avg_sodium_mg', AVG(total_sodium_mg),
        'avg_sugar_g', AVG(total_sugar_g),
        'meal_count', COUNT(*)
    ) INTO daily_avg
    FROM nutrition.meal_logs
    WHERE user_id = user_uuid 
    AND timestamp BETWEEN date_from AND date_to;
    
    -- Calculate nutrition score (simplified algorithm)
    SELECT jsonb_build_object(
        'user_id', user_uuid,
        'period_start', date_from,
        'period_end', date_to,
        'daily_averages', daily_avg,
        'nutrition_score', CASE 
            WHEN (daily_avg->>'avg_calories')::FLOAT BETWEEN 1500 AND 2500 THEN 100
            WHEN (daily_avg->>'avg_calories')::FLOAT BETWEEN 1200 AND 3000 THEN 80
            WHEN (daily_avg->>'avg_calories')::FLOAT BETWEEN 1000 AND 3500 THEN 60
            ELSE 40
        END,
        'protein_score', CASE 
            WHEN (daily_avg->>'avg_protein_g')::FLOAT >= 50 THEN 100
            WHEN (daily_avg->>'avg_protein_g')::FLOAT >= 30 THEN 80
            WHEN (daily_avg->>'avg_protein_g')::FLOAT >= 20 THEN 60
            ELSE 40
        END,
        'fiber_score', CASE 
            WHEN (daily_avg->>'avg_fiber_g')::FLOAT >= 25 THEN 100
            WHEN (daily_avg->>'avg_fiber_g')::FLOAT >= 15 THEN 80
            WHEN (daily_avg->>'avg_fiber_g')::FLOAT >= 10 THEN 60
            ELSE 40
        END
    ) INTO score;
    
    RETURN score;
END;
$$ LANGUAGE plpgsql;

-- Function to get user's nutrition insights
CREATE OR REPLACE FUNCTION nutrition.get_user_nutrition_insights(
    user_uuid VARCHAR,
    days_back INTEGER DEFAULT 30
)
RETURNS JSONB AS $$
DECLARE
    insights JSONB;
    recent_meals JSONB;
    top_foods JSONB;
BEGIN
    -- Get recent meal patterns
    SELECT jsonb_build_object(
        'total_meals', COUNT(*),
        'avg_meals_per_day', ROUND(COUNT(*)::FLOAT / days_back, 2),
        'meal_type_distribution', jsonb_object_agg(meal_type, count)
    ) INTO recent_meals
    FROM (
        SELECT meal_type, COUNT(*) as count
        FROM nutrition.meal_logs
        WHERE user_id = user_uuid 
        AND timestamp >= CURRENT_DATE - INTERVAL '1 day' * days_back
        GROUP BY meal_type
    ) meal_stats;
    
    -- Get top consumed foods
    SELECT jsonb_agg(jsonb_build_object(
        'food_name', food_name,
        'consumption_count', consumption_count
    )) INTO top_foods
    FROM (
        SELECT 
            jsonb_array_elements_text(food_items->'foods') as food_name,
            COUNT(*) as consumption_count
        FROM nutrition.meal_logs
        WHERE user_id = user_uuid 
        AND timestamp >= CURRENT_DATE - INTERVAL '1 day' * days_back
        GROUP BY food_name
        ORDER BY consumption_count DESC
        LIMIT 10
    ) top_food_stats;
    
    -- Build insights
    SELECT jsonb_build_object(
        'user_id', user_uuid,
        'analysis_period_days', days_back,
        'meal_patterns', recent_meals,
        'top_consumed_foods', top_foods,
        'nutrition_score', nutrition.calculate_nutrition_score(user_uuid, CURRENT_DATE - INTERVAL '1 day' * days_back, CURRENT_DATE),
        'recommendations', jsonb_build_array(
            'Consider increasing fiber intake if below 25g daily',
            'Aim for 50g+ of protein daily for muscle health',
            'Monitor sodium intake to stay under 2300mg daily'
        )
    ) INTO insights;
    
    RETURN insights;
END;
$$ LANGUAGE plpgsql; 