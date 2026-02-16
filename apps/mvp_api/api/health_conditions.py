"""
Health Conditions — CRUD + Condition-Variable Mapping

Allows Pro+ users to track health conditions/chronic concerns.
Maps conditions to relevant tracked variables so the correlation
engine can prioritize condition-relevant metric pairs.
"""

# pylint: disable=line-too-long

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    UsageGate,
    _supabase_get,
    _supabase_upsert,
)

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Condition → variable mapping
# ---------------------------------------------------------------------------

# Maps common health conditions to the nutrition/oura variables most relevant
# for monitoring.  The correlation engine uses these to lower thresholds and
# prioritise condition-specific pairs.
CONDITION_VARIABLE_MAP: Dict[str, Dict[str, Any]] = {
    "type_2_diabetes": {
        "label": "Type 2 Diabetes",
        "category": "metabolic",
        "variables": [
            "total_carbs_g",
            "total_sugar_g",
            "glycemic_load_est",
            "total_fiber_g",
            "hrv_balance",
            "resting_heart_rate",
            "readiness_score",
            "sleep_score",
        ],
        "watch_metrics": ["Blood sugar spikes correlate with high glycemic load meals"],
    },
    "hypertension": {
        "label": "Hypertension",
        "category": "cardiovascular",
        "variables": [
            "total_sodium_mg",
            "resting_heart_rate",
            "hrv_balance",
            "readiness_score",
            "total_calories",
            "steps",
        ],
        "watch_metrics": ["High sodium intake may elevate blood pressure"],
    },
    "ibs": {
        "label": "Irritable Bowel Syndrome (IBS)",
        "category": "digestive",
        "variables": [
            "total_fiber_g",
            "total_fat_g",
            "total_sugar_g",
            "sleep_score",
            "readiness_score",
            "hrv_balance",
        ],
        "watch_metrics": ["High-fiber or high-fat meals may trigger symptoms"],
    },
    "pcos": {
        "label": "Polycystic Ovary Syndrome (PCOS)",
        "category": "metabolic",
        "variables": [
            "total_carbs_g",
            "total_sugar_g",
            "glycemic_load_est",
            "total_protein_g",
            "hrv_balance",
            "sleep_score",
            "temperature_deviation",
        ],
        "watch_metrics": ["Insulin resistance worsens with high glycemic load"],
    },
    "hypothyroidism": {
        "label": "Hypothyroidism",
        "category": "metabolic",
        "variables": [
            "total_calories",
            "resting_heart_rate",
            "temperature_deviation",
            "sleep_score",
            "readiness_score",
            "steps",
        ],
        "watch_metrics": ["Monitor energy levels and temperature deviations"],
    },
    "hyperthyroidism": {
        "label": "Hyperthyroidism",
        "category": "metabolic",
        "variables": [
            "total_calories",
            "resting_heart_rate",
            "temperature_deviation",
            "sleep_score",
            "hrv_balance",
            "active_calories",
        ],
        "watch_metrics": ["Elevated heart rate and temperature may indicate flare"],
    },
    "anxiety": {
        "label": "Anxiety Disorder",
        "category": "mental_health",
        "variables": [
            "hrv_balance",
            "resting_heart_rate",
            "sleep_score",
            "sleep_efficiency",
            "deep_sleep_hours",
            "readiness_score",
            "total_sugar_g",
            "last_meal_hour",
        ],
        "watch_metrics": [
            "Low HRV and poor sleep often correlate with anxiety episodes"
        ],
    },
    "depression": {
        "label": "Depression",
        "category": "mental_health",
        "variables": [
            "sleep_score",
            "deep_sleep_hours",
            "steps",
            "activity_score",
            "readiness_score",
            "hrv_balance",
            "total_calories",
        ],
        "watch_metrics": ["Activity levels and sleep quality can reflect mood state"],
    },
    "celiac_disease": {
        "label": "Celiac Disease",
        "category": "autoimmune",
        "variables": [
            "total_calories",
            "total_protein_g",
            "total_fiber_g",
            "readiness_score",
            "hrv_balance",
            "sleep_score",
        ],
        "watch_metrics": ["Gluten exposure may reduce readiness and HRV"],
    },
    "crohns_disease": {
        "label": "Crohn's Disease",
        "category": "autoimmune",
        "variables": [
            "total_fiber_g",
            "total_fat_g",
            "total_calories",
            "temperature_deviation",
            "hrv_balance",
            "readiness_score",
        ],
        "watch_metrics": ["Inflammation markers may rise with certain foods"],
    },
    "rheumatoid_arthritis": {
        "label": "Rheumatoid Arthritis",
        "category": "autoimmune",
        "variables": [
            "temperature_deviation",
            "hrv_balance",
            "resting_heart_rate",
            "total_sugar_g",
            "readiness_score",
            "sleep_score",
        ],
        "watch_metrics": ["Sugar and inflammation are closely linked in RA"],
    },
    "gerd": {
        "label": "GERD / Acid Reflux",
        "category": "digestive",
        "variables": [
            "last_meal_hour",
            "total_fat_g",
            "total_calories",
            "sleep_score",
            "sleep_efficiency",
        ],
        "watch_metrics": ["Late meals and high-fat foods worsen reflux and sleep"],
    },
    "insomnia": {
        "label": "Insomnia",
        "category": "mental_health",
        "variables": [
            "sleep_score",
            "sleep_efficiency",
            "deep_sleep_hours",
            "total_sleep_hours",
            "last_meal_hour",
            "total_sugar_g",
            "hrv_balance",
            "resting_heart_rate",
        ],
        "watch_metrics": ["Meal timing and sugar intake strongly affect sleep onset"],
    },
    "iron_deficiency_anemia": {
        "label": "Iron Deficiency Anemia",
        "category": "metabolic",
        "variables": [
            "total_calories",
            "total_protein_g",
            "resting_heart_rate",
            "readiness_score",
            "activity_score",
            "steps",
        ],
        "watch_metrics": ["Low energy and elevated heart rate may indicate low iron"],
    },
    "migraine": {
        "label": "Migraine",
        "category": "other",
        "variables": [
            "total_sodium_mg",
            "total_sugar_g",
            "sleep_score",
            "sleep_efficiency",
            "hrv_balance",
            "temperature_deviation",
        ],
        "watch_metrics": [
            "Sleep disruption, dehydration, and sugar spikes can trigger migraines"
        ],
    },
    "obesity": {
        "label": "Obesity",
        "category": "metabolic",
        "variables": [
            "total_calories",
            "total_carbs_g",
            "total_fat_g",
            "total_sugar_g",
            "steps",
            "active_calories",
            "activity_score",
        ],
        "watch_metrics": [
            "Calorie balance and activity levels are key tracking metrics"
        ],
    },
    "sleep_apnea": {
        "label": "Sleep Apnea",
        "category": "other",
        "variables": [
            "sleep_score",
            "sleep_efficiency",
            "deep_sleep_hours",
            "total_sleep_hours",
            "resting_heart_rate",
            "hrv_balance",
            "readiness_score",
        ],
        "watch_metrics": [
            "Sleep efficiency and deep sleep duration reflect apnea severity"
        ],
    },
}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class CreateConditionRequest(BaseModel):
    condition_name: str = Field(..., min_length=1, max_length=200)
    condition_category: str = Field(
        default="other",
        pattern="^(metabolic|cardiovascular|autoimmune|digestive|mental_health|other)$",
    )
    severity: str = Field(default="moderate", pattern="^(mild|moderate|severe)$")
    diagnosed_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class UpdateConditionRequest(BaseModel):
    condition_name: Optional[str] = None
    condition_category: Optional[str] = None
    severity: Optional[str] = None
    diagnosed_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ConditionResponse(BaseModel):
    id: str
    user_id: str
    condition_name: str
    condition_category: str
    severity: str
    diagnosed_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool
    tracked_variables: List[str]
    watch_metrics: List[str]


class ConditionCatalogItem(BaseModel):
    key: str
    label: str
    category: str
    tracked_variable_count: int


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------


async def _supabase_delete(table: str, params: str) -> bool:
    """DELETE from Supabase PostgREST."""
    import aiohttp

    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not supabase_url or not supabase_key:
        return False

    url = f"{supabase_url}/rest/v1/{table}?{params}"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
    }
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.delete(url, headers=headers) as resp:
                return resp.status in (200, 204)
    except (aiohttp.ClientError, TimeoutError) as exc:
        logger.warning("Supabase DELETE %s failed: %s", table, exc)
        return False


async def _supabase_patch(table: str, params: str, body: dict) -> Optional[dict]:
    """PATCH to Supabase PostgREST."""
    import aiohttp

    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not supabase_url or not supabase_key:
        return None

    url = f"{supabase_url}/rest/v1/{table}?{params}"
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.patch(url, headers=headers, json=body) as resp:
                if resp.status in (200, 201):
                    data = await resp.json()
                    return data[0] if isinstance(data, list) and data else data
                return None
    except (aiohttp.ClientError, TimeoutError) as exc:
        logger.warning("Supabase PATCH %s failed: %s", table, exc)
        return None


def _resolve_tracked_variables(condition_name: str) -> List[str]:
    """Look up tracked variables for a condition from the hardcoded map."""
    # Try exact key match
    key = condition_name.lower().replace(" ", "_").replace("-", "_")
    if key in CONDITION_VARIABLE_MAP:
        return CONDITION_VARIABLE_MAP[key]["variables"]

    # Try fuzzy match on label
    name_lower = condition_name.lower()
    for _k, v in CONDITION_VARIABLE_MAP.items():
        if name_lower in v["label"].lower() or v["label"].lower() in name_lower:
            return v["variables"]

    return []


def _resolve_watch_metrics(condition_name: str) -> List[str]:
    """Look up watch metrics for a condition from the hardcoded map."""
    key = condition_name.lower().replace(" ", "_").replace("-", "_")
    if key in CONDITION_VARIABLE_MAP:
        return CONDITION_VARIABLE_MAP[key].get("watch_metrics", [])

    name_lower = condition_name.lower()
    for _k, v in CONDITION_VARIABLE_MAP.items():
        if name_lower in v["label"].lower() or v["label"].lower() in name_lower:
            return v.get("watch_metrics", [])

    return []


def _row_to_response(row: dict) -> ConditionResponse:
    """Convert a Supabase row to a ConditionResponse."""
    tracked = row.get("tracked_variables") or []
    if isinstance(tracked, str):
        try:
            tracked = json.loads(tracked)
        except (json.JSONDecodeError, TypeError):
            tracked = []

    # Always resolve from our map for the most up-to-date variables
    condition_name = row.get("condition_name", "")
    resolved_vars = _resolve_tracked_variables(condition_name)
    if resolved_vars:
        tracked = resolved_vars

    watch = _resolve_watch_metrics(condition_name)

    return ConditionResponse(
        id=row.get("id", ""),
        user_id=row.get("user_id", ""),
        condition_name=condition_name,
        condition_category=row.get("condition_category", "other"),
        severity=row.get("severity", "moderate"),
        diagnosed_date=row.get("diagnosed_date"),
        notes=row.get("notes"),
        is_active=row.get("is_active", True),
        tracked_variables=tracked,
        watch_metrics=watch,
    )


# ---------------------------------------------------------------------------
# Public helper for correlation engine
# ---------------------------------------------------------------------------


async def get_condition_variables(user_id: str) -> List[str]:
    """
    Return the union of tracked variables for all active conditions.
    Used by the correlation engine to prioritise condition-relevant pairs.
    """
    rows = await _supabase_get(
        "health_conditions",
        f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name",
    )
    if not rows or not isinstance(rows, list):
        return []

    all_vars: set = set()
    for row in rows:
        name = row.get("condition_name", "")
        all_vars.update(_resolve_tracked_variables(name))
    return list(all_vars)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/catalog", response_model=List[ConditionCatalogItem])
async def get_condition_catalog(
    current_user: dict = Depends(get_current_user),
):
    """Return the catalog of known conditions with variable counts."""
    catalog = []
    for key, info in CONDITION_VARIABLE_MAP.items():
        catalog.append(
            ConditionCatalogItem(
                key=key,
                label=info["label"],
                category=info["category"],
                tracked_variable_count=len(info["variables"]),
            )
        )
    catalog.sort(key=lambda c: c.label)
    return catalog


@router.get("", response_model=List[ConditionResponse])
async def list_conditions(
    current_user: dict = Depends(get_current_user),
):
    """List all health conditions for the authenticated user."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "health_conditions",
        f"user_id=eq.{user_id}&select=*&order=created_at.desc",
    )
    if not rows or not isinstance(rows, list):
        return []
    return [_row_to_response(r) for r in rows]


@router.post("", response_model=ConditionResponse, status_code=201)
async def add_condition(
    body: CreateConditionRequest,
    current_user: dict = Depends(UsageGate("health_conditions")),
):
    """Add a new health condition for the user."""
    user_id = current_user["id"]
    tracked = _resolve_tracked_variables(body.condition_name)

    row_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "condition_name": body.condition_name,
        "condition_category": body.condition_category,
        "severity": body.severity,
        "diagnosed_date": body.diagnosed_date,
        "notes": body.notes,
        "is_active": body.is_active,
        "tracked_variables": json.dumps(tracked),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await _supabase_upsert("health_conditions", row_data)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to save condition")

    return _row_to_response(result)


@router.put("/{condition_id}", response_model=ConditionResponse)
async def update_condition(
    condition_id: str,
    body: UpdateConditionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing health condition."""
    user_id = current_user["id"]

    # Verify ownership
    rows = await _supabase_get(
        "health_conditions",
        f"id=eq.{condition_id}&user_id=eq.{user_id}&select=*&limit=1",
    )
    if not rows or not isinstance(rows, list) or not rows[0]:
        raise HTTPException(status_code=404, detail="Condition not found")

    updates: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if body.condition_name is not None:
        updates["condition_name"] = body.condition_name
        updates["tracked_variables"] = json.dumps(
            _resolve_tracked_variables(body.condition_name)
        )
    if body.condition_category is not None:
        updates["condition_category"] = body.condition_category
    if body.severity is not None:
        updates["severity"] = body.severity
    if body.diagnosed_date is not None:
        updates["diagnosed_date"] = body.diagnosed_date
    if body.notes is not None:
        updates["notes"] = body.notes
    if body.is_active is not None:
        updates["is_active"] = body.is_active

    result = await _supabase_patch(
        "health_conditions",
        f"id=eq.{condition_id}&user_id=eq.{user_id}",
        updates,
    )
    if not result:
        raise HTTPException(status_code=500, detail="Failed to update condition")

    return _row_to_response(result)


@router.delete("/{condition_id}", status_code=204)
async def delete_condition(
    condition_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a health condition."""
    user_id = current_user["id"]

    # Verify ownership
    rows = await _supabase_get(
        "health_conditions",
        f"id=eq.{condition_id}&user_id=eq.{user_id}&select=id&limit=1",
    )
    if not rows or not isinstance(rows, list) or not rows[0]:
        raise HTTPException(status_code=404, detail="Condition not found")

    success = await _supabase_delete(
        "health_conditions",
        f"id=eq.{condition_id}&user_id=eq.{user_id}",
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete condition")
