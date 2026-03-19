"""
Specialist Onboarding Conversation — Day 1-7 proactive questions

Instead of a form, the specialist agent collects remaining profile data
through contextual nudges over the first 7 days. Each question maps to a
user_health_profile field and skips automatically if the data already exists.
"""

from typing import Any, Dict, List, Optional

# Each entry: day to ask, nudge title/body, data_field to check, skip condition
QuestionSchedule = Dict[str, Any]

SPECIALIST_ONBOARDING: Dict[str, List[QuestionSchedule]] = {
    "endocrinologist": [
        {
            "day": 1,
            "nudge_type": "experiment_morning",
            "title": "Your Endocrinologist has a question",
            "body": "What medications or supplements are you currently taking? This helps personalize your plan.",
            "data_field": "medications",
            "check_table": "medications",
            "check_query": "user_id=eq.{user_id}&is_active=eq.true&limit=1",
        },
        {
            "day": 2,
            "nudge_type": "experiment_morning",
            "title": "Quick question from your specialist",
            "body": "When was the first day of your last period? This helps align experiments to your cycle.",
            "data_field": "cycle_start",
            "check_table": "cycle_logs",
            "check_query": "user_id=eq.{user_id}&event_type=eq.period_start&limit=1",
        },
        {
            "day": 3,
            "nudge_type": "experiment_morning",
            "title": "Sleep matters for your condition",
            "body": "How would you rate your sleep quality lately? (Open the app to answer)",
            "data_field": "sleep_quality",
            "check_table": None,
        },
        {
            "day": 5,
            "nudge_type": "experiment_morning",
            "title": "Lab results help set your baseline",
            "body": "Do you have any recent lab results? Even from months ago — tap to add them.",
            "data_field": "labs",
            "check_table": "lab_results",
            "check_query": "user_id=eq.{user_id}&limit=1",
        },
    ],
    "diabetologist": [
        {
            "day": 1,
            "nudge_type": "experiment_morning",
            "title": "Your Diabetologist needs this",
            "body": "What diabetes medications are you taking, and at what doses? This is critical for safe recommendations.",
            "data_field": "medications",
            "check_table": "medications",
            "check_query": "user_id=eq.{user_id}&is_active=eq.true&limit=1",
        },
        {
            "day": 2,
            "nudge_type": "experiment_morning",
            "title": "CGM data helps tremendously",
            "body": "Do you use a continuous glucose monitor? If so, connect it from Profile → Devices.",
            "data_field": "cgm_device",
            "check_table": None,
        },
        {
            "day": 3,
            "nudge_type": "experiment_morning",
            "title": "A1C helps track your progress",
            "body": "What was your most recent A1C? Tap to add it to your lab results.",
            "data_field": "a1c",
            "check_table": "lab_results",
            "check_query": "user_id=eq.{user_id}&limit=1",
        },
        {
            "day": 5,
            "nudge_type": "experiment_morning",
            "title": "Dietary patterns matter for glucose",
            "body": "Do you follow any specific dietary pattern? Log a meal to start tracking nutrition-glucose connections.",
            "data_field": "dietary",
            "check_table": None,
        },
    ],
    "metabolic_coach": [
        {
            "day": 1,
            "nudge_type": "experiment_morning",
            "title": "Nutrition is key for your goal",
            "body": "Log your first meal today — this helps your Metabolic Coach analyze your nutrition patterns.",
            "data_field": "meals",
            "check_table": "meal_entries",
            "check_query": "user_id=eq.{user_id}&limit=1",
        },
        {
            "day": 3,
            "nudge_type": "experiment_morning",
            "title": "Exercise tracking helps too",
            "body": "How often do you exercise? Connect your wearable to auto-track workouts.",
            "data_field": "exercise",
            "check_table": None,
        },
        {
            "day": 5,
            "nudge_type": "experiment_morning",
            "title": "Any supplements?",
            "body": "Are you taking any supplements? Protein powder, creatine, vitamins — add them to your profile.",
            "data_field": "supplements",
            "check_table": None,
        },
    ],
    "cardiologist": [
        {
            "day": 1,
            "nudge_type": "experiment_morning",
            "title": "Your Cardiologist needs medication info",
            "body": "What cardiac medications are you on? This is essential for safe monitoring.",
            "data_field": "medications",
            "check_table": "medications",
            "check_query": "user_id=eq.{user_id}&is_active=eq.true&limit=1",
        },
        {
            "day": 2,
            "nudge_type": "experiment_morning",
            "title": "Blood pressure tracking",
            "body": "Do you check your BP at home? Log a reading to start tracking trends.",
            "data_field": "bp",
            "check_table": None,
        },
        {
            "day": 4,
            "nudge_type": "experiment_morning",
            "title": "Recent labs?",
            "body": "Add your latest lipid panel or cardiac labs to set your baseline.",
            "data_field": "labs",
            "check_table": "lab_results",
            "check_query": "user_id=eq.{user_id}&limit=1",
        },
    ],
    "gi_specialist": [
        {
            "day": 1,
            "nudge_type": "experiment_morning",
            "title": "Food logging is critical for your GI plan",
            "body": "Log every meal today — your GI Specialist needs food data to identify triggers.",
            "data_field": "meals",
            "check_table": "meal_entries",
            "check_query": "user_id=eq.{user_id}&limit=1",
        },
        {
            "day": 2,
            "nudge_type": "experiment_morning",
            "title": "Track your symptoms",
            "body": "Log any digestive symptoms today (bloating, pain, etc.) — this builds your trigger map.",
            "data_field": "symptoms",
            "check_table": "symptom_entries",
            "check_query": "user_id=eq.{user_id}&limit=1",
        },
        {
            "day": 4,
            "nudge_type": "experiment_morning",
            "title": "Any GI medications?",
            "body": "Are you taking anything for your gut health? Add medications and supplements to your profile.",
            "data_field": "medications",
            "check_table": "medications",
            "check_query": "user_id=eq.{user_id}&is_active=eq.true&limit=1",
        },
    ],
    "womens_health": [
        {
            "day": 1,
            "nudge_type": "experiment_morning",
            "title": "Cycle tracking helps your specialist",
            "body": "When did your last period start? Log it so your Women's Health specialist can align insights to your cycle.",
            "data_field": "cycle",
            "check_table": "cycle_logs",
            "check_query": "user_id=eq.{user_id}&event_type=eq.period_start&limit=1",
        },
        {
            "day": 2,
            "nudge_type": "experiment_morning",
            "title": "Track your symptoms by phase",
            "body": "Log any symptoms today — your specialist will correlate them with your cycle phase.",
            "data_field": "symptoms",
            "check_table": "symptom_entries",
            "check_query": "user_id=eq.{user_id}&limit=1",
        },
        {
            "day": 4,
            "nudge_type": "experiment_morning",
            "title": "Any medications or HRT?",
            "body": "Are you on any medications or hormone therapy? Add them to your profile.",
            "data_field": "medications",
            "check_table": "medications",
            "check_query": "user_id=eq.{user_id}&is_active=eq.true&limit=1",
        },
    ],
    "sleep_specialist": [
        {
            "day": 1,
            "nudge_type": "experiment_morning",
            "title": "Connect your wearable for sleep data",
            "body": "Your Sleep Specialist needs sleep metrics. Connect your device from Profile → Devices.",
            "data_field": "device",
            "check_table": "oura_connections",
            "check_query": "user_id=eq.{user_id}&is_active=eq.true&limit=1",
        },
        {
            "day": 3,
            "nudge_type": "experiment_morning",
            "title": "Caffeine and meal timing matter",
            "body": "Log your meals today — your Sleep Specialist wants to check for late-night eating and caffeine patterns.",
            "data_field": "meals",
            "check_table": "meal_entries",
            "check_query": "user_id=eq.{user_id}&limit=1",
        },
        {
            "day": 5,
            "nudge_type": "experiment_morning",
            "title": "Any sleep aids or supplements?",
            "body": "Melatonin, magnesium, prescriptions — add them so your specialist knows what you've tried.",
            "data_field": "supplements",
            "check_table": None,
        },
    ],
    "behavioral_health": [
        {
            "day": 1,
            "nudge_type": "experiment_morning",
            "title": "Track your mood today",
            "body": "Your Behavioral Health specialist uses mood data alongside sleep and HRV to find patterns.",
            "data_field": "mood",
            "check_table": None,
        },
        {
            "day": 3,
            "nudge_type": "experiment_morning",
            "title": "Any medications?",
            "body": "Are you on any medications for anxiety, depression, or sleep? Add them to your profile.",
            "data_field": "medications",
            "check_table": "medications",
            "check_query": "user_id=eq.{user_id}&is_active=eq.true&limit=1",
        },
        {
            "day": 5,
            "nudge_type": "experiment_morning",
            "title": "Movement helps — let's track it",
            "body": "Log a walk, workout, or yoga session. Your specialist correlates activity with mood and sleep.",
            "data_field": "exercise",
            "check_table": None,
        },
    ],
    "exercise_physiologist": [
        {
            "day": 1,
            "nudge_type": "experiment_morning",
            "title": "Connect your wearable",
            "body": "Your Exercise Physiologist needs activity and recovery data. Connect from Profile → Devices.",
            "data_field": "device",
            "check_table": "oura_connections",
            "check_query": "user_id=eq.{user_id}&is_active=eq.true&limit=1",
        },
        {
            "day": 3,
            "nudge_type": "experiment_morning",
            "title": "Protein matters for your goal",
            "body": "Log your meals today — your specialist will check if you're hitting protein targets.",
            "data_field": "meals",
            "check_table": "meal_entries",
            "check_query": "user_id=eq.{user_id}&limit=1",
        },
    ],
}

# Default fallback for specialists not in the map
DEFAULT_ONBOARDING: List[QuestionSchedule] = [
    {
        "day": 1,
        "nudge_type": "experiment_morning",
        "title": "Help your specialist help you",
        "body": "Add any medications or supplements you're taking to your profile.",
        "data_field": "medications",
        "check_table": "medications",
        "check_query": "user_id=eq.{user_id}&is_active=eq.true&limit=1",
    },
    {
        "day": 3,
        "nudge_type": "experiment_morning",
        "title": "Log a meal to start nutrition tracking",
        "body": "Your specialist can find food-health connections once you start logging meals.",
        "data_field": "meals",
        "check_table": "meal_entries",
        "check_query": "user_id=eq.{user_id}&limit=1",
    },
    {
        "day": 5,
        "nudge_type": "experiment_morning",
        "title": "Any recent lab results?",
        "body": "Add labs to set your health baseline — even results from months ago are helpful.",
        "data_field": "labs",
        "check_table": "lab_results",
        "check_query": "user_id=eq.{user_id}&limit=1",
    },
]


def get_onboarding_schedule(specialist_type: str) -> List[QuestionSchedule]:
    """Get the onboarding question schedule for a specialist type."""
    return SPECIALIST_ONBOARDING.get(specialist_type, DEFAULT_ONBOARDING)
