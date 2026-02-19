-- Migration 012: Medical Literature - Evidence hierarchy and embedding support
-- Adds evidence_level (Meta-analysis > RCT > Observational) and publication_types for display.

-- Evidence hierarchy: meta_analysis > rct > observational > other
ALTER TABLE research_articles
  ADD COLUMN IF NOT EXISTS evidence_level TEXT DEFAULT 'other',
  ADD COLUMN IF NOT EXISTS publication_types JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN research_articles.evidence_level IS 'Evidence hierarchy: meta_analysis, rct, observational, other';
COMMENT ON COLUMN research_articles.publication_types IS 'PubMed PublicationType list (e.g. Meta-Analysis, Randomized Controlled Trial)';

-- Allow backend to insert embeddings (RLS)
CREATE POLICY embeddings_insert ON article_embeddings
    FOR INSERT WITH CHECK (true);
