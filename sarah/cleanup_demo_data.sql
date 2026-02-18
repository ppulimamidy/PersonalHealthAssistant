-- ============================================================================
-- DEMO DATA CLEANUP SCRIPT
-- ============================================================================
-- Purpose: Delete all demo data for Sarah Chen to allow fresh reloading
-- Usage: Replace '22144dc2-f352-48aa-b34b-aebfa9f7e638' with actual UUID before running
-- ============================================================================

-- Show current record counts BEFORE cleanup
SELECT 'BEFORE CLEANUP - Record Counts:' as status;

SELECT
    'health_conditions' as table_name,
    COUNT(*) as record_count
FROM health_conditions
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'medications' as table_name,
    COUNT(*) as record_count
FROM medications
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'supplements' as table_name,
    COUNT(*) as record_count
FROM supplements
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'medication_adherence_log' as table_name,
    COUNT(*) as record_count
FROM medication_adherence_log
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'lab_results' as table_name,
    COUNT(*) as record_count
FROM lab_results
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'meal_logs' as table_name,
    COUNT(*) as record_count
FROM meal_logs
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'symptom_journal' as table_name,
    COUNT(*) as record_count
FROM symptom_journal
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'user_health_profile' as table_name,
    COUNT(*) as record_count
FROM user_health_profile
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638';

-- ============================================================================
-- DELETE OPERATIONS (in correct order to respect foreign keys)
-- ============================================================================

-- Delete symptom journal entries
DELETE FROM symptom_journal
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638';

-- Delete nutrition meal logs
DELETE FROM meal_logs
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638';

-- Delete medication adherence logs
DELETE FROM medication_adherence_log
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638';

-- Delete lab results
DELETE FROM lab_results
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638';

-- Delete supplements
DELETE FROM supplements
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638';

-- Delete medications
DELETE FROM medications
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638';

-- Delete health conditions
DELETE FROM health_conditions
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638';

-- Delete user health profile
DELETE FROM user_health_profile
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638';

-- ============================================================================
-- VERIFICATION - Show counts AFTER cleanup
-- ============================================================================

SELECT 'AFTER CLEANUP - Record Counts (should all be 0):' as status;

SELECT
    'health_conditions' as table_name,
    COUNT(*) as record_count
FROM health_conditions
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'medications' as table_name,
    COUNT(*) as record_count
FROM medications
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'supplements' as table_name,
    COUNT(*) as record_count
FROM supplements
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'medication_adherence_log' as table_name,
    COUNT(*) as record_count
FROM medication_adherence_log
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'lab_results' as table_name,
    COUNT(*) as record_count
FROM lab_results
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'meal_logs' as table_name,
    COUNT(*) as record_count
FROM meal_logs
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'symptom_journal' as table_name,
    COUNT(*) as record_count
FROM symptom_journal
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638'

UNION ALL

SELECT
    'user_health_profile' as table_name,
    COUNT(*) as record_count
FROM user_health_profile
WHERE user_id = '22144dc2-f352-48aa-b34b-aebfa9f7e638';

SELECT '✅ Cleanup complete! All demo data deleted.' as status;
