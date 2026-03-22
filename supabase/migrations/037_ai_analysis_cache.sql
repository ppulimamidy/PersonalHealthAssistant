-- Cache AI-generated analyses to avoid regeneration on every page load.
-- Persisted on the source record or in a dedicated cache table.

-- 1. Medical record insights — stored directly on the record
ALTER TABLE medical_records ADD COLUMN IF NOT EXISTS ai_insight TEXT;

-- 2. AI analysis cache — generic cache for medication recommendations,
--    research topics, and other AI-generated analyses.
CREATE TABLE IF NOT EXISTS ai_analysis_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  analysis_type TEXT NOT NULL,  -- 'medication_recommendations', 'research_topics', etc.
  result_json JSONB NOT NULL,
  data_hash TEXT NOT NULL,  -- hash of input data; if inputs change, regenerate
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days'),
  UNIQUE(user_id, analysis_type)
);

CREATE INDEX IF NOT EXISTS idx_ai_cache_user_type
  ON ai_analysis_cache(user_id, analysis_type);
CREATE INDEX IF NOT EXISTS idx_ai_cache_expires
  ON ai_analysis_cache(expires_at);

-- RLS
ALTER TABLE ai_analysis_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY ai_cache_select ON ai_analysis_cache
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY ai_cache_insert ON ai_analysis_cache
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY ai_cache_update ON ai_analysis_cache
  FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY ai_cache_delete ON ai_analysis_cache
  FOR DELETE USING (auth.uid() = user_id);
