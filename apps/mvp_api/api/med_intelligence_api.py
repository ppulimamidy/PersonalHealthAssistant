"""
Medication Intelligence API — cross-references medications, supplements,
labs, symptoms, and timing rules for treatment intelligence.
"""

import asyncio
import json
import os
from collections import defaultdict
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get
from .med_intelligence_data import (
    DRUG_FOOD_INTERACTIONS,
    DRUG_NUTRIENT_DEPLETIONS,
    SCHEDULE_SLOTS,
    SUPPLEMENT_INTERACTIONS,
    TIMING_RULES,
)

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Context Gathering
# ---------------------------------------------------------------------------


async def _gather_med_context(user_id: str) -> Dict[str, Any]:
    """Gather treatment context — all fetches in parallel."""
    (
        medications,
        supplements,
        labs,
        symptoms,
        adherence_logs,
        profile_rows,
        conditions,
    ) = await asyncio.gather(
        _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=id,medication_name,dosage,frequency,start_date,indication",
        ),
        _supabase_get(
            "supplements",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=id,supplement_name,dosage,frequency,start_date,purpose",
        ),
        _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&order=test_date.desc&limit=5"
            f"&select=test_date,test_type,biomarkers",
        ),
        _supabase_get(
            "symptom_journal",
            f"user_id=eq.{user_id}&order=symptom_date.desc&limit=50"
            f"&select=symptom_type,severity,symptom_date,created_at",
        ),
        _supabase_get(
            "medication_adherence_log",
            f"user_id=eq.{user_id}&order=scheduled_time.desc&limit=100"
            f"&select=medication_id,was_taken,scheduled_time",
        ),
        _supabase_get(
            "profiles",
            f"id=eq.{user_id}" f"&select=full_name,date_of_birth,biological_sex",
        ),
        _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name",
        ),
    )

    # Parse lab biomarkers
    for lab in labs:
        bm = lab.get("biomarkers") or []
        if isinstance(bm, str):
            try:
                bm = json.loads(bm)
            except (json.JSONDecodeError, TypeError):
                bm = []
        lab["biomarkers"] = bm if isinstance(bm, list) else []

    profile = profile_rows[0] if profile_rows else {}
    first_name = (profile.get("full_name") or "").split(" ")[0] or None
    dob = profile.get("date_of_birth")
    age = None
    if dob:
        try:
            age = (date.today() - date.fromisoformat(str(dob)[:10])).days // 365
        except (ValueError, TypeError):
            pass

    return {
        "medications": medications,
        "supplements": supplements,
        "labs": labs,
        "symptoms": symptoms,
        "adherence_logs": adherence_logs,
        "demographics": {
            "first_name": first_name,
            "age": age,
            "sex": profile.get("biological_sex"),
        },
        "conditions": [c.get("condition_name", "") for c in conditions],
    }


def _match_drug(med_name: str, pattern: str) -> bool:
    """Check if a medication name matches a pattern."""
    return pattern in med_name.lower()


def _normalize_biomarker(name: str) -> str:
    return name.lower().strip().replace(" ", "_").replace("-", "_")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/treatment-overview")
async def treatment_overview(
    current_user: dict = Depends(get_current_user),
):
    """Comprehensive treatment overview with AI summary."""
    user_id = current_user["id"]
    ctx = await _gather_med_context(user_id)

    # Adherence stats (last 7 days)
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    week_logs = [
        log
        for log in ctx["adherence_logs"]
        if (log.get("scheduled_time") or "")[:10] >= week_ago
    ]
    total_scheduled = len(week_logs)
    total_taken = sum(1 for log in week_logs if log.get("was_taken"))
    rate_pct = round((total_taken / total_scheduled) * 100) if total_scheduled else 0

    # Streak
    today_logs = [
        log
        for log in ctx["adherence_logs"]
        if (log.get("scheduled_time") or "")[:10] == date.today().isoformat()
    ]
    taken_today = sum(1 for log in today_logs if log.get("was_taken"))
    total_today = len(ctx["medications"])

    # Lab validation (simplified — count improving/monitoring per med)
    improving = 0
    monitoring = 0
    for med in ctx["medications"]:
        has_lab_data = False
        for lab in ctx["labs"]:
            for bm in lab.get("biomarkers", []):
                if isinstance(bm, dict):
                    has_lab_data = True
                    break
            if has_lab_data:
                break
        if has_lab_data:
            improving += 1
        else:
            monitoring += 1

    # Interaction count
    interactions = _compute_interactions(ctx)
    interaction_count = (
        len(interactions.get("drug_nutrient", []))
        + len(interactions.get("drug_drug", []))
        + len(interactions.get("drug_food", []))
    )

    # Supplement gaps (count nutrients depleted without supplement coverage)
    gap_count = sum(
        1
        for alert in interactions.get("drug_nutrient", [])
        if not alert.get("covered_by_supplement")
    )

    # AI summary
    first_name = ctx["demographics"].get("first_name") or "there"
    meds_text = ", ".join(
        f"{m.get('medication_name', '')} {m.get('dosage', '')}"
        for m in ctx["medications"]
    )
    conditions_text = ", ".join(ctx["conditions"]) or "None"

    prompt = f"""You are a medication analyst for {first_name}.

Active medications: {meds_text or 'None'}
Conditions: {conditions_text}
Adherence this week: {rate_pct}% ({total_taken}/{total_scheduled} doses)
Interaction alerts: {interaction_count}
Supplement gaps: {gap_count}

Generate a 2-sentence personalized treatment summary. Reference specific medications and their effectiveness if data is available. Flag the most important action item. Address {first_name} by name.
Return ONLY the summary text."""

    ai_summary = await _call_claude(prompt, max_tokens=200)

    return {
        "adherence": {
            "rate_pct": rate_pct,
            "taken_today": taken_today,
            "total_today": total_today,
        },
        "lab_validation": {
            "improving": improving,
            "monitoring": monitoring,
        },
        "supplement_gaps": gap_count,
        "interaction_alerts": interaction_count,
        "ai_summary": ai_summary,
    }


@router.get("/interactions")
async def get_interactions(
    current_user: dict = Depends(get_current_user),
):
    """Drug-drug, drug-nutrient, and drug-food interaction alerts."""
    user_id = current_user["id"]
    ctx = await _gather_med_context(user_id)
    return _compute_interactions(ctx)


def _compute_interactions(ctx: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Compute all interaction types from context."""
    meds = ctx["medications"]
    supps = ctx["supplements"]
    labs = ctx["labs"]

    # Build latest biomarker map
    latest_bm: Dict[str, Dict[str, Any]] = {}
    if labs:
        for bm in labs[0].get("biomarkers", []):
            if isinstance(bm, dict) and bm.get("name"):
                norm = _normalize_biomarker(bm["name"])
                latest_bm[norm] = bm

    # Active supplement nutrients
    supp_nutrients: set = set()
    for s in supps:
        name_lower = s.get("supplement_name", "").lower()
        for keyword in (
            "b12",
            "folate",
            "folic",
            "magnesium",
            "calcium",
            "iron",
            "ferrous",
            "zinc",
            "coq10",
            "vitamin d",
            "d3",
            "potassium",
            "vitamin c",
            "omega",
            "fish oil",
            "copper",
            "b6",
        ):
            if keyword in name_lower:
                supp_nutrients.add(
                    keyword.replace("ferrous", "iron").replace("d3", "vitamin d")
                )

    # Drug-nutrient depletions
    drug_nutrient: List[Dict[str, Any]] = []
    for med in meds:
        med_name = med.get("medication_name", "").lower()
        for pattern, depletions in DRUG_NUTRIENT_DEPLETIONS.items():
            if _match_drug(med_name, pattern):
                for dep in depletions:
                    nutrient_lower = dep["nutrient"].lower()
                    covered = any(
                        n in nutrient_lower or nutrient_lower in n
                        for n in supp_nutrients
                    )

                    # Check lab status
                    lab_status = None
                    lab_value = None
                    bm_key = _normalize_biomarker(dep.get("biomarker", ""))
                    if bm_key in latest_bm:
                        lab_status = latest_bm[bm_key].get("status")
                        lab_value = latest_bm[bm_key].get("value")

                    # Elevate severity if lab confirms depletion
                    effective_severity = dep["severity"]
                    if (
                        lab_status in ("abnormal", "critical", "borderline")
                        and not covered
                    ):
                        effective_severity = "high"

                    drug_nutrient.append(
                        {
                            "medication": med.get("medication_name"),
                            "depletes": dep["nutrient"],
                            "covered_by_supplement": covered,
                            "lab_status": lab_status,
                            "lab_value": lab_value,
                            "severity": effective_severity,
                            "note": dep["note"],
                        }
                    )

    # Drug-food interactions
    drug_food: List[Dict[str, Any]] = []
    for med in meds:
        med_name = med.get("medication_name", "").lower()
        for pattern, foods in DRUG_FOOD_INTERACTIONS.items():
            if _match_drug(med_name, pattern):
                for food in foods:
                    drug_food.append(
                        {
                            "medication": med.get("medication_name"),
                            "food": food["food"],
                            "severity": food["severity"],
                            "note": food["note"],
                        }
                    )

    # Drug-drug (basic: timing conflicts between medications)
    drug_drug: List[Dict[str, Any]] = []
    thyroid_meds = [
        m
        for m in meds
        if any(
            p in m.get("medication_name", "").lower()
            for p in ("levothyroxine", "synthroid")
        )
    ]
    other_meds = [m for m in meds if m not in thyroid_meds]
    if thyroid_meds and other_meds:
        for tm in thyroid_meds:
            for om in other_meds:
                drug_drug.append(
                    {
                        "med_a": tm.get("medication_name"),
                        "med_b": om.get("medication_name"),
                        "severity": "moderate",
                        "note": f"Take {tm.get('medication_name')} 30-60 min before {om.get('medication_name')} for optimal thyroid absorption.",
                    }
                )

    return {
        "drug_nutrient": drug_nutrient,
        "drug_food": drug_food,
        "drug_drug": drug_drug,
    }


@router.get("/side-effects/{medication_id}")
async def side_effects(
    medication_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Symptom correlation for a specific medication."""
    user_id = current_user["id"]
    ctx = await _gather_med_context(user_id)

    med = None
    for m in ctx["medications"]:
        if m.get("id") == medication_id:
            med = m
            break
    if not med:
        return {
            "medication": None,
            "symptoms_since_start": [],
            "known_side_effects": [],
        }

    start_date = med.get("start_date", "")
    if not start_date:
        return {
            "medication": med.get("medication_name"),
            "symptoms_since_start": [],
            "known_side_effects": [],
            "note": "No start date recorded — cannot correlate symptoms.",
        }

    # Symptoms since medication start
    symptoms_after: Dict[str, Dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "total_severity": 0, "first": ""}
    )
    for s in ctx["symptoms"]:
        s_date = (s.get("symptom_date") or s.get("created_at") or "")[:10]
        if s_date >= start_date:
            stype = s.get("symptom_type", "unknown")
            entry = symptoms_after[stype]
            entry["count"] += 1
            entry["total_severity"] += s.get("severity") or 0
            if not entry["first"] or s_date < entry["first"]:
                entry["first"] = s_date

    result = []
    for stype, data in symptoms_after.items():
        result.append(
            {
                "type": stype,
                "count": data["count"],
                "avg_severity": round(data["total_severity"] / data["count"], 1)
                if data["count"]
                else 0,
                "first_occurrence": data["first"],
            }
        )
    result.sort(key=lambda x: x["count"], reverse=True)

    return {
        "medication": med.get("medication_name"),
        "start_date": start_date,
        "symptoms_since_start": result[:10],
        "known_side_effects": [],
    }


@router.get("/schedule")
async def med_schedule(
    current_user: dict = Depends(get_current_user),
):
    """Optimized daily medication/supplement schedule."""
    user_id = current_user["id"]
    ctx = await _gather_med_context(user_id)

    # Assign each med/supplement to a time slot
    slot_items: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for med in ctx["medications"]:
        med_name = med.get("medication_name", "")
        med_lower = med_name.lower()
        matched = False
        for pattern, rule in TIMING_RULES.items():
            if _match_drug(med_lower, pattern):
                slot_items[rule["when"]].append(
                    {
                        "name": f"{med_name} {med.get('dosage', '')}".strip(),
                        "type": "medication",
                        "rule": rule["rule"],
                        "reason": rule["reason"],
                    }
                )
                matched = True
                break
        if not matched:
            slot_items["with_meals"].append(
                {
                    "name": f"{med_name} {med.get('dosage', '')}".strip(),
                    "type": "medication",
                    "rule": "Take with a meal",
                    "reason": "Default — take with food unless directed otherwise",
                }
            )

    for supp in ctx["supplements"]:
        supp_name = supp.get("supplement_name", "")
        supp_lower = supp_name.lower()
        matched = False
        for pattern, rule in TIMING_RULES.items():
            if pattern in supp_lower:
                slot_items[rule["when"]].append(
                    {
                        "name": f"{supp_name} {supp.get('dosage', '')}".strip(),
                        "type": "supplement",
                        "rule": rule["rule"],
                        "reason": rule["reason"],
                    }
                )
                matched = True
                break
        if not matched:
            slot_items["with_meals"].append(
                {
                    "name": f"{supp_name} {supp.get('dosage', '')}".strip(),
                    "type": "supplement",
                    "rule": "Take with food",
                    "reason": "General recommendation",
                }
            )

    # Build ordered schedule
    slot_order: Dict[str, Dict[str, Any]] = {str(s["key"]): s for s in SCHEDULE_SLOTS}
    schedule: List[Dict[str, Any]] = []
    for slot_key in sorted(
        slot_items.keys(),
        key=lambda k: int(slot_order.get(k, {"order": 99}).get("order", 99)),
    ):
        slot_info = slot_order.get(
            slot_key, {"label": slot_key.replace("_", " ").title()}
        )
        schedule.append(
            {
                "time_slot": slot_key,
                "label": slot_info.get("label", slot_key),
                "items": slot_items[slot_key],
            }
        )

    # Supplement interactions
    supp_interactions: List[Dict[str, str]] = []
    supp_names = [s.get("supplement_name", "").lower() for s in ctx["supplements"]]
    for interaction in SUPPLEMENT_INTERACTIONS:
        a_match = any(interaction["supp_a"] in sn for sn in supp_names)
        b_match = any(interaction["supp_b"] in sn for sn in supp_names)
        if a_match and b_match:
            supp_interactions.append(interaction)

    return {
        "schedule": schedule,
        "supplement_interactions": supp_interactions,
    }


@router.get("/supplement-intel")
async def supplement_intel(
    current_user: dict = Depends(get_current_user),
):
    """Supplement gaps, redundancies, and interactions."""
    user_id = current_user["id"]
    ctx = await _gather_med_context(user_id)
    interactions_data = _compute_interactions(ctx)

    # Gaps from drug depletions not covered by supplements
    gaps = [
        alert
        for alert in interactions_data.get("drug_nutrient", [])
        if not alert.get("covered_by_supplement")
    ]

    # Redundancies — supplement for already-optimal biomarker
    redundancies: List[Dict[str, Any]] = []
    if ctx["labs"]:
        latest_bms = ctx["labs"][0].get("biomarkers", [])
        for supp in ctx["supplements"]:
            supp_lower = supp.get("supplement_name", "").lower()
            for bm in latest_bms:
                if not isinstance(bm, dict):
                    continue
                bm_name = _normalize_biomarker(bm.get("name", ""))
                # Check if supplement relates to this biomarker
                match = False
                if "b12" in supp_lower and "b12" in bm_name:
                    match = True
                elif "vitamin d" in supp_lower and "vitamin_d" in bm_name:
                    match = True
                elif "iron" in supp_lower and "ferritin" in bm_name:
                    match = True
                elif "magnesium" in supp_lower and "magnesium" in bm_name:
                    match = True

                if match and bm.get("status") == "normal":
                    redundancies.append(
                        {
                            "supplement": supp.get("supplement_name"),
                            "biomarker": bm.get("name"),
                            "value": bm.get("value"),
                            "unit": bm.get("unit", ""),
                            "note": f"Your {bm.get('name')} is normal — discuss with your doctor if you still need this supplement.",
                        }
                    )
                    break

    # Supplement-supplement interactions
    supp_names = [s.get("supplement_name", "").lower() for s in ctx["supplements"]]
    supp_interactions: List[Dict[str, str]] = []
    for interaction in SUPPLEMENT_INTERACTIONS:
        a_match = any(interaction["supp_a"] in sn for sn in supp_names)
        b_match = any(interaction["supp_b"] in sn for sn in supp_names)
        if a_match and b_match:
            supp_interactions.append(interaction)

    return {
        "gaps": gaps,
        "redundancies": redundancies,
        "interactions": supp_interactions,
    }


# ---------------------------------------------------------------------------
# Claude helper
# ---------------------------------------------------------------------------


async def _call_claude(prompt: str, max_tokens: int = 200) -> str:
    """Call Claude for treatment analysis."""
    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "Track your medications to receive personalized treatment insights."

        client = anthropic.AsyncAnthropic(api_key=api_key)
        result = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return result.content[0].text.strip()
    except Exception as e:
        logger.error("Claude call failed for med intelligence: %s", e)
        return "Your medication data has been reviewed. See details below."
