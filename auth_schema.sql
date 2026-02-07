-- Auth Service Database Schema
-- This file creates the necessary enum types and tables for the auth service

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create enum types
CREATE TYPE mfastatus AS ENUM ('disabled', 'enabled', 'required', 'setup_required');
CREATE TYPE usertype AS ENUM ('patient', 'doctor', 'admin', 'pharma', 'insurance', 'retail_store', 'researcher', 'caregiver', 'lab_technician', 'nurse', 'specialist', 'emergency_contact');
CREATE TYPE userstatus AS ENUM ('active', 'inactive', 'suspended', 'pending_verification', 'locked');

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supabase_user_id VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    phone VARCHAR UNIQUE,
    password_hash VARCHAR,
    auth0_user_id VARCHAR,
    mfa_status mfastatus DEFAULT 'disabled',
    mfa_secret VARCHAR,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    date_of_birth TIMESTAMP WITHOUT TIME ZONE,
    gender VARCHAR,
    user_type usertype NOT NULL,
    status userstatus DEFAULT 'pending_verification',
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    hipaa_consent_given BOOLEAN DEFAULT FALSE,
    hipaa_consent_date TIMESTAMP WITHOUT TIME ZONE,
    data_processing_consent BOOLEAN DEFAULT FALSE,
    marketing_consent BOOLEAN DEFAULT FALSE,
    failed_login_attempts INTEGER DEFAULT 0,
    last_failed_login TIMESTAMP WITHOUT TIME ZONE,
    account_locked_until TIMESTAMP WITHOUT TIME ZONE,
    password_changed_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    last_login_at TIMESTAMP WITHOUT TIME ZONE,
    user_metadata JSONB DEFAULT '{}'
);

-- Create user_profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    avatar_url VARCHAR,
    bio TEXT,
    location VARCHAR,
    timezone VARCHAR,
    language VARCHAR DEFAULT 'en',
    blood_type VARCHAR,
    height INTEGER,
    weight INTEGER,
    emergency_contact_name VARCHAR,
    emergency_contact_phone VARCHAR,
    emergency_contact_relationship VARCHAR,
    license_number VARCHAR,
    specialization VARCHAR,
    years_of_experience INTEGER,
    certifications JSONB DEFAULT '[]',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email_notifications BOOLEAN DEFAULT TRUE,
    sms_notifications BOOLEAN DEFAULT FALSE,
    push_notifications BOOLEAN DEFAULT TRUE,
    profile_visibility VARCHAR DEFAULT 'private',
    data_sharing_preferences JSONB DEFAULT '{}',
    theme VARCHAR DEFAULT 'light',
    language VARCHAR DEFAULT 'en',
    health_goal_reminders BOOLEAN DEFAULT TRUE,
    medication_reminders BOOLEAN DEFAULT TRUE,
    appointment_reminders BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_supabase_user_id ON users(supabase_user_id);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_auth0_user_id ON users(auth0_user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences(user_id);

-- Create trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
