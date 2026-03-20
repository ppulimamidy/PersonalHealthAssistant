"""
Lab Intelligence API — contextual analysis connecting labs ↔ medications ↔ supplements.

Provides:
- Post-upload insights (AI analysis referencing meds, supplements, conditions)
- Biomarker chart data with treatment markers
- Medication lab evidence (proving treatment effectiveness)
- Supplement gap detection
- Smart retest reminders
- Treatment summary for home screen
"""

import asyncio
import json
import os
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get

logger = get_logger(__name__)
router = APIRouter()

# Nutrient → biomarker mapping for gap detection
NUTRIENT_BIOMARKER_MAP: Dict[str, List[str]] = {
    "iron": ["ferritin", "iron", "serum_iron"],
    "vitamin_d": ["vitamin_d", "25_oh_vitamin_d", "25_hydroxy_vitamin_d"],
    "b12": ["b12", "vitamin_b12", "cobalamin"],
    "folate": ["folate", "folic_acid"],
    "magnesium": ["magnesium", "mg"],
    "calcium": ["calcium", "ca"],
    "omega_3": [],  # No standard lab marker — inferred from triglycerides
    "zinc": ["zinc", "zn"],
}

# Supplement name patterns → nutrient key
SUPPLEMENT_NUTRIENT_MAP = {
    "iron": "iron",
    "ferrous": "iron",
    "vitamin d": "vitamin_d",
    "d3": "vitamin_d",
    "cholecalciferol": "vitamin_d",
    "b12": "b12",
    "methylcobalamin": "b12",
    "cyanocobalamin": "b12",
    "folate": "folate",
    "folic acid": "folate",
    "magnesium": "magnesium",
    "calcium": "calcium",
    "omega": "omega_3",
    "fish oil": "omega_3",
    "zinc": "zinc",
}

# Condition → required tests + intervals (days)
CONDITION_TEST_MAP: Dict[str, List[Dict[str, Any]]] = {
    "type_2_diabetes": [
        {"test": "A1C / HbA1c", "interval": 90, "reason": "Diabetes monitoring"},
        {
            "test": "Metabolic Panel",
            "interval": 180,
            "reason": "Kidney function + glucose",
        },
        {"test": "Lipid Panel", "interval": 365, "reason": "Cardiovascular risk"},
    ],
    "pcos": [
        {"test": "Hormone Panel", "interval": 180, "reason": "PCOS management"},
        {
            "test": "Metabolic Panel",
            "interval": 180,
            "reason": "Insulin resistance check",
        },
    ],
    "hypothyroidism": [
        {"test": "Thyroid Panel", "interval": 180, "reason": "Thyroid monitoring"},
    ],
    "hypertension": [
        {"test": "Metabolic Panel", "interval": 180, "reason": "Electrolytes + kidney"},
        {"test": "Lipid Panel", "interval": 365, "reason": "Cardiovascular risk"},
    ],
}

# Medication → required monitoring
MEDICATION_TEST_MAP: Dict[str, List[Dict[str, Any]]] = {
    "metformin": [
        {"test": "A1C / HbA1c", "interval": 90, "reason": "Metformin efficacy"},
        {"test": "B12", "interval": 365, "reason": "Metformin depletes B12"},
        {"test": "Metabolic Panel", "interval": 180, "reason": "Kidney function"},
    ],
    "statin": [
        {"test": "Lipid Panel", "interval": 180, "reason": "Statin efficacy"},
        {"test": "Liver Function", "interval": 365, "reason": "Statin hepatotoxicity"},
    ],
    "levothyroxine": [
        {"test": "Thyroid Panel", "interval": 180, "reason": "Thyroid dose adjustment"},
    ],
    "ace_inhibitor": [
        {"test": "Metabolic Panel", "interval": 180, "reason": "Kidney + potassium"},
    ],
    "lisinopril": [
        {"test": "Metabolic Panel", "interval": 180, "reason": "Kidney + potassium"},
    ],
}


# ---------------------------------------------------------------------------
# Context Gathering
# ---------------------------------------------------------------------------


async def _gather_lab_context(user_id: str) -> Dict[str, Any]:
    """Gather full context for lab intelligence — all fetches in parallel."""
    (
        labs,
        medications,
        supplements,
        conditions,
        profile_rows,
        wearable,
        experiments,
    ) = await asyncio.gather(
        _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&order=test_date.desc&limit=50"
            f"&select=id,test_date,test_type,biomarkers,abnormal_count,ai_summary",
        ),
        _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=id,medication_name,dosage,frequency,start_date,indication",
        ),
        _supabase_get(
            "supplements",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=id,supplement_name,dosage,start_date,purpose",
        ),
        _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=condition_name,condition_category",
        ),
        _supabase_get(
            "profiles",
            f"id=eq.{user_id}"
            f"&select=date_of_birth,biological_sex,weight_kg,height_cm,full_name",
        ),
        _supabase_get(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&date=eq.{date.today().isoformat()}"
            f"&select=metric_type,score,latest_value",
        ),
        _supabase_get(
            "active_interventions",
            f"user_id=eq.{user_id}&status=eq.active"
            f"&select=title,started_at,duration_days&limit=3",
        ),
    )

    # Parse biomarkers from JSONB
    for lab in labs:
        bm = lab.get("biomarkers") or []
        if isinstance(bm, str):
            try:
                bm = json.loads(bm)
            except (json.JSONDecodeError, TypeError):
                bm = []
        lab["biomarkers"] = bm if isinstance(bm, list) else []

    # Demographics
    profile = profile_rows[0] if profile_rows else {}
    dob = profile.get("date_of_birth")
    age = None
    if dob:
        try:
            birth = date.fromisoformat(str(dob)[:10])
            age = (date.today() - birth).days // 365
        except (ValueError, TypeError):
            pass

    return {
        "labs": labs,
        "medications": medications,
        "supplements": supplements,
        "conditions": [c.get("condition_name", "") for c in conditions],
        "demographics": {
            "age": age,
            "sex": profile.get("biological_sex"),
            "weight_kg": profile.get("weight_kg"),
            "first_name": (profile.get("full_name") or "").split(" ")[0] or None,
        },
        "wearable": {w.get("metric_type", ""): w.get("latest_value") for w in wearable},
        "experiments": experiments,
    }


def _normalize_biomarker_name(name: str) -> str:
    """Normalize biomarker name for matching."""
    return name.lower().strip().replace(" ", "_").replace("-", "_")


def _find_supplement_nutrient(supp_name: str) -> Optional[str]:
    """Map a supplement name to its nutrient key."""
    lower = supp_name.lower()
    for pattern, nutrient in SUPPLEMENT_NUTRIENT_MAP.items():
        if pattern in lower:
            return nutrient
    return None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


class PostUploadInsightRequest(BaseModel):
    lab_result_id: Optional[str] = None
    biomarkers: Optional[List[Dict[str, Any]]] = None
    test_type: Optional[str] = None
    test_date: Optional[str] = None


class SupplementGap(BaseModel):
    biomarker: str
    status: str
    value: float
    unit: str
    suggested_supplement: str
    reason: str


class PostUploadInsightResponse(BaseModel):
    insight: str
    headline: str
    biomarker_count: int
    abnormal_count: int
    supplement_gaps: List[SupplementGap]
    quick_actions: List[str]


@router.post("/post-upload-insight", response_model=PostUploadInsightResponse)
async def post_upload_insight(
    body: PostUploadInsightRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate personalized AI insight after lab upload."""
    user_id = current_user["id"]
    ctx = await _gather_lab_context(user_id)

    # Get the lab result — either by ID or from body
    biomarkers: List[Dict[str, Any]] = []
    test_type = body.test_type or "Lab Panel"
    test_date_str = body.test_date or date.today().isoformat()

    if body.lab_result_id and ctx["labs"]:
        for lab in ctx["labs"]:
            if lab.get("id") == body.lab_result_id:
                biomarkers = lab.get("biomarkers", [])
                test_type = lab.get("test_type", test_type)
                test_date_str = lab.get("test_date", test_date_str)
                break
    elif body.biomarkers:
        biomarkers = body.biomarkers

    if not biomarkers and ctx["labs"]:
        # Use most recent lab
        biomarkers = ctx["labs"][0].get("biomarkers", [])
        test_type = ctx["labs"][0].get("test_type", test_type)
        test_date_str = ctx["labs"][0].get("test_date", test_date_str)

    biomarker_count = len(biomarkers)
    abnormal = [
        b
        for b in biomarkers
        if isinstance(b, dict)
        and b.get("status") in ("abnormal", "critical", "borderline")
    ]
    abnormal_count = len(abnormal)

    # Detect supplement gaps
    supplement_gaps = _detect_supplement_gaps(biomarkers, ctx["supplements"])

    # Build headline
    if abnormal_count == 0:
        headline = f"All {biomarker_count} biomarkers look good"
    else:
        headline = f"{abnormal_count} of {biomarker_count} biomarkers need attention"

    # Build AI prompt
    first_name = ctx["demographics"].get("first_name") or "there"
    demo = ctx["demographics"]
    demo_text = f"{first_name}"
    if demo.get("age"):
        demo_text += f", {demo['age']}yo"
    if demo.get("sex"):
        demo_text += f" {demo['sex']}"

    bm_lines = []
    for b in biomarkers:
        if not isinstance(b, dict):
            continue
        status = b.get("status", "unknown")
        marker = (
            "⚠️"
            if status in ("abnormal", "critical")
            else "✓"
            if status == "normal"
            else "~"
        )
        bm_lines.append(
            f"  {marker} {b.get('name', '?')}: {b.get('value', '?')} {b.get('unit', '')} [{status}]"
        )

    # Previous labs for comparison
    prev_summary = ""
    prev_labs = [
        l
        for l in ctx["labs"]
        if l.get("test_type") == test_type and l.get("test_date", "") < test_date_str
    ]
    if prev_labs:
        prev = prev_labs[0]
        prev_summary = f"\nPrevious {test_type} ({prev.get('test_date', '?')}): "
        prev_bms = prev.get("biomarkers", [])
        for pb in prev_bms[:5]:
            if isinstance(pb, dict):
                prev_summary += f"{pb.get('name', '?')}={pb.get('value', '?')}, "

    meds_text = (
        ", ".join(
            f"{m.get('medication_name', '?')} {m.get('dosage', '')} (since {m.get('start_date', '?')})"
            for m in ctx["medications"]
        )
        or "None"
    )

    supps_text = (
        ", ".join(
            f"{s.get('supplement_name', '?')} {s.get('dosage', '')}"
            for s in ctx["supplements"]
        )
        or "None"
    )

    conditions_text = ", ".join(ctx["conditions"]) or "None"

    gaps_text = ""
    if supplement_gaps:
        gaps_text = "\nSUPPLEMENT GAPS DETECTED:\n" + "\n".join(
            f"  - {g.biomarker} is {g.status} ({g.value} {g.unit}) — no {g.suggested_supplement} supplement"
            for g in supplement_gaps
        )

    prompt = f"""You are a lab results analyst for {demo_text}.

LAB RESULT: {test_type}, {test_date_str}
{chr(10).join(bm_lines)}
{prev_summary}

ACTIVE MEDICATIONS: {meds_text}
ACTIVE SUPPLEMENTS: {supps_text}
HEALTH CONDITIONS: {conditions_text}
{gaps_text}

Generate a 2-3 sentence personalized analysis. Rules:
- Address {first_name} by name
- Highlight the most important finding first
- If a biomarker improved/worsened vs previous, correlate with medication timing
- If a nutrient is low and no supplement covers it, flag the gap
- Reference conditions to explain why specific biomarkers matter
- Be encouraging about improvements, gentle about concerns
- End with one clear next action
- Return ONLY the insight text"""

    insight = await _call_claude(prompt, max_tokens=300)

    # Quick actions
    quick_actions = []
    if supplement_gaps:
        quick_actions.append("Adjust supplements")
    quick_actions.append("Share with doctor")
    if abnormal_count > 0:
        quick_actions.append("Set retest reminder")

    return PostUploadInsightResponse(
        insight=insight,
        headline=headline,
        biomarker_count=biomarker_count,
        abnormal_count=abnormal_count,
        supplement_gaps=supplement_gaps,
        quick_actions=quick_actions,
    )


def _detect_supplement_gaps(
    biomarkers: List[Dict[str, Any]], supplements: list
) -> List[SupplementGap]:
    """Cross-reference low biomarkers with active supplements to find gaps."""
    # Build set of nutrients covered by supplements
    covered_nutrients: set = set()
    for s in supplements:
        nutrient = _find_supplement_nutrient(s.get("supplement_name", ""))
        if nutrient:
            covered_nutrients.add(nutrient)

    gaps: List[SupplementGap] = []
    for bm in biomarkers:
        if not isinstance(bm, dict):
            continue
        if bm.get("status") not in ("abnormal", "critical", "borderline"):
            continue

        norm_name = _normalize_biomarker_name(bm.get("name", ""))
        # Check if this biomarker maps to a nutrient
        for nutrient, biomarker_names in NUTRIENT_BIOMARKER_MAP.items():
            if norm_name in biomarker_names or any(
                alias in norm_name for alias in biomarker_names
            ):
                if nutrient not in covered_nutrients:
                    gaps.append(
                        SupplementGap(
                            biomarker=bm.get("name", "Unknown"),
                            status=bm.get("status", "unknown"),
                            value=bm.get("value", 0),
                            unit=bm.get("unit", ""),
                            suggested_supplement=nutrient.replace("_", " ").title(),
                            reason=f"Your {bm.get('name', '')} is {bm.get('status', '')} "
                            f"but you're not taking a {nutrient.replace('_', ' ')} supplement",
                        )
                    )
                break

    return gaps


@router.get("/biomarker-chart/{biomarker_name}")
async def biomarker_chart(
    biomarker_name: str,
    current_user: dict = Depends(get_current_user),
):
    """Get time-series data for a biomarker with medication/supplement markers."""
    user_id = current_user["id"]
    ctx = await _gather_lab_context(user_id)
    norm_target = _normalize_biomarker_name(biomarker_name)

    # Collect data points from all labs
    data_points: List[Dict[str, Any]] = []
    display_name = biomarker_name
    unit = ""

    for lab in reversed(ctx["labs"]):  # chronological order
        for bm in lab.get("biomarkers", []):
            if not isinstance(bm, dict):
                continue
            norm_bm = _normalize_biomarker_name(bm.get("name", ""))
            if (
                norm_bm == norm_target
                or norm_target in norm_bm
                or norm_bm in norm_target
            ):
                display_name = bm.get("name", biomarker_name)
                unit = bm.get("unit", unit)
                data_points.append(
                    {
                        "date": lab.get("test_date", ""),
                        "value": bm.get("value"),
                        "status": bm.get("status", "unknown"),
                    }
                )

    # Medication markers
    med_markers = [
        {
            "date": m.get("start_date", ""),
            "label": f"Started {m.get('medication_name', '?')} {m.get('dosage', '')}".strip(),
            "type": "med_start",
        }
        for m in ctx["medications"]
        if m.get("start_date")
    ]

    # Supplement markers
    supp_markers = [
        {
            "date": s.get("start_date", ""),
            "label": f"Started {s.get('supplement_name', '?')} {s.get('dosage', '')}".strip(),
            "type": "supp_start",
        }
        for s in ctx["supplements"]
        if s.get("start_date")
    ]

    return {
        "biomarker": norm_target,
        "display_name": display_name,
        "unit": unit,
        "data_points": data_points,
        "medication_markers": med_markers,
        "supplement_markers": supp_markers,
    }


@router.get("/supplement-gaps")
async def get_supplement_gaps(
    current_user: dict = Depends(get_current_user),
):
    """Detect nutrient gaps from latest labs vs active supplements."""
    user_id = current_user["id"]
    ctx = await _gather_lab_context(user_id)

    if not ctx["labs"]:
        return {"gaps": [], "redundancies": []}

    latest_biomarkers = ctx["labs"][0].get("biomarkers", [])
    gaps = _detect_supplement_gaps(latest_biomarkers, ctx["supplements"])

    # Detect redundancies (supplement for already-optimal biomarker)
    redundancies: List[Dict[str, Any]] = []
    for s in ctx["supplements"]:
        nutrient = _find_supplement_nutrient(s.get("supplement_name", ""))
        if not nutrient:
            continue
        for bm in latest_biomarkers:
            if not isinstance(bm, dict):
                continue
            norm_bm = _normalize_biomarker_name(bm.get("name", ""))
            biomarker_names = NUTRIENT_BIOMARKER_MAP.get(nutrient, [])
            if norm_bm in biomarker_names and bm.get("status") == "normal":
                val = bm.get("value", 0)
                # Only flag if well within normal
                redundancies.append(
                    {
                        "supplement": s.get("supplement_name"),
                        "biomarker": bm.get("name"),
                        "value": val,
                        "unit": bm.get("unit", ""),
                        "status": "normal",
                        "note": f"Your {bm.get('name')} is already normal — "
                        f"discuss with your doctor if you still need this supplement",
                    }
                )
                break

    return {"gaps": [g.model_dump() for g in gaps], "redundancies": redundancies}


@router.get("/retest-schedule")
async def retest_schedule(
    current_user: dict = Depends(get_current_user),
):
    """Smart retest recommendations based on conditions and medications."""
    user_id = current_user["id"]
    ctx = await _gather_lab_context(user_id)

    # Build required tests from conditions
    required: Dict[str, Dict[str, Any]] = {}  # test_type → {interval, reason}

    for condition in ctx["conditions"]:
        norm_cond = condition.lower().replace(" ", "_").replace("'", "")
        tests = CONDITION_TEST_MAP.get(norm_cond, [])
        for t in tests:
            key = t["test"].lower()
            if key not in required or t["interval"] < required[key]["interval"]:
                required[key] = {
                    "test": t["test"],
                    "interval": t["interval"],
                    "reason": t["reason"],
                }

    for med in ctx["medications"]:
        med_name = (med.get("medication_name") or "").lower()
        for pattern, tests in MEDICATION_TEST_MAP.items():
            if pattern in med_name:
                for t in tests:
                    key = t["test"].lower()
                    if key not in required or t["interval"] < required[key]["interval"]:
                        required[key] = {
                            "test": t["test"],
                            "interval": t["interval"],
                            "reason": t["reason"],
                        }

    # Default if nothing specific
    if not required:
        required["cbc"] = {"test": "CBC", "interval": 365, "reason": "Annual wellness"}
        required["metabolic panel"] = {
            "test": "Metabolic Panel",
            "interval": 365,
            "reason": "Annual wellness",
        }

    # Find last lab date per test type
    last_dates: Dict[str, str] = {}
    for lab in ctx["labs"]:
        tt = (lab.get("test_type") or "").lower()
        if tt and tt not in last_dates:
            last_dates[tt] = lab.get("test_date", "")

    # Compute schedule
    today_iso = date.today().isoformat()
    schedule: List[Dict[str, Any]] = []

    for key, info in required.items():
        last = last_dates.get(key, "")
        if last:
            try:
                last_d = date.fromisoformat(last[:10])
                due_date = last_d + timedelta(days=info["interval"])
                days_until = (due_date - date.today()).days
            except (ValueError, TypeError):
                days_until = 0
        else:
            days_until = 0  # Never done → overdue

        if days_until <= 0:
            status = "overdue"
        elif days_until <= 30:
            status = "due_soon"
        else:
            status = "on_track"

        schedule.append(
            {
                "test_type": info["test"],
                "last_date": last or None,
                "interval_days": info["interval"],
                "days_until_due": days_until,
                "status": status,
                "reason": info["reason"],
            }
        )

    # Sort: overdue first, then due_soon, then on_track
    priority = {"overdue": 0, "due_soon": 1, "on_track": 2}
    schedule.sort(key=lambda x: (priority.get(x["status"], 3), x["days_until_due"]))

    return {"schedule": schedule}


@router.get("/med-evidence/{medication_id}")
async def medication_lab_evidence(
    medication_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get lab-validated effectiveness evidence for a medication."""
    user_id = current_user["id"]
    ctx = await _gather_lab_context(user_id)

    # Find the medication
    med = None
    for m in ctx["medications"]:
        if m.get("id") == medication_id:
            med = m
            break

    if not med:
        return {"medication": None, "evidence": []}

    med_name = med.get("medication_name", "")
    start_date = med.get("start_date", "")
    indication = (med.get("indication") or "").lower()

    # Determine relevant biomarkers based on medication
    relevant_biomarkers: set = set()
    med_lower = med_name.lower()

    if "metformin" in med_lower:
        relevant_biomarkers = {"hba1c", "a1c", "glucose", "fasting_glucose"}
    elif (
        "statin" in med_lower
        or "atorvastatin" in med_lower
        or "rosuvastatin" in med_lower
    ):
        relevant_biomarkers = {
            "ldl",
            "ldl_cholesterol",
            "total_cholesterol",
            "triglycerides",
            "hdl",
        }
    elif "levothyroxine" in med_lower or "synthroid" in med_lower:
        relevant_biomarkers = {"tsh", "free_t4", "t4", "t3"}
    elif "lisinopril" in med_lower or "amlodipine" in med_lower:
        relevant_biomarkers = {"potassium", "creatinine", "bun"}

    if not relevant_biomarkers and indication:
        # Try to infer from indication
        if "diabetes" in indication or "glucose" in indication:
            relevant_biomarkers = {"hba1c", "glucose"}
        elif "cholesterol" in indication or "lipid" in indication:
            relevant_biomarkers = {"ldl", "total_cholesterol", "triglycerides"}

    # Get before/after values
    evidence: List[Dict[str, Any]] = []
    for target_bm in relevant_biomarkers:
        before_values: List[Dict[str, Any]] = []
        after_values: List[Dict[str, Any]] = []

        for lab in ctx["labs"]:
            lab_date = lab.get("test_date", "")
            for bm in lab.get("biomarkers", []):
                if not isinstance(bm, dict):
                    continue
                norm = _normalize_biomarker_name(bm.get("name", ""))
                if norm == target_bm or target_bm in norm:
                    entry = {
                        "date": lab_date,
                        "value": bm.get("value"),
                        "status": bm.get("status"),
                        "name": bm.get("name"),
                        "unit": bm.get("unit", ""),
                    }
                    if start_date and lab_date < start_date:
                        before_values.append(entry)
                    else:
                        after_values.append(entry)

        if not after_values:
            continue

        baseline = before_values[0]["value"] if before_values else None
        current = after_values[0]["value"]  # Most recent (labs ordered desc)

        delta_pct = None
        verdict = "insufficient_data"
        if baseline is not None and baseline != 0:
            delta_pct = round(((current - baseline) / abs(baseline)) * 100, 1)
            if abs(delta_pct) < 5:
                verdict = "no_change"
            elif delta_pct < 0:
                # Decrease — good for most things (cholesterol, glucose, A1C)
                verdict = "improving"
            else:
                verdict = "worsening"

        evidence.append(
            {
                "biomarker": after_values[0].get("name", target_bm),
                "unit": after_values[0].get("unit", ""),
                "baseline": baseline,
                "baseline_date": before_values[0]["date"] if before_values else None,
                "current": current,
                "current_date": after_values[0]["date"],
                "delta_pct": delta_pct,
                "verdict": verdict,
            }
        )

    return {
        "medication": {
            "name": med_name,
            "dosage": med.get("dosage"),
            "start_date": start_date,
        },
        "evidence": evidence,
    }


@router.get("/treatment-summary")
async def treatment_summary(
    current_user: dict = Depends(get_current_user),
):
    """Compact treatment intelligence for the home screen card."""
    user_id = current_user["id"]
    ctx = await _gather_lab_context(user_id)

    # Med adherence today
    today_iso = date.today().isoformat()
    adherence_logs = await _supabase_get(
        "medication_adherence_log",
        f"user_id=eq.{user_id}&scheduled_time=gte.{today_iso}T00:00:00"
        f"&scheduled_time=lte.{today_iso}T23:59:59"
        f"&select=was_taken",
    )
    meds_total = len(ctx["medications"])
    meds_taken = sum(1 for log in adherence_logs if log.get("was_taken"))

    # Lab trends — compare latest vs previous for key biomarkers
    lab_trends: List[Dict[str, Any]] = []
    if len(ctx["labs"]) >= 2:
        latest = ctx["labs"][0]
        previous = ctx["labs"][1]
        for bm in latest.get("biomarkers", [])[:5]:
            if not isinstance(bm, dict):
                continue
            name = bm.get("name", "")
            curr_val = bm.get("value")
            # Find same biomarker in previous
            for pbm in previous.get("biomarkers", []):
                if isinstance(pbm, dict) and pbm.get("name") == name:
                    prev_val = pbm.get("value")
                    if curr_val is not None and prev_val is not None and prev_val != 0:
                        direction = (
                            "improving"
                            if curr_val < prev_val
                            else "worsening"
                            if curr_val > prev_val
                            else "stable"
                        )
                        lab_trends.append(
                            {
                                "name": name,
                                "direction": direction,
                                "current": curr_val,
                                "previous": prev_val,
                            }
                        )
                    break

    # Supplement gaps
    supplement_gaps = []
    if ctx["labs"]:
        gaps = _detect_supplement_gaps(
            ctx["labs"][0].get("biomarkers", []), ctx["supplements"]
        )
        supplement_gaps = [g.biomarker for g in gaps]

    # Next retest
    retest_data = await retest_schedule(current_user=current_user)
    next_retest = None
    for item in retest_data.get("schedule", []):
        if item["status"] in ("overdue", "due_soon"):
            next_retest = {
                "test": item["test_type"],
                "days": item["days_until_due"],
                "status": item["status"],
            }
            break

    return {
        "has_data": len(ctx["labs"]) > 0,
        "medications": {
            "total": meds_total,
            "taken_today": meds_taken,
        },
        "lab_trends": lab_trends[:3],
        "supplement_gaps": supplement_gaps,
        "next_retest": next_retest,
    }


# ---------------------------------------------------------------------------
# Session 1-4: Lab Summary, Recommended Tests, Doctor Note
# ---------------------------------------------------------------------------

# Biomarker → body system mapping
BIOMARKER_SYSTEM_MAP: Dict[str, str] = {
    # Metabolic
    "glucose": "metabolic",
    "fasting_glucose": "metabolic",
    "hba1c": "metabolic",
    "a1c": "metabolic",
    "insulin": "metabolic",
    "fasting_insulin": "metabolic",
    "c_peptide": "metabolic",
    # Cardiovascular
    "total_cholesterol": "cardiovascular",
    "ldl": "cardiovascular",
    "ldl_cholesterol": "cardiovascular",
    "hdl": "cardiovascular",
    "hdl_cholesterol": "cardiovascular",
    "triglycerides": "cardiovascular",
    "apob": "cardiovascular",
    "lp_a": "cardiovascular",
    "lpa": "cardiovascular",
    "homocysteine": "cardiovascular",
    "hs_crp": "inflammation",
    "crp": "inflammation",
    # Blood
    "hemoglobin": "blood",
    "hematocrit": "blood",
    "wbc": "blood",
    "white_blood_cells": "blood",
    "rbc": "blood",
    "red_blood_cells": "blood",
    "platelets": "blood",
    "mcv": "blood",
    "mch": "blood",
    "mchc": "blood",
    # Thyroid
    "tsh": "thyroid",
    "free_t4": "thyroid",
    "free_t3": "thyroid",
    "t4": "thyroid",
    "t3": "thyroid",
    "reverse_t3": "thyroid",
    "tpo": "thyroid",
    "tpo_antibodies": "thyroid",
    # Liver
    "alt": "liver",
    "ast": "liver",
    "alp": "liver",
    "bilirubin": "liver",
    "albumin": "liver",
    "ggt": "liver",
    "alanine_aminotransferase": "liver",
    "aspartate_aminotransferase": "liver",
    # Kidney
    "creatinine": "kidney",
    "bun": "kidney",
    "egfr": "kidney",
    "uric_acid": "kidney",
    "microalbumin": "kidney",
    # Nutrients
    "vitamin_d": "nutrients",
    "25_oh_vitamin_d": "nutrients",
    "b12": "nutrients",
    "vitamin_b12": "nutrients",
    "folate": "nutrients",
    "folic_acid": "nutrients",
    "ferritin": "nutrients",
    "iron": "nutrients",
    "serum_iron": "nutrients",
    "magnesium": "nutrients",
    "zinc": "nutrients",
    # Hormones
    "estradiol": "hormones",
    "progesterone": "hormones",
    "testosterone": "hormones",
    "free_testosterone": "hormones",
    "fsh": "hormones",
    "lh": "hormones",
    "dhea_s": "hormones",
    "shbg": "hormones",
    "cortisol": "hormones",
    "amh": "hormones",
    "prolactin": "hormones",
}

SYSTEM_LABELS: Dict[str, str] = {
    "metabolic": "Metabolic",
    "cardiovascular": "Cardiovascular",
    "blood": "Blood",
    "thyroid": "Thyroid",
    "liver": "Liver",
    "kidney": "Kidney",
    "nutrients": "Nutrients",
    "hormones": "Hormones",
    "inflammation": "Inflammation",
}

SYSTEM_ICONS: Dict[str, str] = {
    "metabolic": "flame-outline",
    "cardiovascular": "heart-outline",
    "blood": "water-outline",
    "thyroid": "body-outline",
    "liver": "fitness-outline",
    "kidney": "medical-outline",
    "nutrients": "leaf-outline",
    "hormones": "pulse-outline",
    "inflammation": "alert-circle-outline",
}

# Optimal ranges (tighter than "normal")
OPTIMAL_RANGES: Dict[str, Dict[str, float]] = {
    "ferritin": {"optimal_min": 50, "optimal_max": 150},
    "vitamin_d": {"optimal_min": 50, "optimal_max": 80},
    "25_oh_vitamin_d": {"optimal_min": 50, "optimal_max": 80},
    "b12": {"optimal_min": 500, "optimal_max": 900},
    "vitamin_b12": {"optimal_min": 500, "optimal_max": 900},
    "tsh": {"optimal_min": 1.0, "optimal_max": 2.5},
    "hs_crp": {"optimal_min": 0, "optimal_max": 1.0},
    "hba1c": {"optimal_min": 4.0, "optimal_max": 5.4},
    "a1c": {"optimal_min": 4.0, "optimal_max": 5.4},
    "fasting_insulin": {"optimal_min": 2, "optimal_max": 8},
}

# Advanced biomarker recommendations
ADVANCED_BIOMARKERS: List[Dict[str, Any]] = [
    {
        "test_name": "ApoB",
        "system": "cardiovascular",
        "why": "Better CV risk predictor than LDL — counts atherogenic particles. 'Normal' LDL + high ApoB = hidden risk.",
        "who": "Anyone with CV risk factors, family history, or metabolic syndrome",
        "frequency": "annually",
        "one_time": False,
        "conditions": [
            "heart_disease",
            "metabolic_syndrome",
            "type_2_diabetes",
            "pcos",
        ],
        "priority": "high",
    },
    {
        "test_name": "Lp(a)",
        "system": "cardiovascular",
        "why": "Genetic lipoprotein — 20% of people have elevated levels. Dramatically increases heart attack risk. Standard lipids miss it entirely.",
        "who": "Everyone once, especially with family history of early heart disease",
        "frequency": "one-time",
        "one_time": True,
        "conditions": [],
        "priority": "high",
    },
    {
        "test_name": "Fasting Insulin",
        "system": "metabolic",
        "why": "Catches insulin resistance 10-15 years before glucose goes abnormal. Standard panels only show glucose.",
        "who": "Everyone 35+, PCOS, family diabetes history, weight concerns",
        "frequency": "annually",
        "one_time": False,
        "conditions": ["pcos", "type_2_diabetes", "metabolic_syndrome", "weight_loss"],
        "priority": "high",
    },
    {
        "test_name": "hs-CRP",
        "system": "inflammation",
        "why": "High-sensitivity CRP measures chronic low-grade inflammation — a key driver of heart disease, metabolic issues, and autoimmune flares.",
        "who": "Everyone 40+, autoimmune conditions, metabolic syndrome",
        "frequency": "annually",
        "one_time": False,
        "conditions": ["autoimmune", "heart_disease", "type_2_diabetes"],
        "priority": "medium",
    },
    {
        "test_name": "Homocysteine",
        "system": "cardiovascular",
        "why": "Elevated = cardiovascular + neurological risk. Often fixable with B6, B12, and folate supplementation.",
        "who": "Everyone 40+, CV risk, MTHFR mutations",
        "frequency": "annually",
        "one_time": False,
        "conditions": ["heart_disease"],
        "priority": "medium",
    },
    {
        "test_name": "RBC Magnesium",
        "system": "nutrients",
        "why": "Serum magnesium is nearly useless — body maintains levels by pulling from cells. RBC magnesium shows true cellular status.",
        "who": "Muscle cramps, anxiety, sleep issues, heart palpitations",
        "frequency": "annually",
        "one_time": False,
        "conditions": ["sleep_optimization", "mental_health"],
        "priority": "medium",
    },
    {
        "test_name": "Omega-3 Index",
        "system": "cardiovascular",
        "why": "RBC membrane omega-3 content. Predicts CV risk better than counting fish oil pills. Target: 8-12%.",
        "who": "Everyone, especially if not eating fatty fish 2x/week",
        "frequency": "annually",
        "one_time": False,
        "conditions": [],
        "priority": "low",
    },
    {
        "test_name": "Free T3",
        "system": "thyroid",
        "why": "Active thyroid hormone. TSH + Free T4 can look normal while Free T3 is low (poor conversion). Explains persistent fatigue.",
        "who": "Anyone with fatigue, weight issues, cold intolerance with 'normal' TSH",
        "frequency": "with thyroid panel",
        "one_time": False,
        "conditions": ["hypothyroidism"],
        "priority": "high",
    },
    {
        "test_name": "Reverse T3",
        "system": "thyroid",
        "why": "Blocks T3 from working even when levels look normal. Elevated by stress, illness, calorie restriction.",
        "who": "Thyroid symptoms with normal standard panel",
        "frequency": "with thyroid panel",
        "one_time": False,
        "conditions": ["hypothyroidism"],
        "priority": "medium",
    },
    {
        "test_name": "TPO Antibodies",
        "system": "thyroid",
        "why": "Catches autoimmune thyroid (Hashimoto's) years before TSH goes abnormal. 1 in 8 women affected.",
        "who": "Women 30+, family history of autoimmune disease, thyroid symptoms",
        "frequency": "one-time (unless positive, then monitor)",
        "one_time": True,
        "conditions": ["hypothyroidism", "autoimmune"],
        "priority": "high",
    },
    {
        "test_name": "DHEA-S",
        "system": "hormones",
        "why": "Adrenal health marker. Declines with age. Correlates with energy, immunity, and hormone balance.",
        "who": "Women 35+, chronic fatigue, low libido, chronic stress",
        "frequency": "annually",
        "one_time": False,
        "conditions": ["pcos", "mental_health"],
        "priority": "medium",
    },
    {
        "test_name": "Ferritin",
        "system": "nutrients",
        "why": "Iron storage — not just 'are you anemic.' Low ferritin (even 'in range') causes fatigue, hair loss, brain fog. Optimal: 50-150.",
        "who": "Menstruating women, athletes, vegetarians",
        "frequency": "annually",
        "one_time": False,
        "conditions": [],
        "priority": "medium",
    },
    {
        "test_name": "Urine Microalbumin",
        "system": "kidney",
        "why": "Earliest marker of kidney damage. Standard panels (creatinine/BUN) only catch damage after significant loss.",
        "who": "Diabetics, hypertensives, long-term NSAID users",
        "frequency": "annually",
        "one_time": False,
        "conditions": ["type_2_diabetes", "hypertension"],
        "priority": "high",
    },
    {
        "test_name": "GGT",
        "system": "liver",
        "why": "Liver enzyme indicating oxidative stress. Goes abnormal before ALT/AST. Also reflects alcohol impact and metabolic liver disease.",
        "who": "Metabolic syndrome, alcohol consumption, liver concerns",
        "frequency": "annually",
        "one_time": False,
        "conditions": ["metabolic_syndrome"],
        "priority": "low",
    },
]

# Standard age/sex screening
STANDARD_SCREENING: List[Dict[str, Any]] = [
    {
        "test_name": "CBC",
        "age_min": 18,
        "sex": "all",
        "frequency": "annually",
        "reason": "General health baseline",
    },
    {
        "test_name": "Metabolic Panel",
        "age_min": 18,
        "sex": "all",
        "frequency": "annually",
        "reason": "Organ function + electrolytes",
    },
    {
        "test_name": "Lipid Panel",
        "age_min": 20,
        "sex": "all",
        "frequency": "annually",
        "reason": "Cardiovascular risk",
    },
    {
        "test_name": "Thyroid Panel (TSH)",
        "age_min": 35,
        "sex": "female",
        "frequency": "every 5 years",
        "reason": "Thyroid screening — risk increases with age",
    },
    {
        "test_name": "Thyroid Panel (TSH)",
        "age_min": 40,
        "sex": "all",
        "frequency": "every 5 years",
        "reason": "Thyroid screening",
    },
    {
        "test_name": "Vitamin D",
        "age_min": 30,
        "sex": "all",
        "frequency": "annually",
        "reason": "Widespread deficiency affecting immunity, bones, mood",
    },
    {
        "test_name": "Hemoglobin A1C",
        "age_min": 35,
        "sex": "all",
        "frequency": "every 3 years",
        "reason": "Diabetes screening",
    },
    {
        "test_name": "FSH + Estradiol",
        "age_min": 40,
        "age_max": 55,
        "sex": "female",
        "frequency": "as needed",
        "reason": "Perimenopause assessment",
    },
    {
        "test_name": "DEXA Bone Density",
        "age_min": 50,
        "sex": "female",
        "frequency": "every 2 years",
        "reason": "Post-menopausal bone loss screening",
    },
    {
        "test_name": "Estradiol + FSH + Calcium + Vitamin D",
        "age_min": 50,
        "sex": "female",
        "frequency": "annually",
        "reason": "Post-menopausal health monitoring",
    },
    {
        "test_name": "PSA (discuss with doctor)",
        "age_min": 50,
        "sex": "male",
        "frequency": "annually",
        "reason": "Prostate screening",
    },
    {
        "test_name": "Testosterone (Total + Free)",
        "age_min": 40,
        "sex": "male",
        "frequency": "as needed",
        "reason": "Andropause assessment if symptoms present",
    },
    {
        "test_name": "B12",
        "age_min": 50,
        "sex": "all",
        "frequency": "annually",
        "reason": "Absorption decreases with age",
    },
    {
        "test_name": "Ferritin",
        "age_min": 18,
        "sex": "female",
        "frequency": "annually",
        "reason": "Iron stores — menstrual blood loss risk",
    },
]


@router.get("/lab-summary")
async def lab_summary(
    current_user: dict = Depends(get_current_user),
):
    """Structured summary of latest labs grouped by body system."""
    user_id = current_user["id"]
    ctx = await _gather_lab_context(user_id)

    if not ctx["labs"]:
        return {"systems": [], "watch_items": [], "doctor_discussion": []}

    latest = ctx["labs"][0]
    biomarkers = latest.get("biomarkers", [])
    test_type = latest.get("test_type", "Lab Panel")
    test_date = latest.get("test_date", "")

    # Find previous lab of same type for deltas
    prev_map: Dict[str, float] = {}
    for lab in ctx["labs"][1:]:
        if lab.get("test_type") == test_type:
            for bm in lab.get("biomarkers", []):
                if isinstance(bm, dict) and bm.get("name"):
                    norm = _normalize_biomarker_name(bm["name"])
                    if norm not in prev_map and bm.get("value") is not None:
                        prev_map[norm] = bm["value"]
            break

    # Group by system
    systems_data: Dict[str, List[Dict[str, Any]]] = {}
    for bm in biomarkers:
        if not isinstance(bm, dict):
            continue
        name = bm.get("name", "")
        norm = _normalize_biomarker_name(name)
        system = BIOMARKER_SYSTEM_MAP.get(norm, "other")
        if system not in systems_data:
            systems_data[system] = []

        entry: Dict[str, Any] = {
            "name": name,
            "value": bm.get("value"),
            "unit": bm.get("unit", ""),
            "status": bm.get("status", "unknown"),
            "reference_range": bm.get("reference_range"),
        }

        # Delta vs previous
        if norm in prev_map and bm.get("value") is not None:
            entry["previous"] = prev_map[norm]
            entry["delta"] = round(bm["value"] - prev_map[norm], 2)

        # Optimal range check
        if norm in OPTIMAL_RANGES and bm.get("status") == "normal":
            opt = OPTIMAL_RANGES[norm]
            val = bm.get("value", 0)
            if val < opt["optimal_min"] or val > opt["optimal_max"]:
                entry["optimal_flag"] = True
                entry["optimal_range"] = f"{opt['optimal_min']}-{opt['optimal_max']}"

        systems_data[system].append(entry)

    # Build system summaries
    systems: List[Dict[str, Any]] = []
    for sys_key, bms in systems_data.items():
        normal_count = sum(1 for b in bms if b["status"] == "normal")
        has_abnormal = any(b["status"] in ("abnormal", "critical") for b in bms)
        has_borderline = any(b["status"] == "borderline" for b in bms)
        status = (
            "has_abnormal"
            if has_abnormal
            else "has_borderline"
            if has_borderline
            else "all_normal"
        )
        systems.append(
            {
                "key": sys_key,
                "name": SYSTEM_LABELS.get(sys_key, sys_key.title()),
                "icon": SYSTEM_ICONS.get(sys_key, "ellipse-outline"),
                "status": status,
                "total": len(bms),
                "normal_count": normal_count,
                "biomarkers": bms,
            }
        )
    systems.sort(
        key=lambda s: {"has_abnormal": 0, "has_borderline": 1, "all_normal": 2}[
            s["status"]
        ]
    )

    # Watch items
    watch_items: List[Dict[str, Any]] = []
    for bm in biomarkers:
        if not isinstance(bm, dict):
            continue
        if bm.get("status") in ("abnormal", "critical", "borderline"):
            norm = _normalize_biomarker_name(bm.get("name", ""))
            delta_text = ""
            if norm in prev_map and bm.get("value") is not None:
                d = bm["value"] - prev_map[norm]
                delta_text = f" ({'↑' if d > 0 else '↓'}{abs(round(d, 1))} vs previous)"

            watch_items.append(
                {
                    "biomarker": bm.get("name", ""),
                    "value": bm.get("value"),
                    "unit": bm.get("unit", ""),
                    "status": bm.get("status"),
                    "delta_text": delta_text,
                }
            )

    # HOMA-IR auto-calculation
    glucose_val = None
    insulin_val = None
    for bm in biomarkers:
        if not isinstance(bm, dict):
            continue
        norm = _normalize_biomarker_name(bm.get("name", ""))
        if norm in ("glucose", "fasting_glucose") and bm.get("value"):
            glucose_val = bm["value"]
        elif norm in ("insulin", "fasting_insulin") and bm.get("value"):
            insulin_val = bm["value"]
    homa_ir = None
    if glucose_val and insulin_val:
        homa_ir = round((glucose_val * insulin_val) / 405, 2)

    # Doctor discussion — AI-generated
    first_name = ctx["demographics"].get("first_name") or "there"
    demo = ctx["demographics"]
    conditions_text = ", ".join(ctx["conditions"]) or "None"
    meds_text = (
        ", ".join(m.get("medication_name", "") for m in ctx["medications"]) or "None"
    )

    if watch_items:
        watch_text = "\n".join(
            f"- {w['biomarker']}: {w['value']} {w['unit']} ({w['status']}){w['delta_text']}"
            for w in watch_items
        )
        prompt = f"""You are a lab results analyst for {first_name} ({demo.get('age', '?')}yo {demo.get('sex', '?')}).
Conditions: {conditions_text}. Medications: {meds_text}.

These biomarkers need attention:
{watch_text}
{"HOMA-IR calculated: " + str(homa_ir) if homa_ir else ""}

Generate a JSON array of the top 3 doctor discussion items. Each item:
{{"finding": "short title", "what_it_means": "1 sentence plain language", "what_to_ask": "specific question for doctor", "follow_up": "recommended action"}}

Return ONLY valid JSON array, no markdown."""

        raw = await _call_claude(prompt, max_tokens=500)
        try:
            if "```" in raw:
                raw = raw[raw.find("[") : raw.rfind("]") + 1]
            doctor_discussion = json.loads(raw)
            if not isinstance(doctor_discussion, list):
                doctor_discussion = []
        except (json.JSONDecodeError, ValueError):
            doctor_discussion = []
    else:
        doctor_discussion = []

    return {
        "test_type": test_type,
        "test_date": test_date,
        "systems": systems,
        "watch_items": watch_items,
        "doctor_discussion": doctor_discussion,
        "homa_ir": homa_ir,
    }


@router.get("/recommended-tests")
async def recommended_tests(
    current_user: dict = Depends(get_current_user),
):
    """Age/sex/condition-based test recommendations + advanced biomarkers."""
    user_id = current_user["id"]
    ctx = await _gather_lab_context(user_id)
    demo = ctx["demographics"]
    age = demo.get("age") or 30
    sex = demo.get("sex") or "all"
    conditions = [c.lower().replace(" ", "_") for c in ctx["conditions"]]
    first_name = demo.get("first_name") or "there"

    # Collect all biomarkers ever tested
    tested_biomarkers: set = set()
    tested_test_types: set = set()
    for lab in ctx["labs"]:
        tt = (lab.get("test_type") or "").lower()
        if tt:
            tested_test_types.add(tt)
        for bm in lab.get("biomarkers", []):
            if isinstance(bm, dict) and bm.get("name"):
                tested_biomarkers.add(_normalize_biomarker_name(bm["name"]))

    # Standard screening recommendations
    standard: List[Dict[str, Any]] = []
    for s in STANDARD_SCREENING:
        if age < s.get("age_min", 0):
            continue
        if s.get("age_max") and age > s["age_max"]:
            continue
        if s.get("sex", "all") != "all" and s["sex"] != sex:
            continue
        test_lower = s["test_name"].lower()
        ever_tested = any(t in test_lower or test_lower in t for t in tested_test_types)
        standard.append(
            {
                "test_name": s["test_name"],
                "category": "standard",
                "reason": s["reason"],
                "frequency": s.get("frequency", "annually"),
                "ever_tested": ever_tested,
                "priority": "medium",
            }
        )

    # Advanced biomarker recommendations
    advanced: List[Dict[str, Any]] = []
    for ab in ADVANCED_BIOMARKERS:
        norm = _normalize_biomarker_name(ab["test_name"])
        ever_tested = norm in tested_biomarkers

        # Compute relevance for this user
        relevant = False
        personalized_reason = ab["why"]

        # Check condition relevance
        if ab.get("conditions"):
            for cond in conditions:
                if any(c in cond for c in ab["conditions"]):
                    relevant = True
                    personalized_reason = (
                        f"With your {cond.replace('_', ' ')}, {ab['why'][:100]}"
                    )
                    break

        # Age/sex relevance
        if not relevant:
            if (
                sex == "female"
                and age >= 35
                and ab["system"] in ("hormones", "thyroid")
            ):
                relevant = True
            elif age >= 40 and ab["system"] in ("cardiovascular", "metabolic"):
                relevant = True
            elif ab["priority"] == "high":
                relevant = True

        if relevant or not ab.get("conditions"):
            advanced.append(
                {
                    "test_name": ab["test_name"],
                    "category": "advanced",
                    "system": ab["system"],
                    "why": ab["why"],
                    "who": ab["who"],
                    "personalized_reason": personalized_reason,
                    "frequency": ab["frequency"],
                    "one_time": ab.get("one_time", False),
                    "ever_tested": ever_tested,
                    "priority": ab["priority"],
                }
            )

    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    advanced.sort(
        key=lambda x: (priority_order.get(x["priority"], 3), x["ever_tested"])
    )

    return {
        "user_profile": f"{first_name}, {age}yo {sex}",
        "conditions": ctx["conditions"],
        "standard": standard,
        "advanced": advanced,
    }


@router.post("/doctor-note")
async def generate_doctor_note(
    current_user: dict = Depends(get_current_user),
):
    """Generate a shareable doctor discussion note."""
    user_id = current_user["id"]
    ctx = await _gather_lab_context(user_id)
    demo = ctx["demographics"]
    first_name = demo.get("first_name") or "Patient"
    age = demo.get("age") or "?"
    sex = demo.get("sex") or "?"

    # Get recommended tests
    recs = await recommended_tests(current_user=current_user)
    retest = await retest_schedule(current_user=current_user)

    # Build note
    lines: List[str] = [
        f"Lab Test Discussion Notes for {first_name}",
        f"Generated by Vitalix · {date.today().strftime('%B %d, %Y')}",
        f"Profile: {age}yo {sex}",
    ]
    if ctx["conditions"]:
        lines.append(f"Conditions: {', '.join(ctx['conditions'])}")
    if ctx["medications"]:
        lines.append(
            f"Medications: {', '.join(m.get('medication_name', '') + ' ' + m.get('dosage', '') for m in ctx['medications'])}"
        )
    lines.append("")

    # Recommended tests not yet done
    untested_advanced = [
        t for t in recs.get("advanced", []) if not t.get("ever_tested")
    ]
    if untested_advanced:
        lines.append("RECOMMENDED TESTS TO DISCUSS:")
        for t in untested_advanced[:8]:
            lines.append(
                f"  ○ {t['test_name']} — {t.get('personalized_reason', t.get('why', ''))[:100]}"
            )
        lines.append("")

    # Retest due
    due_tests = [
        t for t in retest.get("schedule", []) if t["status"] in ("overdue", "due_soon")
    ]
    if due_tests:
        lines.append("RETEST DUE:")
        for t in due_tests:
            status_txt = (
                f"{abs(t['days_until_due'])}d overdue"
                if t["status"] == "overdue"
                else f"due in {t['days_until_due']}d"
            )
            lines.append(f"  ○ {t['test_type']} — {status_txt} ({t['reason']})")
        lines.append("")

    # Watch items from latest labs
    if ctx["labs"]:
        latest = ctx["labs"][0]
        abnormals = [
            bm
            for bm in latest.get("biomarkers", [])
            if isinstance(bm, dict)
            and bm.get("status") in ("abnormal", "critical", "borderline")
        ]
        if abnormals:
            lines.append("CURRENT WATCH ITEMS:")
            for bm in abnormals[:5]:
                lines.append(
                    f"  ○ {bm.get('name', '?')}: {bm.get('value', '?')} {bm.get('unit', '')} ({bm.get('status', '')})"
                )
            lines.append("")

    lines.append("---")
    lines.append(
        "Note: This is not medical advice. Discuss all findings with your healthcare provider."
    )

    return {"note_text": "\n".join(lines)}


# ---------------------------------------------------------------------------
# Claude helper
# ---------------------------------------------------------------------------


async def _call_claude(prompt: str, max_tokens: int = 300) -> str:
    """Call Claude for lab analysis."""
    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "Upload your lab results to receive personalized analysis."

        client = anthropic.AsyncAnthropic(api_key=api_key)
        result = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return result.content[0].text.strip()
    except Exception as e:
        logger.error("Claude call failed for lab analysis: %s", e)
        return "Your lab results have been saved. Review the biomarker details below."
