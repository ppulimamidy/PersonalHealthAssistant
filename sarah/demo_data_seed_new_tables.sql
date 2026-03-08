-- Demo seed data for Sarah Chen (22144dc2-f352-48aa-b34b-aebfa9f7e638)
-- Tables added in migrations 016-019: user_goals, weekly_checkins, care_plans, saved_insights

-- ============================================================
-- USER GOALS (with pinned doctor instructions)
-- ============================================================
INSERT INTO user_goals (user_id, goal_text, category, status, due_date, notes, source, is_pinned) VALUES
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'Reduce A1C below 5.7% (normal range)',
  'lab_result',
  'active',
  (NOW() + INTERVAL '90 days')::date,
  'Target set by Dr. Martinez at last visit. Currently at 6.2% — prediabetes range. Achieve through diet and exercise.',
  'doctor',
  true
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'Take Levothyroxine 75mcg every morning before food',
  'medication',
  'active',
  NULL,
  'Pinned reminder from Dr. Martinez. Thyroid medication requires consistent timing for effectiveness.',
  'doctor',
  true
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'Walk 30 minutes at least 5 days per week',
  'exercise',
  'active',
  (NOW() + INTERVAL '30 days')::date,
  'Aim for consistency over intensity. Evening walks after dinner work well.',
  'user',
  false
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'Limit processed sugar intake — no more than 25g added sugar per day',
  'diet',
  'active',
  NULL,
  'Focus on eliminating afternoon snack cookies and sweetened drinks.',
  'user',
  false
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'Reduce LDL cholesterol to below 100 mg/dL',
  'lab_result',
  'active',
  (NOW() + INTERVAL '90 days')::date,
  'Currently at 138 mg/dL. Dietary changes and possible statin review at next appointment.',
  'doctor',
  true
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'Sleep 7-8 hours per night',
  'sleep',
  'active',
  NULL,
  'Poor sleep correlated with worse blood sugar control.',
  'user',
  false
);

-- ============================================================
-- WEEKLY CHECKINS
-- ============================================================
INSERT INTO weekly_checkins (user_id, energy, mood, pain, notes, checked_in_at) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 3, 3, 4, 'Feeling sluggish this week. Afternoon energy crashes are bad. Skipped two workouts.', NOW() - INTERVAL '28 days'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 3, 4, 3, 'Slightly better. Started taking Levothyroxine more consistently. Still getting headaches mid-week.', NOW() - INTERVAL '21 days'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 4, 4, 2, 'Energy improving. Managed 3 walks this week. Cut back on sugary snacks.', NOW() - INTERVAL '14 days'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 4, 5, 2, 'Best week in a while. 4 walks completed. Sleep was better. Less bloating.', NOW() - INTERVAL '7 days'),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', 5, 5, 1, 'Feeling great. Keeping up with the routine. Blood pressure reading at home was 128/82 — improvement!', NOW() - INTERVAL '1 day');

-- ============================================================
-- CARE PLANS (tracking A1C, blood pressure, weight)
-- ============================================================
INSERT INTO care_plans (user_id, title, description, metric_type, target_value, target_unit, target_date, start_date, source, status, notes) VALUES
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'Prediabetes Reversal Plan',
  'Lower A1C from 6.2% to below 5.7% through diet, exercise, and consistent medication adherence. Focus on reducing processed carbohydrates and increasing daily movement.',
  'lab_result',
  5.7,
  '%',
  (NOW() + INTERVAL '90 days')::date,
  (NOW() - INTERVAL '7 days')::date,
  'doctor',
  'active',
  'A1C target: below 5.7%. Recommended by Dr. Martinez. Review at 3-month follow-up.'
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'Blood Pressure Management',
  'Reduce systolic blood pressure from ~140 to below 130 mmHg through lifestyle modifications: reduced sodium, regular aerobic exercise, and stress management.',
  'symptom_severity',
  2.0,
  'severity',
  (NOW() + INTERVAL '60 days')::date,
  (NOW() - INTERVAL '14 days')::date,
  'doctor',
  'active',
  'Salt restriction to 2000mg/day. 30 min cardio 5x/week. Monitor at home 2x/week. Target: systolic <130.'
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'Weight Reduction Goal',
  'Gradual weight reduction of 10-15 lbs over 3 months. Sustainable calorie deficit through food logging and portion awareness.',
  'weight',
  155.0,
  'lbs',
  (NOW() + INTERVAL '90 days')::date,
  (NOW() - INTERVAL '21 days')::date,
  'self',
  'active',
  'Current: ~168 lbs. Goal: 155 lbs. Rate: 0.5 lbs/week. No crash dieting.'
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'Medication Adherence Improvement',
  'Take Levothyroxine consistently every morning before food. Achieve 90%+ medication adherence to stabilize thyroid function and support metabolic health.',
  'medication_adherence',
  90.0,
  '%',
  (NOW() + INTERVAL '30 days')::date,
  (NOW() - INTERVAL '7 days')::date,
  'doctor',
  'active',
  'Thyroid medication requires consistent AM timing. Set daily 7am reminder. Track in app.'
);

-- ============================================================
-- SAVED INSIGHTS (mix of recent + ~30 days ago for follow-up feature)
-- ============================================================
INSERT INTO saved_insights (user_id, metric_key, title, summary, insight_type, category, metric_value, metric_unit, week_bucket, created_at) VALUES
-- ~30 days ago (for follow-up feature demo)
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'energy_pattern',
  'Afternoon Energy Crash Pattern',
  'Analysis of your symptom journal reveals a consistent energy crash between 2-4pm on 6 of the last 7 days. This correlates with high-carbohydrate lunch choices (>100g carbs) logged the same days. Blood sugar spikes from refined carbs likely causing insulin overshoot. Consider lower-GI lunch options.',
  'warning',
  'nutrition',
  3.2,
  'severity',
  (NOW() - INTERVAL '35 days')::date,
  NOW() - INTERVAL '35 days'
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'medication_adherence',
  'Thyroid Medication Timing Inconsistency',
  'Levothyroxine was logged at varying times (morning 7 of 14 days, afternoon 4 days, not logged 3 days). Thyroid medication requires consistent morning timing on empty stomach for optimal absorption. Inconsistent timing reduces efficacy by up to 40%.',
  'warning',
  'medication',
  50.0,
  '%',
  (NOW() - INTERVAL '35 days')::date,
  NOW() - INTERVAL '35 days'
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'a1c_trajectory',
  'A1C Trending into Prediabetes Territory',
  'Your A1C of 6.2% (Jan 19 labs) is in the prediabetes range (5.7-6.4%). This is a critical intervention window — research shows lifestyle changes at this stage can reverse prediabetes in 58% of cases. Primary drivers: high refined carb intake and sedentary work schedule.',
  'critical',
  'lab',
  6.2,
  '%',
  (NOW() - INTERVAL '35 days')::date,
  NOW() - INTERVAL '35 days'
),
-- Recent insights (last 2 weeks)
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'exercise_improvement',
  'Exercise Consistency Improving — Keep It Up!',
  'You completed 4 walks this week totaling ~120 minutes of moderate aerobic activity. This is a 33% improvement over last week (3 walks). Regular aerobic exercise at this level can reduce A1C by 0.3-0.5% over 3 months. Your evening walks are well-timed to help with post-dinner blood sugar control.',
  'positive',
  'activity',
  4.0,
  'walks',
  (NOW() - INTERVAL '7 days')::date,
  NOW() - INTERVAL '6 days'
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'sodium_intake',
  'Sodium Still High — Blood Pressure Risk',
  'Average daily sodium from food logs: 2,847mg (target <2,000mg for blood pressure management). Top contributors: frozen meals (avg 1,800mg each), deli sandwiches (~1,900mg), and takeout. Switching 3 meals/week to home-cooked could reduce sodium by ~1,200mg/day.',
  'warning',
  'nutrition',
  2847.0,
  'mg',
  (NOW() - INTERVAL '7 days')::date,
  NOW() - INTERVAL '5 days'
),
(
  '22144dc2-f352-48aa-b34b-aebfa9f7e638',
  'inflammation_correlation',
  'Stress + Poor Sleep Linked to CRP Elevation',
  'Cross-referencing your symptom journal stress ratings (avg 7.2/10 on work days) with your hs-CRP of 3.2 mg/L suggests chronic stress-driven inflammation. Elevated CRP at this level increases cardiovascular risk by 2x. Stress management (even 10 min/day mindfulness) shown to reduce CRP by 15-20%.',
  'warning',
  'biomarker',
  3.2,
  'mg/L',
  (NOW() - INTERVAL '14 days')::date,
  NOW() - INTERVAL '12 days'
);
