-- ============================================================================
-- DEMO DATA: Nutrition Analyst Preferences — Sarah Chen
-- ============================================================================
-- Profile:  Sarah Chen, 52F, sedentary office job
-- User ID:  22144dc2-f352-48aa-b34b-aebfa9f7e638
-- Conditions: Prediabetes (A1C 6.2%), Hypertension, Hypothyroidism, Mild Anxiety
-- Diet story: Started week 3 tracking her food triggers, switched to
--             low-glycemic mediterranean-style eating.
-- These preferences reflect what the Nutrition Analyst collected from Sarah
-- during her first agent conversation.
-- ============================================================================

-- Run migration 013 first (creates the table):
--   supabase/migrations/013_nutrition_analyst_prefs.sql

INSERT INTO public.nutrition_analyst_prefs (
    user_id,
    preferences,
    created_at,
    updated_at
)
VALUES (
    '22144dc2-f352-48aa-b34b-aebfa9f7e638',
    '{
        "goals": [
            "Improve blood sugar control and reduce A1C below 5.7%",
            "Lower LDL cholesterol and triglycerides through diet",
            "Reduce dependence on Metformin with lifestyle changes",
            "Increase energy levels throughout the day",
            "Better manage stress-related eating",
            "Reach a healthy weight (current 78 kg, target 70 kg)"
        ],
        "allergies": [],
        "dietary_restrictions": [
            "Lactose intolerant — use lactose-free dairy or plant alternatives",
            "Low-glycemic — avoid refined carbs, white rice, white bread, sugary foods",
            "Reduce sodium — under 1500 mg/day for blood pressure management",
            "Anti-inflammatory — limit processed foods, trans fats, added sugars",
            "No alcohol — interacts with Metformin and raises blood sugar"
        ],
        "dislikes": [
            "Cilantro",
            "Very spicy food",
            "Liver and organ meats",
            "Bitter melon",
            "Overly sweet desserts"
        ],
        "food_preferences": [
            "Baked or grilled salmon and cod",
            "Eggs in any form",
            "Leafy greens (spinach, arugula, kale)",
            "Berries (especially blueberries and strawberries)",
            "Avocado",
            "Sweet potatoes",
            "Quinoa and steel-cut oats",
            "Walnuts and almonds",
            "Hummus and vegetables",
            "Greek-style food without heavy sauces",
            "Simple weeknight meals under 30 minutes"
        ],
        "health_conditions": [
            "Prediabetes — A1C 6.2%, fasting glucose 110-125 mg/dL. Prioritise low-GI foods, pair carbs with protein and fat.",
            "Essential Hypertension — on Lisinopril 10mg. Sodium-sensitive; target < 1500 mg sodium/day. DASH diet principles apply.",
            "Hypothyroidism (Hashimoto) — on Levothyroxine 75mcg. Avoid raw cruciferous vegetables in large amounts. No soy near medication time.",
            "Generalized Anxiety — limit caffeine after noon. Magnesium-rich foods (pumpkin seeds, spinach, almonds) support relaxation.",
            "Insulin resistance indicators — pair every carb serving with protein or healthy fat to blunt glucose spikes."
        ],
        "cuisine_preferences": [
            "Mediterranean",
            "Japanese (grilled fish, miso soup, edamame)",
            "Middle Eastern (hummus, tabbouleh, grilled chicken shawarma without bread)",
            "Simple American home cooking",
            "Mexican (with modifications — no chips, flour tortillas replaced with lettuce wraps or corn tortillas)"
        ],
        "meal_timing": "3 structured meals + 1 afternoon snack. Breakfast between 7:30-8:30 AM (after 30-60 min Levothyroxine window). Dinner before 7:30 PM to allow fasting window. No late-night eating — raises fasting glucose.",
        "cooking_skill": "intermediate",
        "budget": "moderate — prefers meal prepping on Sundays to reduce weekday takeout",
        "notes": "Sarah is 52F, 165 cm, 78 kg, sedentary office job. Target daily calories approx 1700-1850 kcal for gradual weight loss. Minimum 25g fibre/day for blood sugar control. At least 90g protein/day to preserve muscle. Key medication interactions: Levothyroxine must be taken 30-60 min before breakfast on an empty stomach — no calcium, iron, soy, or coffee within 4 hours. Metformin taken WITH meals (breakfast + dinner) to reduce nausea. Supplements: Vitamin D3 and Omega-3 with breakfast; Magnesium Glycinate with dinner. Trigger foods identified from her 30-day journal: refined carbs cause afternoon energy crashes and elevated next-morning glucose; high-sodium meals worsen bloating and raise BP; skipping breakfast leads to overeating at lunch."
    }'::jsonb,
    NOW() - INTERVAL '16 days',   -- set during week 3 when she started the agent
    NOW() - INTERVAL '3 days'     -- updated recently as she refined her approach
)
ON CONFLICT (user_id)
DO UPDATE SET
    preferences = EXCLUDED.preferences,
    updated_at  = EXCLUDED.updated_at;
