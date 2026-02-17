-- Migration 009: Lab Results & Health Twin
-- Phase 5 of Health Intelligence Features
-- Created: 2026-02-17

-- ============================================================================
-- LAB RESULTS & BIOMARKERS
-- ============================================================================

-- Lab test categories (standardized test types)
CREATE TABLE IF NOT EXISTS lab_test_categories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    category_code TEXT NOT NULL UNIQUE, -- cbc, metabolic_panel, lipid_panel, hormone_panel, etc.
    category_name TEXT NOT NULL,
    description TEXT,
    typical_markers JSONB, -- array of typical biomarker names
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- User lab results
CREATE TABLE IF NOT EXISTS lab_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Test metadata
    test_date DATE NOT NULL,
    test_type TEXT NOT NULL, -- cbc, metabolic_panel, lipid_panel, thyroid, etc.
    lab_name TEXT, -- name of laboratory/facility
    ordering_provider TEXT,

    -- Results data
    biomarkers JSONB NOT NULL, -- [{name, value, unit, reference_range, status}]

    -- File attachments
    pdf_url TEXT, -- S3/storage URL for PDF report
    original_filename TEXT,

    -- Analysis
    abnormal_count INT DEFAULT 0,
    critical_count INT DEFAULT 0,
    ai_summary TEXT, -- AI-generated summary of results

    -- User notes
    notes TEXT,
    tags TEXT[], -- user-defined tags

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Biomarker reference ranges (standardized ranges by age/gender)
CREATE TABLE IF NOT EXISTS biomarker_references (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

    -- Biomarker identification
    biomarker_code TEXT NOT NULL, -- wbc, rbc, glucose, cholesterol, etc.
    biomarker_name TEXT NOT NULL,
    unit TEXT NOT NULL,

    -- Reference ranges
    age_min INT,
    age_max INT,
    gender TEXT, -- male, female, all

    -- Range values
    optimal_min FLOAT,
    optimal_max FLOAT,
    normal_min FLOAT NOT NULL,
    normal_max FLOAT NOT NULL,
    critical_low FLOAT,
    critical_high FLOAT,

    -- Interpretation
    description TEXT,
    clinical_significance TEXT,

    created_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(biomarker_code, gender, age_min, age_max)
);

-- Biomarker trends over time
CREATE TABLE IF NOT EXISTS biomarker_trends (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Biomarker
    biomarker_code TEXT NOT NULL,
    biomarker_name TEXT NOT NULL,

    -- Trend analysis
    trend_type TEXT NOT NULL, -- improving, worsening, stable, fluctuating
    direction TEXT, -- increasing, decreasing, stable
    slope FLOAT, -- rate of change per month

    -- Time window
    first_test_date DATE NOT NULL,
    last_test_date DATE NOT NULL,
    test_count INT NOT NULL,

    -- Statistics
    current_value FLOAT NOT NULL,
    previous_value FLOAT,
    min_value FLOAT,
    max_value FLOAT,
    avg_value FLOAT,
    std_deviation FLOAT,

    -- Status
    current_status TEXT, -- normal, borderline, abnormal, critical
    trend_significance TEXT, -- clinically_significant, notable, minor

    -- Interpretation
    interpretation TEXT,
    recommendations TEXT[],

    -- Timestamps
    computed_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ
);

-- Lab result insights and correlations
CREATE TABLE IF NOT EXISTS lab_insights (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Insight details
    insight_type TEXT NOT NULL, -- biomarker_correlation, health_metric_correlation, risk_indicator
    category TEXT, -- cardiovascular, metabolic, inflammation, hormonal

    -- Data points
    lab_result_ids UUID[], -- related lab results
    biomarkers_involved TEXT[], -- biomarker codes

    -- Findings
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    key_findings JSONB, -- structured findings data

    -- Correlations with health metrics
    correlated_health_metrics JSONB, -- {metric: correlation_strength}

    -- Significance
    confidence_score FLOAT,
    priority TEXT, -- high, medium, low

    -- Recommendations
    recommendations JSONB,

    -- User interaction
    is_acknowledged BOOLEAN DEFAULT false,
    user_notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    acknowledged_at TIMESTAMPTZ
);

-- ============================================================================
-- HEALTH TWIN (Digital Health Model)
-- ============================================================================

-- Health twin base profile (user's digital twin)
CREATE TABLE IF NOT EXISTS health_twin_profile (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Model metadata
    model_version TEXT DEFAULT 'v1',
    last_calibrated_at TIMESTAMPTZ DEFAULT now(),

    -- Base health metrics (averaged/baseline)
    baseline_metrics JSONB, -- {sleep_score, readiness, hrv, rhr, etc.}

    -- Health factors
    health_age FLOAT, -- calculated health age vs chronological
    resilience_score FLOAT, -- 0-100 recovery capacity
    adaptability_score FLOAT, -- 0-100 stress adaptation

    -- Risk factors
    risk_factors JSONB, -- [{factor, severity, impact}]
    protective_factors JSONB, -- [{factor, strength}]

    -- Trajectory
    health_trajectory TEXT, -- improving, stable, declining
    projected_health_age_1y FLOAT,
    projected_health_age_5y FLOAT,

    -- Model confidence
    data_completeness_score FLOAT, -- 0-1
    model_accuracy_score FLOAT, -- 0-1

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Health twin simulations (what-if scenarios)
CREATE TABLE IF NOT EXISTS health_twin_simulations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Simulation metadata
    simulation_name TEXT NOT NULL,
    simulation_type TEXT NOT NULL, -- lifestyle_change, goal_achievement, risk_mitigation

    -- Scenario definition
    scenario_description TEXT,
    changes JSONB NOT NULL, -- [{metric, current_value, target_value, change_type}]
    duration_days INT, -- simulation timeframe

    -- Results
    predicted_outcomes JSONB, -- {metric: {value, confidence, timeline}}
    health_age_impact FLOAT, -- predicted change in health age
    risk_reduction JSONB, -- {risk_type: reduction_percentage}

    -- Recommendations
    implementation_plan JSONB, -- step-by-step plan
    success_probability FLOAT, -- 0-1
    estimated_effort TEXT, -- low, medium, high

    -- Status
    is_active BOOLEAN DEFAULT true,
    status TEXT DEFAULT 'pending', -- pending, in_progress, completed, abandoned

    -- Tracking
    actual_progress JSONB, -- track real progress if user follows
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Health twin daily snapshots (track twin evolution)
CREATE TABLE IF NOT EXISTS health_twin_snapshots (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Snapshot date
    snapshot_date DATE NOT NULL,

    -- Snapshot data
    health_age FLOAT,
    resilience_score FLOAT,
    overall_health_score FLOAT,

    -- Component scores
    cardiovascular_score FLOAT,
    metabolic_score FLOAT,
    recovery_score FLOAT,
    mental_wellbeing_score FLOAT,

    -- Metrics snapshot
    metrics_snapshot JSONB, -- all relevant health metrics on this date

    -- Deviations from baseline
    deviations JSONB, -- {metric: deviation_from_baseline}

    created_at TIMESTAMPTZ DEFAULT now(),

    UNIQUE(user_id, snapshot_date)
);

-- Health twin goals and trajectories
CREATE TABLE IF NOT EXISTS health_twin_goals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Goal details
    goal_type TEXT NOT NULL, -- improve_biomarker, reduce_health_age, improve_score
    goal_name TEXT NOT NULL,
    target_metric TEXT NOT NULL,

    -- Target
    current_value FLOAT NOT NULL,
    target_value FLOAT NOT NULL,
    target_date DATE,

    -- Twin prediction
    predicted_success_probability FLOAT,
    predicted_completion_date DATE,
    required_changes JSONB, -- what changes needed to achieve goal

    -- Progress tracking
    progress_percentage FLOAT DEFAULT 0,
    milestones JSONB, -- [{name, target, achieved, date}]

    -- Status
    status TEXT DEFAULT 'active', -- active, achieved, abandoned, on_track, at_risk
    is_active BOOLEAN DEFAULT true,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    achieved_at TIMESTAMPTZ
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Lab results indexes
CREATE INDEX IF NOT EXISTS idx_lab_results_user_date ON lab_results(user_id, test_date DESC);
CREATE INDEX IF NOT EXISTS idx_lab_results_type ON lab_results(user_id, test_type);
CREATE INDEX IF NOT EXISTS idx_lab_results_abnormal ON lab_results(user_id, abnormal_count) WHERE abnormal_count > 0;

-- Biomarker trends indexes
CREATE INDEX IF NOT EXISTS idx_biomarker_trends_user ON biomarker_trends(user_id, biomarker_code);
CREATE INDEX IF NOT EXISTS idx_biomarker_trends_significance ON biomarker_trends(trend_significance) WHERE trend_significance IN ('clinically_significant', 'notable');

-- Lab insights indexes
CREATE INDEX IF NOT EXISTS idx_lab_insights_user ON lab_insights(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_lab_insights_priority ON lab_insights(user_id, priority) WHERE is_acknowledged = false;

-- Health twin indexes
CREATE INDEX IF NOT EXISTS idx_health_twin_snapshots ON health_twin_snapshots(user_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_health_twin_simulations ON health_twin_simulations(user_id, status);
CREATE INDEX IF NOT EXISTS idx_health_twin_goals ON health_twin_goals(user_id, status) WHERE is_active = true;

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Lab results RLS
ALTER TABLE lab_results ENABLE ROW LEVEL SECURITY;
CREATE POLICY lab_results_select_own ON lab_results
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY lab_results_insert_own ON lab_results
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY lab_results_update_own ON lab_results
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY lab_results_delete_own ON lab_results
    FOR DELETE USING (auth.uid() = user_id);

-- Biomarker trends RLS
ALTER TABLE biomarker_trends ENABLE ROW LEVEL SECURITY;
CREATE POLICY biomarker_trends_select_own ON biomarker_trends
    FOR SELECT USING (auth.uid() = user_id);

-- Lab insights RLS
ALTER TABLE lab_insights ENABLE ROW LEVEL SECURITY;
CREATE POLICY lab_insights_select_own ON lab_insights
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY lab_insights_update_own ON lab_insights
    FOR UPDATE USING (auth.uid() = user_id);

-- Health twin profile RLS
ALTER TABLE health_twin_profile ENABLE ROW LEVEL SECURITY;
CREATE POLICY health_twin_profile_select_own ON health_twin_profile
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY health_twin_profile_insert_own ON health_twin_profile
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY health_twin_profile_update_own ON health_twin_profile
    FOR UPDATE USING (auth.uid() = user_id);

-- Health twin simulations RLS
ALTER TABLE health_twin_simulations ENABLE ROW LEVEL SECURITY;
CREATE POLICY health_twin_simulations_select_own ON health_twin_simulations
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY health_twin_simulations_insert_own ON health_twin_simulations
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY health_twin_simulations_update_own ON health_twin_simulations
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY health_twin_simulations_delete_own ON health_twin_simulations
    FOR DELETE USING (auth.uid() = user_id);

-- Health twin snapshots RLS
ALTER TABLE health_twin_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY health_twin_snapshots_select_own ON health_twin_snapshots
    FOR SELECT USING (auth.uid() = user_id);

-- Health twin goals RLS
ALTER TABLE health_twin_goals ENABLE ROW LEVEL SECURITY;
CREATE POLICY health_twin_goals_select_own ON health_twin_goals
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY health_twin_goals_insert_own ON health_twin_goals
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY health_twin_goals_update_own ON health_twin_goals
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY health_twin_goals_delete_own ON health_twin_goals
    FOR DELETE USING (auth.uid() = user_id);

-- Biomarker references (public read)
ALTER TABLE biomarker_references ENABLE ROW LEVEL SECURITY;
CREATE POLICY biomarker_references_public_read ON biomarker_references
    FOR SELECT USING (true);

-- Lab test categories (public read)
ALTER TABLE lab_test_categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY lab_test_categories_public_read ON lab_test_categories
    FOR SELECT USING (true);

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Insert common lab test categories
INSERT INTO lab_test_categories (category_code, category_name, description, typical_markers, display_order) VALUES
('cbc', 'Complete Blood Count', 'Comprehensive blood cell analysis', '["WBC", "RBC", "Hemoglobin", "Hematocrit", "Platelets"]', 1),
('metabolic_panel', 'Metabolic Panel', 'Basic metabolic function tests', '["Glucose", "Calcium", "Sodium", "Potassium", "CO2", "Chloride", "BUN", "Creatinine"]', 2),
('lipid_panel', 'Lipid Panel', 'Cholesterol and triglycerides', '["Total Cholesterol", "LDL", "HDL", "Triglycerides"]', 3),
('thyroid', 'Thyroid Panel', 'Thyroid hormone levels', '["TSH", "T3", "T4", "Free T4"]', 4),
('liver_function', 'Liver Function Tests', 'Liver enzyme levels', '["ALT", "AST", "ALP", "Bilirubin", "Albumin"]', 5),
('kidney_function', 'Kidney Function', 'Kidney health markers', '["BUN", "Creatinine", "GFR", "Uric Acid"]', 6),
('hormone_panel', 'Hormone Panel', 'Hormone level analysis', '["Testosterone", "Estrogen", "Cortisol", "DHEA"]', 7),
('vitamin_panel', 'Vitamin Levels', 'Vitamin and mineral status', '["Vitamin D", "Vitamin B12", "Folate", "Iron", "Ferritin"]', 8),
('inflammation', 'Inflammation Markers', 'Inflammatory response indicators', '["CRP", "ESR", "Homocysteine"]', 9)
ON CONFLICT (category_code) DO NOTHING;

-- Insert common biomarker reference ranges
INSERT INTO biomarker_references (biomarker_code, biomarker_name, unit, gender, age_min, age_max, optimal_min, optimal_max, normal_min, normal_max, critical_low, critical_high, description) VALUES
-- Lipid Panel
('total_cholesterol', 'Total Cholesterol', 'mg/dL', 'all', 18, 120, 125, 200, 125, 240, NULL, 300, 'Total cholesterol level'),
('ldl', 'LDL Cholesterol', 'mg/dL', 'all', 18, 120, 0, 100, 0, 160, NULL, 190, 'Low-density lipoprotein (bad cholesterol)'),
('hdl', 'HDL Cholesterol', 'mg/dL', 'male', 18, 120, 40, 80, 40, 120, 20, NULL, 'High-density lipoprotein (good cholesterol) - Male'),
('hdl', 'HDL Cholesterol', 'mg/dL', 'female', 18, 120, 50, 90, 50, 120, 30, NULL, 'High-density lipoprotein (good cholesterol) - Female'),
('triglycerides', 'Triglycerides', 'mg/dL', 'all', 18, 120, 0, 100, 0, 150, NULL, 500, 'Blood fat levels'),

-- Metabolic
('glucose', 'Glucose', 'mg/dL', 'all', 18, 120, 70, 100, 65, 110, 40, 400, 'Fasting blood sugar'),
('hba1c', 'HbA1c', '%', 'all', 18, 120, 4.0, 5.6, 4.0, 6.4, NULL, 10.0, '3-month average blood sugar'),

-- Thyroid
('tsh', 'TSH', 'mIU/L', 'all', 18, 120, 0.5, 2.5, 0.4, 4.5, 0.1, 20.0, 'Thyroid stimulating hormone'),
('t4_free', 'Free T4', 'ng/dL', 'all', 18, 120, 1.0, 1.8, 0.8, 2.0, 0.3, 5.0, 'Free thyroxine'),

-- Inflammation
('crp', 'C-Reactive Protein', 'mg/L', 'all', 18, 120, 0, 1.0, 0, 3.0, NULL, 10.0, 'Inflammation marker'),

-- Vitamins
('vitamin_d', 'Vitamin D', 'ng/mL', 'all', 18, 120, 40, 80, 30, 100, 10, 150, '25-hydroxyvitamin D'),
('vitamin_b12', 'Vitamin B12', 'pg/mL', 'all', 18, 120, 400, 1000, 200, 1100, 100, 2000, 'Cobalamin')
ON CONFLICT (biomarker_code, gender, age_min, age_max) DO NOTHING;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE lab_results IS 'User lab test results and biomarkers';
COMMENT ON TABLE biomarker_trends IS 'Trends analysis for individual biomarkers over time';
COMMENT ON TABLE lab_insights IS 'AI-generated insights from lab results';
COMMENT ON TABLE health_twin_profile IS 'Digital health twin base profile';
COMMENT ON TABLE health_twin_simulations IS 'What-if scenario simulations using health twin';
COMMENT ON TABLE health_twin_snapshots IS 'Daily snapshots of health twin evolution';
COMMENT ON TABLE health_twin_goals IS 'Health goals tracked by digital twin';

COMMENT ON COLUMN lab_results.biomarkers IS 'JSON array of biomarker objects: [{name, value, unit, reference_range, status}]';
COMMENT ON COLUMN health_twin_profile.baseline_metrics IS 'JSON object with averaged baseline health metrics';
COMMENT ON COLUMN health_twin_simulations.changes IS 'JSON array of proposed changes for simulation';
