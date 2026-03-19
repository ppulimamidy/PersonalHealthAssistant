-- ============================================================================
-- 032: Push tokens table + Nudge queue for closed-loop notifications
-- ============================================================================

-- Expo push tokens (referenced in notifications.py but migration was missing)
CREATE TABLE IF NOT EXISTS push_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  token TEXT NOT NULL,
  platform TEXT NOT NULL CHECK (platform IN ('ios', 'android')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (user_id, token)
);

CREATE INDEX IF NOT EXISTS idx_push_tokens_uid ON push_tokens(user_id);

ALTER TABLE push_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users manage own push tokens"
  ON push_tokens FOR ALL
  USING (auth.uid()::text = user_id);

CREATE POLICY "Service role full access on push_tokens"
  ON push_tokens FOR ALL
  USING (auth.role() = 'service_role');

-- Nudge queue: scheduled push notifications for the closed loop
CREATE TABLE IF NOT EXISTS nudge_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id TEXT NOT NULL,
  nudge_type TEXT NOT NULL CHECK (nudge_type IN (
    'experiment_morning', 'experiment_checkin', 'experiment_halfway',
    'experiment_complete', 'recommendation_weekly', 'phase_transition',
    'lab_reminder', 'reengagement'
  )),
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  data JSONB DEFAULT '{}',
  scheduled_for TIMESTAMPTZ NOT NULL,
  sent_at TIMESTAMPTZ,
  opened_at TIMESTAMPTZ,
  intervention_id UUID,
  journey_id UUID,
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending','sent','opened','dismissed','cancelled')),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nudge_pending ON nudge_queue(status, scheduled_for) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_nudge_user ON nudge_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_nudge_intervention ON nudge_queue(intervention_id) WHERE intervention_id IS NOT NULL;

ALTER TABLE nudge_queue ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users read own nudges"
  ON nudge_queue FOR SELECT
  USING (auth.uid()::text = user_id);

CREATE POLICY "Service role full access on nudge_queue"
  ON nudge_queue FOR ALL
  USING (auth.role() = 'service_role');
