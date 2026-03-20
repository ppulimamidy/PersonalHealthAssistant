"""
Medication Intelligence Data — static config for drug interactions,
nutrient depletions, timing rules, and supplement interactions.
"""

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Drug-Nutrient Depletions
# Pattern matched against medication_name.lower()
# ---------------------------------------------------------------------------

DRUG_NUTRIENT_DEPLETIONS: Dict[str, List[Dict[str, str]]] = {
    "metformin": [
        {
            "nutrient": "B12",
            "biomarker": "b12",
            "severity": "high",
            "note": "Metformin reduces B12 absorption by up to 30%. Monitor annually.",
        },
        {
            "nutrient": "Folate",
            "biomarker": "folate",
            "severity": "medium",
            "note": "May reduce folate levels. Important if planning pregnancy.",
        },
        {
            "nutrient": "Magnesium",
            "biomarker": "magnesium",
            "severity": "low",
            "note": "Long-term use may lower magnesium.",
        },
    ],
    "statin": [
        {
            "nutrient": "CoQ10",
            "biomarker": "coq10",
            "severity": "medium",
            "note": "Statins block CoQ10 synthesis. May cause muscle fatigue and pain.",
        },
    ],
    "atorvastatin": [
        {
            "nutrient": "CoQ10",
            "biomarker": "coq10",
            "severity": "medium",
            "note": "Statins block CoQ10 synthesis. Consider supplementing, especially if muscle symptoms.",
        },
    ],
    "rosuvastatin": [
        {
            "nutrient": "CoQ10",
            "biomarker": "coq10",
            "severity": "medium",
            "note": "Statins block CoQ10 synthesis. Consider supplementing.",
        },
    ],
    "omeprazole": [
        {
            "nutrient": "Magnesium",
            "biomarker": "magnesium",
            "severity": "high",
            "note": "Long-term PPI use significantly depletes magnesium.",
        },
        {
            "nutrient": "Calcium",
            "biomarker": "calcium",
            "severity": "medium",
            "note": "PPIs reduce calcium absorption. Increases fracture risk long-term.",
        },
        {
            "nutrient": "B12",
            "biomarker": "b12",
            "severity": "high",
            "note": "PPIs reduce stomach acid needed for B12 absorption.",
        },
        {
            "nutrient": "Iron",
            "biomarker": "iron",
            "severity": "medium",
            "note": "Reduced stomach acid impairs iron absorption.",
        },
    ],
    "pantoprazole": [
        {
            "nutrient": "Magnesium",
            "biomarker": "magnesium",
            "severity": "high",
            "note": "Long-term PPI use depletes magnesium.",
        },
        {
            "nutrient": "B12",
            "biomarker": "b12",
            "severity": "high",
            "note": "PPIs reduce B12 absorption.",
        },
    ],
    "lisinopril": [
        {
            "nutrient": "Zinc",
            "biomarker": "zinc",
            "severity": "low",
            "note": "ACE inhibitors may increase zinc excretion.",
        },
    ],
    "enalapril": [
        {
            "nutrient": "Zinc",
            "biomarker": "zinc",
            "severity": "low",
            "note": "ACE inhibitors may increase zinc excretion.",
        },
    ],
    "furosemide": [
        {
            "nutrient": "Potassium",
            "biomarker": "potassium",
            "severity": "high",
            "note": "Loop diuretics cause significant potassium loss. Monitor closely.",
        },
        {
            "nutrient": "Magnesium",
            "biomarker": "magnesium",
            "severity": "high",
            "note": "Loop diuretics deplete magnesium.",
        },
        {
            "nutrient": "Calcium",
            "biomarker": "calcium",
            "severity": "medium",
            "note": "Increases calcium excretion.",
        },
    ],
    "hydrochlorothiazide": [
        {
            "nutrient": "Potassium",
            "biomarker": "potassium",
            "severity": "high",
            "note": "Thiazide diuretics deplete potassium.",
        },
        {
            "nutrient": "Magnesium",
            "biomarker": "magnesium",
            "severity": "medium",
            "note": "May deplete magnesium over time.",
        },
    ],
    "prednisone": [
        {
            "nutrient": "Calcium",
            "biomarker": "calcium",
            "severity": "high",
            "note": "Corticosteroids accelerate bone loss. Supplement calcium + vitamin D.",
        },
        {
            "nutrient": "Vitamin D",
            "biomarker": "vitamin_d",
            "severity": "high",
            "note": "Corticosteroids impair vitamin D metabolism.",
        },
        {
            "nutrient": "Potassium",
            "biomarker": "potassium",
            "severity": "medium",
            "note": "May cause potassium loss.",
        },
    ],
    "sertraline": [
        {
            "nutrient": "Folate",
            "biomarker": "folate",
            "severity": "low",
            "note": "SSRIs may benefit from folate supplementation for efficacy.",
        },
    ],
    "methotrexate": [
        {
            "nutrient": "Folate",
            "biomarker": "folate",
            "severity": "high",
            "note": "Methotrexate depletes folate. Folic acid supplementation is standard protocol.",
        },
    ],
    "oral contraceptive": [
        {
            "nutrient": "B6",
            "biomarker": "b6",
            "severity": "medium",
            "note": "Oral contraceptives deplete B6, which may affect mood.",
        },
        {
            "nutrient": "B12",
            "biomarker": "b12",
            "severity": "medium",
            "note": "May reduce B12 levels.",
        },
        {
            "nutrient": "Folate",
            "biomarker": "folate",
            "severity": "high",
            "note": "Depletes folate — critical if discontinuing for pregnancy.",
        },
        {
            "nutrient": "Magnesium",
            "biomarker": "magnesium",
            "severity": "medium",
            "note": "May reduce magnesium levels.",
        },
        {
            "nutrient": "Zinc",
            "biomarker": "zinc",
            "severity": "low",
            "note": "May lower zinc levels.",
        },
    ],
}

# ---------------------------------------------------------------------------
# Drug-Food Interactions
# ---------------------------------------------------------------------------

DRUG_FOOD_INTERACTIONS: Dict[str, List[Dict[str, str]]] = {
    "levothyroxine": [
        {
            "food": "Coffee",
            "severity": "moderate",
            "note": "Separate by 30-60 min. Coffee reduces thyroid hormone absorption by up to 36%.",
        },
        {
            "food": "Calcium-rich foods (milk, yogurt, cheese)",
            "severity": "moderate",
            "note": "Separate by 4 hours. Calcium binds to thyroid hormone.",
        },
        {
            "food": "Soy products",
            "severity": "moderate",
            "note": "Separate by 4 hours. Soy interferes with absorption.",
        },
        {
            "food": "High-fiber foods",
            "severity": "minor",
            "note": "Very high fiber meals may reduce absorption. Take medication before eating.",
        },
    ],
    "synthroid": [
        {"food": "Coffee", "severity": "moderate", "note": "Separate by 30-60 min."},
        {
            "food": "Calcium-rich foods",
            "severity": "moderate",
            "note": "Separate by 4 hours.",
        },
    ],
    "simvastatin": [
        {
            "food": "Grapefruit",
            "severity": "major",
            "note": "Grapefruit inhibits statin metabolism, increasing blood levels and side effect risk. Avoid entirely.",
        },
    ],
    "atorvastatin": [
        {
            "food": "Grapefruit",
            "severity": "moderate",
            "note": "Large amounts of grapefruit may increase statin levels. Limit intake.",
        },
    ],
    "metformin": [
        {
            "food": "Alcohol",
            "severity": "major",
            "note": "Alcohol + Metformin increases lactic acidosis risk. Limit consumption.",
        },
    ],
    "warfarin": [
        {
            "food": "Vitamin K-rich foods (kale, spinach, broccoli)",
            "severity": "major",
            "note": "Vitamin K counteracts warfarin. Keep intake consistent (don't eliminate, just be consistent).",
        },
    ],
}

# ---------------------------------------------------------------------------
# Medication Timing Rules
# ---------------------------------------------------------------------------

TIMING_RULES: Dict[str, Dict[str, str]] = {
    "levothyroxine": {
        "when": "morning_empty",
        "rule": "Take on empty stomach, 30-60 min before breakfast",
        "reason": "Food, coffee, and supplements reduce absorption by 20-40%",
    },
    "synthroid": {
        "when": "morning_empty",
        "rule": "Take on empty stomach, 30-60 min before breakfast",
        "reason": "Same as levothyroxine — absorption is critical",
    },
    "metformin": {
        "when": "with_meals",
        "rule": "Take with breakfast and dinner",
        "reason": "Reduces GI side effects (nausea, diarrhea) significantly",
    },
    "simvastatin": {
        "when": "evening",
        "rule": "Take in the evening",
        "reason": "Liver produces most cholesterol at night; short half-life",
    },
    "atorvastatin": {
        "when": "any_time",
        "rule": "Take at any consistent time",
        "reason": "Long half-life — equally effective morning or evening",
    },
    "rosuvastatin": {
        "when": "any_time",
        "rule": "Take at any consistent time",
        "reason": "Long half-life — timing flexible",
    },
    "iron": {
        "when": "before_dinner",
        "rule": "Take with vitamin C on empty stomach. Separate from calcium, dairy, coffee, tea by 2h",
        "reason": "Vitamin C enhances absorption 2-3x; calcium and tannins block it",
    },
    "ferrous": {
        "when": "before_dinner",
        "rule": "Take with vitamin C. Separate from calcium by 2 hours",
        "reason": "Iron absorption is highly sensitive to timing and co-factors",
    },
    "calcium": {
        "when": "with_meals",
        "rule": "Take with food. Separate from iron by 2 hours. Pair with vitamin D",
        "reason": "Needs stomach acid for absorption; vitamin D enhances uptake",
    },
    "magnesium": {
        "when": "bedtime",
        "rule": "Take in the evening or at bedtime. Separate from calcium",
        "reason": "Supports sleep quality; competes with calcium for absorption",
    },
    "vitamin d": {
        "when": "with_fatty_meal",
        "rule": "Take with your largest meal (containing some fat)",
        "reason": "Fat-soluble — absorption increases 50% with dietary fat",
    },
    "d3": {
        "when": "with_fatty_meal",
        "rule": "Take with a fatty meal",
        "reason": "Fat-soluble vitamin needs dietary fat for absorption",
    },
    "fish oil": {
        "when": "with_meals",
        "rule": "Take with a meal",
        "reason": "Reduces fishy burps; fat-soluble absorption improved with food",
    },
    "omega": {
        "when": "with_meals",
        "rule": "Take with a meal",
        "reason": "Better tolerated and absorbed with food",
    },
    "probiotics": {
        "when": "before_breakfast",
        "rule": "Take 30 min before breakfast on empty stomach",
        "reason": "Stomach acid is lower before eating, improving bacterial survival",
    },
    "coq10": {
        "when": "with_fatty_meal",
        "rule": "Take with a meal containing fat",
        "reason": "Fat-soluble — absorption significantly improved with dietary fat",
    },
    "zinc": {
        "when": "with_meals",
        "rule": "Take with food to prevent nausea. Separate from iron and calcium",
        "reason": "Can cause stomach upset on empty stomach; competes with iron/calcium",
    },
}

# ---------------------------------------------------------------------------
# Supplement-Supplement Interactions
# ---------------------------------------------------------------------------

SUPPLEMENT_INTERACTIONS: List[Dict[str, str]] = [
    {
        "supp_a": "iron",
        "supp_b": "calcium",
        "rule": "Separate by 2+ hours",
        "reason": "Calcium blocks iron absorption by up to 60%",
    },
    {
        "supp_a": "iron",
        "supp_b": "zinc",
        "rule": "Separate by 2+ hours",
        "reason": "Compete for the same absorption pathway",
    },
    {
        "supp_a": "calcium",
        "supp_b": "magnesium",
        "rule": "Separate or take in 2:1 ratio",
        "reason": "High calcium can inhibit magnesium absorption",
    },
    {
        "supp_a": "zinc",
        "supp_b": "copper",
        "rule": "If taking zinc long-term, add 1-2mg copper",
        "reason": "Zinc depletes copper over time",
    },
    {
        "supp_a": "vitamin c",
        "supp_b": "b12",
        "rule": "Separate by 2 hours",
        "reason": "High-dose vitamin C may reduce B12 absorption",
    },
    {
        "supp_a": "vitamin e",
        "supp_b": "vitamin k",
        "rule": "High-dose vitamin E may interfere with vitamin K",
        "reason": "Anticoagulant effect competition",
    },
]

# ---------------------------------------------------------------------------
# Time slot ordering for schedule builder
# ---------------------------------------------------------------------------

SCHEDULE_SLOTS = [
    {"key": "morning_empty", "label": "Morning (empty stomach)", "order": 0},
    {"key": "before_breakfast", "label": "Before breakfast", "order": 1},
    {"key": "with_breakfast", "label": "With breakfast", "order": 2},
    {"key": "with_meals", "label": "With meals", "order": 3},
    {"key": "with_fatty_meal", "label": "With a fatty meal", "order": 4},
    {"key": "with_lunch", "label": "With lunch", "order": 5},
    {"key": "before_dinner", "label": "Before dinner", "order": 6},
    {"key": "evening", "label": "Evening", "order": 7},
    {"key": "bedtime", "label": "Bedtime", "order": 8},
    {"key": "any_time", "label": "Any consistent time", "order": 9},
]
