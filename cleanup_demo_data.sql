-- ============================================================================
-- DEMO DATA CLEANUP SCRIPT
-- ============================================================================
-- Purpose: Delete all demo data for Sarah Chen to allow fresh reloading
-- Usage: Replace 'demo_user_sarah_chen' with actual UUID before running
-- ============================================================================

-- Show current record counts BEFORE cleanup
SELECT 'BEFORE CLEANUP - Record Counts:' as status;

SELECT
    'health_conditions' as table_name,
    COUNT(*) as record_count
FROM health_conditions
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'medications' as table_name,
    COUNT(*) as record_count
FROM medications
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'supplements' as table_name,
    COUNT(*) as record_count
FROM supplements
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'medication_adherence_log' as table_name,
    COUNT(*) as record_count
FROM medication_adherence_log
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'lab_results' as table_name,
    COUNT(*) as record_count
FROM lab_results
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'meal_logs' as table_name,
    COUNT(*) as record_count
FROM meal_logs
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'symptom_journal' as table_name,
    COUNT(*) as record_count
FROM symptom_journal
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'user_health_profile' as table_name,
    COUNT(*) as record_count
FROM user_health_profile
WHERE user_id = 'demo_user_sarah_chen';

-- ============================================================================
-- DELETE OPERATIONS (in correct order to respect foreign keys)
-- ============================================================================

-- Delete symptom journal entries
DELETE FROM symptom_journal
WHERE user_id = 'demo_user_sarah_chen';

-- Delete nutrition meal logs
DELETE FROM meal_logs
WHERE user_id = 'demo_user_sarah_chen';

-- Delete medication adherence logs
DELETE FROM medication_adherence_log
WHERE user_id = 'demo_user_sarah_chen';

-- Delete lab results
DELETE FROM lab_results
WHERE user_id = 'demo_user_sarah_chen';

-- Delete supplements
DELETE FROM supplements
WHERE user_id = 'demo_user_sarah_chen';

-- Delete medications
DELETE FROM medications
WHERE user_id = 'demo_user_sarah_chen';

-- Delete health conditions
DELETE FROM health_conditions
WHERE user_id = 'demo_user_sarah_chen';

-- Delete user health profile
DELETE FROM user_health_profile
WHERE user_id = 'demo_user_sarah_chen';

-- ============================================================================
-- VERIFICATION - Show counts AFTER cleanup
-- ============================================================================

SELECT 'AFTER CLEANUP - Record Counts (should all be 0):' as status;

SELECT
    'health_conditions' as table_name,
    COUNT(*) as record_count
FROM health_conditions
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'medications' as table_name,
    COUNT(*) as record_count
FROM medications
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'supplements' as table_name,
    COUNT(*) as record_count
FROM supplements
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'medication_adherence_log' as table_name,
    COUNT(*) as record_count
FROM medication_adherence_log
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'lab_results' as table_name,
    COUNT(*) as record_count
FROM lab_results
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'meal_logs' as table_name,
    COUNT(*) as record_count
FROM meal_logs
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'symptom_journal' as table_name,
    COUNT(*) as record_count
FROM symptom_journal
WHERE user_id = 'demo_user_sarah_chen'

UNION ALL

SELECT
    'user_health_profile' as table_name,
    COUNT(*) as record_count
FROM user_health_profile
WHERE user_id = 'demo_user_sarah_chen';

SELECT '✅ Cleanup complete! All demo data deleted.' as status;
