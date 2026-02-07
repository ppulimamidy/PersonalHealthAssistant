-- Migration script to update auth.users table to match expected schema
-- This script adds missing columns and updates the table structure

-- Add missing enum types if they don't exist
DO $$ BEGIN
    CREATE TYPE mfastatus AS ENUM ('disabled', 'enabled', 'required', 'setup_required');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE usertype AS ENUM ('patient', 'doctor', 'admin', 'pharma', 'insurance', 'retail_store', 'researcher', 'caregiver', 'lab_technician', 'nurse', 'specialist', 'emergency_contact');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE userstatus AS ENUM ('active', 'inactive', 'suspended', 'pending_verification', 'locked');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Add missing columns to auth.users table
ALTER TABLE auth.users 
ADD COLUMN IF NOT EXISTS supabase_user_id VARCHAR UNIQUE,
ADD COLUMN IF NOT EXISTS auth0_user_id VARCHAR,
ADD COLUMN IF NOT EXISTS mfa_status mfastatus DEFAULT 'disabled',
ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR,
ADD COLUMN IF NOT EXISTS user_type usertype,
ADD COLUMN IF NOT EXISTS status userstatus DEFAULT 'pending_verification',
ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS phone_verified BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS hipaa_consent_given BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS hipaa_consent_date TIMESTAMP WITHOUT TIME ZONE,
ADD COLUMN IF NOT EXISTS data_processing_consent BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS marketing_consent BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_failed_login TIMESTAMP WITHOUT TIME ZONE,
ADD COLUMN IF NOT EXISTS account_locked_until TIMESTAMP WITHOUT TIME ZONE,
ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP WITHOUT TIME ZONE,
ADD COLUMN IF NOT EXISTS user_metadata JSONB DEFAULT '{}';

-- Update existing users to have default values
UPDATE auth.users 
SET 
    user_type = 'patient'::usertype,
    status = 'active'::userstatus,
    email_verified = is_verified,
    supabase_user_id = id::text
WHERE user_type IS NULL;

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_users_supabase_user_id ON auth.users(supabase_user_id);
CREATE INDEX IF NOT EXISTS idx_users_auth0_user_id ON auth.users(auth0_user_id);
CREATE INDEX IF NOT EXISTS idx_users_user_type ON auth.users(user_type);
CREATE INDEX IF NOT EXISTS idx_users_status ON auth.users(status); 