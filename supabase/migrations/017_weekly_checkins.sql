-- 017: Weekly mood/energy/pain check-ins
-- Lightweight self-reported well-being snapshots (0-10 scale each).
-- Surfaced as a reminder modal when the user hasn't checked in for 7 days.

CREATE TABLE IF NOT EXISTS weekly_checkins (
  id            UUID         DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       UUID         NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  energy        SMALLINT     NOT NULL CHECK (energy BETWEEN 0 AND 10),
  mood          SMALLINT     NOT NULL CHECK (mood BETWEEN 0 AND 10),
  pain          SMALLINT     NOT NULL CHECK (pain BETWEEN 0 AND 10),
  notes         TEXT,
  checked_in_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weekly_checkins_user_date
  ON weekly_checkins (user_id, checked_in_at DESC);

-- Row-level security
ALTER TABLE weekly_checkins ENABLE ROW LEVEL SECURITY;

CREATE POLICY weekly_checkins_select ON weekly_checkins
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY weekly_checkins_insert ON weekly_checkins
  FOR INSERT WITH CHECK (auth.uid() = user_id);

COMMENT ON TABLE weekly_checkins IS 'Weekly self-reported mood/energy/pain snapshots (0-10 each)';
