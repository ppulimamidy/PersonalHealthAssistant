-- Migration 011: Symptom Correlations
-- Extend correlation engine to include symptom-based correlations

-- ============================================================================
-- Symptom Correlations Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS symptom_correlations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,

    -- Symptom info
    symptom_type TEXT NOT NULL,
    symptom_metric TEXT NOT NULL, -- 'severity', 'frequency', 'duration'

    -- Correlated variable
    correlation_type TEXT NOT NULL CHECK (correlation_type IN (
        'symptom_nutrition',
        'symptom_oura',
        'symptom_medication',
        'symptom_symptom'
    )),

    -- The variable being correlated with
    correlated_variable TEXT NOT NULL, -- e.g., 'total_sugar_g', 'hrv_balance', 'medication_adherence'
    correlated_variable_label TEXT NOT NULL, -- Human-readable label

    -- Correlation statistics
    correlation_coefficient REAL NOT NULL,
    p_value REAL NOT NULL,
    sample_size INTEGER NOT NULL,
    lag_days INTEGER NOT NULL DEFAULT 0, -- 0 = same-day, 1 = next-day, etc.

    -- Effect description
    effect_type TEXT NOT NULL CHECK (effect_type IN ('positive', 'negative', 'neutral')),
    effect_magnitude TEXT CHECK (effect_magnitude IN ('large', 'moderate', 'small')),
    effect_description TEXT NOT NULL, -- AI-generated description

    -- Insights
    clinical_significance TEXT,
    recommendation TEXT,
    trigger_identified BOOLEAN DEFAULT false,
    trigger_confidence REAL, -- 0-1 confidence that this is a trigger

    -- Data quality
    data_quality_score REAL NOT NULL DEFAULT 0.0,
    days_analyzed INTEGER NOT NULL,

    -- Caching
    analysis_period_days INTEGER NOT NULL DEFAULT 30,
    computed_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT (now() + interval '7 days'),

    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_symptom_corr_user ON symptom_correlations(user_id);
CREATE INDEX idx_symptom_corr_type ON symptom_correlations(symptom_type);
CREATE INDEX idx_symptom_corr_correlation_type ON symptom_correlations(correlation_type);
CREATE INDEX idx_symptom_corr_expires ON symptom_correlations(expires_at);

-- RLS Policies
ALTER TABLE symptom_correlations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own symptom correlations"
    ON symptom_correlations FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY "System can insert symptom correlations"
    ON symptom_correlations FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own symptom correlations"
    ON symptom_correlations FOR DELETE
    USING (auth.uid()::text = user_id);

-- ============================================================================
-- Symptom Trigger Patterns
-- ============================================================================

CREATE TABLE IF NOT EXISTS symptom_trigger_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,

    -- Pattern info
    symptom_type TEXT NOT NULL,
    pattern_type TEXT NOT NULL CHECK (pattern_type IN (
        'food_trigger',
        'medication_side_effect',
        'stress_trigger',
        'sleep_trigger',
        'activity_trigger',
        'weather_trigger',
        'multi_factor'
    )),

    -- Trigger variables
    trigger_variables JSONB NOT NULL, -- Array of {variable, coefficient, p_value}

    -- Pattern strength
    pattern_strength REAL NOT NULL, -- 0-1, how strong the pattern is
    confidence_score REAL NOT NULL, -- 0-1, how confident we are

    -- Description
    pattern_description TEXT NOT NULL,
    trigger_threshold JSONB, -- e.g., {"total_sugar_g": {"min": 50, "unit": "grams"}}

    -- Recommendations
    recommendations TEXT[], -- Array of action items

    -- Validation
    times_observed INTEGER DEFAULT 0,
    times_validated INTEGER DEFAULT 0, -- User confirmed the pattern
    last_observed_at TIMESTAMPTZ,

    -- Status
    is_active BOOLEAN DEFAULT true,
    user_acknowledged BOOLEAN DEFAULT false,

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_symptom_trigger_user ON symptom_trigger_patterns(user_id);
CREATE INDEX idx_symptom_trigger_type ON symptom_trigger_patterns(symptom_type);
CREATE INDEX idx_symptom_trigger_pattern ON symptom_trigger_patterns(pattern_type);
CREATE INDEX idx_symptom_trigger_active ON symptom_trigger_patterns(is_active);

-- RLS Policies
ALTER TABLE symptom_trigger_patterns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own trigger patterns"
    ON symptom_trigger_patterns FOR ALL
    USING (auth.uid()::text = user_id);

-- ============================================================================
-- Functions
-- ============================================================================

-- Function to clean up expired symptom correlations
CREATE OR REPLACE FUNCTION cleanup_expired_symptom_correlations()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM symptom_correlations
    WHERE expires_at < now();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to update trigger pattern validation
CREATE OR REPLACE FUNCTION update_trigger_validation(
    p_pattern_id UUID,
    p_user_id TEXT,
    p_validated BOOLEAN
)
RETURNS VOID AS $$
BEGIN
    UPDATE symptom_trigger_patterns
    SET
        times_validated = times_validated + CASE WHEN p_validated THEN 1 ELSE 0 END,
        last_observed_at = now(),
        times_observed = times_observed + 1,
        updated_at = now()
    WHERE id = p_pattern_id AND user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE symptom_correlations IS 'Correlations between symptoms and nutrition/oura/medications';
COMMENT ON TABLE symptom_trigger_patterns IS 'Detected trigger patterns for symptoms with multi-variable analysis';
