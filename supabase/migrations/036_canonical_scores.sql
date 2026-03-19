-- ============================================================================
-- 036: Canonical scores — device-agnostic 0-100 scores for intelligence layer
-- ============================================================================

ALTER TABLE health_metric_summaries ADD COLUMN IF NOT EXISTS canonical_metric TEXT;
ALTER TABLE health_metric_summaries ADD COLUMN IF NOT EXISTS canonical_score FLOAT;

CREATE INDEX IF NOT EXISTS idx_summaries_canonical
  ON health_metric_summaries(user_id, canonical_metric)
  WHERE canonical_metric IS NOT NULL;
