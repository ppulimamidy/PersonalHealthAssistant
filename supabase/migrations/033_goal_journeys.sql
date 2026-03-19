-- ============================================================================
-- 033: Goal Journeys — multi-phase, milestone-based health journeys
-- ============================================================================

CREATE TABLE IF NOT EXISTS goal_journeys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  title TEXT NOT NULL,
  condition TEXT,
  goal_type TEXT NOT NULL CHECK (goal_type IN (
    'condition_management', 'weight_loss', 'weight_gain', 'muscle_building',
    'sleep_optimization', 'hormone_optimization', 'gut_health',
    'cardiac_rehab', 'mental_health', 'general_wellness', 'custom'
  )),
  specialist_agent_id TEXT,
  duration_type TEXT NOT NULL CHECK (duration_type IN ('cycle_based','week_based','milestone_based')),
  target_metrics TEXT[] DEFAULT '{}',
  phases JSONB NOT NULL DEFAULT '[]',
  current_phase INT DEFAULT 0,
  status TEXT DEFAULT 'active' CHECK (status IN ('active','paused','completed','abandoned')),
  baseline_snapshot JSONB,
  outcome_snapshot JSONB,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_journey_user ON goal_journeys(user_id);
CREATE INDEX IF NOT EXISTS idx_journey_status ON goal_journeys(user_id, status);

ALTER TABLE goal_journeys ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own journeys"
  ON goal_journeys FOR ALL
  USING (auth.uid()::text = user_id);

CREATE POLICY "Service role full access on goal_journeys"
  ON goal_journeys FOR ALL
  USING (auth.role() = 'service_role');

-- Link interventions to journey phases
ALTER TABLE active_interventions ADD COLUMN IF NOT EXISTS journey_id UUID REFERENCES goal_journeys(id);
ALTER TABLE active_interventions ADD COLUMN IF NOT EXISTS journey_phase INT;

CREATE INDEX IF NOT EXISTS idx_intervention_journey ON active_interventions(journey_id) WHERE journey_id IS NOT NULL;
