-- ============================================================================
-- 035: Onboarding redesign — intent tracking, specialist activation, smart prompts
-- ============================================================================

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS onboarding_intent TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS primary_condition TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS primary_goal TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS specialist_agent_type TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS proposed_journey_key TEXT;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS data_completeness_score INT DEFAULT 0;
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS gender TEXT;

-- Track smart prompt dismissals
CREATE TABLE IF NOT EXISTS smart_prompt_dismissals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  prompt_type TEXT NOT NULL,
  dismissed_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, prompt_type)
);

CREATE INDEX IF NOT EXISTS idx_prompt_dismiss_user ON smart_prompt_dismissals(user_id);

ALTER TABLE smart_prompt_dismissals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own prompt dismissals"
  ON smart_prompt_dismissals FOR ALL
  USING (auth.uid()::text = user_id);

CREATE POLICY "Service role on prompt dismissals"
  ON smart_prompt_dismissals FOR ALL
  USING (auth.role() = 'service_role');
