-- Migration 005: Medications, Supplements, and Symptom Journal
-- Phase 1 of Health Intelligence Features
-- Created: 2026-02-16

-- ============================================================================
-- MEDICATIONS TRACKING
-- ============================================================================

-- Medications table: Track prescription medications
CREATE TABLE IF NOT EXISTS medications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Medication info
    medication_name TEXT NOT NULL,
    generic_name TEXT,
    dosage TEXT NOT NULL, -- e.g., "10mg", "500mg"
    frequency TEXT NOT NULL, -- e.g., "once daily", "twice daily", "as needed"
    route TEXT DEFAULT 'oral', -- oral, topical, injection, inhaled, etc.

    -- Purpose and prescriber
    indication TEXT, -- what it's for
    prescribing_doctor TEXT,
    pharmacy TEXT,
    prescription_number TEXT,

    -- Timeline
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,

    -- Refill tracking
    refill_reminder_enabled BOOLEAN DEFAULT false,
    refill_reminder_days_before INT DEFAULT 7,

    -- Side effects and notes
    side_effects_experienced JSONB DEFAULT '[]'::jsonb,
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Supplements table: Track vitamins, minerals, herbs, etc.
CREATE TABLE IF NOT EXISTS supplements (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Supplement info
    supplement_name TEXT NOT NULL,
    brand TEXT,
    dosage TEXT NOT NULL, -- e.g., "1000mg", "50mcg"
    frequency TEXT NOT NULL, -- e.g., "once daily", "twice daily"
    form TEXT DEFAULT 'capsule', -- capsule, tablet, powder, liquid, gummy

    -- Purpose and timing
    purpose TEXT,
    taken_with_food BOOLEAN,
    time_of_day TEXT, -- morning, afternoon, evening, bedtime

    -- Timeline
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT true,

    -- Notes
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Medication/supplement adherence log
CREATE TABLE IF NOT EXISTS medication_adherence_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Link to medication or supplement
    medication_id UUID REFERENCES medications(id) ON DELETE CASCADE,
    supplement_id UUID REFERENCES supplements(id) ON DELETE CASCADE,

    -- Adherence tracking
    scheduled_time TIMESTAMPTZ NOT NULL,
    taken_time TIMESTAMPTZ,
    was_taken BOOLEAN DEFAULT false,
    missed_reason TEXT,
    side_effects_noted TEXT,

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Ensure either medication or supplement is linked, not both
    CONSTRAINT medication_or_supplement CHECK (
        (medication_id IS NOT NULL AND supplement_id IS NULL) OR
        (medication_id IS NULL AND supplement_id IS NOT NULL)
    )
);

-- ============================================================================
-- SYMPTOM JOURNAL
-- ============================================================================

-- Symptom journal entries
CREATE TABLE IF NOT EXISTS symptom_journal (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- When
    symptom_date DATE NOT NULL,
    symptom_time TIME,

    -- What
    symptom_type TEXT NOT NULL, -- pain, fatigue, nausea, headache, digestive, mental_health, etc.
    severity INT CHECK (severity BETWEEN 1 AND 10), -- 1-10 scale
    location TEXT, -- body location for pain/physical symptoms
    duration_minutes INT,

    -- Triggers and associations
    triggers JSONB DEFAULT '[]'::jsonb, -- potential triggers (foods, activities, stress, weather, etc.)
    associated_symptoms JSONB DEFAULT '[]'::jsonb,
    medications_taken JSONB DEFAULT '[]'::jsonb, -- medications taken for this symptom

    -- Context
    notes TEXT,
    mood TEXT, -- happy, anxious, stressed, sad, neutral
    weather_conditions TEXT,
    stress_level INT CHECK (stress_level BETWEEN 1 AND 10),
    sleep_hours_previous_night FLOAT,

    -- Optional photo (for rashes, swelling, etc.)
    photo_url TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Symptom patterns cache (AI-generated insights)
CREATE TABLE IF NOT EXISTS symptom_patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Pattern details
    pattern_type TEXT NOT NULL, -- time_based, trigger_based, cyclic, correlation
    symptom_type TEXT NOT NULL,
    pattern_description TEXT,
    confidence_score FLOAT,

    -- Supporting data
    supporting_entries JSONB DEFAULT '[]'::jsonb, -- array of symptom_journal IDs
    recommendations JSONB DEFAULT '[]'::jsonb,

    -- Status
    detected_at TIMESTAMPTZ DEFAULT now(),
    is_active BOOLEAN DEFAULT true
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Medications indexes
CREATE INDEX IF NOT EXISTS idx_medications_user ON medications(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_medications_start_date ON medications(user_id, start_date DESC);

-- Supplements indexes
CREATE INDEX IF NOT EXISTS idx_supplements_user ON supplements(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_supplements_start_date ON supplements(user_id, start_date DESC);

-- Adherence log indexes
CREATE INDEX IF NOT EXISTS idx_adherence_log_user_time ON medication_adherence_log(user_id, scheduled_time DESC);
CREATE INDEX IF NOT EXISTS idx_adherence_log_med ON medication_adherence_log(medication_id) WHERE medication_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_adherence_log_supp ON medication_adherence_log(supplement_id) WHERE supplement_id IS NOT NULL;

-- Symptom journal indexes
CREATE INDEX IF NOT EXISTS idx_symptom_journal_user_date ON symptom_journal(user_id, symptom_date DESC);
CREATE INDEX IF NOT EXISTS idx_symptom_journal_type ON symptom_journal(user_id, symptom_type);
CREATE INDEX IF NOT EXISTS idx_symptom_journal_severity ON symptom_journal(user_id, severity DESC);

-- Symptom patterns indexes
CREATE INDEX IF NOT EXISTS idx_symptom_patterns_user ON symptom_patterns(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_symptom_patterns_type ON symptom_patterns(user_id, symptom_type, is_active);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE medications ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplements ENABLE ROW LEVEL SECURITY;
ALTER TABLE medication_adherence_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE symptom_journal ENABLE ROW LEVEL SECURITY;
ALTER TABLE symptom_patterns ENABLE ROW LEVEL SECURITY;

-- Medications RLS policies (users manage their own medications)
CREATE POLICY medications_select_own ON medications
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY medications_insert_own ON medications
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY medications_update_own ON medications
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY medications_delete_own ON medications
    FOR DELETE USING (auth.uid() = user_id);

-- Supplements RLS policies (users manage their own supplements)
CREATE POLICY supplements_select_own ON supplements
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY supplements_insert_own ON supplements
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY supplements_update_own ON supplements
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY supplements_delete_own ON supplements
    FOR DELETE USING (auth.uid() = user_id);

-- Adherence log RLS policies (users manage their own logs)
CREATE POLICY adherence_log_select_own ON medication_adherence_log
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY adherence_log_insert_own ON medication_adherence_log
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY adherence_log_update_own ON medication_adherence_log
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY adherence_log_delete_own ON medication_adherence_log
    FOR DELETE USING (auth.uid() = user_id);

-- Symptom journal RLS policies (users manage their own journal)
CREATE POLICY symptom_journal_select_own ON symptom_journal
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY symptom_journal_insert_own ON symptom_journal
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY symptom_journal_update_own ON symptom_journal
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY symptom_journal_delete_own ON symptom_journal
    FOR DELETE USING (auth.uid() = user_id);

-- Symptom patterns RLS policies (users manage their own patterns)
CREATE POLICY symptom_patterns_select_own ON symptom_patterns
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY symptom_patterns_insert_own ON symptom_patterns
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY symptom_patterns_update_own ON symptom_patterns
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY symptom_patterns_delete_own ON symptom_patterns
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================================================
-- COMMENTS (for documentation)
-- ============================================================================

COMMENT ON TABLE medications IS 'User prescription medications with dosage, frequency, and adherence tracking';
COMMENT ON TABLE supplements IS 'User vitamins, minerals, and supplements with timing and purpose';
COMMENT ON TABLE medication_adherence_log IS 'Adherence tracking for medications and supplements';
COMMENT ON TABLE symptom_journal IS 'User symptom logs with severity, triggers, and context';
COMMENT ON TABLE symptom_patterns IS 'AI-detected symptom patterns and recommendations';

COMMENT ON COLUMN medications.side_effects_experienced IS 'JSON array of side effects user has experienced';
COMMENT ON COLUMN symptom_journal.triggers IS 'JSON array of potential triggers (foods, activities, stress, etc.)';
COMMENT ON COLUMN symptom_journal.associated_symptoms IS 'JSON array of other symptoms occurring simultaneously';
COMMENT ON COLUMN symptom_journal.medications_taken IS 'JSON array of medications/supplements taken for this symptom';
COMMENT ON COLUMN symptom_patterns.supporting_entries IS 'JSON array of symptom_journal entry IDs supporting this pattern';
COMMENT ON COLUMN symptom_patterns.recommendations IS 'JSON array of AI-generated recommendations for this pattern';
