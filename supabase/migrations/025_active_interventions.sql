-- Migration 025: N-of-1 Active Interventions
-- Stores user-accepted nutrition/lifestyle interventions for personal learning loop.
-- Designed to be health-data-source agnostic: data_sources JSONB supports
-- oura, apple_health, google_health, manual, or any future integration.

-- ── active_interventions ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS active_interventions (
  id                  UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id             TEXT        NOT NULL,
  recommendation_pattern TEXT     NOT NULL,  -- overtraining|inflammation|poor_recovery|sleep_disruption
  title               TEXT        NOT NULL,
  description         TEXT,
  duration_days       INT         NOT NULL DEFAULT 7,
  started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ends_at             TIMESTAMPTZ NOT NULL,
  status              TEXT        NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active', 'completed', 'abandoned')),
  -- Baseline captured from health timeline at acceptance (source-agnostic)
  baseline_metrics    JSONB,
  -- Outcome captured from health timeline at completion
  outcome_metrics     JSONB,
  -- Computed % deltas per metric (e.g. {"hrv_balance": 8.3, "sleep_score": 5.1})
  outcome_delta       JSONB,
  adherence_days      INT         DEFAULT 0,
  -- Extensible: ['oura'] | ['apple_health'] | ['google_health'] | ['oura','apple_health']
  data_sources        JSONB       DEFAULT '["oura"]'::jsonb,
  created_at          TIMESTAMPTZ DEFAULT NOW(),
  updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_active_interventions_user_id
  ON active_interventions(user_id);
CREATE INDEX IF NOT EXISTS idx_active_interventions_status
  ON active_interventions(status);
CREATE INDEX IF NOT EXISTS idx_active_interventions_ends_at
  ON active_interventions(ends_at);

-- RLS: users manage only their own interventions
ALTER TABLE active_interventions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own interventions"
  ON active_interventions
  FOR ALL
  USING (user_id = auth.uid()::text)
  WITH CHECK (user_id = auth.uid()::text);

-- Allow service role full access (for API server reads/writes)
CREATE POLICY "Service role full access to interventions"
  ON active_interventions
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ── intervention_checkins ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS intervention_checkins (
  id               UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
  intervention_id  UUID        REFERENCES active_interventions(id) ON DELETE CASCADE,
  user_id          TEXT        NOT NULL,
  checkin_date     DATE        NOT NULL DEFAULT CURRENT_DATE,
  adhered          BOOL        NOT NULL DEFAULT TRUE,
  notes            TEXT,
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(intervention_id, checkin_date)
);

CREATE INDEX IF NOT EXISTS idx_intervention_checkins_intervention_id
  ON intervention_checkins(intervention_id);
CREATE INDEX IF NOT EXISTS idx_intervention_checkins_user_id
  ON intervention_checkins(user_id);

-- RLS
ALTER TABLE intervention_checkins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own checkins"
  ON intervention_checkins
  FOR ALL
  USING (user_id = auth.uid()::text)
  WITH CHECK (user_id = auth.uid()::text);

CREATE POLICY "Service role full access to checkins"
  ON intervention_checkins
  FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);
