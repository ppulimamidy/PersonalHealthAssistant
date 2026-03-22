"""
Care Team Sharing API.

Patients create secure share tokens and give the URL to their care team.
Recipients (doctors, nutritionists, etc.) open /share/<token> on the frontend
to see a read-only health summary — no account required.

Authenticated endpoints (require JWT):
  GET  /api/v1/share          — list the current user's share links
  POST /api/v1/share          — create a new share link
  DELETE /api/v1/share/{id}   — revoke a share link

Public endpoint (no auth):
  GET  /api/v1/share/public/{token}  — return the shared health summary
"""

import secrets
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    _supabase_get,
    _supabase_insert,
    _supabase_delete,
    _supabase_patch,
)

logger = get_logger(__name__)
router = APIRouter()


# ── Pydantic models ────────────────────────────────────────────────────────────


class CreateShareRequest(BaseModel):
    label: Optional[str] = None  # e.g. "Dr. Smith – Primary Care"
    permissions: Optional[List[str]] = None  # defaults to all sections
    expires_days: Optional[int] = None  # None = never expires


class ShareLink(BaseModel):
    id: str
    token: str
    label: Optional[str]
    permissions: List[str]
    expires_at: Optional[str]
    last_accessed_at: Optional[str]
    access_count: int
    created_at: str


_DEFAULT_PERMISSIONS = [
    "summary",
    "medications",
    "lab_results",
    "symptoms",
    "care_plans",
    "insights",
    "interventions",
    "intelligence",
]


# ── Authenticated endpoints ────────────────────────────────────────────────────


@router.get("/", response_model=List[ShareLink])
async def list_shares(current_user: dict = Depends(get_current_user)):
    """List all share links created by the current user."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "shared_access",
        f"grantor_id=eq.{user_id}&order=created_at.desc&select=*",
    )
    return [
        ShareLink(
            id=r["id"],
            token=r["token"],
            label=r.get("label"),
            permissions=r.get("permissions") or _DEFAULT_PERMISSIONS,
            expires_at=r.get("expires_at"),
            last_accessed_at=r.get("last_accessed_at"),
            access_count=r.get("access_count", 0),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.post("/", response_model=ShareLink, status_code=201)
async def create_share(
    body: CreateShareRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new share link for the current user."""
    user_id = current_user["id"]
    token = secrets.token_urlsafe(32)  # 44-char URL-safe string

    expires_at = None
    if body.expires_days:
        from datetime import timedelta

        expires_at = (
            datetime.now(timezone.utc) + timedelta(days=body.expires_days)
        ).isoformat()

    row = await _supabase_insert(
        "shared_access",
        {
            "grantor_id": user_id,
            "token": token,
            "label": body.label,
            "permissions": body.permissions or _DEFAULT_PERMISSIONS,
            "expires_at": expires_at,
        },
    )
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create share link")

    return ShareLink(
        id=row["id"],
        token=row["token"],
        label=row.get("label"),
        permissions=row.get("permissions") or _DEFAULT_PERMISSIONS,
        expires_at=row.get("expires_at"),
        last_accessed_at=None,
        access_count=0,
        created_at=row["created_at"],
    )


@router.delete("/{link_id}", status_code=204)
async def revoke_share(
    link_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Revoke (delete) a share link."""
    user_id = current_user["id"]
    deleted = await _supabase_delete(
        "shared_access",
        f"id=eq.{link_id}&grantor_id=eq.{user_id}",
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Share link not found")


# ── Public endpoint (no auth) ─────────────────────────────────────────────────


@router.get("/public/{token}")
async def get_shared_summary(token: str):
    """
    Public endpoint — no authentication required.
    Returns a read-only health summary for the given share token.
    Uses service-role credentials (bypasses RLS) to look up the token.
    """
    # 1. Look up token
    rows = await _supabase_get(
        "shared_access",
        f"token=eq.{token}&select=*&limit=1",
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    link = rows[0]

    # 2. Check expiry
    if link.get("expires_at"):
        expires = datetime.fromisoformat(link["expires_at"].replace("Z", "+00:00"))
        if expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Share link has expired")

    grantor_id = link["grantor_id"]
    permissions: list = link.get("permissions") or _DEFAULT_PERMISSIONS

    # 3. Record access (fire-and-forget — don't await)
    import asyncio

    asyncio.ensure_future(
        _supabase_patch(
            "shared_access",
            f"token=eq.{token}",
            {
                "last_accessed_at": datetime.now(timezone.utc).isoformat(),
                "access_count": link.get("access_count", 0) + 1,
            },
        )
    )

    # 4. Gather health data based on permissions
    summary: dict = {
        "label": link.get("label"),
        "permissions": permissions,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Profile / summary
    if "summary" in permissions:
        profile_rows = await _supabase_get(
            "profiles",
            f"id=eq.{grantor_id}&select=date_of_birth,biological_sex,weight_kg,height_cm&limit=1",
        )
        summary["profile"] = profile_rows[0] if profile_rows else {}

        # Health conditions
        condition_rows = await _supabase_get(
            "health_conditions",
            f"user_id=eq.{grantor_id}&is_active=eq.true&select=condition_name,condition_category",
        )
        summary["conditions"] = [c.get("condition_name", "") for c in condition_rows]

    # Medications
    if "medications" in permissions:
        med_rows = await _supabase_get(
            "medications",
            f"user_id=eq.{grantor_id}&is_active=eq.true"
            f"&select=medication_name,dosage,frequency,prescribing_doctor"
            f"&order=medication_name.asc",
        )
        summary["medications"] = [
            {
                "name": m.get("medication_name", ""),
                "dosage": m.get("dosage", ""),
                "frequency": m.get("frequency", ""),
                "prescribed_by": m.get("prescribing_doctor"),
            }
            for m in med_rows
        ]

        # 30-day adherence
        from datetime import date, timedelta

        thirty_ago = (date.today() - timedelta(days=30)).isoformat()
        adherence_rows = await _supabase_get(
            "medication_adherence_log",
            f"user_id=eq.{grantor_id}&scheduled_time=gte.{thirty_ago}&select=was_taken",
        )
        if adherence_rows:
            taken = sum(1 for r in adherence_rows if r.get("was_taken"))
            summary["medication_adherence_pct"] = round(
                taken / len(adherence_rows) * 100
            )

    # Lab results
    if "lab_results" in permissions:
        from datetime import date, timedelta
        import json as _json

        one_year_ago = (date.today() - timedelta(days=365)).isoformat()
        lab_rows = await _supabase_get(
            "lab_results",
            f"user_id=eq.{grantor_id}&test_date=gte.{one_year_ago}"
            f"&order=test_date.desc&select=test_type,test_date,biomarkers,abnormal_count"
            f"&limit=20",
        )
        # Flatten biomarkers for display
        flat_labs = []
        for lab in lab_rows:
            bms = lab.get("biomarkers") or []
            if isinstance(bms, str):
                try:
                    bms = _json.loads(bms)
                except Exception:
                    bms = []
            for bm in bms:
                if isinstance(bm, dict):
                    flat_labs.append(
                        {
                            "test_name": f"{lab.get('test_type', '')} — {bm.get('name', '')}",
                            "test_date": lab.get("test_date", ""),
                            "value": bm.get("value"),
                            "unit": bm.get("unit", ""),
                            "is_abnormal": bm.get("status") in ("abnormal", "critical"),
                            "reference_range": bm.get("reference_range"),
                        }
                    )
        summary["lab_results"] = flat_labs

    # Symptoms
    if "symptoms" in permissions:
        from datetime import date, timedelta

        thirty_ago = (date.today() - timedelta(days=30)).isoformat()
        symptom_rows = await _supabase_get(
            "symptom_journal",
            f"user_id=eq.{grantor_id}&symptom_date=gte.{thirty_ago}"
            f"&order=symptom_date.desc&select=symptom_type,severity,symptom_date,notes"
            f"&limit=50",
        )
        summary["symptoms"] = [
            {
                "symptom_name": s.get("symptom_type", ""),
                "severity": s.get("severity"),
                "date": s.get("symptom_date", ""),
                "notes": s.get("notes"),
            }
            for s in symptom_rows
        ]

        if symptom_rows:
            severities = [
                r.get("severity", 0)
                for r in symptom_rows
                if r.get("severity") is not None
            ]
            summary["avg_symptom_severity"] = (
                round(sum(severities) / len(severities), 1) if severities else None
            )

    # Care plans (with computed current_value for trajectory display)
    if "care_plans" in permissions:
        plan_rows = await _supabase_get(
            "care_plans",
            f"user_id=eq.{grantor_id}&status=eq.active&order=created_at.desc&select=title,metric_type,target_value,target_unit,target_date,source",
        )
        # Compute current_value for each metric type
        if plan_rows:
            from .care_plans import _compute_current_value as _cpv
            from datetime import date, timedelta as _td

            for plan in plan_rows:
                plan["current_value"] = await _cpv(
                    plan.get("metric_type", "general"), grantor_id
                )
        summary["care_plans"] = plan_rows

    # Insights
    if "insights" in permissions:
        insight_rows = await _supabase_get(
            "saved_insights",
            f"user_id=eq.{grantor_id}&order=created_at.desc"
            f"&select=title,summary,insight_type,category,created_at&limit=5",
        )
        if not insight_rows:
            # Fallback to ai_insights table
            insight_rows = await _supabase_get(
                "ai_insights",
                f"user_id=eq.{grantor_id}&order=created_at.desc"
                f"&select=title,summary,insight_type,category,created_at&limit=5",
            )
        summary["insights"] = insight_rows

    # N-of-1 intervention outcomes — completed trials with deltas + AI summaries
    if "interventions" in permissions:
        from datetime import date, timedelta

        ninety_ago = (date.today() - timedelta(days=90)).isoformat()
        iv_rows = await _supabase_get(
            "active_interventions",
            f"user_id=eq.{grantor_id}&status=eq.completed"
            f"&updated_at=gte.{ninety_ago}"
            f"&order=updated_at.desc"
            f"&select=id,title,recommendation_pattern,duration_days,adherence_days,outcome_delta,updated_at"
            f"&limit=10",
        )
        # Enrich with adherence_pct and flatten outcome_summary from agent_memory
        enriched = []
        for row in iv_rows or []:
            duration = max(row.get("duration_days", 7), 1)
            adherence = row.get("adherence_days", 0) or 0
            intervention_id = row.get("id", "")
            # Try to pull the AI summary from agent_memory for this intervention
            outcome_summary = None
            mem_rows = await _supabase_get(
                "agent_memory",
                f"user_id=eq.{grantor_id}&memory_type=eq.learned_pattern"
                f"&memory_key=like.intervention_outcome_%25_{intervention_id[:8]}"
                f"&limit=1",
            )
            if mem_rows:
                mv = mem_rows[0].get("memory_value") or {}
                if isinstance(mv, str):
                    import json as _json

                    try:
                        mv = _json.loads(mv)
                    except Exception:
                        mv = {}
                outcome_summary = mv.get("summary")
            enriched.append(
                {
                    "id": intervention_id,
                    "title": row.get("title"),
                    "recommendation_pattern": row.get("recommendation_pattern"),
                    "duration_days": row.get("duration_days"),
                    "adherence_days": adherence,
                    "adherence_pct": round((adherence / duration) * 100, 1),
                    "outcome_delta": row.get("outcome_delta") or {},
                    "outcome_summary": outcome_summary,
                    "completed_at": row.get("updated_at"),
                }
            )
        summary["interventions"] = enriched

    # Intelligence — AI medication/supplement recommendations + medical record insights
    if "intelligence" in permissions:
        import json as _json

        # Medication recommendations (calls the same logic as /med-intelligence/recommendations)
        from .med_intelligence_api import medication_recommendations as _med_recs_fn

        try:
            # Build a fake current_user dict for the internal call
            recs_result = await _med_recs_fn(current_user={"id": grantor_id})
            summary["medication_recommendations"] = recs_result.get(
                "recommendations", []
            )
            summary["medication_recommendations_summary"] = recs_result.get(
                "summary", ""
            )
        except Exception as e:
            logger.warning("Intelligence: med recs failed for share: %s", e)
            summary["medication_recommendations"] = []
            summary["medication_recommendations_summary"] = ""

        # Medical record insights (summaries from uploaded records)
        med_records = await _supabase_get(
            "medical_records",
            f"user_id=eq.{grantor_id}&order=created_at.desc"
            f"&select=record_type,title,ai_summary,report_date&limit=10",
        )
        summary["medical_records"] = [
            {
                "record_type": r.get("record_type", ""),
                "title": r.get("title", ""),
                "ai_summary": r.get("ai_summary", ""),
                "report_date": r.get("report_date", ""),
            }
            for r in (med_records or [])
        ]

    return summary
