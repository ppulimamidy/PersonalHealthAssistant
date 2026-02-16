-- Migration 006: Medical Literature RAG System
-- Phase 2 of Health Intelligence Features
-- Created: 2026-02-16

-- ============================================================================
-- MEDICAL LITERATURE & RAG
-- ============================================================================

-- Research articles cache (from PubMed and other sources)
CREATE TABLE IF NOT EXISTS research_articles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Article identifiers
    pubmed_id TEXT UNIQUE,
    doi TEXT,
    pmcid TEXT,

    -- Article metadata
    title TEXT NOT NULL,
    abstract TEXT,
    authors JSONB DEFAULT '[]'::jsonb,
    journal TEXT,
    publication_date DATE,
    keywords JSONB DEFAULT '[]'::jsonb,

    -- Article content
    full_text TEXT,
    sections JSONB DEFAULT '{}'::jsonb, -- {introduction, methods, results, discussion, conclusion}

    -- Categorization
    medical_categories JSONB DEFAULT '[]'::jsonb,
    relevance_score FLOAT,

    -- Citations and impact
    citation_count INT DEFAULT 0,
    impact_factor FLOAT,

    -- Source and metadata
    source TEXT DEFAULT 'pubmed', -- pubmed, pmc, manual, other
    source_url TEXT,

    -- Timestamps
    fetched_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- User research queries and saved searches
CREATE TABLE IF NOT EXISTS research_queries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Query details
    query_text TEXT NOT NULL,
    query_type TEXT DEFAULT 'general', -- general, condition_specific, symptom_research, medication_info

    -- Search parameters
    filters JSONB DEFAULT '{}'::jsonb, -- date range, journal filters, etc.

    -- Results
    article_ids JSONB DEFAULT '[]'::jsonb, -- array of research_articles IDs
    result_count INT DEFAULT 0,

    -- User interaction
    is_saved BOOLEAN DEFAULT false,
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    last_accessed_at TIMESTAMPTZ DEFAULT now()
);

-- Article embeddings for semantic search (vector similarity)
CREATE TABLE IF NOT EXISTS article_embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    article_id UUID NOT NULL REFERENCES research_articles(id) ON DELETE CASCADE,

    -- Embedding details
    embedding_type TEXT NOT NULL, -- title, abstract, full_text, section
    section_name TEXT, -- if embedding_type = 'section'
    text_content TEXT NOT NULL,

    -- Vector embedding (1536 dimensions for OpenAI ada-002, adjust as needed)
    -- Note: Supabase supports pgvector extension for similarity search
    -- embedding VECTOR(1536), -- Requires pgvector extension
    -- For now, store as JSONB until pgvector is enabled
    embedding JSONB,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

-- User-article bookmarks and annotations
CREATE TABLE IF NOT EXISTS article_bookmarks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES research_articles(id) ON DELETE CASCADE,

    -- User annotations
    user_notes TEXT,
    highlighted_text JSONB DEFAULT '[]'::jsonb, -- array of {text, section, page}
    relevance_rating INT CHECK (relevance_rating BETWEEN 1 AND 5),

    -- Categorization
    tags JSONB DEFAULT '[]'::jsonb,
    category TEXT, -- related_to_condition, symptom_research, treatment_option, etc.

    -- Sharing
    is_shared_with_doctor BOOLEAN DEFAULT false,

    -- Timestamps
    bookmarked_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(user_id, article_id)
);

-- RAG conversation history (AI-powered research chat)
CREATE TABLE IF NOT EXISTS rag_conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Conversation details
    title TEXT,
    context_articles JSONB DEFAULT '[]'::jsonb, -- array of article IDs used for context

    -- Conversation messages
    messages JSONB DEFAULT '[]'::jsonb, -- [{role: user/assistant, content, timestamp, sources}]

    -- Status
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Research insights cache (AI-generated summaries and insights)
CREATE TABLE IF NOT EXISTS research_insights (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Insight details
    insight_type TEXT NOT NULL, -- literature_summary, treatment_options, symptom_research, etc.
    topic TEXT NOT NULL,

    -- Content
    summary TEXT NOT NULL,
    key_findings JSONB DEFAULT '[]'::jsonb,
    recommendations JSONB DEFAULT '[]'::jsonb,

    -- Supporting evidence
    source_article_ids JSONB DEFAULT '[]'::jsonb,
    confidence_score FLOAT,

    -- Personalization
    related_conditions JSONB DEFAULT '[]'::jsonb,
    related_symptoms JSONB DEFAULT '[]'::jsonb,

    -- Status
    is_current BOOLEAN DEFAULT true,

    -- Timestamps
    generated_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Research articles indexes
CREATE INDEX IF NOT EXISTS idx_articles_pubmed ON research_articles(pubmed_id) WHERE pubmed_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_articles_doi ON research_articles(doi) WHERE doi IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_articles_date ON research_articles(publication_date DESC);
CREATE INDEX IF NOT EXISTS idx_articles_relevance ON research_articles(relevance_score DESC) WHERE relevance_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_articles_categories ON research_articles USING GIN (medical_categories);
CREATE INDEX IF NOT EXISTS idx_articles_keywords ON research_articles USING GIN (keywords);

-- Research queries indexes
CREATE INDEX IF NOT EXISTS idx_queries_user ON research_queries(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_queries_saved ON research_queries(user_id, is_saved) WHERE is_saved = true;
CREATE INDEX IF NOT EXISTS idx_queries_type ON research_queries(user_id, query_type);

-- Article embeddings indexes
CREATE INDEX IF NOT EXISTS idx_embeddings_article ON article_embeddings(article_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_type ON article_embeddings(embedding_type);

-- Article bookmarks indexes
CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON article_bookmarks(user_id, bookmarked_at DESC);
CREATE INDEX IF NOT EXISTS idx_bookmarks_article ON article_bookmarks(article_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_shared ON article_bookmarks(user_id, is_shared_with_doctor) WHERE is_shared_with_doctor = true;

-- RAG conversations indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user ON rag_conversations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_active ON rag_conversations(user_id, is_active) WHERE is_active = true;

-- Research insights indexes
CREATE INDEX IF NOT EXISTS idx_insights_user_type ON research_insights(user_id, insight_type, is_current);
CREATE INDEX IF NOT EXISTS idx_insights_topic ON research_insights(user_id, topic) WHERE is_current = true;
CREATE INDEX IF NOT EXISTS idx_insights_expires ON research_insights(expires_at) WHERE expires_at IS NOT NULL;

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Research articles are publicly readable (scientific literature)
ALTER TABLE research_articles ENABLE ROW LEVEL SECURITY;
CREATE POLICY articles_public_read ON research_articles
    FOR SELECT USING (true);

-- Research queries RLS (users manage their own queries)
ALTER TABLE research_queries ENABLE ROW LEVEL SECURITY;
CREATE POLICY queries_select_own ON research_queries
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY queries_insert_own ON research_queries
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY queries_update_own ON research_queries
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY queries_delete_own ON research_queries
    FOR DELETE USING (auth.uid() = user_id);

-- Article embeddings are publicly readable
ALTER TABLE article_embeddings ENABLE ROW LEVEL SECURITY;
CREATE POLICY embeddings_public_read ON article_embeddings
    FOR SELECT USING (true);

-- Article bookmarks RLS (users manage their own bookmarks)
ALTER TABLE article_bookmarks ENABLE ROW LEVEL SECURITY;
CREATE POLICY bookmarks_select_own ON article_bookmarks
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY bookmarks_insert_own ON article_bookmarks
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY bookmarks_update_own ON article_bookmarks
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY bookmarks_delete_own ON article_bookmarks
    FOR DELETE USING (auth.uid() = user_id);

-- RAG conversations RLS (users manage their own conversations)
ALTER TABLE rag_conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY conversations_select_own ON rag_conversations
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY conversations_insert_own ON rag_conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY conversations_update_own ON rag_conversations
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY conversations_delete_own ON rag_conversations
    FOR DELETE USING (auth.uid() = user_id);

-- Research insights RLS (users manage their own insights)
ALTER TABLE research_insights ENABLE ROW LEVEL SECURITY;
CREATE POLICY insights_select_own ON research_insights
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY insights_insert_own ON research_insights
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY insights_update_own ON research_insights
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY insights_delete_own ON research_insights
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- COMMENTS (for documentation)
-- ============================================================================

COMMENT ON TABLE research_articles IS 'Medical research articles from PubMed and other sources';
COMMENT ON TABLE research_queries IS 'User research queries and saved searches';
COMMENT ON TABLE article_embeddings IS 'Vector embeddings for semantic similarity search';
COMMENT ON TABLE article_bookmarks IS 'User bookmarks and annotations for research articles';
COMMENT ON TABLE rag_conversations IS 'RAG (Retrieval-Augmented Generation) conversation history';
COMMENT ON TABLE research_insights IS 'AI-generated research insights and summaries';

COMMENT ON COLUMN research_articles.sections IS 'JSON object with article sections: {introduction, methods, results, discussion, conclusion}';
COMMENT ON COLUMN research_articles.medical_categories IS 'JSON array of medical categories: [diabetes, cardiovascular, nutrition, etc.]';
COMMENT ON COLUMN research_queries.filters IS 'JSON object with search filters: {date_from, date_to, journals, categories}';
COMMENT ON COLUMN article_embeddings.embedding IS 'Vector embedding for semantic search (JSONB format, convert to pgvector when available)';
COMMENT ON COLUMN rag_conversations.messages IS 'JSON array of conversation messages with sources and timestamps';
COMMENT ON COLUMN research_insights.source_article_ids IS 'JSON array of research_articles IDs supporting this insight';
