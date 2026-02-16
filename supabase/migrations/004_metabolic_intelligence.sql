-- Metabolic Intelligence tables
-- Run this in Supabase SQL Editor

-- Correlation results cache (one row per user per period)
CREATE TABLE IF NOT EXISTS correlation_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    period_days INTEGER NOT NULL DEFAULT 14,
    correlations JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary TEXT,
    data_quality_score FLOAT DEFAULT 0,
    oura_days_available INTEGER DEFAULT 0,
    nutrition_days_available INTEGER DEFAULT 0,
    computed_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (now() + interval '6 hours'),
    CONSTRAINT unique_user_period UNIQUE (user_id, period_days)
);

-- Health conditions (user-managed chronic conditions / health concerns)
CREATE TABLE IF NOT EXISTS health_conditions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    condition_name TEXT NOT NULL,
    condition_category TEXT NOT NULL DEFAULT 'other',
    severity TEXT DEFAULT 'moderate',
    diagnosed_date DATE,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    tracked_variables JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Extended user health profile for metabolic intelligence
CREATE TABLE IF NOT EXISTS user_health_profile (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    health_goals JSONB DEFAULT '[]'::jsonb,
    dietary_preferences JSONB DEFAULT '[]'::jsonb,
    supplements JSONB DEFAULT '[]'::jsonb,
    medications JSONB DEFAULT '[]'::jsonb,
    questionnaire_responses JSONB DEFAULT '{}'::jsonb,
    questionnaire_completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT unique_user_health_profile UNIQUE (user_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_correlation_user ON correlation_results(user_id);
CREATE INDEX IF NOT EXISTS idx_correlation_expires ON correlation_results(expires_at);
CREATE INDEX IF NOT EXISTS idx_health_conditions_user ON health_conditions(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_health_profile_user ON user_health_profile(user_id);

-- RLS policies
ALTER TABLE correlation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_conditions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_health_profile ENABLE ROW LEVEL SECURITY;

-- Correlation results: users see own data
CREATE POLICY correlation_results_select_own ON correlation_results
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY correlation_results_insert_own ON correlation_results
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY correlation_results_update_own ON correlation_results
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY correlation_results_delete_own ON correlation_results
    FOR DELETE USING (auth.uid() = user_id);

-- Health conditions: users manage own data
CREATE POLICY health_conditions_select_own ON health_conditions
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY health_conditions_insert_own ON health_conditions
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY health_conditions_update_own ON health_conditions
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY health_conditions_delete_own ON health_conditions
    FOR DELETE USING (auth.uid() = user_id);

-- User health profile: users manage own data
CREATE POLICY user_health_profile_select_own ON user_health_profile
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY user_health_profile_insert_own ON user_health_profile
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY user_health_profile_update_own ON user_health_profile
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY user_health_profile_delete_own ON user_health_profile
    FOR DELETE USING (auth.uid() = user_id);
