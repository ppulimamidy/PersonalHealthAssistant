-- 027: Add insight_id to saved_insights for stable GET /{id} lookups
-- The app now generates deterministic IDs per (user_id, metric_key, week_bucket)
-- so that GET /insights/{id} can resolve from the persisted snapshot.

ALTER TABLE saved_insights ADD COLUMN IF NOT EXISTS insight_id VARCHAR(36);

CREATE INDEX IF NOT EXISTS idx_saved_insights_insight_id
    ON saved_insights (user_id, insight_id)
    WHERE insight_id IS NOT NULL;
