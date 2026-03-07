-- ============================================================================
-- DEMO DATA SEED: profiles table (Migration 014)
-- ============================================================================
-- Must be run AFTER migration 014 has been applied.
-- Run in Supabase SQL Editor (service-role context bypasses RLS).
--
-- Sarah Chen  |  DOB 1973-07-15 (age 52)  |  Female  |  78 kg
-- UUID: 22144dc2-f352-48aa-b34b-aebfa9f7e638
-- ============================================================================

INSERT INTO public.profiles (
    id,
    full_name,
    date_of_birth,
    biological_sex,
    weight_kg,
    height_cm,
    primary_goals,
    onboarding_completed_at,
    created_at,
    updated_at
) VALUES (
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    'Sarah Chen',
    '1973-07-15',
    'female',
    78.0,
    165,
    '["manage_condition", "improve_energy", "manage_stress", "improve_sleep"]'::jsonb,
    NOW() - INTERVAL '35 days',
    NOW() - INTERVAL '35 days',
    NOW() - INTERVAL '35 days'
)
ON CONFLICT (id) DO UPDATE SET
    full_name               = EXCLUDED.full_name,
    date_of_birth           = EXCLUDED.date_of_birth,
    biological_sex          = EXCLUDED.biological_sex,
    weight_kg               = EXCLUDED.weight_kg,
    height_cm               = EXCLUDED.height_cm,
    primary_goals           = EXCLUDED.primary_goals,
    onboarding_completed_at = EXCLUDED.onboarding_completed_at,
    updated_at              = NOW();

-- Verify
SELECT
    id,
    full_name,
    date_of_birth,
    biological_sex,
    weight_kg,
    height_cm,
    primary_goals,
    onboarding_completed_at
FROM public.profiles
WHERE id = '22144dc2-f352-48aa-b34b-aebfa9f7e638';
