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
# Medication Recommendations (no active meds)
# ---------------------------------------------------------------------------


@router.get("/recommendations")
async def medication_recommendations(
    current_user: dict = Depends(get_current_user),
):
    """Generate medication/supplement recommendations based on the user's
    health profile (conditions, labs, medical records, symptoms) even when
    they have no medications logged. Returns structured recommendations
    for doctor discussion. Results are cached for 7 days and invalidated
    when underlying health data changes."""
    user_id = current_user["id"]

    # Check cache first
    import hashlib

    cached_rows = await _supabase_get(
        "ai_analysis_cache",
        f"user_id=eq.{user_id}&analysis_type=eq.medication_recommendations&limit=1",
    )
    # We'll validate the cache after gathering context (to compare data_hash)

    # Gather all health context in parallel
    (conditions, labs, medical_records, symptoms, profile_rows,) = await asyncio.gather(
        _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name,severity,diagnosed_date",
        ),
        _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&order=test_date.desc&limit=10"
            f"&select=test_date,test_type,biomarkers",
        ),
        _supabase_get(
            "medical_records",
            f"user_id=eq.{user_id}&order=created_at.desc&limit=5"
            f"&select=record_type,title,ai_summary,extracted_data",
        ),
        _supabase_get(
            "symptom_journal",
            f"user_id=eq.{user_id}&order=symptom_date.desc&limit=30"
            f"&select=symptom_type,severity,symptom_date",
        ),
        _supabase_get(
            "profiles",
            f"id=eq.{user_id}&select=full_name,date_of_birth,biological_sex",
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

    # Parse medical record extracted_data
    for rec in medical_records:
        ed = rec.get("extracted_data")
        if isinstance(ed, str):
            try:
                rec["extracted_data"] = json.loads(ed)
            except Exception:
                rec["extracted_data"] = {}

    profile = profile_rows[0] if profile_rows else {}
    first_name = (profile.get("full_name") or "").split(" ")[0] or "there"
    dob = profile.get("date_of_birth")
    age = None
    if dob:
        try:
            age = (date.today() - date.fromisoformat(str(dob)[:10])).days // 365
        except (ValueError, TypeError):
            pass

    # Build context for Claude
    ctx_parts: list[str] = []
    if age:
        ctx_parts.append(f"Age: {age}, Sex: {profile.get('biological_sex', 'unknown')}")
    if conditions:
        ctx_parts.append(
            "Active conditions: "
            + ", ".join(
                f"{c.get('condition_name', '')} (severity: {c.get('severity', '?')})"
                for c in conditions
            )
        )

    # Lab abnormals
    abnormal: list[str] = []
    for lab in labs:
        for bm in lab.get("biomarkers", []):
            status = (bm.get("status") or "").lower()
            if status in ("high", "low", "critical", "abnormal"):
                abnormal.append(
                    f"{bm.get('name', '?')}: {bm.get('value', '?')} {bm.get('unit', '')} ({status})"
                )
    if abnormal:
        ctx_parts.append("Abnormal lab results: " + "; ".join(abnormal[:15]))

    # Medical records summaries
    for rec in medical_records:
        rtype = rec.get("record_type", "")
        summary = rec.get("ai_summary") or rec.get("title", "")
        if summary:
            ctx_parts.append(f"{rtype.title()} record: {summary}")

    # Symptom patterns
    if symptoms:
        symptom_counts: dict[str, int] = {}
        for s in symptoms:
            st = s.get("symptom_type", "unknown")
            symptom_counts[st] = symptom_counts.get(st, 0) + 1
        top = sorted(symptom_counts.items(), key=lambda x: -x[1])[:5]
        ctx_parts.append("Recent symptoms: " + ", ".join(f"{s} ({n}x)" for s, n in top))

    # Compute data hash for cache validation
    data_hash = hashlib.md5("|".join(sorted(ctx_parts)).encode()).hexdigest()

    # Serve cached result if data hasn't changed
    if cached_rows:
        cached = cached_rows[0]
        if cached.get("data_hash") == data_hash:
            cached_result = cached.get("result_json", {})
            if isinstance(cached_result, str):
                try:
                    cached_result = json.loads(cached_result)
                except Exception:
                    cached_result = {}
            if cached_result.get("recommendations"):
                cached_result["cached"] = True
                return cached_result

    if not ctx_parts:
        return {
            "recommendations": [],
            "summary": "Add your health conditions, lab results, or medical records to receive personalized medication recommendations.",
            "disclaimer": "This is not medical advice. Always consult your doctor.",
        }

    health_context = "\n".join(f"- {p}" for p in ctx_parts)

    prompt = f"""You are a clinical pharmacist reviewing a patient's health profile to suggest medications and supplements they should discuss with their doctor.

Patient profile:
{health_context}

The patient currently takes NO medications or supplements.

Based on their conditions, lab results, medical records, and symptoms, generate a JSON array of medication/supplement recommendations. For each, include:
- "name": medication or supplement name
- "category": "prescription" | "otc" | "supplement"
- "rationale": 1-2 sentence explanation tied to their specific data
- "evidence_level": "strong" | "moderate" | "emerging"
- "priority": "high" | "medium" | "low"
- "discuss_with_doctor": true/false (true for prescriptions)
- "relevant_data": a SHORT string citing the key data point (e.g. "HbA1c 6.2%", "EGFR L858R mutation"). Must be a string, NOT an array.
- "estimated_cost": a string with typical US monthly cost range (e.g. "$15–$40/mo generic", "$12,000–$15,000/mo brand", "$10–$25/mo OTC"). For prescriptions include both generic and brand if applicable. Use "N/A" only if truly unknown.
- "efficacy": a short string summarizing clinical efficacy (e.g. "60–80% response rate in EGFR+ NSCLC", "Reduces HbA1c by 1–1.5%", "Lowers LDL 30–50%"). Be specific to the patient's condition.

IMPORTANT FORMATTING RULES:
- Return ONLY valid JSON. No markdown fences, no commentary before or after.
- Keep each "rationale" to 1-2 sentences MAX (under 40 words each).
- Max 6 recommendations.
- "summary" should be 2 sentences max.

JSON structure:
{{"recommendations": [...], "summary": "..."}}

Be specific to their data. Do NOT give generic wellness advice. Every recommendation must be tied to an abnormal lab, condition, or medical record finding."""

    try:
        raw = await _call_claude(prompt, max_tokens=4000)
        # Strip markdown fences if present
        import re

        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        # Find first { and last } to extract JSON object
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
        parsed = json.loads(text)
        recs = parsed.get("recommendations", [])
        # Normalize relevant_data to string
        for rec in recs:
            rd = rec.get("relevant_data")
            if isinstance(rd, list):
                rec["relevant_data"] = ", ".join(str(x) for x in rd)
        summary = parsed.get("summary", "")
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(
            "Failed to parse recommendations JSON: %s — raw: %s",
            e,
            raw[:200] if raw else "",
        )
        recs = []
        summary = raw if isinstance(raw, str) else "Unable to generate recommendations."

    result = {
        "recommendations": recs,
        "summary": summary,
        "disclaimer": "These are AI-generated suggestions for discussion with your healthcare provider. This is not medical advice.",
        "data_sources": {
            "conditions": len(conditions),
            "lab_results": len(labs),
            "medical_records": len(medical_records),
            "symptoms": len(symptoms),
        },
    }

    # Persist to cache if we got valid recommendations
    if recs:
        try:
            from ..dependencies.usage_gate import _supabase_upsert

            await _supabase_upsert(
                "ai_analysis_cache",
                {
                    "user_id": user_id,
                    "analysis_type": "medication_recommendations",
                    "result_json": json.dumps(result),
                    "data_hash": data_hash,
                },
                on_conflict="user_id,analysis_type",
            )
        except Exception as e:
            logger.warning("Failed to cache med recommendations: %s", e)

    return result


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
        text = result.content[0].text.strip()
        # If truncated, try to repair JSON by closing open structures
        if result.stop_reason == "max_tokens" and max_tokens > 500:
            text = _repair_truncated_json(text)
        return text
    except Exception as e:
        logger.error("Claude call failed for med intelligence: %s", e)
        return "Your medication data has been reviewed. See details below."


def _repair_truncated_json(text: str) -> str:
    """Attempt to close truncated JSON so it can be parsed."""
    # Count open braces/brackets
    opens = 0
    in_string = False
    escape = False
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in ("{", "["):
            opens += 1
        elif ch in ("}", "]"):
            opens -= 1

    if opens <= 0:
        return text

    # If we're inside a string, close it first
    if in_string:
        text += '..."'

    # Find what closers we need by scanning from the end
    # Simple approach: just close with the right braces
    stack: list[str] = []
    in_str = False
    esc = False
    for ch in text:
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if ch == "{":
            stack.append("}")
        elif ch == "[":
            stack.append("]")
        elif ch in ("}", "]") and stack:
            stack.pop()

    # Close in reverse order
    text += "".join(reversed(stack))
    return text
