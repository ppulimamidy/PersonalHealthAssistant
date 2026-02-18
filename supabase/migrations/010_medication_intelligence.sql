-- Migration 010: Medication Intelligence Layer
-- AI drug-nutrient interactions and medication-vitals correlations

-- ============================================================================
-- Medication-Nutrient Interactions
-- ============================================================================

CREATE TABLE IF NOT EXISTS medication_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Medication info
    medication_name TEXT NOT NULL,
    medication_generic_name TEXT,
    medication_class TEXT, -- e.g., "Biguanide", "Statin", "SSRI"

    -- Interaction details
    interaction_type TEXT NOT NULL, -- 'nutrient_depletion', 'absorption_interference', 'metabolism_alteration', 'synergistic_effect'
    interacts_with TEXT NOT NULL, -- nutrient, supplement, or food item name
    interacts_with_category TEXT, -- 'vitamin', 'mineral', 'macronutrient', 'food_group'

    -- Severity and evidence
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'moderate', 'low')),
    evidence_level TEXT NOT NULL CHECK (evidence_level IN ('strong', 'moderate', 'limited', 'theoretical')),

    -- Description and recommendations
    mechanism TEXT, -- How the interaction occurs
    clinical_significance TEXT, -- What it means for the patient
    recommendation TEXT NOT NULL, -- What to do about it
    timing_recommendation TEXT, -- e.g., "Take 2 hours apart", "Take with food"

    -- Sources
    sources JSONB DEFAULT '[]'::jsonb, -- Array of citation objects {title, url, pubmed_id}

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_med_interactions_medication ON medication_interactions(medication_name);
CREATE INDEX idx_med_interactions_interacts_with ON medication_interactions(interacts_with);
CREATE INDEX idx_med_interactions_severity ON medication_interactions(severity);

-- Add some common medication-nutrient interactions as seed data
INSERT INTO medication_interactions (
    medication_name, medication_generic_name, medication_class,
    interaction_type, interacts_with, interacts_with_category,
    severity, evidence_level,
    mechanism, clinical_significance, recommendation, timing_recommendation,
    sources
) VALUES
-- Metformin + B12
(
    'Metformin', 'Metformin', 'Biguanide',
    'nutrient_depletion', 'Vitamin B12', 'vitamin',
    'moderate', 'strong',
    'Metformin reduces B12 absorption in the ileum by interfering with calcium-dependent B12-intrinsic factor complex uptake',
    'Long-term metformin use (>4 months) is associated with 10-30% reduction in B12 levels, potentially leading to peripheral neuropathy, anemia, and cognitive issues',
    'Consider B12 supplementation (500-1000 mcg daily) or monitor B12 levels annually',
    'Take B12 supplement at a different time than metformin',
    '[{"title":"Metformin and vitamin B12 deficiency","url":"https://pubmed.ncbi.nlm.nih.gov/24308062/","pubmed_id":"24308062"}]'::jsonb
),
-- Statins + CoQ10
(
    'Atorvastatin', 'Atorvastatin', 'Statin',
    'nutrient_depletion', 'Coenzyme Q10', 'coenzyme',
    'moderate', 'strong',
    'Statins inhibit HMG-CoA reductase, which is needed for both cholesterol and CoQ10 synthesis',
    'CoQ10 depletion may contribute to statin-related muscle pain (myalgia) and fatigue',
    'Consider CoQ10 supplementation (100-200 mg daily) if experiencing muscle pain or fatigue',
    'Take CoQ10 with a fat-containing meal for better absorption',
    '[{"title":"Coenzyme Q10 and statin-induced myopathy","url":"https://pubmed.ncbi.nlm.nih.gov/17686814/","pubmed_id":"17686814"}]'::jsonb
),
-- Levothyroxine + Calcium
(
    'Levothyroxine', 'Levothyroxine', 'Thyroid Hormone',
    'absorption_interference', 'Calcium', 'mineral',
    'high', 'strong',
    'Calcium binds to levothyroxine in the GI tract, reducing absorption by up to 40%',
    'Reduced thyroid hormone absorption can lead to inadequate TSH control and hypothyroid symptoms',
    'Separate levothyroxine and calcium supplements by at least 4 hours',
    'Take levothyroxine on empty stomach in morning, calcium with meals later',
    '[{"title":"Calcium supplements interfere with levothyroxine","url":"https://pubmed.ncbi.nlm.nih.gov/10448804/","pubmed_id":"10448804"}]'::jsonb
),
-- ACE Inhibitors + Potassium
(
    'Lisinopril', 'Lisinopril', 'ACE Inhibitor',
    'synergistic_effect', 'Potassium', 'mineral',
    'high', 'strong',
    'ACE inhibitors reduce aldosterone, leading to potassium retention',
    'Excessive potassium intake with ACE inhibitors can cause dangerous hyperkalemia (high potassium levels)',
    'Avoid high-dose potassium supplements. Monitor potassium levels regularly. Limit high-potassium foods',
    'Do not take potassium supplements unless directed by physician',
    '[{"title":"Hyperkalemia with ACE inhibitors","url":"https://pubmed.ncbi.nlm.nih.gov/8602852/","pubmed_id":"8602852"}]'::jsonb
),
-- Antibiotics + Probiotics
(
    'Amoxicillin', 'Amoxicillin', 'Penicillin Antibiotic',
    'absorption_interference', 'Probiotics', 'supplement',
    'low', 'moderate',
    'Antibiotics kill both harmful and beneficial bacteria, reducing probiotic effectiveness if taken simultaneously',
    'Taking probiotics with antibiotics may reduce their effectiveness, but probiotics can help restore gut flora',
    'Take probiotics at least 2-3 hours apart from antibiotics, continue for 2 weeks after finishing antibiotic course',
    'Separate by 2-3 hours; take probiotics between antibiotic doses',
    '[{"title":"Probiotics and antibiotics","url":"https://pubmed.ncbi.nlm.nih.gov/22570464/","pubmed_id":"22570464"}]'::jsonb
),
-- Warfarin + Vitamin K
(
    'Warfarin', 'Warfarin', 'Anticoagulant',
    'metabolism_alteration', 'Vitamin K', 'vitamin',
    'critical', 'strong',
    'Vitamin K is the antidote to warfarin; it reverses warfarin''s anticoagulant effect',
    'Inconsistent vitamin K intake can cause dangerous fluctuations in INR (clotting time)',
    'Maintain consistent vitamin K intake. Avoid sudden changes in green leafy vegetable consumption. Do not take vitamin K supplements',
    'Keep dietary vitamin K consistent day-to-day',
    '[{"title":"Warfarin and vitamin K interactions","url":"https://pubmed.ncbi.nlm.nih.gov/15461798/","pubmed_id":"15461798"}]'::jsonb
),
-- PPIs + Magnesium
(
    'Omeprazole', 'Omeprazole', 'Proton Pump Inhibitor',
    'nutrient_depletion', 'Magnesium', 'mineral',
    'moderate', 'strong',
    'PPIs reduce stomach acid, which is needed for magnesium absorption in the intestine',
    'Long-term PPI use (>1 year) can lead to hypomagnesemia, causing muscle cramps, irregular heartbeat, and seizures',
    'Consider magnesium supplementation (200-400 mg daily) or monitor magnesium levels if on long-term PPI therapy',
    'Take magnesium citrate or glycinate for better absorption',
    '[{"title":"Proton pump inhibitors and hypomagnesemia","url":"https://pubmed.ncbi.nlm.nih.gov/21436623/","pubmed_id":"21436623"}]'::jsonb
);

-- ============================================================================
-- User Medication Interaction Alerts
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_medication_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,

    -- Reference to the interaction rule
    interaction_id UUID REFERENCES medication_interactions(id),

    -- User's specific medications/supplements involved
    medication_id UUID REFERENCES medications(id),
    supplement_id UUID REFERENCES supplements(id),
    nutrition_item TEXT, -- If the interaction is with a food/nutrient from nutrition logs

    -- Alert details
    alert_type TEXT NOT NULL CHECK (alert_type IN ('drug_nutrient', 'drug_supplement', 'drug_food', 'supplement_nutrient')),
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    recommendation TEXT NOT NULL,

    -- Status
    is_acknowledged BOOLEAN DEFAULT false,
    acknowledged_at TIMESTAMPTZ,
    is_dismissed BOOLEAN DEFAULT false,
    dismissed_at TIMESTAMPTZ,

    -- Metadata
    detected_at TIMESTAMPTZ DEFAULT now(),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_user_med_alerts_user ON user_medication_alerts(user_id);
CREATE INDEX idx_user_med_alerts_severity ON user_medication_alerts(severity);
CREATE INDEX idx_user_med_alerts_ack ON user_medication_alerts(is_acknowledged);

-- RLS Policies
ALTER TABLE user_medication_alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own medication alerts"
    ON user_medication_alerts FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own medication alerts"
    ON user_medication_alerts FOR UPDATE
    USING (auth.uid()::text = user_id);

-- ============================================================================
-- Medication-Vitals Correlations
-- ============================================================================

CREATE TABLE IF NOT EXISTS medication_vitals_correlations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,

    -- Medication info
    medication_id UUID REFERENCES medications(id),
    medication_name TEXT NOT NULL,

    -- Vital/metric being correlated
    vital_metric TEXT NOT NULL, -- 'hrv_balance', 'resting_heart_rate', 'sleep_score', 'readiness_score', etc.
    vital_label TEXT NOT NULL, -- Human-readable label

    -- Correlation analysis results
    correlation_coefficient REAL NOT NULL, -- Pearson r (-1 to 1)
    p_value REAL NOT NULL, -- Statistical significance
    sample_size INTEGER NOT NULL, -- Number of data points

    -- Timing analysis
    lag_hours INTEGER NOT NULL DEFAULT 0, -- Hours after medication dose
    optimal_timing_window TEXT, -- e.g., "2-4 hours after dose"

    -- Effect description
    effect_type TEXT NOT NULL CHECK (effect_type IN ('positive', 'negative', 'neutral')),
    effect_magnitude TEXT, -- 'large', 'moderate', 'small'
    effect_description TEXT NOT NULL, -- AI-generated description

    -- Clinical interpretation
    clinical_significance TEXT,
    recommendation TEXT,

    -- Data quality
    data_quality_score REAL NOT NULL DEFAULT 0.0,
    days_analyzed INTEGER NOT NULL,

    -- Caching
    analysis_period_days INTEGER NOT NULL DEFAULT 30,
    computed_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT (now() + interval '7 days'),

    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_med_vitals_corr_user ON medication_vitals_correlations(user_id);
CREATE INDEX idx_med_vitals_corr_medication ON medication_vitals_correlations(medication_id);
CREATE INDEX idx_med_vitals_corr_vital ON medication_vitals_correlations(vital_metric);
CREATE INDEX idx_med_vitals_corr_expires ON medication_vitals_correlations(expires_at);

-- RLS Policies
ALTER TABLE medication_vitals_correlations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own medication correlations"
    ON medication_vitals_correlations FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY "System can insert medication correlations"
    ON medication_vitals_correlations FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own medication correlations"
    ON medication_vitals_correlations FOR DELETE
    USING (auth.uid()::text = user_id);

-- ============================================================================
-- Functions
-- ============================================================================

-- Function to clean up expired correlations
CREATE OR REPLACE FUNCTION cleanup_expired_medication_correlations()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM medication_vitals_correlations
    WHERE expires_at < now();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE medication_interactions IS 'Known medication-nutrient/supplement interactions with clinical evidence';
COMMENT ON TABLE user_medication_alerts IS 'User-specific interaction alerts based on their current medications and supplements';
COMMENT ON TABLE medication_vitals_correlations IS 'Correlations between medication timing and vital signs/health metrics';
