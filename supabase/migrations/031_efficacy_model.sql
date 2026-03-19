-- ============================================================================
-- 031: Personal Efficacy Model — tracks what works for each user
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_efficacy_profile (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  pattern TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'nutrition',
  interventions_tried INT DEFAULT 0,
  avg_effect_size FLOAT DEFAULT 0,
  confidence FLOAT DEFAULT 0,
  best_duration INT,
  adherence_avg FLOAT DEFAULT 0,
  conditions_context TEXT[] DEFAULT '{}',
  cycle_phase_effects JSONB,
  last_tested TIMESTAMPTZ,
  status TEXT DEFAULT 'untested' CHECK (status IN ('proven','disproven','inconclusive','untested')),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, pattern)
);

CREATE INDEX IF NOT EXISTS idx_efficacy_user ON user_efficacy_profile(user_id);
CREATE INDEX IF NOT EXISTS idx_efficacy_status ON user_efficacy_profile(user_id, status);

ALTER TABLE user_efficacy_profile ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own efficacy profile"
  ON user_efficacy_profile FOR ALL
  USING (auth.uid()::text = user_id);

CREATE POLICY "Service role full access on efficacy"
  ON user_efficacy_profile FOR ALL
  USING (auth.role() = 'service_role');
