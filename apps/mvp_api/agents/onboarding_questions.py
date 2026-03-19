"""
Quick Context Questions — tailored per condition/goal for onboarding Step 4.

Each condition/goal gets 2-3 questions that collect the minimum data needed
to personalize the first journey proposal.
"""

from typing import Any, Dict, List

QuestionDef = Dict[str, Any]

# ---------------------------------------------------------------------------
# Condition-specific questions
# ---------------------------------------------------------------------------

CONDITION_QUESTIONS: Dict[str, List[QuestionDef]] = {
    "pcos": [
        {
            "id": "medications",
            "question": "Are you currently on any medications for PCOS?",
            "input_type": "choice_then_text",
            "options": ["Yes, tell me", "No", "Skip"],
            "text_prompt": "List name and dose (e.g., Metformin 500mg)",
            "data_field": "medications",
        },
        {
            "id": "cycle_tracking",
            "question": "Do you track your menstrual cycle?",
            "input_type": "choice",
            "options": ["Yes, regularly", "Sometimes", "No"],
            "data_field": "cycle_tracking",
            "followup_if": {
                "Yes, regularly": "last_period_date",
                "Sometimes": "last_period_date",
            },
        },
        {
            "id": "dietary",
            "question": "Any dietary restrictions?",
            "input_type": "multi_choice",
            "options": [
                "Vegetarian",
                "Vegan",
                "Gluten-free",
                "Dairy-free",
                "Low-carb",
                "None",
                "Other",
            ],
            "data_field": "dietary_preferences",
        },
    ],
    "type_2_diabetes": [
        {
            "id": "medications",
            "question": "What diabetes medications are you taking?",
            "input_type": "choice_then_text",
            "options": ["Yes, tell me", "No medications", "Skip"],
            "text_prompt": "List name and dose (e.g., Metformin 1000mg, Jardiance 10mg)",
            "data_field": "medications",
        },
        {
            "id": "cgm",
            "question": "Do you use a continuous glucose monitor (CGM)?",
            "input_type": "choice",
            "options": ["Yes — Dexcom", "Yes — Libre", "Yes — other", "No"],
            "data_field": "cgm_device",
        },
        {
            "id": "a1c",
            "question": "What was your most recent A1C?",
            "input_type": "text",
            "text_prompt": "e.g., 7.2% (or 'I don't know')",
            "data_field": "last_a1c",
        },
    ],
    "hypertension": [
        {
            "id": "medications",
            "question": "Are you on blood pressure medications?",
            "input_type": "choice_then_text",
            "options": ["Yes, tell me", "No", "Skip"],
            "text_prompt": "List name and dose",
            "data_field": "medications",
        },
        {
            "id": "bp_tracking",
            "question": "Do you check your blood pressure at home?",
            "input_type": "choice",
            "options": ["Yes, regularly", "Sometimes", "No"],
            "data_field": "bp_tracking",
        },
        {
            "id": "dietary",
            "question": "Are you watching your sodium intake?",
            "input_type": "choice",
            "options": ["Yes, actively", "Trying to", "Not really"],
            "data_field": "sodium_awareness",
        },
    ],
    "ibs": [
        {
            "id": "triggers",
            "question": "Do you know any food triggers?",
            "input_type": "choice_then_text",
            "options": ["Yes, tell me", "Not sure yet", "Skip"],
            "text_prompt": "List known triggers (e.g., dairy, gluten, onions)",
            "data_field": "known_triggers",
        },
        {
            "id": "medications",
            "question": "Taking any medications or supplements for IBS?",
            "input_type": "choice_then_text",
            "options": ["Yes, tell me", "No", "Skip"],
            "text_prompt": "List name and dose",
            "data_field": "medications",
        },
        {
            "id": "fodmap",
            "question": "Have you tried a low-FODMAP diet before?",
            "input_type": "choice",
            "options": ["Yes, it helped", "Yes, didn't help", "No, never tried"],
            "data_field": "fodmap_history",
        },
    ],
    "anxiety": [
        {
            "id": "medications",
            "question": "Are you on any medications for anxiety?",
            "input_type": "choice_then_text",
            "options": ["Yes, tell me", "No", "Skip"],
            "text_prompt": "List name and dose",
            "data_field": "medications",
        },
        {
            "id": "sleep",
            "question": "How is your sleep quality?",
            "input_type": "choice",
            "options": ["Good", "Fair — sometimes poor", "Poor — regular issues"],
            "data_field": "sleep_quality",
        },
        {
            "id": "exercise",
            "question": "How often do you exercise?",
            "input_type": "choice",
            "options": ["Daily", "3-5x/week", "1-2x/week", "Rarely"],
            "data_field": "exercise_frequency",
        },
    ],
    "depression": [
        {
            "id": "medications",
            "question": "Are you on any medications for depression?",
            "input_type": "choice_then_text",
            "options": ["Yes, tell me", "No", "Skip"],
            "text_prompt": "List name and dose",
            "data_field": "medications",
        },
        {
            "id": "sleep",
            "question": "How is your sleep quality?",
            "input_type": "choice",
            "options": ["Good", "Fair", "Poor — regular issues"],
            "data_field": "sleep_quality",
        },
        {
            "id": "exercise",
            "question": "How often do you exercise?",
            "input_type": "choice",
            "options": ["Daily", "3-5x/week", "1-2x/week", "Rarely"],
            "data_field": "exercise_frequency",
        },
    ],
    "hypothyroidism": [
        {
            "id": "medications",
            "question": "Are you on thyroid medication?",
            "input_type": "choice_then_text",
            "options": ["Yes, tell me", "No", "Skip"],
            "text_prompt": "Name and dose (e.g., Levothyroxine 50mcg)",
            "data_field": "medications",
        },
        {
            "id": "labs",
            "question": "When was your last TSH test?",
            "input_type": "choice",
            "options": [
                "Within 3 months",
                "3-6 months ago",
                "Over 6 months",
                "Don't know",
            ],
            "data_field": "last_tsh_check",
        },
        {
            "id": "symptoms",
            "question": "Main symptoms you're tracking?",
            "input_type": "multi_choice",
            "options": [
                "Fatigue",
                "Weight gain",
                "Cold intolerance",
                "Brain fog",
                "Hair loss",
                "Other",
            ],
            "data_field": "primary_symptoms",
        },
    ],
    "perimenopause": [
        {
            "id": "cycle",
            "question": "How are your cycles currently?",
            "input_type": "choice",
            "options": [
                "Still regular",
                "Becoming irregular",
                "Very irregular",
                "Stopped",
            ],
            "data_field": "cycle_status",
        },
        {
            "id": "symptoms",
            "question": "Main symptoms?",
            "input_type": "multi_choice",
            "options": [
                "Hot flashes",
                "Night sweats",
                "Sleep issues",
                "Mood changes",
                "Weight gain",
                "Brain fog",
            ],
            "data_field": "primary_symptoms",
        },
        {
            "id": "hrt",
            "question": "Are you on or considering HRT?",
            "input_type": "choice",
            "options": [
                "Currently on HRT",
                "Considering it",
                "Not interested",
                "Want to learn more",
            ],
            "data_field": "hrt_status",
        },
    ],
}

# ---------------------------------------------------------------------------
# Goal-specific questions
# ---------------------------------------------------------------------------

GOAL_QUESTIONS: Dict[str, List[QuestionDef]] = {
    "weight_loss": [
        {
            "id": "weight",
            "question": "Current and goal weight?",
            "input_type": "dual_number",
            "labels": ["Current (lbs)", "Goal (lbs)"],
            "data_field": "weight_goals",
        },
        {
            "id": "exercise",
            "question": "How often do you exercise?",
            "input_type": "choice",
            "options": ["Daily", "3-5x/week", "1-2x/week", "Rarely"],
            "data_field": "exercise_frequency",
        },
        {
            "id": "dietary",
            "question": "Any foods you avoid?",
            "input_type": "multi_choice",
            "options": [
                "Vegetarian",
                "Vegan",
                "Gluten-free",
                "Dairy-free",
                "Low-carb",
                "None",
            ],
            "data_field": "dietary_preferences",
        },
    ],
    "sleep_optimization": [
        {
            "id": "challenge",
            "question": "What's your biggest sleep challenge?",
            "input_type": "choice",
            "options": [
                "Falling asleep",
                "Staying asleep",
                "Waking too early",
                "Not feeling rested",
            ],
            "data_field": "sleep_challenge",
        },
        {
            "id": "supplements",
            "question": "Do you take any sleep aids or supplements?",
            "input_type": "choice_then_text",
            "options": ["Yes, tell me", "No"],
            "text_prompt": "List name and dose (e.g., Melatonin 3mg)",
            "data_field": "supplements",
        },
        {
            "id": "bedtime",
            "question": "What time do you usually go to bed?",
            "input_type": "choice",
            "options": ["Before 10pm", "10-11pm", "11pm-12am", "After midnight"],
            "data_field": "bedtime",
        },
    ],
    "muscle_building": [
        {
            "id": "experience",
            "question": "Training experience?",
            "input_type": "choice",
            "options": [
                "Beginner (< 1 year)",
                "Intermediate (1-3 years)",
                "Advanced (3+ years)",
            ],
            "data_field": "training_experience",
        },
        {
            "id": "frequency",
            "question": "How often do you lift?",
            "input_type": "choice",
            "options": ["2-3x/week", "4-5x/week", "6+/week", "Not yet"],
            "data_field": "training_frequency",
        },
        {
            "id": "dietary",
            "question": "Any dietary restrictions?",
            "input_type": "multi_choice",
            "options": ["Vegetarian", "Vegan", "Dairy-free", "None"],
            "data_field": "dietary_preferences",
        },
    ],
    "mental_health": [
        {
            "id": "focus",
            "question": "What are you most focused on?",
            "input_type": "choice",
            "options": [
                "Reducing anxiety",
                "Improving mood",
                "Managing stress",
                "Better sleep",
                "All of the above",
            ],
            "data_field": "mental_health_focus",
        },
        {
            "id": "exercise",
            "question": "How often do you exercise?",
            "input_type": "choice",
            "options": ["Daily", "3-5x/week", "1-2x/week", "Rarely"],
            "data_field": "exercise_frequency",
        },
    ],
    "general_wellness": [],
    "cardiac_rehab": [
        {
            "id": "medications",
            "question": "What cardiac medications are you on?",
            "input_type": "choice_then_text",
            "options": ["Yes, tell me", "None currently"],
            "text_prompt": "List name and dose",
            "data_field": "medications",
        },
        {
            "id": "event",
            "question": "Recent cardiac event?",
            "input_type": "choice",
            "options": [
                "Heart attack",
                "Stent/angioplasty",
                "Bypass surgery",
                "Heart failure diagnosis",
                "Other",
            ],
            "data_field": "cardiac_event",
        },
    ],
    "gut_health": [
        {
            "id": "diagnosis",
            "question": "Do you have a specific gut diagnosis?",
            "input_type": "choice",
            "options": [
                "IBS",
                "IBD (Crohn's/UC)",
                "GERD",
                "SIBO",
                "Celiac",
                "No formal diagnosis",
            ],
            "data_field": "gut_diagnosis",
        },
        {
            "id": "triggers",
            "question": "Do you know any food triggers?",
            "input_type": "choice_then_text",
            "options": ["Yes, tell me", "Not sure yet"],
            "text_prompt": "List known triggers",
            "data_field": "known_triggers",
        },
    ],
    "hormone_optimization": [
        {
            "id": "focus",
            "question": "What's your main concern?",
            "input_type": "choice",
            "options": [
                "Low energy/fatigue",
                "Weight changes",
                "Mood/mental clarity",
                "Cycle issues",
                "Libido",
                "Other",
            ],
            "data_field": "hormone_focus",
        },
        {
            "id": "labs",
            "question": "Have you had hormone labs recently?",
            "input_type": "choice",
            "options": ["Yes, within 3 months", "Yes, older", "No"],
            "data_field": "hormone_labs_status",
        },
    ],
}

# Fallback for conditions not in the map
DEFAULT_CONDITION_QUESTIONS: List[QuestionDef] = [
    {
        "id": "medications",
        "question": "Are you on any medications for this condition?",
        "input_type": "choice_then_text",
        "options": ["Yes, tell me", "No", "Skip"],
        "text_prompt": "List name and dose",
        "data_field": "medications",
    },
    {
        "id": "dietary",
        "question": "Any dietary restrictions?",
        "input_type": "multi_choice",
        "options": ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free", "None"],
        "data_field": "dietary_preferences",
    },
]


def get_questions_for_condition(condition: str) -> List[QuestionDef]:
    """Get quick context questions for a condition."""
    key = condition.lower().strip().replace(" ", "_").replace("-", "_").replace("'", "")
    # Try direct match
    if key in CONDITION_QUESTIONS:
        return CONDITION_QUESTIONS[key]
    # Try partial match
    for k, v in CONDITION_QUESTIONS.items():
        if k in key or key in k:
            return v
    return DEFAULT_CONDITION_QUESTIONS


def get_questions_for_goal(goal: str) -> List[QuestionDef]:
    """Get quick context questions for a goal."""
    key = goal.lower().strip().replace(" ", "_").replace("-", "_")
    return GOAL_QUESTIONS.get(key, [])
