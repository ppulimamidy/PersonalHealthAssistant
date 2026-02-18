-- ============================================================================
-- DEMO DATA SEED: SYMPTOM JOURNAL (30 days)
-- ============================================================================
-- Patterns correlate with:
-- - High-carb/sugar meals → fatigue, energy crashes
-- - High-sodium meals → headaches, bloating
-- - Missed medications → increased symptoms
-- - Stress → headaches, digestive issues, anxiety
-- - Poor sleep (would correlate with Oura) → fatigue, elevated HR
-- ============================================================================

-- Week 1: Frequent symptoms (poor diet, inconsistent meds, high stress)

-- Day 1
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '30 days')::DATE, '14:00:00', 'fatigue', 5, 180, '["large_carb_meal", "afternoon_crash"]'::jsonb, 'Energy crashed hard after pasta lunch. Needed 2 coffees to make it through afternoon meetings.', 'tired', 7),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '30 days')::DATE, '21:00:00', 'digestive_discomfort', 5, 120, '["metformin_side_effect", "large_dinner"]'::jsonb, 'Bloated and uncomfortable after pasta alfredo. Metformin GI side effects?', 'uncomfortable', 5);

-- Day 2
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '29 days')::DATE, '10:00:00', 'headache', 5, 240, '["skipped_breakfast", "dehydration", "caffeine_withdrawal"]'::jsonb, 'Woke up with headache. Skipped breakfast - bad decision. Headache lasted until after lunch.', 'irritable', 6),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '29 days')::DATE, '16:00:00', 'fatigue', 8, 180, '["blood_sugar_crash", "no_breakfast"]'::jsonb, 'Extremely low energy. Shaky and lightheaded. Realize I didn''t eat breakfast - blood sugar must be low.', 'anxious', 7);

-- Day 3
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '28 days')::DATE, '14:30:00', 'fatigue', 5, 150, '["high_sugar_meal", "energy_crash"]'::jsonb, 'Post-lunch crash after Orange Chicken (very sugary sauce). Could barely keep eyes open in 2pm meeting.', 'sluggish', 6),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '28 days')::DATE, '22:00:00', 'digestive_discomfort', 5, 90, '["fried_food", "high_fat"]'::jsonb, 'Stomach upset after burger and fries. Feeling greasy and bloated.', 'regretful', 5);

-- Day 4
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '27 days')::DATE, '11:00:00', 'anxiety', 5, 120, '["work_deadline", "coffee_overconsumption"]'::jsonb, 'Big project deadline. Heart racing, jittery. Drank 3 cups of coffee this morning - too much caffeine.', 'stressed', 8),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '27 days')::DATE, '16:00:00', 'headache', 3, 90, '["stress", "screen_time", "tension"]'::jsonb, 'Tension headache from staring at screen all day. Stress about work.', 'tense', 7);

-- Day 5
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '26 days')::DATE, '09:00:00', 'fatigue', 5, 240, '["poor_sleep", "restless_night"]'::jsonb, 'Barely slept last night. Tossed and turned. Dragging this morning even after coffee.', 'exhausted', 6),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '26 days')::DATE, '15:00:00', 'digestive_discomfort', 3, 60, '["metformin", "empty_stomach"]'::jsonb, 'Took metformin but didn''t eat enough with it. Mild nausea.', 'uncomfortable', 5);

-- Day 6
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '25 days')::DATE, '11:00:00', 'fatigue', 3, 120, '["high_carb_breakfast", "blood_sugar_spike"]'::jsonb, 'Pancakes for breakfast = energy crash by 11am. Noticing a pattern here...', 'sleepy', 4),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '25 days')::DATE, '21:00:00', 'bloating', 5, 180, '["large_restaurant_meal", "high_sodium"]'::jsonb, 'Very bloated after restaurant lasagna. Feel like I''m retaining water. Probably the sodium.', 'uncomfortable', 4);

-- Day 7
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '24 days')::DATE, '14:00:00', 'digestive_discomfort', 3, 90, '["rich_brunch", "eggs_benedict"]'::jsonb, 'Heavy hollandaise sauce not sitting well. Feeling sluggish.', 'content', 3);

-- Week 2: Continuing symptoms, starting to notice patterns

-- Day 8
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '23 days')::DATE, '10:00:00', 'headache', 5, 180, '["forgot_levothyroxine", "hypothyroid_symptom"]'::jsonb, 'Forgot thyroid med this morning (rushed). Now have headache and feel foggy. Need to be more consistent!', 'frustrated', 6),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '23 days')::DATE, '15:00:00', 'fatigue', 5, 150, '["sugar_crash", "processed_food"]'::jsonb, 'Afternoon energy dip again. Starting to see this happens after high-carb lunches.', 'reflective', 5);

-- Day 9
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '22 days')::DATE, '14:00:00', 'anxiety', 5, 90, '["work_stress", "presentation"]'::jsonb, 'Big presentation today. Heart pounding, sweaty palms. Performance anxiety.', 'nervous', 8);

-- Day 10
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '21 days')::DATE, '22:00:00', 'digestive_discomfort', 5, 120, '["pad_thai", "high_sugar_sauce"]'::jsonb, 'Pad Thai was delicious but stomach is not happy. Too much sugar in the sauce?', 'uncomfortable', 5),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '21 days')::DATE, '16:00:00', 'headache', 3, 60, '["dehydration", "not_enough_water"]'::jsonb, 'Mild headache. Realized I only drank 1 glass of water all day. Need to hydrate better.', 'okay', 5);

-- Day 11
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '20 days')::DATE, '14:30:00', 'fatigue', 5, 180, '["insufficient_sleep", "late_dinner"]'::jsonb, 'Didn''t sleep well - ate dinner too late (8:30pm). Woke up feeling unrested. Energy low all day.', 'tired', 6);

-- Day 12
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '19 days')::DATE, '11:00:00', 'bloating', 5, 150, '["high_sodium", "processed_food"]'::jsonb, 'Noticing bloating after salty takeout meals. Rings feel tight on fingers.', 'aware', 5);

-- Day 14 (Reflection Point)
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '17 days')::DATE, '20:00:00', 'general', 1, 0, '["self_reflection"]'::jsonb, 'Looking back at this app data: I see clear patterns! Energy crashes after refined carbs. Bloating from sodium. Forgetting meds = more symptoms. Time to make real changes starting Monday.', 'motivated', 5);

-- Week 3: Intervention begins - symptoms start improving

-- Day 15 (Fresh Start)
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '16 days')::DATE, '11:00:00', 'energy_improvement', 1, 0, '["low_glycemic_breakfast", "stable_blood_sugar"]'::jsonb, 'Steel-cut oats for breakfast - no energy crash! Still have good energy 3 hours later. This is the way!', 'optimistic', 4),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '16 days')::DATE, '21:00:00', 'digestive_comfort', 1, 0, '["light_dinner", "lean_protein", "vegetables"]'::jsonb, 'Light fish dinner. No bloating! Feel comfortable and light. Better than how I''ve felt after heavy pasta dinners.', 'satisfied', 3);

-- Day 16
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '15 days')::DATE, '14:00:00', 'energy_improvement', 1, 0, '["high_protein_breakfast", "sustained_energy"]'::jsonb, 'Veggie omelet kept me full and energized all morning! No 10am snack craving. Protein makes a difference.', 'energized', 4);

-- Day 17
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '14 days')::DATE, '15:30:00', 'headache', 3, 45, '["work_stress", "screen_time"]'::jsonb, 'Mild stress headache but went away quickly after drinking water and taking a walk. Much better than before!', 'calm', 5);

-- Day 18
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '13 days')::DATE, '16:00:00', 'digestive_comfort', 1, 0, '["consistent_meals", "more_fiber"]'::jsonb, 'Digestion feels so much better with consistent meal timing and more vegetables. No more bloating!', 'happy', 4);

-- Day 20
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '11 days')::DATE, '22:00:00', 'sleep_improvement', 1, 0, '["earlier_dinner", "lighter_meal"]'::jsonb, 'Eating dinner earlier (6:30pm) and lighter = much better sleep! Woke up refreshed. Game changer.', 'rested', 3);

-- Day 21 (One Week of Improvements)
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '10 days')::DATE, '19:00:00', 'general', 1, 0, '["lifestyle_changes", "medication_adherence"]'::jsonb, 'One week of better eating and consistent meds: Energy WAY better, no headaches this week, digestion improved, even lost 2 lbs! Feeling hopeful.', 'encouraged', 3);

-- Week 4: Sustained improvement, occasional minor symptoms

-- Day 22
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '9 days')::DATE, '10:00:00', 'energy_improvement', 1, 0, '["morning_routine", "consistent_medication"]'::jsonb, 'Morning routine is solid now: Thyroid med at 6am, breakfast at 7:30am. Energy is stable and high all day.', 'confident', 3);

-- Day 23
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '8 days')::DATE, '16:00:00', 'anxiety', 3, 45, '["work_deadline", "managed_with_breathing"]'::jsonb, 'Work stress today but managed anxiety with deep breathing and a walk. Didn''t spiral like before!', 'proud', 6);

-- Day 25
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '6 days')::DATE, '14:00:00', 'energy_improvement', 1, 0, '["balanced_meals", "stable_blood_sugar"]'::jsonb, 'No energy crashes this week! Balanced meals with protein + fiber + healthy fats = stable blood sugar all day.', 'amazed', 4);

-- Day 26
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '5 days')::DATE, '21:00:00', 'digestive_comfort', 1, 0, '["magnesium_supplement", "better_sleep"]'::jsonb, 'Started magnesium supplement this week. Noticing even better sleep and more regular digestion. Dr. was right!', 'grateful', 3);

-- Day 28
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '3 days')::DATE, '11:00:00', 'headache', 3, 30, '["forgot_water_bottle", "slight_dehydration"]'::jsonb, 'Minor headache from not drinking enough water. Drank 2 glasses and it went away. Small slip but caught it early!', 'mindful', 4),
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '3 days')::DATE, '20:00:00', 'general', 1, 0, '["overall_improvement"]'::jsonb, 'Can''t believe the difference 2 weeks makes. Energy is up, brain fog is gone, clothes fit better. This is sustainable!', 'thriving', 3);

-- Day 30 (Final Reflection)
INSERT INTO symptom_journal (user_id, symptom_date, symptom_time, symptom_type, severity, duration_minutes, triggers, notes, mood, stress_level) VALUES
('22144dc2-f352-48aa-b34b-aebfa9f7e638', (NOW() - INTERVAL '1 day')::DATE, '20:00:00', 'general', 1, 0, '["30_day_reflection", "lifestyle_success"]'::jsonb, '30 DAYS! Comparing to Day 1: Fatigue gone, digestive issues resolved, headaches rare, anxiety manageable, lost 5 lbs, A1C likely improved. The data doesn''t lie - food IS medicine. So grateful for this tracking app showing me the patterns I couldn''t see. Ready for next 30 days!', 'empowered', 2);
