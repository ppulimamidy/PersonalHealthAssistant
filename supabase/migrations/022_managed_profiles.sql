-- 022: Managed Profiles — Family / Caregiver Mode
-- A caregiver links to another user's profile via an invite token.
-- The linked user must first generate a "manage-access" share token from their account.
-- Once linked, the caregiver can view that user's shared health data from their dashboard.
--
-- This deliberately reuses shared_access (table 021): when a caregiver links a profile,
-- we record the share_token_id so the caregiver always views data at the user's current
-- permissions level.

CREATE TABLE IF NOT EXISTS managed_profiles (
  id               UUID         DEFAULT gen_random_uuid() PRIMARY KEY,
  manager_id       UUID         NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,  -- caregiver
  share_token_id   UUID         NOT NULL REFERENCES shared_access(id) ON DELETE CASCADE,
  relationship     VARCHAR(50),          -- e.g. "parent", "child", "spouse", "patient"
  display_name     VARCHAR(100),         -- override name shown in the switcher
  added_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  UNIQUE (manager_id, share_token_id)
);

CREATE INDEX IF NOT EXISTS idx_managed_profiles_manager ON managed_profiles (manager_id);

-- RLS: only the manager can read/manage their own links
ALTER TABLE managed_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY managed_profiles_select ON managed_profiles
  FOR SELECT USING (auth.uid() = manager_id);

CREATE POLICY managed_profiles_insert ON managed_profiles
  FOR INSERT WITH CHECK (auth.uid() = manager_id);

CREATE POLICY managed_profiles_delete ON managed_profiles
  FOR DELETE USING (auth.uid() = manager_id);

COMMENT ON TABLE managed_profiles IS
  'Caregiver-to-patient links: caregivers track family members health via share tokens';
