-- ============================================================================
-- 034: Cycle tracking for cycle-aware experiment engine
-- ============================================================================

CREATE TABLE IF NOT EXISTS cycle_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('period_start','period_end','ovulation','symptom')),
  event_date DATE NOT NULL,
  flow_intensity TEXT CHECK (flow_intensity IN ('light','medium','heavy','spotting')),
  symptoms TEXT[] DEFAULT '{}',
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, event_type, event_date)
);

CREATE INDEX IF NOT EXISTS idx_cycle_user ON cycle_logs(user_id, event_date DESC);

ALTER TABLE cycle_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own cycle logs"
  ON cycle_logs FOR ALL
  USING (auth.uid()::text = user_id);

CREATE POLICY "Service role full access on cycle_logs"
  ON cycle_logs FOR ALL
  USING (auth.role() = 'service_role');
