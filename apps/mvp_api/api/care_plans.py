"""
Care Plans API

Structured health goals tied to measurable metrics.
Unlike free-text user_goals, each care plan item has a target_value
and the backend auto-computes current_value progress from existing data.

Metric types and their auto-computed current values:
  weight              → profiles.weight_kg
  medication_adherence→ medication_adherence_log (30d %)
  symptom_severity    → symptom_journal avg severity (30d)
  calories            → meal_logs avg daily calories (7d)
  steps / sleep_score → None (frontend uses Oura timeline data)
  lab_result / general→ None (manual or not applicable)
"""

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    _supabase_upsert,
    _supabase_patch,
    _supabase_delete,
)

logger = get_logger(__name__)
router = APIRouter()

# ── Pydantic models ────────────────────────────────────────────────────────────

MetricType = str  # weight | steps | sleep_score | medication_adherence | symptom_severity | calories | lab_result | general
PlanStatus = str  # active | completed | abandoned
PlanSource = str  # self | doctor


class CarePlan(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    metric_type: str
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    target_date: Optional[str] = None
    start_date: str
    source: str
    status: str
    notes: Optional[str] = None
    current_value: Optional[float] = None   # computed at query time
    created_at: str
    updated_at: str


class CarePlanListResponse(BaseModel):
    plans: List[CarePlan]


class CreateCarePlanRequest(BaseModel):
    title: str
    description: Optional[str] = None
    metric_type: str = "general"
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    target_date: Optional[str] = None
    source: str = "self"
    notes: Optional[str] = None


class UpdateCarePlanRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    metric_type: Optional[str] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    target_date: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


# ── Current-value computation ──────────────────────────────────────────────────

async def _compute_current_value(metric_type: str, user_id: str) -> Optional[float]:
    """
    Best-effort query of the metric's current value from existing data.
    Returns None when data is unavailable.
    """
    try:
        if metric_type == "weight":
            rows = await _supabase_get(
                "profiles", f"id=eq.{user_id}&select=weight_kg&limit=1"
            )
            if rows and rows[0].get("weight_kg") is not None:
                return float(rows[0]["weight_kg"])

        elif metric_type == "symptom_severity":
            start = (date.today() - timedelta(days=30)).isoformat()
            rows = await _supabase_get(
                "symptom_journal",
                f"user_id=eq.{user_id}&symptom_date=gte.{start}&select=severity&limit=200",
            )
            sevs = [r["severity"] for r in (rows or []) if r.get("severity") is not None]
            return round(sum(sevs) / len(sevs), 1) if sevs else None

        elif metric_type == "medication_adherence":
            start = (date.today() - timedelta(days=30)).isoformat()
            rows = await _supabase_get(
                "medication_adherence_log",
                f"user_id=eq.{user_id}&date=gte.{start}&select=was_taken&limit=500",
            )
            if rows:
                taken = sum(1 for r in rows if r.get("was_taken"))
                return round(taken / len(rows) * 100)

        elif metric_type == "calories":
            start = (date.today() - timedelta(days=7)).isoformat()
            rows = await _supabase_get(
                "meal_logs",
                f"user_id=eq.{user_id}&timestamp=gte.{start}&select=calories&limit=200",
            )
            cals = [r["calories"] for r in (rows or []) if r.get("calories") is not None]
            if cals:
                # Rough daily avg (meal logs can have multiple per day)
                return round(sum(cals) / 7)

        # steps, sleep_score: sourced from Oura timeline — frontend handles these
        # lab_result, general: no auto-computation
    except Exception as exc:
        logger.warning("_compute_current_value(%s): %s", metric_type, exc)

    return None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _row_to_plan(row: dict, current_value: Optional[float] = None) -> CarePlan:
    tv = row.get("target_value")
    return CarePlan(
        id=row["id"],
        user_id=row["user_id"],
        title=row["title"],
        description=row.get("description"),
        metric_type=row.get("metric_type", "general"),
        target_value=float(tv) if tv is not None else None,
        target_unit=row.get("target_unit"),
        target_date=row.get("target_date"),
        start_date=row.get("start_date", ""),
        source=row.get("source", "self"),
        status=row.get("status", "active"),
        notes=row.get("notes"),
        current_value=current_value,
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("", response_model=CarePlanListResponse)
async def list_care_plans(
    status: Optional[str] = Query(default="active"),
    current_user: dict = Depends(get_current_user),
):
    """List care plans, optionally filtered by status. Includes computed current_value."""
    user_id = current_user["id"]
    status_filter = f"&status=eq.{status}" if status else ""
    rows = await _supabase_get(
        "care_plans",
        f"user_id=eq.{user_id}{status_filter}&order=created_at.desc&select=*&limit=50",
    ) or []

    plans = []
    for row in rows:
        current_value = await _compute_current_value(row.get("metric_type", "general"), user_id)
        plans.append(_row_to_plan(row, current_value))

    return CarePlanListResponse(plans=plans)


@router.post("", response_model=CarePlan, status_code=201)
async def create_care_plan(
    body: CreateCarePlanRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new care plan item."""
    user_id = current_user["id"]
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "user_id": user_id,
        "title": body.title.strip(),
        "description": body.description or None,
        "metric_type": body.metric_type,
        "target_value": body.target_value,
        "target_unit": body.target_unit or None,
        "target_date": body.target_date or None,
        "start_date": date.today().isoformat(),
        "source": body.source,
        "status": "active",
        "notes": body.notes or None,
        "created_at": now,
        "updated_at": now,
    }
    row = await _supabase_upsert("care_plans", data)
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create care plan")
    current_value = await _compute_current_value(body.metric_type, user_id)
    logger.info(f"Care plan created for user {user_id}: {body.title[:50]}")
    return _row_to_plan(row, current_value)


@router.patch("/{plan_id}", response_model=CarePlan)
async def update_care_plan(
    plan_id: str,
    body: UpdateCarePlanRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update a care plan (e.g. mark completed, change target)."""
    user_id = current_user["id"]
    existing = await _supabase_get(
        "care_plans",
        f"id=eq.{plan_id}&user_id=eq.{user_id}&select=id,metric_type&limit=1",
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Care plan not found")

    updates: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for field in ("title", "description", "metric_type", "target_value", "target_unit",
                  "target_date", "source", "status", "notes"):
        val = getattr(body, field, None)
        if val is not None:
            updates[field] = val

    row = await _supabase_patch(
        "care_plans", f"id=eq.{plan_id}&user_id=eq.{user_id}", updates
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to update care plan")
    metric_type = updates.get("metric_type") or existing[0].get("metric_type", "general")
    current_value = await _compute_current_value(metric_type, user_id)
    return _row_to_plan(row, current_value)


@router.delete("/{plan_id}", status_code=204)
async def delete_care_plan(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a care plan."""
    user_id = current_user["id"]
    existing = await _supabase_get(
        "care_plans",
        f"id=eq.{plan_id}&user_id=eq.{user_id}&select=id&limit=1",
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Care plan not found")
    await _supabase_delete("care_plans", f"id=eq.{plan_id}&user_id=eq.{user_id}")


# ── Provider: write a care plan for a patient ─────────────────────────────────

class CreatePlanForPatientRequest(BaseModel):
    share_token: str
    title: str
    description: Optional[str] = None
    metric_type: str = "general"
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    target_date: Optional[str] = None
    notes: Optional[str] = None


@router.post("/for-patient", response_model=CarePlan, status_code=201)
async def create_plan_for_patient(
    body: CreatePlanForPatientRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Provider-only: create a care plan on behalf of a patient.
    The provider authenticates normally; the patient is identified by share_token.
    Requires 'care_plans' permission in the share link.
    """
    # 1. Look up the share token
    link_rows = await _supabase_get(
        "shared_access",
        f"token=eq.{body.share_token}&select=grantor_id,permissions,expires_at&limit=1",
    )
    if not link_rows:
        raise HTTPException(status_code=404, detail="Share token not found")

    link = link_rows[0]
    # Check expiry
    if link.get("expires_at"):
        expires = datetime.fromisoformat(link["expires_at"].replace("Z", "+00:00"))
        if expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Share token has expired")

    # Check permission
    permissions = link.get("permissions") or []
    if "care_plans" not in permissions:
        raise HTTPException(status_code=403, detail="Care plan access not permitted by this share link")

    patient_id = link["grantor_id"]

    # 2. Create the care plan for the patient
    now = datetime.now(timezone.utc).isoformat()
    data = {
        "user_id": patient_id,
        "title": body.title.strip(),
        "description": body.description or None,
        "metric_type": body.metric_type,
        "target_value": body.target_value,
        "target_unit": body.target_unit or None,
        "target_date": body.target_date or None,
        "start_date": date.today().isoformat(),
        "source": "doctor",
        "status": "active",
        "notes": body.notes or None,
        "created_at": now,
        "updated_at": now,
    }
    row = await _supabase_upsert("care_plans", data)
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create care plan for patient")

    current_value = await _compute_current_value(body.metric_type, patient_id)
    logger.info(
        f"Provider {current_user['id']} created care plan '{body.title[:50]}' for patient {patient_id}"
    )
    return _row_to_plan(row, current_value)
