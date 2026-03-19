-- ============================================================================
-- 030: Closed-Loop P0 — Recommendation tracking + intervention enhancements
-- ============================================================================

-- Track recommendation → intervention linkage
ALTER TABLE active_interventions ADD COLUMN IF NOT EXISTS recommendation_id TEXT;
ALTER TABLE active_interventions ADD COLUMN IF NOT EXISTS recommendation_evidence JSONB;

-- Track user interactions with recommendations (shown, dismissed, started, etc.)
CREATE TABLE IF NOT EXISTS recommendation_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  recommendation_pattern TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('shown','dismissed','not_now','not_interested','started')),
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rec_events_user ON recommendation_events(user_id);
CREATE INDEX IF NOT EXISTS idx_rec_events_pattern ON recommendation_events(user_id, recommendation_pattern);

ALTER TABLE recommendation_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own recommendation events"
  ON recommendation_events FOR ALL
  USING (auth.uid()::text = user_id);

CREATE POLICY "Service role full access on recommendation_events"
  ON recommendation_events FOR ALL
  USING (auth.role() = 'service_role');

-- Expand status to include habit_adopted
-- (DROP + re-ADD constraint to widen the CHECK)
ALTER TABLE active_interventions DROP CONSTRAINT IF EXISTS active_interventions_status_check;
ALTER TABLE active_interventions ADD CONSTRAINT active_interventions_status_check
  CHECK (status IN ('active','completed','abandoned','habit_adopted'));

-- Add AI summary column to store the generated summary on completion
ALTER TABLE active_interventions ADD COLUMN IF NOT EXISTS outcome_summary TEXT;
