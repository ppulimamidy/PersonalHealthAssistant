-- Migration script to fix enum values to match SQLAlchemy expectations

-- Drop existing enum types and recreate them with uppercase values
DROP TYPE IF EXISTS mfastatus CASCADE;
DROP TYPE IF EXISTS usertype CASCADE;
DROP TYPE IF EXISTS userstatus CASCADE;

-- Recreate enum types with uppercase values
CREATE TYPE mfastatus AS ENUM ('DISABLED', 'ENABLED', 'REQUIRED', 'SETUP_REQUIRED');
CREATE TYPE usertype AS ENUM ('PATIENT', 'DOCTOR', 'ADMIN', 'PHARMA', 'INSURANCE', 'RETAIL_STORE', 'RESEARCHER', 'CAREGIVER', 'LAB_TECHNICIAN', 'NURSE', 'SPECIALIST', 'EMERGENCY_CONTACT');
CREATE TYPE userstatus AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING_VERIFICATION', 'LOCKED');

-- Update the columns to use the new enum types
ALTER TABLE auth.users 
ALTER COLUMN mfa_status TYPE mfastatus USING mfa_status::text::mfastatus,
ALTER COLUMN user_type TYPE usertype USING user_type::text::usertype,
ALTER COLUMN status TYPE userstatus USING status::text::userstatus;

-- Update existing data to use uppercase values
UPDATE auth.users 
SET 
    mfa_status = 'DISABLED'::mfastatus,
    user_type = 'PATIENT'::usertype,
    status = 'ACTIVE'::userstatus
WHERE mfa_status IS NULL OR user_type IS NULL OR status IS NULL;
