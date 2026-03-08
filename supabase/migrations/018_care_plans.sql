-- 018: Care Plans — structured health goals tied to measurable metrics
-- Distinct from user_goals (free-text): care plans have a target_value, unit,
-- and the app auto-computes current_value progress against the target.
-- Source can be 'self' (user-authored) or 'doctor' (clinician-set).

CREATE TABLE IF NOT EXISTS care_plans (
  id            UUID         DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       UUID         NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title         TEXT         NOT NULL,
  description   TEXT,
  metric_type   VARCHAR(50)  NOT NULL DEFAULT 'general'
                             CHECK (metric_type IN (
                               'weight', 'steps', 'sleep_score',
                               'medication_adherence', 'symptom_severity',
                               'calories', 'lab_result', 'general'
                             )),
  target_value  NUMERIC,
  target_unit   VARCHAR(30),
  target_date   DATE,
  start_date    DATE         NOT NULL DEFAULT CURRENT_DATE,
  source        VARCHAR(20)  NOT NULL DEFAULT 'self'
                             CHECK (source IN ('self', 'doctor')),
  status        VARCHAR(20)  NOT NULL DEFAULT 'active'
                             CHECK (status IN ('active', 'completed', 'abandoned')),
  notes         TEXT,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_care_plans_user_status
  ON care_plans (user_id, status);

-- Row-level security
ALTER TABLE care_plans ENABLE ROW LEVEL SECURITY;

CREATE POLICY care_plans_select ON care_plans
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY care_plans_insert ON care_plans
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY care_plans_update ON care_plans
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY care_plans_delete ON care_plans
  FOR DELETE USING (auth.uid() = user_id);

COMMENT ON TABLE care_plans IS 'Structured health goals with measurable targets (weight, steps, adherence, lab, etc.)';
