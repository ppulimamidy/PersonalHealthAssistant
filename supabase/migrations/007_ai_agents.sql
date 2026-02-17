-- Migration 007: AI Agents Multi-Agent System
-- Phase 3 of Health Intelligence Features
-- Created: 2026-02-17

-- ============================================================================
-- AI AGENTS & CONVERSATIONS
-- ============================================================================

-- Agent definitions and metadata
CREATE TABLE IF NOT EXISTS ai_agents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Agent identity
    agent_type TEXT NOT NULL, -- health_coach, nutrition_analyst, symptom_investigator, research_assistant, medication_advisor
    agent_name TEXT NOT NULL,
    agent_description TEXT,

    -- Agent configuration
    capabilities JSONB DEFAULT '[]'::jsonb, -- array of capability strings
    system_prompt TEXT NOT NULL,
    model TEXT DEFAULT 'gpt-4o-mini', -- openai model to use
    temperature FLOAT DEFAULT 0.7,
    max_tokens INT DEFAULT 1000,

    -- Agent behavior
    is_active BOOLEAN DEFAULT true,
    can_initiate_conversation BOOLEAN DEFAULT false, -- can agent start conversations?
    requires_approval BOOLEAN DEFAULT false, -- require user approval for actions?

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(agent_type)
);

-- Multi-agent conversations
CREATE TABLE IF NOT EXISTS agent_conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Conversation metadata
    title TEXT,
    conversation_type TEXT DEFAULT 'general', -- general, health_review, symptom_analysis, nutrition_plan, research

    -- Multi-agent orchestration
    primary_agent_id UUID REFERENCES ai_agents(id),
    participating_agents JSONB DEFAULT '[]'::jsonb, -- array of agent IDs

    -- Conversation state
    status TEXT DEFAULT 'active', -- active, completed, archived
    messages JSONB DEFAULT '[]'::jsonb, -- array of {role, content, agent_id, timestamp, metadata}

    -- Context and memory
    conversation_context JSONB DEFAULT '{}'::jsonb, -- {user_goals, health_data, preferences}
    conversation_summary TEXT, -- AI-generated summary

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    last_message_at TIMESTAMPTZ DEFAULT now()
);

-- Agent actions and recommendations
CREATE TABLE IF NOT EXISTS agent_actions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES ai_agents(id),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Action details
    action_type TEXT NOT NULL, -- recommendation, task, alert, insight, question
    action_description TEXT NOT NULL,
    action_data JSONB DEFAULT '{}'::jsonb,

    -- Action priority and urgency
    priority TEXT DEFAULT 'medium', -- low, medium, high, urgent
    category TEXT, -- nutrition, exercise, sleep, medication, medical_attention

    -- Action lifecycle
    status TEXT DEFAULT 'pending', -- pending, approved, rejected, completed, dismissed
    requires_approval BOOLEAN DEFAULT false,

    -- User response
    user_feedback TEXT,
    user_response JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ
);

-- Agent memory and knowledge base
CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES ai_agents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Memory type
    memory_type TEXT NOT NULL, -- user_preference, health_fact, learned_pattern, interaction_history

    -- Memory content
    memory_key TEXT NOT NULL, -- semantic key for retrieval
    memory_value JSONB NOT NULL,
    memory_text TEXT, -- text representation for search

    -- Memory metadata
    confidence_score FLOAT DEFAULT 1.0,
    source TEXT, -- conversation_id, research_article_id, user_input, etc.

    -- Memory lifecycle
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(agent_id, user_id, memory_key)
);

-- Agent collaboration logs (for multi-agent coordination)
CREATE TABLE IF NOT EXISTS agent_collaborations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES agent_conversations(id) ON DELETE CASCADE,

    -- Collaboration participants
    initiating_agent_id UUID NOT NULL REFERENCES ai_agents(id),
    collaborating_agent_id UUID NOT NULL REFERENCES ai_agents(id),

    -- Collaboration details
    collaboration_type TEXT NOT NULL, -- handoff, consultation, parallel_analysis, consensus
    collaboration_reason TEXT,
    collaboration_data JSONB DEFAULT '{}'::jsonb,

    -- Outcome
    outcome TEXT,
    outcome_data JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- User feedback on agent interactions
CREATE TABLE IF NOT EXISTS agent_feedback (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES agent_conversations(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES ai_agents(id),

    -- Feedback details
    feedback_type TEXT NOT NULL, -- helpful, not_helpful, inaccurate, excellent
    rating INT CHECK (rating BETWEEN 1 AND 5),
    feedback_text TEXT,

    -- Context
    message_id TEXT, -- reference to specific message in conversation

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- AI agents indexes
CREATE INDEX IF NOT EXISTS idx_agents_type ON ai_agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_active ON ai_agents(is_active) WHERE is_active = true;

-- Conversations indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user ON agent_conversations(user_id, last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON agent_conversations(user_id, status);
CREATE INDEX IF NOT EXISTS idx_conversations_type ON agent_conversations(user_id, conversation_type);
CREATE INDEX IF NOT EXISTS idx_conversations_primary_agent ON agent_conversations(primary_agent_id);

-- Actions indexes
CREATE INDEX IF NOT EXISTS idx_actions_conversation ON agent_actions(conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_actions_user_status ON agent_actions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_actions_pending ON agent_actions(user_id, status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_actions_priority ON agent_actions(user_id, priority, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_actions_expires ON agent_actions(expires_at) WHERE expires_at IS NOT NULL;

-- Memory indexes
CREATE INDEX IF NOT EXISTS idx_memory_agent_user ON agent_memory(agent_id, user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_memory_type ON agent_memory(agent_id, user_id, memory_type);
CREATE INDEX IF NOT EXISTS idx_memory_key ON agent_memory(memory_key);
CREATE INDEX IF NOT EXISTS idx_memory_expires ON agent_memory(expires_at) WHERE expires_at IS NOT NULL;

-- Collaboration indexes
CREATE INDEX IF NOT EXISTS idx_collaborations_conversation ON agent_collaborations(conversation_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_collaborations_agents ON agent_collaborations(initiating_agent_id, collaborating_agent_id);

-- Feedback indexes
CREATE INDEX IF NOT EXISTS idx_feedback_user ON agent_feedback(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_agent ON agent_feedback(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_conversation ON agent_feedback(conversation_id);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- AI agents are publicly readable
ALTER TABLE ai_agents ENABLE ROW LEVEL SECURITY;
CREATE POLICY agents_public_read ON ai_agents
    FOR SELECT USING (is_active = true);

-- Conversations RLS (users manage their own conversations)
ALTER TABLE agent_conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY conversations_select_own ON agent_conversations
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY conversations_insert_own ON agent_conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY conversations_update_own ON agent_conversations
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY conversations_delete_own ON agent_conversations
    FOR DELETE USING (auth.uid() = user_id);

-- Actions RLS (users manage their own actions)
ALTER TABLE agent_actions ENABLE ROW LEVEL SECURITY;
CREATE POLICY actions_select_own ON agent_actions
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY actions_insert_own ON agent_actions
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY actions_update_own ON agent_actions
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY actions_delete_own ON agent_actions
    FOR DELETE USING (auth.uid() = user_id);

-- Memory RLS (users access their own memory)
ALTER TABLE agent_memory ENABLE ROW LEVEL SECURITY;
CREATE POLICY memory_select_own ON agent_memory
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY memory_insert_own ON agent_memory
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY memory_update_own ON agent_memory
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY memory_delete_own ON agent_memory
    FOR DELETE USING (auth.uid() = user_id);

-- Collaborations RLS (users see collaborations in their conversations)
ALTER TABLE agent_collaborations ENABLE ROW LEVEL SECURITY;
CREATE POLICY collaborations_select_own ON agent_collaborations
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM agent_conversations
            WHERE agent_conversations.id = agent_collaborations.conversation_id
            AND agent_conversations.user_id = auth.uid()
        )
    );

-- Feedback RLS (users manage their own feedback)
ALTER TABLE agent_feedback ENABLE ROW LEVEL SECURITY;
CREATE POLICY feedback_select_own ON agent_feedback
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY feedback_insert_own ON agent_feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY feedback_update_own ON agent_feedback
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY feedback_delete_own ON agent_feedback
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- SEED DATA - Default AI Agents
-- ============================================================================

INSERT INTO ai_agents (agent_type, agent_name, agent_description, capabilities, system_prompt) VALUES
('health_coach', 'Health Coach', 'Your personal health and wellness guide',
 '["general_health_advice", "goal_setting", "motivation", "lifestyle_recommendations"]'::jsonb,
 'You are a compassionate and knowledgeable health coach. Help users set realistic health goals, provide evidence-based wellness advice, and offer motivation and support. Always encourage users to consult healthcare professionals for medical decisions.'),

('nutrition_analyst', 'Nutrition Analyst', 'Expert in nutrition patterns and meal planning',
 '["nutrition_analysis", "meal_planning", "dietary_recommendations", "nutrient_tracking"]'::jsonb,
 'You are a nutrition expert specializing in analyzing eating patterns and providing personalized meal recommendations. Use data from the user''s meal logs and health metrics to identify patterns and suggest improvements. Be specific and actionable in your advice.'),

('symptom_investigator', 'Symptom Investigator', 'Analyzes symptoms and identifies patterns',
 '["symptom_analysis", "pattern_recognition", "correlation_detection", "medical_information"]'::jsonb,
 'You are a medical data analyst specializing in symptom pattern recognition. Help users understand their symptoms by analyzing trends, correlations with lifestyle factors, and potential triggers. Always recommend consulting healthcare professionals for diagnosis and treatment.'),

('research_assistant', 'Research Assistant', 'Finds and synthesizes medical research',
 '["literature_search", "research_synthesis", "evidence_summary", "study_interpretation"]'::jsonb,
 'You are a medical research assistant. Help users understand relevant medical research by searching PubMed, synthesizing findings from multiple studies, and explaining complex medical information in accessible language. Always cite sources and explain limitations of research.'),

('medication_advisor', 'Medication Advisor', 'Provides medication and supplement insights',
 '["medication_tracking", "interaction_checking", "adherence_support", "side_effect_monitoring"]'::jsonb,
 'You are a medication information specialist. Help users track medications and supplements, understand potential interactions, monitor for side effects, and improve adherence. Always emphasize the importance of consulting pharmacists and doctors for medical advice.')

ON CONFLICT (agent_type) DO NOTHING;

-- ============================================================================
-- COMMENTS (for documentation)
-- ============================================================================

COMMENT ON TABLE ai_agents IS 'AI agent definitions with capabilities and configuration';
COMMENT ON TABLE agent_conversations IS 'Multi-agent conversations with message history and context';
COMMENT ON TABLE agent_actions IS 'Agent-generated recommendations and tasks for users';
COMMENT ON TABLE agent_memory IS 'Agent memory and learned patterns about users';
COMMENT ON TABLE agent_collaborations IS 'Logs of multi-agent collaboration and handoffs';
COMMENT ON TABLE agent_feedback IS 'User feedback on agent interactions for improvement';

COMMENT ON COLUMN ai_agents.capabilities IS 'JSON array of agent capabilities';
COMMENT ON COLUMN agent_conversations.messages IS 'JSON array of conversation messages with agent metadata';
COMMENT ON COLUMN agent_conversations.participating_agents IS 'JSON array of agent IDs involved in conversation';
COMMENT ON COLUMN agent_actions.action_data IS 'JSON object with action-specific data';
COMMENT ON COLUMN agent_memory.memory_value IS 'JSON object storing the actual memory data';
