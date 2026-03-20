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
