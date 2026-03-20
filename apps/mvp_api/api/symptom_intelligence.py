"""
Symptom Intelligence API — cross-references symptoms with wearables,
meals, medications, cycle, and patterns to surface triggers and insights.
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

logger = get_logger(__name__)
router = APIRouter()


async def _gather_symptom_context(user_id: str) -> Dict[str, Any]:
    """Gather context for symptom intelligence — all parallel."""
    today = date.today().isoformat()
    thirty_ago = (date.today() - timedelta(days=30)).isoformat()
    seven_ago = (date.today() - timedelta(days=7)).isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    (
        symptoms_30d,
        wearable,
        meals_yesterday,
        medications,
        conditions,
        profile_rows,
        patterns,
        correlations,
        cycle_logs,
    ) = await asyncio.gather(
        _supabase_get(
            "symptom_journal",
            f"user_id=eq.{user_id}&symptom_date=gte.{thirty_ago}"
            f"&select=symptom_type,severity,symptom_date,mood,stress_level,triggers"
            f"&order=symptom_date.desc",
        ),
        _supabase_get(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&date=gte.{yesterday}&date=lte.{today}"
            f"&select=metric_type,score,latest_value,date",
        ),
        _supabase_get(
            "meal_logs",
            f"user_id=eq.{user_id}&order=timestamp.desc&limit=10"
            f"&select=meal_name,food_name,meal_type,calories,timestamp",
        ),
        _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=id,medication_name,dosage,start_date",
        ),
        _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name",
        ),
        _supabase_get(
            "profiles",
            f"id=eq.{user_id}&select=full_name,date_of_birth,biological_sex",
        ),
        _supabase_get(
            "symptom_patterns",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=pattern_type,symptom_type,pattern_description,confidence_score"
            f"&limit=10",
        ),
        _supabase_get(
            "symptom_correlations",
            f"user_id=eq.{user_id}&order=computed_at.desc"
            f"&select=symptom_type,correlated_variable,correlation_coefficient,effect_description,correlation_type"
            f"&limit=20",
        ),
        _supabase_get(
            "cycle_logs",
            f"user_id=eq.{user_id}&order=event_date.desc"
            f"&select=event_type,event_date&limit=1",
        ),
    )

    profile = profile_rows[0] if profile_rows else {}
    dob = profile.get("date_of_birth")
    age = None
    if dob:
        try:
            age = (date.today() - date.fromisoformat(str(dob)[:10])).days // 365
        except (ValueError, TypeError):
            pass

    # Wearable summary
    wearable_map: Dict[str, Any] = {}
    for w in wearable:
        mt = w.get("metric_type", "")
        d = w.get("date", "")
        key = f"{mt}_{d}"
        wearable_map[mt] = {
            "value": w.get("latest_value") or w.get("score"),
            "date": d,
        }

    # Meals yesterday
    yesterday_meals = [
        m for m in meals_yesterday if (m.get("timestamp") or "")[:10] == yesterday
    ]

    # Cycle phase
    cycle_phase = None
    if cycle_logs:
        last = cycle_logs[0]
        if last.get("event_type") == "period_start":
            try:
                period_start = date.fromisoformat(last["event_date"][:10])
                day_in_cycle = (date.today() - period_start).days
                if day_in_cycle <= 5:
                    cycle_phase = "menstrual"
                elif day_in_cycle <= 13:
                    cycle_phase = "follicular"
                elif day_in_cycle <= 16:
                    cycle_phase = "ovulatory"
                elif day_in_cycle <= 28:
                    cycle_phase = "luteal"
            except (ValueError, TypeError):
                pass

    return {
        "symptoms_30d": symptoms_30d,
        "wearable": wearable_map,
        "meals_yesterday": yesterday_meals,
        "medications": medications,
        "conditions": [c.get("condition_name", "") for c in conditions],
        "demographics": {
            "first_name": (profile.get("full_name") or "").split(" ")[0] or None,
            "age": age,
            "sex": profile.get("biological_sex"),
        },
        "patterns": patterns,
        "correlations": correlations,
        "cycle_phase": cycle_phase,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


class PostLogInsightRequest(BaseModel):
    symptom_type: str
    severity: int = 5
    notes: Optional[str] = None


@router.post("/post-log-insight")
async def post_log_insight(
    body: PostLogInsightRequest,
    current_user: dict = Depends(get_current_user),
):
    """AI insight after logging a symptom — cross-references all data."""
    user_id = current_user["id"]
    ctx = await _gather_symptom_context(user_id)
    first_name = ctx["demographics"].get("first_name") or "there"

    # Frequency this week
    seven_ago = (date.today() - timedelta(days=7)).isoformat()
    this_week = [
        s
        for s in ctx["symptoms_30d"]
        if s.get("symptom_type") == body.symptom_type
        and (s.get("symptom_date") or "") >= seven_ago
    ]
    frequency_this_week = len(this_week) + 1  # include current

    # Severity trend (30d for this type)
    type_symptoms = [
        s for s in ctx["symptoms_30d"] if s.get("symptom_type") == body.symptom_type
    ]
    severities = [s.get("severity", 5) for s in type_symptoms]
    severity_trend = "stable"
    if len(severities) >= 3:
        recent_avg = sum(severities[:3]) / 3
        older_avg = sum(severities[3:]) / max(len(severities[3:]), 1)
        if recent_avg > older_avg + 1:
            severity_trend = "worsening"
        elif recent_avg < older_avg - 1:
            severity_trend = "improving"

    # Likely triggers
    likely_triggers: List[Dict[str, Any]] = []

    # From correlations
    for corr in ctx["correlations"]:
        if corr.get("symptom_type") == body.symptom_type:
            coeff = corr.get("correlation_coefficient", 0)
            if abs(coeff) >= 0.3:
                likely_triggers.append(
                    {
                        "source": corr.get("correlation_type", "unknown"),
                        "label": corr.get("correlated_variable", "")
                        .replace("_", " ")
                        .title(),
                        "confidence": round(abs(coeff), 2),
                        "detail": corr.get("effect_description", ""),
                    }
                )

    # From medication timing
    for med in ctx["medications"]:
        start = med.get("start_date", "")
        if start:
            type_since_start = [
                s for s in type_symptoms if (s.get("symptom_date") or "") >= start
            ]
            if len(type_since_start) >= 2:
                likely_triggers.append(
                    {
                        "source": "medication",
                        "label": med.get("medication_name", ""),
                        "confidence": 0.5,
                        "detail": f"You've logged {body.symptom_type} {len(type_since_start)} times since starting {med.get('medication_name', '')}",
                    }
                )

    # From wearable
    sleep = ctx["wearable"].get("sleep", {})
    hrv = ctx["wearable"].get("hrv_sdnn", {}) or ctx["wearable"].get("hrv", {})
    if sleep.get("value") and sleep["value"] < 70:
        likely_triggers.append(
            {
                "source": "wearable",
                "label": "Poor sleep last night",
                "confidence": 0.6,
                "detail": f"Sleep score {int(sleep['value'])} (below your usual)",
            }
        )
    if hrv.get("value") and hrv["value"] < 30:
        likely_triggers.append(
            {
                "source": "wearable",
                "label": "Low HRV today",
                "confidence": 0.5,
                "detail": f"HRV {int(hrv['value'])}ms — indicates higher stress/lower recovery",
            }
        )

    likely_triggers.sort(key=lambda t: t["confidence"], reverse=True)

    # Build AI prompt
    wearable_text = ""
    if sleep.get("value"):
        wearable_text += f"Sleep score: {int(sleep['value'])}. "
    if hrv.get("value"):
        wearable_text += f"HRV: {int(hrv['value'])}ms. "

    meals_text = ""
    if ctx["meals_yesterday"]:
        meal_names = [
            m.get("meal_name") or m.get("food_name") or "meal"
            for m in ctx["meals_yesterday"][:3]
        ]
        meals_text = f"Yesterday's meals: {', '.join(meal_names)}. "

    meds_text = (
        ", ".join(m.get("medication_name", "") for m in ctx["medications"]) or "None"
    )
    conditions_text = ", ".join(ctx["conditions"]) or "None"
    cycle_text = (
        f"Cycle phase: {ctx['cycle_phase']}. " if ctx.get("cycle_phase") else ""
    )
    triggers_text = (
        ", ".join(t["label"] for t in likely_triggers[:3])
        if likely_triggers
        else "No clear triggers identified yet"
    )

    prompt = f"""You are a symptom analyst for {first_name} ({ctx['demographics'].get('age', '?')}yo {ctx['demographics'].get('sex', '?')}).

SYMPTOM LOGGED: {body.symptom_type}, severity {body.severity}/10
{f'Notes: {body.notes}' if body.notes else ''}
Frequency: {frequency_this_week}x this week. Severity trend: {severity_trend}.
Likely triggers: {triggers_text}

CONTEXT:
{wearable_text}{meals_text}{cycle_text}
Medications: {meds_text}. Conditions: {conditions_text}.

Generate 2-3 sentences. Rules:
- Address {first_name} by name
- Reference at least one cross-data-source finding (sleep, meal, med, cycle)
- If frequency is increasing, flag it with concern
- If a medication may be causing this, mention gently
- End with one practical suggestion
- Return ONLY the insight text"""

    insight = await _call_claude(prompt)

    quick_actions = ["Ask health coach"]
    if likely_triggers:
        quick_actions.insert(0, "See triggers")
    if frequency_this_week >= 3:
        quick_actions.append("Start experiment")

    return {
        "insight": insight,
        "frequency_this_week": frequency_this_week,
        "severity_trend": severity_trend,
        "likely_triggers": likely_triggers[:5],
        "quick_actions": quick_actions,
    }


@router.get("/triggers/{symptom_type}")
async def get_triggers(
    symptom_type: str,
    current_user: dict = Depends(get_current_user),
):
    """Likely triggers for a symptom type from all data sources."""
    user_id = current_user["id"]
    ctx = await _gather_symptom_context(user_id)

    triggers: List[Dict[str, Any]] = []

    # Correlations
    for corr in ctx["correlations"]:
        if (
            corr.get("symptom_type") == symptom_type
            and abs(corr.get("correlation_coefficient", 0)) >= 0.25
        ):
            triggers.append(
                {
                    "source": corr.get("correlation_type", "unknown"),
                    "label": corr.get("correlated_variable", "")
                    .replace("_", " ")
                    .title(),
                    "confidence": round(abs(corr.get("correlation_coefficient", 0)), 2),
                    "detail": corr.get("effect_description", ""),
                }
            )

    # Patterns
    for pat in ctx["patterns"]:
        if pat.get("symptom_type") == symptom_type:
            triggers.append(
                {
                    "source": "pattern",
                    "label": pat.get("pattern_description", "")[:60],
                    "confidence": pat.get("confidence_score", 0.5),
                    "detail": pat.get("pattern_description", ""),
                }
            )

    # Medication side effects
    type_symptoms = [
        s for s in ctx["symptoms_30d"] if s.get("symptom_type") == symptom_type
    ]
    for med in ctx["medications"]:
        start = med.get("start_date", "")
        if start:
            count_since = sum(
                1 for s in type_symptoms if (s.get("symptom_date") or "") >= start
            )
            if count_since >= 2:
                triggers.append(
                    {
                        "source": "medication",
                        "label": f"Possible side effect: {med.get('medication_name', '')}",
                        "confidence": min(0.3 + count_since * 0.1, 0.8),
                        "detail": f"{count_since} occurrences since starting {med.get('medication_name', '')} ({start})",
                    }
                )

    # Wearable
    sleep = ctx["wearable"].get("sleep", {})
    if sleep.get("value") and sleep["value"] < 70:
        triggers.append(
            {
                "source": "wearable",
                "label": "Poor sleep",
                "confidence": 0.5,
                "detail": f"Last night's sleep score: {int(sleep['value'])}",
            }
        )

    triggers.sort(key=lambda t: t["confidence"], reverse=True)
    return {"symptom_type": symptom_type, "triggers": triggers[:8]}


@router.get("/history-summary")
async def history_summary(
    current_user: dict = Depends(get_current_user),
):
    """Frequency trends, severity trends, top correlations, medication links."""
    user_id = current_user["id"]
    ctx = await _gather_symptom_context(user_id)

    seven_ago = (date.today() - timedelta(days=7)).isoformat()
    fourteen_ago = (date.today() - timedelta(days=14)).isoformat()

    # Group by type
    by_type: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for s in ctx["symptoms_30d"]:
        by_type[s.get("symptom_type", "unknown")].append(s)

    type_summaries: List[Dict[str, Any]] = []
    for stype, entries in by_type.items():
        this_week = [e for e in entries if (e.get("symptom_date") or "") >= seven_ago]
        last_week = [
            e
            for e in entries
            if fourteen_ago <= (e.get("symptom_date") or "") < seven_ago
        ]
        severities = [e.get("severity", 5) for e in entries]
        avg_sev = round(sum(severities) / len(severities), 1) if severities else 0

        type_summaries.append(
            {
                "type": stype,
                "this_week": len(this_week),
                "last_week": len(last_week),
                "delta": len(this_week) - len(last_week),
                "total_30d": len(entries),
                "avg_severity": avg_sev,
            }
        )

    type_summaries.sort(key=lambda t: t["this_week"], reverse=True)

    # Top correlations
    top_corr = sorted(
        ctx["correlations"],
        key=lambda c: abs(c.get("correlation_coefficient", 0)),
        reverse=True,
    )[:5]

    # Medication links
    med_links: List[Dict[str, Any]] = []
    for med in ctx["medications"]:
        start = med.get("start_date", "")
        if not start:
            continue
        for stype, entries in by_type.items():
            count_since = sum(
                1 for e in entries if (e.get("symptom_date") or "") >= start
            )
            if count_since >= 3:
                med_links.append(
                    {
                        "medication": med.get("medication_name"),
                        "symptom_type": stype,
                        "count_since_start": count_since,
                        "start_date": start,
                    }
                )

    # Symptom-free days
    symptom_dates = {(s.get("symptom_date") or "")[:10] for s in ctx["symptoms_30d"]}
    days_30 = [(date.today() - timedelta(days=i)).isoformat() for i in range(30)]
    symptom_free = sum(1 for d in days_30 if d not in symptom_dates)

    return {
        "type_summaries": type_summaries,
        "top_correlations": [
            {
                "variable": c.get("correlated_variable", ""),
                "symptom": c.get("symptom_type", ""),
                "coefficient": c.get("correlation_coefficient"),
                "description": c.get("effect_description", ""),
            }
            for c in top_corr
        ],
        "medication_links": med_links,
        "symptom_free_days": symptom_free,
    }


async def _call_claude(prompt: str, max_tokens: int = 250) -> str:
    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "Log more symptoms to get personalized trigger analysis."
        client = anthropic.AsyncAnthropic(api_key=api_key)
        result = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return result.content[0].text.strip()
    except Exception as e:
        logger.error("Claude call failed for symptom intelligence: %s", e)
        return "Your symptom has been logged. Keep tracking to uncover patterns."
