"""
Caregiver / Family Mode API.

Caregivers link to another user's health profile via a share token.
Once linked, they can view that person's health summary from their own dashboard.

Endpoints:
  GET    /api/v1/caregiver/managed          — list linked profiles
  POST   /api/v1/caregiver/managed          — link a new profile via share token
  DELETE /api/v1/caregiver/managed/{id}     — unlink a managed profile
  GET    /api/v1/caregiver/managed/{id}/summary — fetch health summary for a managed profile
"""

from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    _supabase_insert,
    _supabase_delete,
)

logger = get_logger(__name__)
router = APIRouter()


class LinkProfileRequest(BaseModel):
    token: str               # share token from the managed user's account
    relationship: Optional[str] = None   # e.g. "parent", "child", "spouse"
    display_name: Optional[str] = None   # override name in the UI switcher


class ManagedProfile(BaseModel):
    id: str
    share_token: str
    label: Optional[str]           # label from shared_access
    relationship: Optional[str]
    display_name: Optional[str]
    added_at: str


@router.get("/managed", response_model=List[ManagedProfile])
async def list_managed(current_user: dict = Depends(get_current_user)):
    """List all profiles this user manages (as a caregiver)."""
    user_id = current_user["id"]

    # Join managed_profiles with shared_access to get the token + label
    rows = await _supabase_get(
        "managed_profiles",
        f"manager_id=eq.{user_id}&select=id,relationship,display_name,added_at,shared_access(token,label)&order=added_at.desc",
    )

    result = []
    for r in rows:
        sa = r.get("shared_access") or {}
        if isinstance(sa, list):
            sa = sa[0] if sa else {}
        result.append(
            ManagedProfile(
                id=r["id"],
                share_token=sa.get("token", ""),
                label=sa.get("label"),
                relationship=r.get("relationship"),
                display_name=r.get("display_name"),
                added_at=r["added_at"],
            )
        )
    return result


@router.post("/managed", response_model=ManagedProfile, status_code=201)
async def link_profile(
    body: LinkProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    """Link a new managed profile using a share token from the managed user."""
    user_id = current_user["id"]

    # Validate the token exists
    token_rows = await _supabase_get(
        "shared_access",
        f"token=eq.{body.token}&select=id,label&limit=1",
    )
    if not token_rows:
        raise HTTPException(status_code=404, detail="Share token not found")

    share = token_rows[0]
    share_token_id = share["id"]

    # Check not already linked
    existing = await _supabase_get(
        "managed_profiles",
        f"manager_id=eq.{user_id}&share_token_id=eq.{share_token_id}&limit=1",
    )
    if existing:
        raise HTTPException(status_code=409, detail="Profile already linked")

    row = await _supabase_insert(
        "managed_profiles",
        {
            "manager_id": user_id,
            "share_token_id": share_token_id,
            "relationship": body.relationship,
            "display_name": body.display_name,
        },
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to link profile")

    return ManagedProfile(
        id=row["id"],
        share_token=body.token,
        label=share.get("label"),
        relationship=row.get("relationship"),
        display_name=row.get("display_name"),
        added_at=row["added_at"],
    )


@router.delete("/managed/{link_id}", status_code=204)
async def unlink_profile(
    link_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Unlink a managed profile."""
    user_id = current_user["id"]
    deleted = await _supabase_delete(
        "managed_profiles",
        f"id=eq.{link_id}&manager_id=eq.{user_id}",
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Managed profile not found")


# ── Provider / Caregiver alerts endpoint ──────────────────────────────────────

class PatientAlert(BaseModel):
    managed_id: str
    patient_label: str
    metric_name: str
    current_value: Optional[float]
    target_value: Optional[float]
    type: str          # "care_plan" | "lab"
    severity: str      # "warning" | "critical"


@router.get("/alerts", response_model=List[PatientAlert])
async def get_patient_alerts(current_user: dict = Depends(get_current_user)):
    """
    Return out-of-range alerts across all managed patients.
    Checks: care plan target deviation > 20%, abnormal lab results in last 14 days.
    """
    from .care_plans import _compute_current_value

    user_id = current_user["id"]
    alerts: List[PatientAlert] = []

    # Fetch all managed profiles
    rows = await _supabase_get(
        "managed_profiles",
        f"manager_id=eq.{user_id}&select=id,relationship,display_name,shared_access(token,label,grantor_id)&order=added_at.desc",
    ) or []

    fourteen_ago = (date.today() - timedelta(days=14)).isoformat()

    for row in rows:
        sa = row.get("shared_access") or {}
        if isinstance(sa, list):
            sa = sa[0] if sa else {}

        grantor_id = sa.get("grantor_id")
        if not grantor_id:
            continue

        managed_id = row["id"]
        patient_label = row.get("display_name") or sa.get("label") or "Patient"

        # 1. Care plan alerts
        try:
            plans = await _supabase_get(
                "care_plans",
                f"user_id=eq.{grantor_id}&status=eq.active&select=title,metric_type,target_value,target_unit",
            ) or []
            for plan in plans:
                tv = plan.get("target_value")
                mt = plan.get("metric_type", "general")
                if tv is None or mt in ("general", "steps", "sleep_score", "lab_result"):
                    continue
                try:
                    tv = float(tv)
                except (TypeError, ValueError):
                    continue
                current = await _compute_current_value(mt, grantor_id)
                if current is None:
                    continue
                # Deviation check
                lower_better = mt == "symptom_severity"
                if lower_better:
                    deviation = current - tv  # positive = worse
                else:
                    deviation = tv - current  # positive = below target

                if deviation > tv * 0.2:  # >20% off target
                    severity = "critical" if deviation > tv * 0.4 else "warning"
                    alerts.append(PatientAlert(
                        managed_id=managed_id,
                        patient_label=patient_label,
                        metric_name=plan.get("title", mt.replace("_", " ").title()),
                        current_value=round(current, 1),
                        target_value=tv,
                        type="care_plan",
                        severity=severity,
                    ))
        except Exception as exc:
            logger.warning(f"Care plan alert check failed for {grantor_id}: {exc}")

        # 2. Abnormal lab alerts (last 14 days)
        try:
            labs = await _supabase_get(
                "lab_results",
                f"user_id=eq.{grantor_id}&test_date=gte.{fourteen_ago}&select=test_type,biomarkers",
            ) or []
            for lab in labs:
                biomarkers = lab.get("biomarkers") or []
                if isinstance(biomarkers, str):
                    import json
                    try:
                        biomarkers = json.loads(biomarkers)
                    except Exception:
                        biomarkers = []
                for bm in biomarkers:
                    status = bm.get("status", "")
                    if status in ("abnormal", "critical"):
                        alerts.append(PatientAlert(
                            managed_id=managed_id,
                            patient_label=patient_label,
                            metric_name=f"{bm.get('biomarker_name', '?')} ({lab.get('test_type', 'lab')})",
                            current_value=bm.get("value"),
                            target_value=None,
                            type="lab",
                            severity="critical" if status == "critical" else "warning",
                        ))
                        break  # one alert per lab result
        except Exception as exc:
            logger.warning(f"Lab alert check failed for {grantor_id}: {exc}")

    return alerts
