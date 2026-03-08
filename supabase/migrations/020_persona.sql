-- 020: Persona / user role stub
-- Adds user_role to profiles so the app can adapt its UI for patients vs providers vs caregivers.
-- Phase 2 will add full provider dashboard; this stub just captures the field and exposes it to the frontend.

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS user_role VARCHAR(20) NOT NULL DEFAULT 'patient'
  CHECK (user_role IN ('patient', 'provider', 'caregiver'));

COMMENT ON COLUMN profiles.user_role IS
  'persona: patient (self-tracking), provider (clinician view), or caregiver (tracking on behalf of another)';
