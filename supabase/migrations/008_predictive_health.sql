-- Migration 008: Predictive Health Predictions
-- Phase 4 of Health Intelligence Features
-- Created: 2026-02-17

-- ============================================================================
-- HEALTH PREDICTIONS & FORECASTING
-- ============================================================================

-- Health metric predictions and forecasts
CREATE TABLE IF NOT EXISTS health_predictions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Prediction metadata
    prediction_type TEXT NOT NULL, -- sleep_score, readiness_score, hrv_forecast, symptom_risk, recovery_forecast
    metric_name TEXT NOT NULL, -- sleep, readiness, hrv, recovery, activity_score

    -- Time window
    prediction_date DATE NOT NULL, -- date for which prediction is made
    prediction_horizon_days INT DEFAULT 1, -- how many days ahead (1, 3, 7, 14)

    -- Prediction values
    predicted_value FLOAT NOT NULL,
    confidence_score FLOAT, -- 0-1 confidence in prediction
    prediction_range JSONB, -- {"lower": float, "upper": float} for confidence interval

    -- Actual outcome (filled after prediction date)
    actual_value FLOAT,
    prediction_error FLOAT, -- |predicted - actual|

    -- Model information
    model_type TEXT DEFAULT 'statistical', -- statistical, ml, hybrid, agent_based
    model_version TEXT,
    features_used JSONB, -- array of feature names used for prediction

    -- Context
    contributing_factors JSONB, -- factors influencing prediction
    recommendations JSONB, -- suggested actions to improve outcome

    -- Status
    is_accurate BOOLEAN, -- true if within acceptable error margin
    status TEXT DEFAULT 'pending', -- pending, confirmed, inaccurate

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    confirmed_at TIMESTAMPTZ
);

-- Risk assessments for health conditions
CREATE TABLE IF NOT EXISTS health_risk_assessments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Risk details
    risk_type TEXT NOT NULL, -- symptom_flare, sleep_decline, recovery_decline, burnout, illness
    risk_category TEXT, -- cardiovascular, metabolic, mental_health, sleep, recovery

    -- Risk scoring
    risk_score FLOAT NOT NULL, -- 0-1, higher = higher risk
    risk_level TEXT NOT NULL, -- low, moderate, high, critical

    -- Time window
    risk_window_start DATE NOT NULL,
    risk_window_end DATE NOT NULL,

    -- Risk factors
    contributing_factors JSONB NOT NULL, -- [{factor, impact_score, description}]
    protective_factors JSONB, -- factors reducing risk

    -- Recommendations
    recommendations JSONB NOT NULL, -- [{priority, action, rationale}]
    early_warning_signs JSONB, -- signs to watch for

    -- Evidence
    historical_patterns JSONB, -- past instances of similar risk
    confidence_score FLOAT,

    -- User interaction
    user_acknowledged BOOLEAN DEFAULT false,
    user_notes TEXT,

    -- Status
    is_active BOOLEAN DEFAULT true,
    resolved_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Health trend analysis
CREATE TABLE IF NOT EXISTS health_trends (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Trend details
    metric_name TEXT NOT NULL, -- sleep_score, hrv, readiness, etc.
    trend_type TEXT NOT NULL, -- improving, declining, stable, fluctuating

    -- Time window
    analysis_start_date DATE NOT NULL,
    analysis_end_date DATE NOT NULL,
    window_days INT,

    -- Trend statistics
    slope FLOAT, -- rate of change
    r_squared FLOAT, -- trend strength (0-1)
    average_value FLOAT,
    std_deviation FLOAT,

    -- Change analysis
    percent_change FLOAT,
    absolute_change FLOAT,

    -- Pattern detection
    detected_patterns JSONB, -- ["weekly_cycle", "stress_correlation", etc.]
    anomalies JSONB, -- unusual data points

    -- Forecasting
    forecast_7d FLOAT, -- predicted value in 7 days
    forecast_14d FLOAT, -- predicted value in 14 days
    forecast_30d FLOAT, -- predicted value in 30 days

    -- Interpretation
    interpretation TEXT, -- human-readable summary
    significance TEXT, -- clinically_significant, notable, minor, noise

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ
);

-- Personalized health scores and indices
CREATE TABLE IF NOT EXISTS personalized_health_scores (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Score details
    score_date DATE NOT NULL,
    score_type TEXT NOT NULL, -- overall_health, recovery_capacity, resilience, metabolic_health

    -- Score value
    score_value FLOAT NOT NULL, -- 0-100 scale
    percentile FLOAT, -- compared to similar users

    -- Component scores
    component_scores JSONB, -- breakdown of score components

    -- Influencing factors
    positive_factors JSONB, -- factors improving score
    negative_factors JSONB, -- factors lowering score

    -- Trend
    trend_7d TEXT, -- up, down, stable
    change_7d FLOAT, -- +/- change from 7 days ago

    -- Recommendations
    improvement_recommendations JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(user_id, score_date, score_type)
);

-- Prediction model performance tracking
CREATE TABLE IF NOT EXISTS prediction_model_performance (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Model identification
    model_type TEXT NOT NULL,
    model_version TEXT NOT NULL,
    prediction_type TEXT NOT NULL,

    -- Performance metrics
    mean_absolute_error FLOAT,
    mean_squared_error FLOAT,
    r_squared FLOAT,
    accuracy_percentage FLOAT,

    -- Evaluation period
    evaluation_start DATE NOT NULL,
    evaluation_end DATE NOT NULL,
    sample_size INT,

    -- Model details
    features JSONB,
    hyperparameters JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(model_type, model_version, prediction_type, evaluation_start)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Predictions indexes
CREATE INDEX IF NOT EXISTS idx_predictions_user_date ON health_predictions(user_id, prediction_date DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_type ON health_predictions(user_id, prediction_type, status);
CREATE INDEX IF NOT EXISTS idx_predictions_pending ON health_predictions(user_id, status) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_predictions_metric ON health_predictions(metric_name, prediction_date);

-- Risk assessments indexes
CREATE INDEX IF NOT EXISTS idx_risks_user_active ON health_risk_assessments(user_id, is_active, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_risks_type ON health_risk_assessments(user_id, risk_type);
CREATE INDEX IF NOT EXISTS idx_risks_level ON health_risk_assessments(user_id, risk_level) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_risks_window ON health_risk_assessments(risk_window_start, risk_window_end);

-- Trends indexes
CREATE INDEX IF NOT EXISTS idx_trends_user_metric ON health_trends(user_id, metric_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_trends_dates ON health_trends(analysis_start_date, analysis_end_date);
CREATE INDEX IF NOT EXISTS idx_trends_expires ON health_trends(expires_at) WHERE expires_at IS NOT NULL;

-- Health scores indexes
CREATE INDEX IF NOT EXISTS idx_scores_user_date ON personalized_health_scores(user_id, score_date DESC);
CREATE INDEX IF NOT EXISTS idx_scores_type ON personalized_health_scores(user_id, score_type, score_date DESC);

-- Model performance indexes
CREATE INDEX IF NOT EXISTS idx_model_perf_type ON prediction_model_performance(model_type, model_version, prediction_type);
CREATE INDEX IF NOT EXISTS idx_model_perf_dates ON prediction_model_performance(evaluation_start, evaluation_end);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Predictions RLS
ALTER TABLE health_predictions ENABLE ROW LEVEL SECURITY;
CREATE POLICY predictions_select_own ON health_predictions
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY predictions_insert_own ON health_predictions
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY predictions_update_own ON health_predictions
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY predictions_delete_own ON health_predictions
    FOR DELETE USING (auth.uid() = user_id);

-- Risk assessments RLS
ALTER TABLE health_risk_assessments ENABLE ROW LEVEL SECURITY;
CREATE POLICY risks_select_own ON health_risk_assessments
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY risks_insert_own ON health_risk_assessments
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY risks_update_own ON health_risk_assessments
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY risks_delete_own ON health_risk_assessments
    FOR DELETE USING (auth.uid() = user_id);

-- Trends RLS
ALTER TABLE health_trends ENABLE ROW LEVEL SECURITY;
CREATE POLICY trends_select_own ON health_trends
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY trends_insert_own ON health_trends
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY trends_update_own ON health_trends
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY trends_delete_own ON health_trends
    FOR DELETE USING (auth.uid() = user_id);

-- Health scores RLS
ALTER TABLE personalized_health_scores ENABLE ROW LEVEL SECURITY;
CREATE POLICY scores_select_own ON personalized_health_scores
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY scores_insert_own ON personalized_health_scores
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY scores_update_own ON personalized_health_scores
    FOR UPDATE USING (auth.uid() = user_id);

-- Model performance is publicly readable for transparency
ALTER TABLE prediction_model_performance ENABLE ROW LEVEL SECURITY;
CREATE POLICY model_perf_public_read ON prediction_model_performance
    FOR SELECT USING (true);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE health_predictions IS 'AI-powered predictions for health metrics and outcomes';
COMMENT ON TABLE health_risk_assessments IS 'Risk assessments and early warning system';
COMMENT ON TABLE health_trends IS 'Trend analysis and forecasting for health metrics';
COMMENT ON TABLE personalized_health_scores IS 'Personalized health scores and indices';
COMMENT ON TABLE prediction_model_performance IS 'Tracking accuracy of prediction models';

COMMENT ON COLUMN health_predictions.prediction_range IS 'JSON: {"lower": float, "upper": float} confidence interval';
COMMENT ON COLUMN health_predictions.features_used IS 'JSON array of features used in prediction model';
COMMENT ON COLUMN health_risk_assessments.contributing_factors IS 'JSON array of risk factors with impact scores';
COMMENT ON COLUMN health_trends.detected_patterns IS 'JSON array of detected patterns in the data';
COMMENT ON COLUMN personalized_health_scores.component_scores IS 'JSON object with breakdown of score components';
