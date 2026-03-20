"""
Insights Intelligence API — trend explanations, day summaries,
and cross-referenced intelligence for the Insights screens.
"""

import asyncio
import json
import os
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get

logger = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Metric display names and relevance
# ---------------------------------------------------------------------------

METRIC_LABELS: Dict[str, str] = {
    "sleep": "Sleep Score",
    "readiness": "Readiness",
    "activity": "Activity Score",
    "resting_heart_rate": "Resting HR",
    "hrv_sdnn": "HRV",
    "hrv": "HRV",
    "spo2": "SpO2",
    "respiratory_rate": "Respiratory Rate",
    "steps": "Steps",
    "active_calories": "Active Calories",
    "vo2_max": "VO2 Max",
}

# Metrics affected by cycle phase
CYCLE_AFFECTED_METRICS = {"hrv_sdnn", "hrv", "resting_heart_rate", "sleep", "readiness"}


async def _gather_insights_context(user_id: str) -> Dict[str, Any]:
    """Gather context for insights intelligence."""
    today = date.today().isoformat()
    thirty_ago = (date.today() - timedelta(days=30)).isoformat()

    (
        metric_summaries,
        medications,
        experiments,
        symptoms,
        profile_rows,
        conditions,
        cycle_logs,
    ) = await asyncio.gather(
        _supabase_get(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&date=gte.{thirty_ago}"
            f"&select=metric_type,score,latest_value,date,trend_7d"
            f"&order=date.desc&limit=500",
        ),
        _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=medication_name,dosage,start_date",
        ),
        _supabase_get(
            "active_interventions",
            f"user_id=eq.{user_id}&status=in.(active,completed)"
            f"&select=title,started_at,ends_at,duration_days,status&limit=5",
        ),
        _supabase_get(
            "symptom_journal",
            f"user_id=eq.{user_id}&symptom_date=gte.{thirty_ago}"
            f"&select=symptom_type,severity,symptom_date&order=symptom_date.desc",
        ),
        _supabase_get(
            "profiles",
            f"id=eq.{user_id}&select=full_name,date_of_birth,biological_sex",
        ),
        _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name",
        ),
        _supabase_get(
            "cycle_logs",
            f"user_id=eq.{user_id}&event_type=eq.period_start"
            f"&order=event_date.desc&select=event_date&limit=3",
        ),
    )

    profile = profile_rows[0] if profile_rows else {}
    first_name = (profile.get("full_name") or "").split(" ")[0] or None
    dob = profile.get("date_of_birth")
    age = None
    if dob:
        try:
            age = (date.today() - date.fromisoformat(str(dob)[:10])).days // 365
        except (ValueError, TypeError):
            pass

    # Cycle phase estimation
    cycle_phase = None
    if cycle_logs:
        try:
            last_period = date.fromisoformat(cycle_logs[0]["event_date"][:10])
            day_in_cycle = (date.today() - last_period).days
            if day_in_cycle <= 5:
                cycle_phase = {"phase": "menstrual", "day": day_in_cycle}
            elif day_in_cycle <= 13:
                cycle_phase = {"phase": "follicular", "day": day_in_cycle}
            elif day_in_cycle <= 16:
                cycle_phase = {"phase": "ovulatory", "day": day_in_cycle}
            elif day_in_cycle <= 28:
                cycle_phase = {"phase": "luteal", "day": day_in_cycle}
        except (ValueError, TypeError, KeyError):
            pass

    # Group metrics by type → time series
    metrics_by_type: Dict[str, List[Dict[str, Any]]] = {}
    for m in metric_summaries:
        mt = m.get("metric_type", "")
        if mt not in metrics_by_type:
            metrics_by_type[mt] = []
        metrics_by_type[mt].append(m)

    return {
        "metrics_by_type": metrics_by_type,
        "medications": medications,
        "experiments": experiments,
        "symptoms": symptoms,
        "demographics": {
            "first_name": first_name,
            "age": age,
            "sex": profile.get("biological_sex"),
        },
        "conditions": [c.get("condition_name", "") for c in conditions],
        "cycle_phase": cycle_phase,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/trend-explanations")
async def trend_explanations(
    current_user: dict = Depends(get_current_user),
):
    """Per-metric AI explanation with contributing factors and markers."""
    user_id = current_user["id"]
    ctx = await _gather_insights_context(user_id)
    first_name = ctx["demographics"].get("first_name") or "there"

    # Build markers for each metric
    metrics_result: List[Dict[str, Any]] = []

    for metric_type, data_points in ctx["metrics_by_type"].items():
        if len(data_points) < 3:
            continue

        label = METRIC_LABELS.get(metric_type, metric_type.replace("_", " ").title())
        dates = [d.get("date", "") for d in data_points]
        values = [d.get("latest_value") or d.get("score") or 0 for d in data_points]

        # Build markers
        markers: List[Dict[str, Any]] = []

        # Medication start markers
        for med in ctx["medications"]:
            start = med.get("start_date", "")
            if start and start >= dates[-1] if dates else False:
                # Find closest date index
                for i, d in enumerate(dates):
                    if d <= start:
                        markers.append(
                            {
                                "index": i,
                                "type": "med_change",
                                "label": f"Started {med.get('medication_name', '')}",
                            }
                        )
                        break

        # Experiment markers
        for exp in ctx["experiments"]:
            exp_start = (exp.get("started_at") or "")[:10]
            exp_end = (exp.get("ends_at") or "")[:10]
            if exp_start:
                for i, d in enumerate(dates):
                    if d <= exp_start:
                        markers.append(
                            {
                                "index": i,
                                "type": "experiment_start",
                                "label": exp.get("title", "Experiment"),
                            }
                        )
                        break
            if exp_end:
                for i, d in enumerate(dates):
                    if d <= exp_end:
                        markers.append(
                            {
                                "index": i,
                                "type": "experiment_end",
                                "label": f"{exp.get('title', '')} ended",
                            }
                        )
                        break

        # Contributing factors
        factors: List[str] = []

        # Cycle phase impact
        if ctx["cycle_phase"] and metric_type in CYCLE_AFFECTED_METRICS:
            phase = ctx["cycle_phase"]["phase"]
            factors.append(f"cycle_phase ({phase})")

        # Recent symptoms
        related_symptoms = [s for s in ctx["symptoms"] if s.get("severity", 0) >= 6]
        if related_symptoms:
            types = list({s.get("symptom_type", "") for s in related_symptoms[:5]})
            factors.append(f"symptoms ({', '.join(types[:2])})")

        # Medications
        if ctx["medications"]:
            factors.append("active_medications")

        # Experiments
        active_exps = [e for e in ctx["experiments"] if e.get("status") == "active"]
        if active_exps:
            factors.append(f"experiment ({active_exps[0].get('title', '')})")

        metrics_result.append(
            {
                "metric": metric_type,
                "label": label,
                "markers": markers,
                "contributing_factors": factors,
                "data_points_count": len(data_points),
            }
        )

    # Batch AI explanation for all metrics
    if metrics_result:
        metrics_context = "\n".join(
            f"- {m['label']}: {m['data_points_count']} data points, factors: {', '.join(m['contributing_factors']) or 'none'}"
            for m in metrics_result
        )

        cycle_text = ""
        if ctx["cycle_phase"]:
            cycle_text = f"Cycle: {ctx['cycle_phase']['phase']} phase, day {ctx['cycle_phase']['day']}. "

        conditions_text = ", ".join(ctx["conditions"]) or "None"
        meds_text = (
            ", ".join(m.get("medication_name", "") for m in ctx["medications"])
            or "None"
        )

        prompt = f"""You are a health trends analyst for {first_name}.

METRICS (last 30 days):
{metrics_context}

CONTEXT:
{cycle_text}Conditions: {conditions_text}. Medications: {meds_text}.

For each metric listed, generate a 1-sentence explanation of the likely reason for the trend.
Return ONLY valid JSON (no markdown):
{{
  "explanations": {{
    "metric_type": "1 sentence explanation referencing the most likely contributing factor"
  }}
}}

Rules:
- Reference specific factors (cycle phase, medication, experiment, symptoms)
- If cycle affects HRV/RHR/sleep, say it's normal and expected
- If medication started recently and metric is improving, credit the medication
- Be concise — max 20 words per explanation
- Address {first_name} naturally"""

        raw = await _call_claude(prompt, max_tokens=500)
        try:
            if "```" in raw:
                raw = raw[raw.find("{") : raw.rfind("}") + 1]
            parsed = json.loads(raw)
            explanations = parsed.get("explanations", {})
        except (json.JSONDecodeError, ValueError):
            explanations = {}

        for m in metrics_result:
            m["explanation"] = explanations.get(m["metric"], "")

    return {"metrics": metrics_result}


@router.get("/day-summaries")
async def day_summaries(
    days: int = Query(default=7, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
):
    """AI one-liner summaries per day connecting wearable data + user actions."""
    user_id = current_user["id"]
    start_date = (date.today() - timedelta(days=days)).isoformat()

    # Fetch timeline and actions in parallel
    timeline_data, actions_data, symptoms = await asyncio.gather(
        _supabase_get(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&date=gte.{start_date}"
            f"&select=metric_type,score,latest_value,date"
            f"&order=date.desc&limit=300",
        ),
        _supabase_get(
            "medication_adherence_log",
            f"user_id=eq.{user_id}&scheduled_time=gte.{start_date}T00:00:00"
            f"&select=was_taken,scheduled_time&limit=200",
        ),
        _supabase_get(
            "symptom_journal",
            f"user_id=eq.{user_id}&symptom_date=gte.{start_date}"
            f"&select=symptom_type,severity,symptom_date",
        ),
    )

    # Group by date
    day_data: Dict[str, Dict[str, Any]] = {}
    for m in timeline_data:
        d = m.get("date", "")
        if d not in day_data:
            day_data[d] = {
                "metrics": {},
                "symptoms": [],
                "meds_taken": 0,
                "meds_total": 0,
            }
        mt = m.get("metric_type", "")
        day_data[d]["metrics"][mt] = m.get("latest_value") or m.get("score")

    for s in symptoms:
        d = (s.get("symptom_date") or "")[:10]
        if d in day_data:
            day_data[d]["symptoms"].append(
                f"{s.get('symptom_type', '')} ({s.get('severity', '?')}/10)"
            )

    for a in actions_data:
        d = (a.get("scheduled_time") or "")[:10]
        if d in day_data:
            day_data[d]["meds_total"] += 1
            if a.get("was_taken"):
                day_data[d]["meds_taken"] += 1

    if not day_data:
        return {"summaries": []}

    # Build batch context for AI
    day_lines: List[str] = []
    sorted_dates = sorted(day_data.keys(), reverse=True)[:days]
    for d in sorted_dates:
        dd = day_data[d]
        metrics = dd["metrics"]
        parts: List[str] = [d]
        if "sleep" in metrics:
            parts.append(f"sleep={int(metrics['sleep'])}")
        if "hrv_sdnn" in metrics or "hrv" in metrics:
            val = metrics.get("hrv_sdnn") or metrics.get("hrv")
            parts.append(f"HRV={int(val)}")
        if "steps" in metrics:
            parts.append(f"steps={int(metrics['steps']):,}")
        if dd["symptoms"]:
            parts.append(f"symptoms=[{', '.join(dd['symptoms'][:2])}]")
        if dd["meds_total"] > 0:
            parts.append(f"meds={dd['meds_taken']}/{dd['meds_total']}")
        day_lines.append(" | ".join(parts))

    prompt = f"""Generate a brief 1-sentence summary for each day. Connect the data points into a coherent narrative.

DAILY DATA:
{chr(10).join(day_lines)}

Return ONLY valid JSON (no markdown):
{{
  "YYYY-MM-DD": "One casual sentence connecting the dots for that day"
}}

Rules:
- Max 15 words per day
- Reference specific metrics when notable (good sleep, low HRV, high steps)
- If symptoms logged, connect to metrics
- Be conversational, not clinical"""

    raw = await _call_claude(prompt, max_tokens=800)
    try:
        if "```" in raw:
            raw = raw[raw.find("{") : raw.rfind("}") + 1]
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        parsed = {}

    summaries = [
        {"date": d, "summary": parsed.get(d, "")} for d in sorted_dates if parsed.get(d)
    ]

    return {"summaries": summaries}


# ---------------------------------------------------------------------------
# Claude helper
# ---------------------------------------------------------------------------


async def _call_claude(prompt: str, max_tokens: int = 500) -> str:
    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "{}"
        client = anthropic.AsyncAnthropic(api_key=api_key)
        result = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return result.content[0].text.strip()
    except Exception as e:
        logger.error("Claude call failed for insights intelligence: %s", e)
        return "{}"
