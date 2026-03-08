-- 021: Care Team Sharing — patients share read-only access to their health data
-- A patient creates a token; they share the URL with their doctor/nutritionist/caregiver.
-- The recipient opens /share/<token> to see a structured read-only health summary.
-- No registration required for the recipient — the token is the credential.

CREATE TABLE IF NOT EXISTS shared_access (
  id             UUID         DEFAULT gen_random_uuid() PRIMARY KEY,
  grantor_id     UUID         NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  token          VARCHAR(64)  NOT NULL UNIQUE,
  label          VARCHAR(100),                         -- e.g. "Dr. Smith – Primary Care"
  permissions    JSONB        NOT NULL DEFAULT '["summary","medications","lab_results","symptoms","care_plans","insights"]',
  expires_at     TIMESTAMPTZ,                          -- NULL = never expires
  last_accessed_at TIMESTAMPTZ,
  access_count   INTEGER      NOT NULL DEFAULT 0,
  created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_shared_access_grantor ON shared_access (grantor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_shared_access_token   ON shared_access (token);

-- RLS: only the grantor can manage their own links
ALTER TABLE shared_access ENABLE ROW LEVEL SECURITY;

CREATE POLICY shared_access_select ON shared_access
  FOR SELECT USING (auth.uid() = grantor_id);

CREATE POLICY shared_access_insert ON shared_access
  FOR INSERT WITH CHECK (auth.uid() = grantor_id);

CREATE POLICY shared_access_delete ON shared_access
  FOR DELETE USING (auth.uid() = grantor_id);

-- Note: the public /share/public/{token} endpoint uses service-role credentials (bypasses RLS)
-- so it can look up any token without the viewer being authenticated.

COMMENT ON TABLE shared_access IS 'Care-team share links: patients grant read-only access to their health summary';
