"""
Pre-built Journey Templates per Condition/Goal

Each template provides a starting structure that the specialist agent
personalizes based on the user's actual data and health profile.
"""

from typing import Any, Dict, List

JOURNEY_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # ── PCOS ─────────────────────────────────────────────────────────────────
    "pcos": {
        "title": "PCOS Management",
        "goal_type": "condition_management",
        "duration_type": "cycle_based",
        "specialist": "endocrinologist",
        "target_metrics": [
            "cycle_length",
            "weight",
            "glucose_avg",
            "hrv_balance",
            "acne_severity",
            "mood_score",
        ],
        "phases": [
            {
                "name": "Baseline Observation",
                "description": "Track one full menstrual cycle without changes to establish your personal baseline.",
                "phase_type": "observation",
                "duration_days_estimate": 35,
                "duration_type": "cycle_based",
                "tracked_metrics": [
                    "cycle_length",
                    "weight",
                    "glucose_avg",
                    "mood_score",
                    "acne_severity",
                    "hrv_balance",
                ],
            },
            {
                "name": "Anti-Inflammatory Nutrition",
                "description": "Reduce refined carbs and add omega-3 rich foods. Track impact over one full cycle.",
                "phase_type": "intervention",
                "duration_days_estimate": 35,
                "duration_type": "cycle_based",
                "experiment": {
                    "title": "Anti-inflammatory diet for PCOS",
                    "description": "Cut refined carbs, add 2g omega-3 daily, increase leafy greens. Add inositol if tolerated.",
                    "recommendation_pattern": "inflammation",
                },
                "tracked_metrics": [
                    "cycle_length",
                    "weight",
                    "glucose_avg",
                    "mood_score",
                    "acne_severity",
                ],
            },
            {
                "name": "Add Strength Training",
                "description": "Add 3x/week strength training while continuing anti-inflammatory diet.",
                "phase_type": "intervention",
                "duration_days_estimate": 35,
                "duration_type": "cycle_based",
                "experiment": {
                    "title": "Strength training for PCOS",
                    "description": "3x/week resistance training (compound movements). Continue anti-inflammatory nutrition.",
                    "recommendation_pattern": "poor_recovery",
                },
                "tracked_metrics": [
                    "cycle_length",
                    "weight",
                    "hrv_balance",
                    "readiness_score",
                ],
            },
            {
                "name": "Lab Checkpoint",
                "description": "Time for follow-up labs: fasting insulin, testosterone, SHBG, AMH, DHEA-S.",
                "phase_type": "checkpoint",
                "duration_days_estimate": 14,
                "duration_type": "until_lab",
                "checkpoints": [
                    {
                        "action": "Order labs: fasting insulin, testosterone, SHBG, AMH, DHEA-S",
                        "type": "lab_reminder",
                    }
                ],
                "tracked_metrics": ["fasting_insulin", "testosterone", "shbg"],
            },
        ],
    },
    # ── Type 2 Diabetes ──────────────────────────────────────────────────────
    "type_2_diabetes": {
        "title": "Glucose Optimization",
        "goal_type": "condition_management",
        "duration_type": "week_based",
        "specialist": "diabetologist",
        "target_metrics": [
            "glucose_fasting",
            "glucose_variability",
            "time_in_range",
            "weight",
            "hrv_balance",
        ],
        "phases": [
            {
                "name": "Glucose Baseline",
                "description": "2 weeks of normal eating with glucose monitoring to identify your personal response patterns.",
                "phase_type": "observation",
                "duration_days_estimate": 14,
                "tracked_metrics": [
                    "glucose_fasting",
                    "glucose_postprandial",
                    "glucose_variability",
                ],
            },
            {
                "name": "Food Swap Experiments",
                "description": "Replace your top 3 glucose-spiking foods with lower-GI alternatives.",
                "phase_type": "intervention",
                "duration_days_estimate": 14,
                "experiment": {
                    "title": "Low-GI food swaps",
                    "description": "Replace high-spike foods with pre-identified alternatives. Track glucose response.",
                    "recommendation_pattern": "inflammation",
                },
                "tracked_metrics": [
                    "glucose_fasting",
                    "glucose_variability",
                    "time_in_range",
                ],
            },
            {
                "name": "Post-Meal Activity",
                "description": "Add 15-minute walks after meals to test impact on postprandial glucose.",
                "phase_type": "intervention",
                "duration_days_estimate": 14,
                "experiment": {
                    "title": "Post-meal walking",
                    "description": "15-minute walk within 30 minutes of finishing each meal. Track glucose response.",
                    "recommendation_pattern": "poor_recovery",
                },
                "tracked_metrics": ["glucose_postprandial", "steps", "time_in_range"],
            },
            {
                "name": "A1C Check",
                "description": "Time for A1C recheck to measure overall glucose control improvement.",
                "phase_type": "checkpoint",
                "duration_days_estimate": 7,
                "duration_type": "until_lab",
                "checkpoints": [
                    {"action": "Order A1C lab test", "type": "lab_reminder"}
                ],
                "tracked_metrics": ["a1c"],
            },
        ],
    },
    # ── Weight Loss ──────────────────────────────────────────────────────────
    "weight_loss": {
        "title": "Sustainable Weight Management",
        "goal_type": "weight_loss",
        "duration_type": "week_based",
        "specialist": "metabolic_coach",
        "target_metrics": [
            "weight",
            "active_calories",
            "steps",
            "sleep_score",
            "protein_g",
        ],
        "phases": [
            {
                "name": "Metabolic Baseline",
                "description": "2 weeks of normal eating with careful tracking to estimate your TDEE.",
                "phase_type": "observation",
                "duration_days_estimate": 14,
                "tracked_metrics": ["weight", "total_calories", "steps", "sleep_score"],
            },
            {
                "name": "Moderate Deficit",
                "description": "300-calorie daily deficit with high protein. Track weekly weight average.",
                "phase_type": "intervention",
                "duration_days_estimate": 28,
                "experiment": {
                    "title": "Moderate caloric deficit",
                    "description": "Reduce daily intake by ~300 calories. Maintain protein at 1.6g/kg. Track 7-day rolling weight average.",
                    "recommendation_pattern": "overtraining",
                },
                "tracked_metrics": [
                    "weight",
                    "total_calories",
                    "protein_g",
                    "sleep_score",
                ],
            },
            {
                "name": "Add Structured Exercise",
                "description": "Add 3x/week strength training + daily walking to preserve lean mass.",
                "phase_type": "intervention",
                "duration_days_estimate": 28,
                "experiment": {
                    "title": "Exercise + deficit",
                    "description": "Continue caloric deficit. Add 3x/week strength training and 8000 daily steps target.",
                    "recommendation_pattern": "poor_recovery",
                },
                "tracked_metrics": [
                    "weight",
                    "steps",
                    "workout_minutes",
                    "hrv_balance",
                ],
            },
        ],
    },
    # ── Perimenopause ────────────────────────────────────────────────────────
    "perimenopause": {
        "title": "Perimenopause Wellness",
        "goal_type": "hormone_optimization",
        "duration_type": "week_based",
        "specialist": "womens_health",
        "target_metrics": [
            "sleep_score",
            "hrv_balance",
            "hot_flash_count",
            "mood_score",
            "weight",
        ],
        "phases": [
            {
                "name": "Symptom Mapping",
                "description": "4 weeks tracking symptoms without intervention. Identify your personal pattern.",
                "phase_type": "observation",
                "duration_days_estimate": 28,
                "tracked_metrics": [
                    "sleep_score",
                    "hot_flash_count",
                    "night_sweat_count",
                    "mood_score",
                    "hrv_balance",
                ],
            },
            {
                "name": "Sleep + Cooling Protocol",
                "description": "Optimize sleep environment and add magnesium glycinate before bed.",
                "phase_type": "intervention",
                "duration_days_estimate": 28,
                "experiment": {
                    "title": "Sleep optimization for perimenopause",
                    "description": "Cool bedroom to 65°F, magnesium glycinate 400mg before bed, no screens 1hr before sleep.",
                    "recommendation_pattern": "sleep_disruption",
                },
                "tracked_metrics": [
                    "sleep_score",
                    "sleep_efficiency",
                    "hot_flash_count",
                    "night_sweat_count",
                ],
            },
            {
                "name": "HRT Discussion Prep",
                "description": "Generate a comprehensive report of your 8+ weeks of data for your OB/GYN.",
                "phase_type": "checkpoint",
                "duration_days_estimate": 7,
                "duration_type": "manual",
                "checkpoints": [
                    {
                        "action": "Generate Visit Prep report for OB/GYN with perimenopause data",
                        "type": "visit_prep",
                    }
                ],
                "tracked_metrics": [],
            },
        ],
    },
    # ── Cardiac Rehab ────────────────────────────────────────────────────────
    "cardiac_rehab": {
        "title": "Cardiac Recovery Journey",
        "goal_type": "cardiac_rehab",
        "duration_type": "milestone_based",
        "specialist": "cardiologist",
        "target_metrics": [
            "resting_heart_rate",
            "hrv_balance",
            "steps",
            "blood_pressure_systolic",
            "spo2",
        ],
        "phases": [
            {
                "name": "Gentle Recovery",
                "description": "4 weeks of gentle activity with careful monitoring. Daily 10-min slow walks.",
                "phase_type": "intervention",
                "duration_days_estimate": 28,
                "experiment": {
                    "title": "Gentle walking recovery",
                    "description": "Daily 10-minute slow walks. Monitor HR (stay below prescribed limit). Track symptoms.",
                    "recommendation_pattern": "poor_recovery",
                },
                "tracked_metrics": [
                    "resting_heart_rate",
                    "steps",
                    "hrv_balance",
                    "spo2",
                ],
            },
            {
                "name": "Progressive Activity",
                "description": "Increase to 20-min walks, add light resistance exercises.",
                "phase_type": "intervention",
                "duration_days_estimate": 28,
                "experiment": {
                    "title": "Progressive cardiac rehab",
                    "description": "20-minute walks + light resistance bands. Monitor exercise tolerance and recovery.",
                    "recommendation_pattern": "overtraining",
                },
                "tracked_metrics": [
                    "resting_heart_rate",
                    "steps",
                    "hrv_balance",
                    "readiness_score",
                ],
            },
            {
                "name": "Lifestyle Consolidation",
                "description": "Mediterranean diet emphasis + continued exercise. Track lipid panel.",
                "phase_type": "intervention",
                "duration_days_estimate": 28,
                "experiment": {
                    "title": "Mediterranean diet + exercise",
                    "description": "Mediterranean diet pattern (olive oil, fish, vegetables). Continue walking + resistance.",
                    "recommendation_pattern": "inflammation",
                },
                "tracked_metrics": ["resting_heart_rate", "weight", "hrv_balance"],
            },
            {
                "name": "Cardiac Panel Check",
                "description": "Time for follow-up cardiac labs.",
                "phase_type": "checkpoint",
                "duration_days_estimate": 7,
                "duration_type": "until_lab",
                "checkpoints": [
                    {
                        "action": "Order lipid panel + cardiac markers",
                        "type": "lab_reminder",
                    }
                ],
                "tracked_metrics": ["ldl", "hdl", "triglycerides", "crp"],
            },
        ],
    },
    # ── IBS ───────────────────────────────────────────────────────────────────
    "ibs": {
        "title": "IBS Trigger Identification",
        "goal_type": "gut_health",
        "duration_type": "week_based",
        "specialist": "gi_specialist",
        "target_metrics": [
            "bloating_score",
            "abdominal_pain",
            "stool_type",
            "sleep_score",
        ],
        "phases": [
            {
                "name": "Symptom Baseline",
                "description": "2 weeks of detailed food-symptom logging without dietary changes.",
                "phase_type": "observation",
                "duration_days_estimate": 14,
                "tracked_metrics": [
                    "bloating_score",
                    "abdominal_pain",
                    "stool_type",
                    "meal_log",
                ],
            },
            {
                "name": "Low-FODMAP Elimination",
                "description": "Strict low-FODMAP diet for 4 weeks to reduce symptoms.",
                "phase_type": "intervention",
                "duration_days_estimate": 28,
                "experiment": {
                    "title": "Low-FODMAP elimination",
                    "description": "Follow strict low-FODMAP diet. Eliminate: wheat, onion, garlic, legumes, dairy, stone fruits, honey.",
                    "recommendation_pattern": "inflammation",
                },
                "tracked_metrics": ["bloating_score", "abdominal_pain", "stool_type"],
            },
            {
                "name": "Systematic Reintroduction",
                "description": "Reintroduce one FODMAP group every 3 days to identify personal triggers.",
                "phase_type": "intervention",
                "duration_days_estimate": 42,
                "experiment": {
                    "title": "FODMAP reintroduction",
                    "description": "Reintroduce one FODMAP group every 3 days: fructans, GOS, lactose, fructose, sorbitol, mannitol.",
                    "recommendation_pattern": "inflammation",
                },
                "tracked_metrics": [
                    "bloating_score",
                    "abdominal_pain",
                    "stool_type",
                    "trigger_food",
                ],
            },
        ],
    },
    # ── Sleep Optimization ───────────────────────────────────────────────────
    "sleep_optimization": {
        "title": "Sleep Optimization Program",
        "goal_type": "sleep_optimization",
        "duration_type": "week_based",
        "specialist": "sleep_specialist",
        "target_metrics": [
            "sleep_score",
            "sleep_efficiency",
            "deep_sleep_hours",
            "hrv_balance",
        ],
        "phases": [
            {
                "name": "Sleep Audit",
                "description": "1 week tracking sleep habits, caffeine, screens, and timing.",
                "phase_type": "observation",
                "duration_days_estimate": 7,
                "tracked_metrics": [
                    "sleep_score",
                    "sleep_efficiency",
                    "deep_sleep_hours",
                    "caffeine_intake",
                    "screen_time",
                ],
            },
            {
                "name": "Sleep Hygiene Protocol",
                "description": "Consistent wake time, no caffeine after 2pm, no screens 1hr before bed.",
                "phase_type": "intervention",
                "duration_days_estimate": 14,
                "experiment": {
                    "title": "Core sleep hygiene",
                    "description": "Fixed wake time (±30min), no caffeine after 2pm, no screens 60min before bed, cool dark room.",
                    "recommendation_pattern": "sleep_disruption",
                },
                "tracked_metrics": [
                    "sleep_score",
                    "sleep_efficiency",
                    "deep_sleep_hours",
                ],
            },
            {
                "name": "Nutrition for Sleep",
                "description": "Add sleep-supporting foods and optimal meal timing.",
                "phase_type": "intervention",
                "duration_days_estimate": 14,
                "experiment": {
                    "title": "Sleep nutrition optimization",
                    "description": "No heavy meals after 7pm. Add: kiwi, almonds, chamomile tea. Magnesium glycinate 400mg before bed.",
                    "recommendation_pattern": "sleep_disruption",
                },
                "tracked_metrics": ["sleep_score", "sleep_efficiency", "hrv_balance"],
            },
        ],
    },
    # ── Muscle Building ──────────────────────────────────────────────────────
    "muscle_building": {
        "title": "Muscle Building Program",
        "goal_type": "muscle_building",
        "duration_type": "week_based",
        "specialist": "exercise_physiologist",
        "target_metrics": [
            "weight",
            "workout_minutes",
            "protein_g",
            "hrv_balance",
            "sleep_score",
        ],
        "phases": [
            {
                "name": "Training Baseline",
                "description": "2 weeks establishing training baseline and recovery capacity.",
                "phase_type": "observation",
                "duration_days_estimate": 14,
                "tracked_metrics": [
                    "workout_minutes",
                    "steps",
                    "protein_g",
                    "sleep_score",
                    "hrv_balance",
                ],
            },
            {
                "name": "Progressive Overload",
                "description": "Structured strength program with progressive overload. Caloric surplus.",
                "phase_type": "intervention",
                "duration_days_estimate": 42,
                "experiment": {
                    "title": "Strength + surplus",
                    "description": "4x/week compound lifts. 200-300 cal surplus. Protein 2g/kg. Track recovery via HRV.",
                    "recommendation_pattern": "overtraining",
                },
                "tracked_metrics": [
                    "weight",
                    "workout_minutes",
                    "protein_g",
                    "hrv_balance",
                    "readiness_score",
                ],
            },
            {
                "name": "Deload + Assessment",
                "description": "1 week deload to assess recovery and measure progress.",
                "phase_type": "observation",
                "duration_days_estimate": 7,
                "tracked_metrics": [
                    "weight",
                    "hrv_balance",
                    "readiness_score",
                    "sleep_score",
                ],
            },
        ],
    },
    # ── Mental Health ────────────────────────────────────────────────────────
    "mental_health": {
        "title": "Mental Wellness Program",
        "goal_type": "mental_health",
        "duration_type": "week_based",
        "specialist": "behavioral_health",
        "target_metrics": ["mood_score", "sleep_score", "hrv_balance", "steps"],
        "phases": [
            {
                "name": "Mood-Body Mapping",
                "description": "2 weeks tracking mood alongside physical metrics to find connections.",
                "phase_type": "observation",
                "duration_days_estimate": 14,
                "tracked_metrics": [
                    "mood_score",
                    "anxiety_level",
                    "sleep_score",
                    "hrv_balance",
                    "steps",
                ],
            },
            {
                "name": "Exercise for Mood",
                "description": "30-minute daily movement (walk, yoga, or any enjoyable activity).",
                "phase_type": "intervention",
                "duration_days_estimate": 21,
                "experiment": {
                    "title": "Daily movement for mood",
                    "description": "30 minutes of enjoyable movement daily. Walk, yoga, dance — whatever feels good. Track mood before and after.",
                    "recommendation_pattern": "poor_recovery",
                },
                "tracked_metrics": [
                    "mood_score",
                    "steps",
                    "hrv_balance",
                    "sleep_score",
                ],
            },
            {
                "name": "Sleep + Social",
                "description": "Optimize sleep schedule and add one social activity per week.",
                "phase_type": "intervention",
                "duration_days_estimate": 21,
                "experiment": {
                    "title": "Sleep + social connection",
                    "description": "Fixed sleep schedule (±30min). One planned social activity per week. Continue daily movement.",
                    "recommendation_pattern": "sleep_disruption",
                },
                "tracked_metrics": ["mood_score", "sleep_score", "hrv_balance"],
            },
        ],
    },
}


def get_template(condition_or_goal: str) -> Dict[str, Any] | None:
    """Look up a journey template by condition name or goal type."""
    key = (
        condition_or_goal.lower()
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("'", "")
    )
    return JOURNEY_TEMPLATES.get(key)


def list_available_templates() -> list[dict[str, str]]:
    """List all available journey templates with basic info."""
    return [
        {
            "key": k,
            "title": v["title"],
            "goal_type": v["goal_type"],
            "specialist": v["specialist"],
            "phases": str(len(v["phases"])),
        }
        for k, v in JOURNEY_TEMPLATES.items()
    ]
