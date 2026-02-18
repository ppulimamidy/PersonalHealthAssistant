-- ============================================================================
-- DEMO DATA SEED: 30-Day Research-Backed Synthetic Health Data
-- ============================================================================
-- Profile: Sarah Chen, 52F, sedentary office job
-- Conditions: Prediabetes (A1C 6.2%), Hypertension, Hypothyroidism, Mild Anxiety
-- Story Arc: Optimization journey showing trigger discovery and improvement
-- ============================================================================

-- DEMO USER ID (replace with actual user_id after creation)
-- For this script, we'll use: '22144dc2-f352-48aa-b34b-aebfa9f7e638'

-- ============================================================================
-- 1. USER HEALTH PROFILE
-- ============================================================================

INSERT INTO user_health_profile (
    user_id,
    health_goals,
    dietary_preferences,
    supplements,
    medications,
    questionnaire_responses,
    questionnaire_completed_at
) VALUES (
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    '["Improve blood sugar control", "Reduce medication dependence", "Increase energy levels", "Better stress management"]'::jsonb,
    '{
        "diet_type": "low_glycemic",
        "allergies": [],
        "intolerances": ["lactose"],
        "preferences": ["mediterranean", "anti_inflammatory"],
        "restrictions": ["limit_refined_carbs", "reduce_sodium"]
    }'::jsonb,
    '["Vitamin D3 2000 IU", "Omega-3 Fish Oil 1000mg", "Magnesium Glycinate 400mg"]'::jsonb,
    '["Metformin 500mg", "Lisinopril 10mg", "Levothyroxine 75mcg"]'::jsonb,
    '{
        "age": 52,
        "gender": "female",
        "height_cm": 165,
        "weight_kg": 78,
        "occupation": "software_project_manager",
        "stress_level": "moderate_to_high",
        "exercise_frequency": "1-2_times_per_week",
        "sleep_quality": "poor_to_fair",
        "family_history": ["type_2_diabetes", "hypertension", "thyroid_disease"]
    }'::jsonb,
    NOW() - INTERVAL '35 days'
);

-- ============================================================================
-- 2. HEALTH CONDITIONS
-- ============================================================================

INSERT INTO health_conditions (user_id, condition_name, condition_category, severity, diagnosed_date, notes, is_active, tracked_variables) VALUES
(
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    'Prediabetes',
    'metabolic',
    'moderate',
    '2024-11-15',
    'A1C 6.2%, Fasting glucose 110-125 mg/dL. Family history of T2D. Managing with lifestyle and Metformin.',
    true,
    '["fasting_glucose", "post_meal_glucose", "carbohydrate_intake", "fiber_intake", "energy_levels", "weight"]'::jsonb
),
(
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    'Essential Hypertension',
    'cardiovascular',
    'mild',
    '2023-08-20',
    'BP averaging 135/88. Controlled with Lisinopril 10mg. Sodium-sensitive.',
    true,
    '["systolic_bp", "diastolic_bp", "resting_heart_rate", "sodium_intake", "stress_level", "sleep_quality"]'::jsonb
),
(
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    'Hypothyroidism',
    'endocrine',
    'mild',
    '2022-03-10',
    'TSH 4.8 mIU/L at diagnosis, now 2.1 on Levothyroxine 75mcg. Hashimoto antibodies present.',
    true,
    '["energy_levels", "weight", "mood", "cold_sensitivity", "medication_adherence"]'::jsonb
),
(
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    'Generalized Anxiety Disorder',
    'mental_health',
    'mild',
    '2023-01-15',
    'Work-related stress and health anxiety. Managing with lifestyle interventions, no anxiolytics currently.',
    true,
    '["stress_level", "sleep_quality", "mood", "heart_rate_variability", "digestive_symptoms"]'::jsonb
);

-- ============================================================================
-- 3. MEDICATIONS
-- ============================================================================

INSERT INTO medications (
    user_id, medication_name, generic_name, dosage, frequency, route,
    indication, prescribing_doctor, start_date, is_active,
    refill_reminder_enabled, refill_reminder_days_before,
    side_effects_experienced, notes
) VALUES
(
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    'Glucophage',
    'Metformin HCl',
    '500mg',
    'twice_daily',
    'oral',
    'Prediabetes / Insulin Resistance',
    'Dr. Jennifer Martinez, MD (Endocrinology)',
    '2024-11-20',
    true,
    true,
    7,
    '["mild_nausea", "occasional_diarrhea"]'::jsonb,
    'Take with meals to reduce GI side effects. Started at 500mg to assess tolerance.'
),
(
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    'Prinivil',
    'Lisinopril',
    '10mg',
    'once_daily',
    'oral',
    'Hypertension',
    'Dr. Jennifer Martinez, MD (Endocrinology)',
    '2023-08-25',
    true,
    true,
    7,
    '[]'::jsonb,
    'Take in morning. Monitor for dizziness, dry cough.'
),
(
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    'Synthroid',
    'Levothyroxine Sodium',
    '75mcg',
    'once_daily',
    'oral',
    'Hypothyroidism (Hashimoto''s)',
    'Dr. Jennifer Martinez, MD (Endocrinology)',
    '2022-03-15',
    true,
    true,
    10,
    '[]'::jsonb,
    'CRITICAL: Take on empty stomach 30-60 min before breakfast. Do not take with calcium, iron, or coffee. Wait 4 hours before taking supplements.'
);

-- ============================================================================
-- 4. SUPPLEMENTS
-- ============================================================================

INSERT INTO supplements (
    user_id, supplement_name, brand, dosage, frequency, form,
    purpose, taken_with_food, time_of_day, start_date, is_active, notes
) VALUES
(
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    'Vitamin D3',
    'Nordic Naturals',
    '2000 IU',
    'once_daily',
    'softgel',
    'Bone health, immune support, mood. Deficiency common with hypothyroidism.',
    true,
    'morning',
    '2023-06-01',
    true,
    'Take with breakfast (fat-soluble). Wait 4 hours after levothyroxine.'
),
(
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    'Omega-3 Fish Oil',
    'Nordic Naturals',
    '1000mg (EPA 500mg, DHA 250mg)',
    'once_daily',
    'softgel',
    'Cardiovascular health, inflammation, triglycerides.',
    true,
    'morning',
    '2023-09-01',
    true,
    'High-quality, molecularly distilled. Take with breakfast.'
),
(
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    'Magnesium Glycinate',
    'Pure Encapsulations',
    '400mg',
    'once_daily',
    'capsule',
    'Blood sugar regulation, sleep quality, muscle relaxation, stress management.',
    true,
    'evening',
    '2024-12-01',
    true,
    'Glycinate form for better absorption and less GI upset. Take with dinner. Wait 4 hours after levothyroxine.'
);

-- ============================================================================
-- 5. LAB RESULTS (Baseline - 45 days ago)
-- ============================================================================

-- Metabolic Panel
INSERT INTO lab_results (
    user_id, test_date, test_type, lab_name, ordering_provider,
    biomarkers, abnormal_count, critical_count, ai_summary
) VALUES (
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    NOW() - INTERVAL '45 days',
    'metabolic_panel',
    'LabCorp',
    'Dr. Jennifer Martinez',
    '[
        {
            "name": "Hemoglobin A1C",
            "value": 6.2,
            "unit": "%",
            "reference_range": {"min": 4.0, "max": 5.6},
            "status": "high",
            "notes": "Prediabetes range (5.7-6.4%). Recheck in 3 months."
        },
        {
            "name": "Fasting Glucose",
            "value": 118,
            "unit": "mg/dL",
            "reference_range": {"min": 70, "max": 99},
            "status": "high",
            "notes": "Impaired fasting glucose. Lifestyle + Metformin initiated."
        },
        {
            "name": "Fasting Insulin",
            "value": 18.5,
            "unit": "μIU/mL",
            "reference_range": {"min": 2.6, "max": 24.9},
            "status": "normal",
            "notes": "Elevated-normal, suggests insulin resistance."
        }
    ]'::jsonb,
    2,
    0,
    'Metabolic panel shows prediabetes (A1C 6.2%) and impaired fasting glucose (118 mg/dL), consistent with insulin resistance. Metformin initiated and lifestyle modifications recommended.'
);

-- Lipid Panel
INSERT INTO lab_results (
    user_id, test_date, test_type, lab_name, ordering_provider,
    biomarkers, abnormal_count, critical_count, ai_summary
) VALUES (
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    NOW() - INTERVAL '45 days',
    'lipid_panel',
    'LabCorp',
    'Dr. Jennifer Martinez',
    '[
        {
            "name": "Total Cholesterol",
            "value": 215,
            "unit": "mg/dL",
            "reference_range": {"min": 0, "max": 200},
            "status": "high",
            "notes": "Borderline high. Focus on diet, omega-3."
        },
        {
            "name": "LDL Cholesterol",
            "value": 138,
            "unit": "mg/dL",
            "reference_range": {"min": 0, "max": 100},
            "status": "high",
            "notes": "Above optimal. Target <100 mg/dL."
        },
        {
            "name": "HDL Cholesterol",
            "value": 52,
            "unit": "mg/dL",
            "reference_range": {"min": 40, "max": 999},
            "status": "normal",
            "notes": "Adequate but could be higher. Exercise recommended."
        },
        {
            "name": "Triglycerides",
            "value": 165,
            "unit": "mg/dL",
            "reference_range": {"min": 0, "max": 150},
            "status": "high",
            "notes": "Elevated. Reduce refined carbs, increase omega-3."
        }
    ]'::jsonb,
    3,
    0,
    'Lipid panel shows dyslipidemia: elevated total cholesterol (215 mg/dL), LDL (138 mg/dL), and triglycerides (165 mg/dL). Pattern consistent with metabolic syndrome. Dietary modifications (low refined carbs, omega-3 supplementation) and exercise recommended.'
);

-- Thyroid Panel
INSERT INTO lab_results (
    user_id, test_date, test_type, lab_name, ordering_provider,
    biomarkers, abnormal_count, critical_count, ai_summary
) VALUES (
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    NOW() - INTERVAL '45 days',
    'thyroid_panel',
    'LabCorp',
    'Dr. Jennifer Martinez',
    '[
        {
            "name": "TSH",
            "value": 2.1,
            "unit": "mIU/L",
            "reference_range": {"min": 0.4, "max": 4.0},
            "status": "normal",
            "notes": "Well-controlled on Levothyroxine 75mcg."
        },
        {
            "name": "Free T4",
            "value": 1.3,
            "unit": "ng/dL",
            "reference_range": {"min": 0.8, "max": 1.8},
            "status": "normal",
            "notes": "Mid-range, optimal."
        },
        {
            "name": "Free T3",
            "value": 3.1,
            "unit": "pg/mL",
            "reference_range": {"min": 2.3, "max": 4.2},
            "status": "normal",
            "notes": "Good T4 to T3 conversion."
        },
        {
            "name": "TPO Antibodies",
            "value": 125,
            "unit": "IU/mL",
            "reference_range": {"min": 0, "max": 35},
            "status": "high",
            "notes": "Hashimoto''s thyroiditis confirmed."
        }
    ]'::jsonb,
    1,
    0,
    'Thyroid function well-controlled on Levothyroxine 75mcg (TSH 2.1, Free T4 1.3, Free T3 3.1). Elevated TPO antibodies (125 IU/mL) confirm Hashimoto''s thyroiditis diagnosis. Continue current dose.'
);

-- Vitamin Panel
INSERT INTO lab_results (
    user_id, test_date, test_type, lab_name, ordering_provider,
    biomarkers, abnormal_count, critical_count, ai_summary
) VALUES (
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    NOW() - INTERVAL '45 days',
    'vitamin_panel',
    'LabCorp',
    'Dr. Jennifer Martinez',
    '[
        {
            "name": "Vitamin D, 25-OH",
            "value": 28,
            "unit": "ng/mL",
            "reference_range": {"min": 30, "max": 100},
            "status": "low",
            "notes": "Insufficient. Supplementing with 2000 IU daily."
        }
    ]'::jsonb,
    1,
    0,
    'Vitamin D insufficiency (28 ng/mL). Supplementation with 2000 IU daily initiated. Recheck in 3 months.'
);

-- Mineral Panel
INSERT INTO lab_results (
    user_id, test_date, test_type, lab_name, ordering_provider,
    biomarkers, abnormal_count, critical_count, ai_summary
) VALUES (
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    NOW() - INTERVAL '45 days',
    'mineral_panel',
    'LabCorp',
    'Dr. Jennifer Martinez',
    '[
        {
            "name": "Magnesium, Serum",
            "value": 1.8,
            "unit": "mg/dL",
            "reference_range": {"min": 1.7, "max": 2.2},
            "status": "normal",
            "notes": "Low-normal. May benefit from supplementation."
        }
    ]'::jsonb,
    0,
    0,
    'Serum magnesium low-normal (1.8 mg/dL). May benefit from supplementation for metabolic health and insulin sensitivity.'
);

-- Inflammatory Markers
INSERT INTO lab_results (
    user_id, test_date, test_type, lab_name, ordering_provider,
    biomarkers, abnormal_count, critical_count, ai_summary
) VALUES (
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    NOW() - INTERVAL '45 days',
    'inflammatory_markers',
    'LabCorp',
    'Dr. Jennifer Martinez',
    '[
        {
            "name": "hs-CRP",
            "value": 3.2,
            "unit": "mg/L",
            "reference_range": {"min": 0, "max": 3.0},
            "status": "high",
            "notes": "Mild inflammation. Related to metabolic syndrome."
        }
    ]'::jsonb,
    1,
    0,
    'Elevated hs-CRP (3.2 mg/L) indicates mild systemic inflammation, consistent with metabolic syndrome and insulin resistance. Anti-inflammatory diet and exercise recommended.'
);

-- ============================================================================
-- 6. MEDICATION ADHERENCE LOGS (30 days)
-- ============================================================================

-- Helper: We'll create adherence logs showing:
-- Week 1-2: Poor adherence (60-70% - missed doses, inconsistent timing)
-- Week 3-4: Improved adherence (90-95% - consistent after user realizes impact)

DO $$
DECLARE
    med_metformin_id UUID;
    med_lisinopril_id UUID;
    med_levothyroxine_id UUID;
    sup_vitamin_d_id UUID;
    sup_omega3_id UUID;
    sup_magnesium_id UUID;
    day_offset INT;
    log_date TIMESTAMP;
    adherence_rate FLOAT;
BEGIN
    -- Get medication IDs
    SELECT id INTO med_metformin_id FROM medications WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638' AND generic_name = 'Metformin HCl';
    SELECT id INTO med_lisinopril_id FROM medications WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638' AND generic_name = 'Lisinopril';
    SELECT id INTO med_levothyroxine_id FROM medications WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638' AND generic_name = 'Levothyroxine Sodium';
    SELECT id INTO sup_vitamin_d_id FROM supplements WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638' AND supplement_name = 'Vitamin D3';
    SELECT id INTO sup_omega3_id FROM supplements WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638' AND supplement_name = 'Omega-3 Fish Oil';
    SELECT id INTO sup_magnesium_id FROM supplements WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638' AND supplement_name = 'Magnesium Glycinate';

    -- Generate 30 days of adherence data
    FOR day_offset IN 0..29 LOOP
        log_date := NOW() - INTERVAL '30 days' + (day_offset || ' days')::INTERVAL;

        -- Determine adherence pattern based on week
        IF day_offset < 14 THEN
            adherence_rate := 0.65; -- Week 1-2: 65% adherence
        ELSE
            adherence_rate := 0.93; -- Week 3-4: 93% adherence
        END IF;

        -- Levothyroxine (morning, empty stomach)
        IF RANDOM() < adherence_rate THEN
            INSERT INTO medication_adherence_log (user_id, medication_id, scheduled_time, taken_time, was_taken)
            VALUES (
                '22144dc2-f352-48aa-b34b-aebfa9f7e638',
                med_levothyroxine_id,
                log_date + INTERVAL '6 hours',
                log_date + INTERVAL '6 hours' + (RANDOM() * 30 || ' minutes')::INTERVAL,
                true
            );
        ELSE
            INSERT INTO medication_adherence_log (user_id, medication_id, scheduled_time, was_taken, missed_reason)
            VALUES (
                '22144dc2-f352-48aa-b34b-aebfa9f7e638',
                med_levothyroxine_id,
                log_date + INTERVAL '6 hours',
                false,
                CASE WHEN RANDOM() < 0.5 THEN 'Forgot - rushed morning' ELSE 'Slept through alarm' END
            );
        END IF;

        -- Lisinopril (morning with breakfast)
        IF RANDOM() < adherence_rate THEN
            INSERT INTO medication_adherence_log (user_id, medication_id, scheduled_time, taken_time, was_taken)
            VALUES (
                '22144dc2-f352-48aa-b34b-aebfa9f7e638',
                med_lisinopril_id,
                log_date + INTERVAL '7 hours 30 minutes',
                log_date + INTERVAL '7 hours 30 minutes' + (RANDOM() * 45 || ' minutes')::INTERVAL,
                true
            );
        ELSE
            INSERT INTO medication_adherence_log (user_id, medication_id, scheduled_time, was_taken, missed_reason)
            VALUES (
                '22144dc2-f352-48aa-b34b-aebfa9f7e638',
                med_lisinopril_id,
                log_date + INTERVAL '7 hours 30 minutes',
                false,
                'Forgot to take with breakfast'
            );
        END IF;

        -- Metformin (breakfast)
        IF RANDOM() < adherence_rate THEN
            INSERT INTO medication_adherence_log (user_id, medication_id, scheduled_time, taken_time, was_taken, side_effects_noted)
            VALUES (
                '22144dc2-f352-48aa-b34b-aebfa9f7e638',
                med_metformin_id,
                log_date + INTERVAL '7 hours 30 minutes',
                log_date + INTERVAL '7 hours 30 minutes' + (RANDOM() * 30 || ' minutes')::INTERVAL,
                true,
                CASE WHEN RANDOM() < 0.15 THEN 'Mild nausea' ELSE NULL END
            );
        ELSE
            INSERT INTO medication_adherence_log (user_id, medication_id, scheduled_time, was_taken, missed_reason)
            VALUES (
                '22144dc2-f352-48aa-b34b-aebfa9f7e638',
                med_metformin_id,
                log_date + INTERVAL '7 hours 30 minutes',
                false,
                CASE WHEN RANDOM() < 0.5 THEN 'Concerned about GI side effects' ELSE 'Forgot' END
            );
        END IF;

        -- Metformin (dinner)
        IF RANDOM() < adherence_rate THEN
            INSERT INTO medication_adherence_log (user_id, medication_id, scheduled_time, taken_time, was_taken, side_effects_noted)
            VALUES (
                '22144dc2-f352-48aa-b34b-aebfa9f7e638',
                med_metformin_id,
                log_date + INTERVAL '18 hours 30 minutes',
                log_date + INTERVAL '18 hours 30 minutes' + (RANDOM() * 30 || ' minutes')::INTERVAL,
                true,
                CASE WHEN RANDOM() < 0.12 THEN 'Digestive discomfort' ELSE NULL END
            );
        ELSE
            INSERT INTO medication_adherence_log (user_id, medication_id, scheduled_time, was_taken, missed_reason)
            VALUES (
                '22144dc2-f352-48aa-b34b-aebfa9f7e638',
                med_metformin_id,
                log_date + INTERVAL '18 hours 30 minutes',
                false,
                'Ate out, forgot to bring medication'
            );
        END IF;

        -- Vitamin D (morning with breakfast)
        IF RANDOM() < (adherence_rate * 0.9) THEN -- Supplements have slightly lower adherence
            INSERT INTO medication_adherence_log (user_id, supplement_id, scheduled_time, taken_time, was_taken)
            VALUES (
                '22144dc2-f352-48aa-b34b-aebfa9f7e638',
                sup_vitamin_d_id,
                log_date + INTERVAL '7 hours 30 minutes',
                log_date + INTERVAL '7 hours 30 minutes' + (RANDOM() * 60 || ' minutes')::INTERVAL,
                true
            );
        END IF;

        -- Omega-3 (morning with breakfast)
        IF RANDOM() < (adherence_rate * 0.9) THEN
            INSERT INTO medication_adherence_log (user_id, supplement_id, scheduled_time, taken_time, was_taken)
            VALUES (
                '22144dc2-f352-48aa-b34b-aebfa9f7e638',
                sup_omega3_id,
                log_date + INTERVAL '7 hours 30 minutes',
                log_date + INTERVAL '7 hours 30 minutes' + (RANDOM() * 60 || ' minutes')::INTERVAL,
                true
            );
        END IF;

        -- Magnesium (evening with dinner)
        IF RANDOM() < (adherence_rate * 0.85) THEN
            INSERT INTO medication_adherence_log (user_id, supplement_id, scheduled_time, taken_time, was_taken)
            VALUES (
                '22144dc2-f352-48aa-b34b-aebfa9f7e638',
                sup_magnesium_id,
                log_date + INTERVAL '18 hours 30 minutes',
                log_date + INTERVAL '18 hours 30 minutes' + (RANDOM() * 60 || ' minutes')::INTERVAL,
                true
            );
        END IF;

    END LOOP;
END $$;

-- ============================================================================
-- 7. NUTRITION MEAL LOGS (30 days)
-- ============================================================================
-- Pattern: Week 1-2 (poor choices), Week 3-4 (improved diet)
-- Research-based portions and macros for 52F, sedentary, 78kg

-- Week 1: Poor Management (Days 1-7)
-- High refined carbs, low fiber, irregular timing, eating out frequently

-- Day 1
INSERT INTO meal_logs (user_id, meal_type, meal_name, timestamp, total_calories, total_protein_g, total_carbs_g, total_fat_g, total_fiber_g, total_sugar_g, total_sodium_mg, food_items, user_notes) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'breakfast', 'Blueberry Muffin & Latte', NOW() - INTERVAL '30 days' + INTERVAL '8 hours', 520, 8, 72, 22, 2, 38, 420, '[{"name": "Blueberry muffin", "quantity": "1 large", "calories": 380}, {"name": "Vanilla latte (whole milk)", "quantity": "16 oz", "calories": 140}]'::jsonb, 'Grabbed at coffee shop on way to work'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'lunch', 'Chicken Teriyaki Bowl with White Rice', NOW() - INTERVAL '30 days' + INTERVAL '12 hours 30 minutes', 780, 32, 112, 18, 3, 28, 1680, '[{"name": "White rice", "quantity": "2 cups", "calories": 410}, {"name": "Teriyaki chicken", "quantity": "6 oz", "calories": 280}, {"name": "Stir-fried vegetables", "quantity": "1 cup", "calories": 90}]'::jsonb, 'Takeout lunch at desk, very high sodium'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'dinner', 'Pasta Alfredo with Garlic Bread', NOW() - INTERVAL '30 days' + INTERVAL '19 hours', 1050, 28, 135, 42, 5, 12, 1540, '[{"name": "Fettuccine alfredo", "quantity": "2.5 cups", "calories": 850}, {"name": "Garlic bread", "quantity": "2 slices", "calories": 200}]'::jsonb, 'Too tired to cook, ate comfort food. Felt bloated after.'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'snack', 'Chocolate Chip Cookies', NOW() - INTERVAL '30 days' + INTERVAL '15 hours', 280, 3, 38, 14, 1, 24, 180, '[{"name": "Chocolate chip cookies", "quantity": "3 medium", "calories": 280}]'::jsonb, 'Afternoon energy crash, reached for cookies');

-- Day 2
INSERT INTO meal_logs (user_id, meal_type, meal_name, timestamp, total_calories, total_protein_g, total_carbs_g, total_fat_g, total_fiber_g, total_sugar_g, total_sodium_mg, food_items, user_notes) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'breakfast', 'Skipped Breakfast', NOW() - INTERVAL '29 days' + INTERVAL '8 hours', 0, 0, 0, 0, 0, 0, 0, '[]'::jsonb, 'Rushed morning, no time. Felt shaky by 10am.'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'lunch', 'Turkey Sub Sandwich & Chips', NOW() - INTERVAL '29 days' + INTERVAL '13 hours', 820, 38, 95, 32, 5, 14, 1920, '[{"name": "12-inch turkey sub", "quantity": "1", "calories": 650}, {"name": "Potato chips", "quantity": "1.5 oz", "calories": 160}, {"name": "Diet Coke", "quantity": "12 oz", "calories": 0}]'::jsonb, 'Deli lunch, very salty'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'snack', 'Granola Bar & Coffee', NOW() - INTERVAL '29 days' + INTERVAL '15 hours 30 minutes', 210, 4, 32, 8, 2, 18, 120, '[{"name": "Granola bar", "quantity": "1 bar", "calories": 190}, {"name": "Coffee with cream", "quantity": "8 oz", "calories": 20}]'::jsonb, NULL),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'dinner', 'Frozen Pizza', NOW() - INTERVAL '29 days' + INTERVAL '20 hours', 940, 36, 108, 38, 4, 12, 2180, '[{"name": "Frozen pepperoni pizza", "quantity": "3/4 pizza", "calories": 940}]'::jsonb, 'Exhausted from work, quick frozen dinner');

-- Day 3
INSERT INTO meal_logs (user_id, meal_type, meal_name, timestamp, total_calories, total_protein_g, total_carbs_g, total_fat_g, total_fiber_g, total_sugar_g, total_sodium_mg, food_items, user_notes) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'breakfast', 'Bagel with Cream Cheese', NOW() - INTERVAL '28 days' + INTERVAL '7 hours 30 minutes', 450, 14, 68, 14, 3, 8, 620, '[{"name": "Plain bagel", "quantity": "1 large", "calories": 320}, {"name": "Cream cheese", "quantity": "2 tbsp", "calories": 100}, {"name": "Orange juice", "quantity": "8 oz", "calories": 110}]'::jsonb, NULL),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'lunch', 'Chinese Takeout - Orange Chicken', NOW() - INTERVAL '28 days' + INTERVAL '12 hours', 920, 28, 128, 32, 3, 42, 1840, '[{"name": "Orange chicken", "quantity": "2 cups", "calories": 720}, {"name": "Fried rice", "quantity": "1.5 cups", "calories": 350}]'::jsonb, 'Team lunch, very sugary sauce'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'snack', 'Vending Machine Crackers', NOW() - INTERVAL '28 days' + INTERVAL '15 hours', 190, 3, 24, 9, 1, 3, 280, '[{"name": "Cheese crackers", "quantity": "1 pack", "calories": 190}]'::jsonb, NULL),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'dinner', 'Burger and Fries (Takeout)', NOW() - INTERVAL '28 days' + INTERVAL '19 hours 30 minutes', 1180, 42, 118, 58, 6, 18, 1560, '[{"name": "Cheeseburger", "quantity": "1", "calories": 750}, {"name": "French fries", "quantity": "medium", "calories": 380}, {"name": "Diet soda", "quantity": "16 oz", "calories": 0}]'::jsonb, 'Didn''t feel like cooking');

-- Day 4
INSERT INTO meal_logs (user_id, meal_type, meal_name, timestamp, total_calories, total_protein_g, total_carbs_g, total_fat_g, total_fiber_g, total_sugar_g, total_sodium_mg, food_items, user_notes) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'breakfast', 'Instant Oatmeal with Brown Sugar', NOW() - INTERVAL '27 days' + INTERVAL '8 hours', 320, 8, 58, 6, 4, 22, 340, '[{"name": "Instant oatmeal (maple brown sugar)", "quantity": "2 packets", "calories": 320}]'::jsonb, 'Quick breakfast'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'lunch', 'Chicken Caesar Salad', NOW() - INTERVAL '27 days' + INTERVAL '12 hours 30 minutes', 680, 38, 32, 42, 4, 6, 1240, '[{"name": "Caesar salad with chicken", "quantity": "large", "calories": 680}]'::jsonb, 'Tried to eat healthier but dressing was very heavy'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'snack', 'Apple', NOW() - INTERVAL '27 days' + INTERVAL '15 hours', 95, 0, 25, 0, 4, 19, 2, '[{"name": "Medium apple", "quantity": "1", "calories": 95}]'::jsonb, 'Good choice!'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'dinner', 'Spaghetti with Meatballs', NOW() - INTERVAL '27 days' + INTERVAL '19 hours', 850, 38, 98, 32, 6, 14, 1180, '[{"name": "Spaghetti with marinara", "quantity": "2 cups", "calories": 480}, {"name": "Meatballs", "quantity": "4", "calories": 320}, {"name": "Parmesan cheese", "quantity": "2 tbsp", "calories": 50}]'::jsonb, NULL);

-- Day 5
INSERT INTO meal_logs (user_id, meal_type, meal_name, timestamp, total_calories, total_protein_g, total_carbs_g, total_fat_g, total_fiber_g, total_sugar_g, total_sodium_mg, food_items, user_notes) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'breakfast', 'Breakfast Sandwich (Fast Food)', NOW() - INTERVAL '26 days' + INTERVAL '7 hours 45 minutes', 520, 22, 42, 28, 2, 6, 1140, '[{"name": "Sausage egg cheese biscuit", "quantity": "1", "calories": 520}]'::jsonb, 'Grabbed on way to early meeting'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'lunch', 'Chicken Quesadilla', NOW() - INTERVAL '26 days' + INTERVAL '13 hours', 780, 36, 68, 38, 4, 6, 1520, '[{"name": "Chicken quesadilla", "quantity": "1 large", "calories": 780}]'::jsonb, 'Lunch meeting catering'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'snack', 'Trail Mix', NOW() - INTERVAL '26 days' + INTERVAL '16 hours', 280, 8, 28, 16, 4, 18, 95, '[{"name": "Trail mix with M&Ms", "quantity": "1/2 cup", "calories": 280}]'::jsonb, NULL),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'dinner', 'Rotisserie Chicken with Mac & Cheese', NOW() - INTERVAL '26 days' + INTERVAL '20 hours', 820, 48, 72, 32, 3, 8, 1420, '[{"name": "Rotisserie chicken breast", "quantity": "6 oz", "calories": 280}, {"name": "Mac and cheese", "quantity": "1.5 cups", "calories": 540}]'::jsonb, 'Store-bought rotisserie, easier than cooking');

-- Day 6 (Saturday)
INSERT INTO meal_logs (user_id, meal_type, meal_name, timestamp, total_calories, total_protein_g, total_carbs_g, total_fat_g, total_fiber_g, total_sugar_g, total_sodium_mg, food_items, user_notes) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'breakfast', 'Pancakes with Syrup', NOW() - INTERVAL '25 days' + INTERVAL '9 hours', 680, 12, 112, 18, 3, 48, 820, '[{"name": "Buttermilk pancakes", "quantity": "3 large", "calories": 510}, {"name": "Maple syrup", "quantity": "4 tbsp", "calories": 210}, {"name": "Butter", "quantity": "1 tbsp", "calories": 100}]'::jsonb, 'Weekend breakfast'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'lunch', 'Leftover Pizza', NOW() - INTERVAL '25 days' + INTERVAL '13 hours 30 minutes', 620, 24, 72, 25, 3, 8, 1450, '[{"name": "Frozen pizza leftovers", "quantity": "1/2 pizza", "calories": 620}]'::jsonb, NULL),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'snack', 'Ice Cream', NOW() - INTERVAL '25 days' + INTERVAL '16 hours', 340, 5, 42, 16, 0, 36, 75, '[{"name": "Vanilla ice cream", "quantity": "1 cup", "calories": 340}]'::jsonb, 'Weekend treat'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'dinner', 'Restaurant Italian - Lasagna', NOW() - INTERVAL '25 days' + INTERVAL '19 hours 30 minutes', 1050, 42, 95, 52, 5, 18, 1880, '[{"name": "Meat lasagna", "quantity": "large serving", "calories": 850}, {"name": "Garlic bread", "quantity": "2 slices", "calories": 200}]'::jsonb, 'Dinner out with friends. Felt very full and bloated.');

-- Day 7 (Sunday)
INSERT INTO meal_logs (user_id, meal_type, meal_name, timestamp, total_calories, total_protein_g, total_carbs_g, total_fat_g, total_fiber_g, total_sugar_g, total_sodium_mg, food_items, user_notes) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'breakfast', 'Brunch - Eggs Benedict', NOW() - INTERVAL '24 days' + INTERVAL '10 hours', 720, 28, 48, 42, 2, 6, 1240, '[{"name": "Eggs benedict", "quantity": "2", "calories": 720}]'::jsonb, 'Sunday brunch'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'lunch', 'Light Snacking', NOW() - INTERVAL '24 days' + INTERVAL '14 hours', 380, 12, 48, 14, 3, 18, 420, '[{"name": "Crackers and cheese", "quantity": "1 serving", "calories": 280}, {"name": "Grapes", "quantity": "1 cup", "calories": 100}]'::jsonb, 'Not very hungry after big brunch'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 'dinner', 'Homemade Tacos', NOW() - INTERVAL '24 days' + INTERVAL '18 hours 30 minutes', 680, 32, 62, 28, 8, 6, 980, '[{"name": "Ground beef tacos", "quantity": "3 tacos", "calories": 680}]'::jsonb, 'Actually cooked! Used lean beef and added lettuce, tomatoes.');

-- Week 2: Still Poor but Starting to Notice Patterns (Days 8-14)
