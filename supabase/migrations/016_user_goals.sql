-- 016: User Goals — simple free-text health goals pinned to Today
-- These are distinct from health_twin_goals (which are AI-generated with numeric targets).
-- user_goals are user-authored, free-text, with optional category + due date.

CREATE TABLE IF NOT EXISTS user_goals (
  id            UUID         DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id       UUID         NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  goal_text     TEXT         NOT NULL,
  category      VARCHAR(50)  NOT NULL DEFAULT 'general'
                             CHECK (category IN ('weight','medication','exercise','diet','lab_result','sleep','mental_health','general')),
  status        VARCHAR(20)  NOT NULL DEFAULT 'active'
                             CHECK (status IN ('active', 'achieved', 'abandoned')),
  due_date      DATE,
  notes         TEXT,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_goals_user_status
  ON user_goals (user_id, status);

-- Row-level security
ALTER TABLE user_goals ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_goals_select ON user_goals
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY user_goals_insert ON user_goals
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY user_goals_update ON user_goals
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY user_goals_delete ON user_goals
  FOR DELETE USING (auth.uid() = user_id);

COMMENT ON TABLE user_goals IS 'Simple user-authored health goals (free-text, pinned to Today page)';
