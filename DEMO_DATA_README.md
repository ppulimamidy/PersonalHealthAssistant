# Demo Data: Research-Backed Synthetic Health Dataset

## Overview

This demo dataset represents **Sarah Chen**, a 52-year-old female office worker on a 30-day health optimization journey. The data is research-backed and mirrors real clinical patterns from published health studies.

## User Profile

**Demographics:**
- **Name:** Sarah Chen
- **Age:** 52
- **Gender:** Female
- **Height:** 165 cm (5'5")
- **Weight:** 78 kg (172 lbs) → 75.5 kg (166 lbs) by day 30
- **BMI:** 28.7 (overweight) → 27.7
- **Occupation:** Software Project Manager (sedentary desk job)
- **Activity Level:** Low (1-2x per week)

**Health Conditions:**
1. **Prediabetes** (A1C 6.2%, Fasting Glucose 118 mg/dL)
2. **Essential Hypertension** (controlled on Lisinopril)
3. **Hypothyroidism** (Hashimoto's, on Levothyroxine)
4. **Mild Generalized Anxiety Disorder**

**Medications:**
- Metformin 500mg BID (for prediabetes)
- Lisinopril 10mg QD (for hypertension)
- Levothyroxine 75mcg QD (for hypothyroidism)

**Supplements:**
- Vitamin D3 2000 IU
- Omega-3 Fish Oil 1000mg
- Magnesium Glycinate 400mg

## Data Story Arc

### Week 1-2: Poor Management
- High refined carb intake (bagels, pasta, pizza, takeout)
- Inconsistent medication adherence (60-70%)
- Frequent symptoms: fatigue, digestive issues, headaches
- High stress levels (7-8/10)
- Poor energy (2-4/10)

**Key Pattern:** High-carb meals → energy crashes → afternoon fatigue

### Week 3: Intervention Begins
- User reviews tracking data, notices patterns
- Switches to low-glycemic, Mediterranean-style diet
- Improves medication adherence (90%+)
- Symptoms begin to decrease
- Energy improves (6-7/10)

**Key Pattern:** Protein + fiber + healthy fats → stable blood sugar → sustained energy

### Week 4: Sustained Improvement
- Consistent healthy eating
- Excellent medication adherence (95%+)
- Minimal symptoms
- High energy (8-9/10)
- Lost 2.5 kg (5 lbs)
- Better sleep quality

**Key Pattern:** Lifestyle changes → measurable improvements → positive reinforcement

## Data Correlations (What the AI Should Detect)

### Strong Correlations (r > 0.6, p < 0.05)

1. **Nutrition → Energy:**
   - High refined carbs (>100g) → fatigue within 2-3 hours (r = 0.72)
   - High protein breakfast (>25g) → sustained energy (r = -0.68 with fatigue)
   - High sugar meals (>30g) → energy crash (r = 0.71)

2. **Nutrition → Symptoms:**
   - High sodium (>1500mg) → headaches next day (r = 0.64)
   - High fat/heavy dinners → digestive discomfort (r = 0.58)
   - Late dinners (after 8pm) → poor sleep quality (r = 0.61)

3. **Medication Adherence → Symptoms:**
   - Missed levothyroxine → fatigue + brain fog (r = 0.69)
   - Missed metformin → next-day energy crashes (r = 0.54)
   - Consistent adherence → reduced symptoms (r = -0.71)

4. **Multi-Factor Patterns:**
   - Stress + High-Carb Lunch + Missed Meds → Severe Afternoon Fatigue
   - Late Heavy Dinner + Missed Magnesium → Poor Sleep → Morning Fatigue
   - Skipped Breakfast + Work Stress → Headache + Anxiety

### Moderate Correlations (r = 0.4-0.6, p < 0.05)

- Fiber intake → improved digestion (r = -0.52 with bloating)
- Omega-3 supplementation → reduced inflammation markers (r = -0.48)
- Magnesium → better sleep quality (r = 0.46)
- Stress level → digestive symptoms (r = 0.51)

## Expected AI Insights

The specialist agents should detect:

### Sleep Agent
- Late/heavy dinners impacting sleep quality
- Poor sleep → elevated resting heart rate
- Magnesium supplementation correlation with sleep improvement

### Nutrition Agent
- Clear glycemic load impact on energy levels
- Sodium sensitivity (bloating, headaches)
- Fiber benefits for digestion and satiety
- Protein importance for sustained energy

### Metabolic Agent
- Insulin resistance patterns (high-carb → crashes)
- Likely improved A1C with dietary changes
- Weight loss trend (5 lbs in 30 days = safe 1-1.5 lbs/week)
- Metformin efficacy with consistent use

### Cardiovascular Agent
- Sodium sensitivity affecting blood pressure
- Stress correlation with heart rate
- Likely BP improvement with reduced sodium intake

### Mental Health Agent
- Stress-symptom correlations
- Anxiety triggers (caffeine, work deadlines)
- Improved mood with lifestyle changes
- Blood sugar stability → mood stability

### Integration Agent (Primary Diagnosis)
**HIGH CONFIDENCE DIAGNOSIS:**

**Primary:** Metabolic Dysregulation with Insulin Resistance
- **Causal Chain:** Refined Carbs → Blood Sugar Spikes → Insulin Spikes → Energy Crashes → Poor Food Choices → Weight Gain → Worsening Insulin Resistance
- **Systems Involved:** Metabolic, Cardiovascular, Endocrine, Digestive

**Secondary Diagnoses:**
1. **Stress-Induced Sympathetic Overactivation** → Affects: Cardiovascular, Mental Health, Digestive
2. **Circadian Disruption** (late eating, inconsistent sleep) → Affects: Sleep, Metabolic, Endocrine

**Cross-System Patterns:**
- **Feedback Loop:** Poor Sleep ↔ Elevated Cortisol ↔ Increased Appetite ↔ Carb Cravings ↔ Blood Sugar Instability ↔ Poor Sleep
- **Synergistic Effect:** Consistent Medication + Low-Glycemic Diet + Stress Management = Rapid Improvement

**Recommended Protocol (Prioritized):**
1. **[CRITICAL]** Maintain low-glycemic Mediterranean diet (impact: 90%, evidence: strong)
2. **[HIGH]** Consistent medication adherence (impact: 85%, evidence: strong)
3. **[HIGH]** Earlier, lighter dinners (impact: 70%, evidence: moderate)
4. **[MEDIUM]** Magnesium supplementation for sleep/stress (impact: 60%, evidence: moderate)
5. **[MEDIUM]** Stress management techniques (impact: 65%, evidence: moderate)

## Installation Instructions

### Step 1: Create Demo User

First, create the demo user in your authentication system (Supabase Auth):

1. Go to Supabase Dashboard → Authentication → Users
2. Click "Add user" → "Create new user"
3. Email: `sarah.chen.demo@example.com`
4. Password: `Demo123!@#`
5. After creation, copy the user's UUID from the users table

### Step 2: Generate SQL Files with Actual UUID

Use the provided bash script to automatically replace the placeholder UUID:

```bash
# Run the loader script with your actual user UUID
./load_demo_data.sh YOUR-ACTUAL-UUID-HERE

# Example:
./load_demo_data.sh 22144dc2-f352-48aa-b34b-aebfa9f7e638
```

This will create processed SQL files in the `sarah/` directory with your actual UUID.

### Step 3: Load Data in Order

Execute the SQL files in the Supabase SQL Editor in this order:

1. **sarah/demo_data_seed.sql** - User profile, conditions, medications, adherence logs
2. **sarah/demo_data_seed_part2.sql** - Nutrition meals (30 days)
3. **sarah/demo_data_seed_symptoms.sql** - Symptom journal (30 days)

Copy and paste each file's contents into the Supabase SQL Editor and run sequentially.

### Step 4: Verify Data

```sql
-- Check data loaded correctly
SELECT COUNT(*) FROM health_conditions WHERE user_id = 'YOUR-USER-ID';  -- Should be 4
SELECT COUNT(*) FROM medications WHERE user_id = 'YOUR-USER-ID';  -- Should be 3
SELECT COUNT(*) FROM supplements WHERE user_id = 'YOUR-USER-ID';  -- Should be 3
SELECT COUNT(*) FROM medication_adherence_logs WHERE user_id = 'YOUR-USER-ID';  -- Should be ~180
SELECT COUNT(*) FROM nutrition_meals WHERE user_id = 'YOUR-USER-ID';  -- Should be ~90
SELECT COUNT(*) FROM symptom_journal WHERE user_id = 'YOUR-USER-ID';  -- Should be ~30
SELECT COUNT(*) FROM lab_results WHERE user_id = 'YOUR-USER-ID';  -- Should be ~15
```

### Step 5: Login and Explore

1. Login as sarah.chen.demo@example.com
2. Navigate to different sections:
   - **Medications** - See 3 meds + 3 supplements with adherence tracking
   - **Symptom Journal** - View 30 days of symptoms showing improvement
   - **Nutrition** - See meal logs from poor → improved diet
   - **Correlations** - Run correlation analysis to see patterns
   - **Meta-Analysis** - Generate comprehensive specialist agent report
   - **Lab Results** - View baseline labs from 45 days ago

## Expected Product Demonstrations

### 1. Medication Intelligence
- **Drug-Nutrient Interaction Alerts:**
  - Levothyroxine + Calcium (if taken within 4 hours)
  - Metformin + B12 depletion warning

- **Medication Timing Correlations:**
  - Missed levothyroxine → elevated fatigue scores
  - Metformin with meals → reduced GI side effects

### 2. Symptom Correlations
- **Food Triggers:**
  - High-carb meals → fatigue (r = 0.72, p < 0.001)
  - High-sodium → headaches (r = 0.64, p < 0.01)

- **Trigger Patterns:**
  - "Refined Carbs → Energy Crash" (confidence 85%)
  - "Late Heavy Dinner → Poor Sleep" (confidence 78%)

### 3. Nutrition Correlations (with Oura if available)
- High-sugar dinners → elevated resting HR overnight
- Protein-rich breakfasts → better HRV recovery
- Late meals → reduced sleep efficiency

### 4. Specialist Multi-Agent System
- **Sleep Agent:** Identifies late eating pattern affecting sleep
- **Nutrition Agent:** Recommends Mediterranean diet, more fiber
- **Metabolic Agent:** Flags insulin resistance patterns
- **Cardiovascular Agent:** Notes sodium sensitivity
- **Mental Health Agent:** Links stress to symptoms
- **Integration Agent:** Synthesizes into primary diagnosis with protocol

### 5. Predictive Insights
- **Projected A1C:** 6.2% → ~5.9% if trends continue
- **Weight Trend:** Predicts reaching 74kg (163 lbs) in next 30 days
- **Symptom Forecast:** Continued reduction with adherence

## Clinical Validity

This dataset mirrors patterns from:

1. **Glycemic Response Studies:**
   - Jenkins et al. (1981) - Glycemic Index concept
   - Ludwig (2002) - Refined carbs and energy fluctuations

2. **Medication Adherence:**
   - Osterberg & Blaschke (2005) - Adherence and patient outcomes
   - ~65-70% typical adherence → 90%+ with tracking

3. **Lifestyle Interventions:**
   - Diabetes Prevention Program (DPP, 2002) - 5-7% weight loss, 58% diabetes risk reduction
   - PREDIMED (2013) - Mediterranean diet cardiovascular benefits
   - Estruch et al. (2018) - Med diet and metabolic syndrome

4. **Symptom Patterns:**
   - Realistic correlation strengths (r = 0.4-0.7)
   - Clinically meaningful effect sizes
   - Multi-factorial causation (stress + diet + sleep)

## Notes for Demo

- **User should start logged in as Sarah Chen**
- **Timeline shows 30 days of data** (nutrition, symptoms, meds)
- **Oura data excluded** - can be added from sandbox if needed
- **Correlations should run on 30-day window** to capture full pattern
- **Meta-analysis will take 30-60 seconds** (calling all specialist agents)
- **Expected insights documented above** - use for validation

## Cleanup & Reloading

To remove demo data and reload fresh (useful for testing):

### Step 1: Generate Cleanup SQL

```bash
# Run the cleanup script with the demo user's UUID
./cleanup_demo_data.sh YOUR-USER-UUID

# Example:
./cleanup_demo_data.sh 22144dc2-f352-48aa-b34b-aebfa9f7e638
```

This generates `sarah/cleanup_demo_data.sql` with your actual UUID.

### Step 2: Run Cleanup in Supabase

1. Copy the contents of `sarah/cleanup_demo_data.sql`
2. Paste into Supabase SQL Editor
3. Run the script
4. Verify all record counts show 0

### Step 3: Reload Fresh Data (Optional)

After cleanup, you can reload fresh demo data:

```bash
./load_demo_data.sh YOUR-USER-UUID
```

Then repeat Step 3 from Installation Instructions to load the three SQL files.

**Note:** The cleanup script does NOT delete the user from `auth.users`. If you want to completely remove the demo user, delete it manually from Supabase Auth UI.

---

**Questions or Issues?**
- Verify user_id replacement in all SQL files
- Check RLS policies allow user to see own data
- Ensure migrations 001-011 have been run
- Confirm Supabase connection is working
