"""
Profile Intelligence API — health summary, specialists, goal suggestions.
Powers the post-onboarding discoverability and goal management features.
"""

import asyncio
import json
import os
from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get

logger = get_logger(__name__)
router = APIRouter()

# Import specialist configs
try:
    from ..agents.specialist_configs import (
        CONDITION_SPECIALIST_MAP,
        GOAL_SPECIALIST_MAP,
        list_all_specialists,
    )
except ImportError:
    CONDITION_SPECIALIST_MAP = {}
    GOAL_SPECIALIST_MAP = {}

    def list_all_specialists():  # type: ignore[misc]
        return []


SPECIALIST_LABELS: Dict[str, Dict[str, str]] = {
    "endocrinologist": {
        "name": "Endocrinologist",
        "icon": "body-outline",
        "color": "#818CF8",
    },
    "diabetologist": {
        "name": "Diabetologist",
        "icon": "analytics-outline",
        "color": "#F5A623",
    },
    "cardiologist": {
        "name": "Cardiologist",
        "icon": "heart-outline",
        "color": "#F87171",
    },
    "gi_specialist": {
        "name": "GI Specialist",
        "icon": "medical-outline",
        "color": "#6EE7B7",
    },
    "behavioral_health": {
        "name": "Behavioral Health",
        "icon": "happy-outline",
        "color": "#60A5FA",
    },
    "sleep_specialist": {
        "name": "Sleep Specialist",
        "icon": "moon-outline",
        "color": "#A78BFA",
    },
    "pulmonologist": {
        "name": "Pulmonologist",
        "icon": "fitness-outline",
        "color": "#2DD4BF",
    },
    "rheumatologist": {
        "name": "Rheumatologist",
        "icon": "hand-left-outline",
        "color": "#EC4899",
    },
    "oncology_support": {
        "name": "Oncology Support",
        "icon": "shield-outline",
        "color": "#F87171",
    },
    "pain_management": {
        "name": "Pain Management",
        "icon": "bandage-outline",
        "color": "#F5A623",
    },
    "womens_health": {
        "name": "Women's Health",
        "icon": "female-outline",
        "color": "#EC4899",
    },
    "dermatologist": {
        "name": "Dermatologist",
        "icon": "sunny-outline",
        "color": "#F5A623",
    },
    "neurologist": {"name": "Neurologist", "icon": "flash-outline", "color": "#818CF8"},
    "nephrologist": {
        "name": "Nephrologist",
        "icon": "water-outline",
        "color": "#60A5FA",
    },
    "metabolic_coach": {
        "name": "Metabolic Coach",
        "icon": "flame-outline",
        "color": "#F5A623",
    },
    "exercise_physiologist": {
        "name": "Exercise Physiologist",
        "icon": "barbell-outline",
        "color": "#6EE7B7",
    },
    "health_coach": {
        "name": "Health Coach",
        "icon": "fitness-outline",
        "color": "#00D4AA",
    },
    "nutrition_analyst": {
        "name": "Nutrition Analyst",
        "icon": "nutrition-outline",
        "color": "#6EE7B7",
    },
    "longevity_specialist": {
        "name": "Longevity Specialist",
        "icon": "hourglass-outline",
        "color": "#2DD4BF",
    },
}

HINTS = [
    "Managing another condition? Add it to get a dedicated specialist.",
    "Set a health goal to track your progress with real data.",
    "Need specialist guidance? Add your conditions to unlock expert agents.",
    "Your specialists monitor your data and personalize every recommendation.",
]


def _map_condition_to_specialist(condition_name: str) -> Optional[str]:
    """Map a condition name to its specialist type."""
    norm = condition_name.lower().replace(" ", "_").replace("'", "")
    # Direct match
    if norm in CONDITION_SPECIALIST_MAP:
        return CONDITION_SPECIALIST_MAP[norm]
    # Partial match
    for key, specialist in CONDITION_SPECIALIST_MAP.items():
        if key in norm or norm in key:
            return specialist
    return None


@router.get("/health-summary")
async def health_summary(
    current_user: dict = Depends(get_current_user),
):
    """Quick summary of conditions, goals, specialists for profile card."""
    user_id = current_user["id"]

    conditions, goals, profile = await asyncio.gather(
        _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=condition_name,condition_category",
        ),
        _supabase_get(
            "user_goals",
            f"user_id=eq.{user_id}&status=eq.active&select=id",
        ),
        _supabase_get(
            "profiles",
            f"id=eq.{user_id}&select=primary_goal",
        ),
    )

    # Map conditions to specialists
    specialists: List[Dict[str, Any]] = []
    seen_types: set = set()
    for cond in conditions:
        cname = cond.get("condition_name", "")
        spec_type = _map_condition_to_specialist(cname)
        if spec_type and spec_type not in seen_types:
            seen_types.add(spec_type)
            label = SPECIALIST_LABELS.get(
                spec_type,
                {
                    "name": spec_type.replace("_", " ").title(),
                    "icon": "person-outline",
                    "color": "#526380",
                },
            )
            specialists.append(
                {
                    "type": spec_type,
                    "name": label["name"],
                    "icon": label.get("icon", "person-outline"),
                    "color": label.get("color", "#526380"),
                    "for_condition": cname,
                }
            )

    # Always include health coach
    if "health_coach" not in seen_types:
        hc = SPECIALIST_LABELS["health_coach"]
        specialists.append(
            {
                "type": "health_coach",
                "name": hc["name"],
                "icon": hc["icon"],
                "color": hc["color"],
                "for_condition": "General wellness",
            }
        )

    # Hint rotation based on what's missing
    import random

    hint_idx = random.randint(0, len(HINTS) - 1)
    if len(conditions) == 0:
        hint = "Add a health condition to get a dedicated specialist agent."
    elif len(goals) == 0:
        hint = "Set a health goal to track your progress with real data."
    else:
        hint = HINTS[hint_idx]

    return {
        "conditions": [
            {
                "name": c.get("condition_name", ""),
                "category": c.get("condition_category", ""),
            }
            for c in conditions
        ],
        "conditions_count": len(conditions),
        "active_goals_count": len(goals),
        "specialists": specialists,
        "specialists_count": len(specialists),
        "hint": hint,
    }


@router.get("/my-specialists")
async def my_specialists(
    current_user: dict = Depends(get_current_user),
):
    """List user's active specialists with monitored metrics."""
    user_id = current_user["id"]

    conditions = await _supabase_get(
        "health_conditions",
        f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name",
    )

    # Map conditions to specialists with details
    specialists: List[Dict[str, Any]] = []
    seen_types: set = set()

    for cond in conditions:
        cname = cond.get("condition_name", "")
        spec_type = _map_condition_to_specialist(cname)
        if spec_type and spec_type not in seen_types:
            seen_types.add(spec_type)
            label = SPECIALIST_LABELS.get(
                spec_type,
                {
                    "name": spec_type.replace("_", " ").title(),
                    "icon": "person-outline",
                    "color": "#526380",
                },
            )

            # Get monitored metrics from specialist config
            all_specs = list_all_specialists()
            monitored: List[str] = []
            for s in all_specs:
                if s.get("agent_type") == spec_type:
                    monitored = s.get("tracked_metrics", [])[:5]
                    break

            specialists.append(
                {
                    "type": spec_type,
                    "name": label["name"],
                    "icon": label.get("icon", "person-outline"),
                    "color": label.get("color", "#526380"),
                    "for_conditions": [cname],
                    "monitored_metrics": monitored,
                    "can_chat": True,
                    "can_consult": len(seen_types) > 1,
                }
            )

    # Always include health coach
    if "health_coach" not in seen_types:
        hc = SPECIALIST_LABELS["health_coach"]
        specialists.append(
            {
                "type": "health_coach",
                "name": hc["name"],
                "icon": hc["icon"],
                "color": hc["color"],
                "for_conditions": ["General wellness"],
                "monitored_metrics": ["sleep", "activity", "nutrition", "stress"],
                "can_chat": True,
                "can_consult": False,
            }
        )

    return {"specialists": specialists}


@router.get("/goals/suggested")
async def suggested_goals(
    current_user: dict = Depends(get_current_user),
):
    """AI-suggested goals based on conditions, labs, and data gaps."""
    user_id = current_user["id"]

    conditions, labs, goals = await asyncio.gather(
        _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name",
        ),
        _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&order=test_date.desc&limit=1&select=biomarkers",
        ),
        _supabase_get(
            "user_goals",
            f"user_id=eq.{user_id}&status=eq.active&select=goal_text,category",
        ),
    )

    suggestions: List[Dict[str, Any]] = []

    # Condition-specific goals
    for cond in conditions:
        cname = cond.get("condition_name", "")
        norm = cname.lower()
        if "diabetes" in norm or "pcos" in norm:
            suggestions.append(
                {
                    "text": f"Get A1C below 6.5%",
                    "category": "lab_result",
                    "reason": f"Recommended for {cname} management",
                }
            )
        if "hypertension" in norm:
            suggestions.append(
                {
                    "text": "Maintain BP below 130/80",
                    "category": "general",
                    "reason": "ACC/AHA target for hypertension",
                }
            )
        if "insomnia" in norm or "sleep" in norm:
            suggestions.append(
                {
                    "text": "Achieve 7+ hours sleep consistently",
                    "category": "sleep",
                    "reason": "Sleep hygiene is first-line for insomnia",
                }
            )

    # Lab-based goals
    if labs:
        bms = labs[0].get("biomarkers") or []
        if isinstance(bms, str):
            try:
                bms = json.loads(bms)
            except Exception:
                bms = []
        for bm in bms:
            if isinstance(bm, dict) and bm.get("status") in ("abnormal", "borderline"):
                suggestions.append(
                    {
                        "text": f"Improve {bm.get('name', 'biomarker')} to normal range",
                        "category": "lab_result",
                        "reason": f"Currently {bm.get('status')}: {bm.get('value')} {bm.get('unit', '')}",
                    }
                )

    # General suggestions if few goals set
    existing_cats = {g.get("category") for g in goals}
    if "exercise" not in existing_cats:
        suggestions.append(
            {
                "text": "Walk 8,000 steps daily",
                "category": "exercise",
                "reason": "WHO recommends 150 min moderate activity/week",
            }
        )
    if "diet" not in existing_cats:
        suggestions.append(
            {
                "text": "Log meals 5 days per week",
                "category": "diet",
                "reason": "Consistent logging unlocks nutrition patterns",
            }
        )

    return {"suggestions": suggestions[:6]}


@router.get("/goals/{goal_id}/progress")
async def goal_progress(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Live progress for a measurable goal."""
    user_id = current_user["id"]

    goal_rows = await _supabase_get(
        "user_goals",
        f"id=eq.{goal_id}&user_id=eq.{user_id}&select=goal_text,category,due_date",
    )
    if not goal_rows:
        return {"progress": None}

    goal = goal_rows[0]
    category = goal.get("category", "general")

    progress: Dict[str, Any] = {"category": category, "measurable": False}

    if category == "exercise":
        # Get avg steps from wearable
        summaries = await _supabase_get(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&metric_type=eq.steps&order=date.desc&limit=7&select=latest_value",
        )
        if summaries:
            vals = [
                s.get("latest_value", 0) for s in summaries if s.get("latest_value")
            ]
            if vals:
                progress["measurable"] = True
                progress["current_value"] = round(sum(vals) / len(vals))
                progress["unit"] = "avg steps/day"

    elif category == "sleep":
        summaries = await _supabase_get(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&metric_type=eq.sleep&order=date.desc&limit=7&select=latest_value",
        )
        if summaries:
            vals = [
                s.get("latest_value", 0) for s in summaries if s.get("latest_value")
            ]
            if vals:
                progress["measurable"] = True
                progress["current_value"] = round(sum(vals) / len(vals), 1)
                progress["unit"] = "avg sleep score"

    elif category == "lab_result":
        labs = await _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&order=test_date.desc&limit=1&select=biomarkers",
        )
        if labs:
            bms = labs[0].get("biomarkers") or []
            if isinstance(bms, str):
                try:
                    bms = json.loads(bms)
                except Exception:
                    bms = []
            # Try to match goal text to a biomarker
            goal_lower = goal.get("goal_text", "").lower()
            for bm in bms:
                if isinstance(bm, dict) and bm.get("name", "").lower() in goal_lower:
                    progress["measurable"] = True
                    progress["current_value"] = bm.get("value")
                    progress["unit"] = bm.get("unit", "")
                    progress["status"] = bm.get("status")
                    break

    return {"progress": progress}
