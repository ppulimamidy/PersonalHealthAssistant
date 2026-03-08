-- 019: Saved Insight Snapshots — persist generated insights for follow-up
-- When the app generates an insight (e.g. "Sleep declining"), it upserts a row
-- here keyed on (user_id, metric_key, week_bucket).
-- 30 days later, the app queries this table to show "what changed since" comparisons.

CREATE TABLE IF NOT EXISTS saved_insights (
  id             UUID         DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id        UUID         NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  metric_key     VARCHAR(100) NOT NULL,   -- e.g. "sleep_score", "steps", "symptom_severity"
  title          TEXT         NOT NULL,
  summary        TEXT,
  insight_type   VARCHAR(30)  NOT NULL DEFAULT 'trend',  -- trend | alert | recommendation
  category       VARCHAR(30)  NOT NULL DEFAULT 'general',
  metric_value   NUMERIC,                -- snapshot value at time of insight
  metric_unit    VARCHAR(20),
  week_bucket    DATE         NOT NULL,  -- Monday of the week this was generated
  created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Upsert key: one snapshot per user + metric + week
CREATE UNIQUE INDEX IF NOT EXISTS idx_saved_insights_upsert
  ON saved_insights (user_id, metric_key, week_bucket);

CREATE INDEX IF NOT EXISTS idx_saved_insights_user_date
  ON saved_insights (user_id, created_at DESC);

-- RLS
ALTER TABLE saved_insights ENABLE ROW LEVEL SECURITY;

CREATE POLICY saved_insights_select ON saved_insights
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY saved_insights_insert ON saved_insights
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY saved_insights_update ON saved_insights
  FOR UPDATE USING (auth.uid() = user_id);

COMMENT ON TABLE saved_insights IS 'Auto-persisted insight snapshots for 30-day follow-up comparisons';
