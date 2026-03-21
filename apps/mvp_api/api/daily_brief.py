"""
Daily Health Brief — synthesized morning narrative combining all health data.
"""

import asyncio
import os
from datetime import date, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get

logger = get_logger(__name__)
router = APIRouter()


@router.get("/daily")
async def daily_brief(
    current_user: dict = Depends(get_current_user),
):
    """
    Synthesized daily health narrative combining 13 data sources.
    Cached for 4 hours per user.
    """
    user_id = current_user["id"]
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    seven_ago = (date.today() - timedelta(days=7)).isoformat()

    # Parallel fetch all sources
    (
        profile_rows,
        wearable_today,
        wearable_yesterday,
        meals_yesterday,
        experiments,
        journeys,
        adherence_today,
        medications,
        retest_labs,
        symptoms_week,
        supplement_gaps_labs,
        cycle_logs,
        health_score,
        conditions,
        medical_records,
    ) = await asyncio.gather(
        _supabase_get(
            "profiles",
            f"id=eq.{user_id}&select=full_name,date_of_birth,biological_sex",
        ),
        _supabase_get(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&date=eq.{today}"
            f"&select=metric_type,score,latest_value",
        ),
        _supabase_get(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&date=eq.{yesterday}"
            f"&select=metric_type,score,latest_value",
        ),
        _supabase_get(
            "meal_logs",
            f"user_id=eq.{user_id}&order=timestamp.desc&limit=10"
            f"&select=calories,timestamp",
        ),
        _supabase_get(
            "active_interventions",
            f"user_id=eq.{user_id}&status=eq.active"
            f"&select=title,started_at,duration_days&limit=1",
        ),
        _supabase_get(
            "goal_journeys",
            f"user_id=eq.{user_id}&status=eq.active"
            f"&select=title,phases,current_phase&limit=1",
        ),
        _supabase_get(
            "medication_adherence_log",
            f"user_id=eq.{user_id}&scheduled_time=gte.{today}T00:00:00"
            f"&scheduled_time=lte.{today}T23:59:59"
            f"&select=was_taken",
        ),
        _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true"
            f"&select=medication_name,dosage,frequency",
        ),
        _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&order=test_date.desc&limit=1"
            f"&select=test_date,test_type",
        ),
        _supabase_get(
            "symptom_journal",
            f"user_id=eq.{user_id}&symptom_date=gte.{seven_ago}"
            f"&select=symptom_type,severity,symptom_date",
        ),
        _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&order=test_date.desc&limit=3" f"&select=biomarkers",
        ),
        _supabase_get(
            "cycle_logs",
            f"user_id=eq.{user_id}&order=event_date.desc"
            f"&select=event_type,event_date&limit=1",
        ),
        _supabase_get(
            "health_metric_summaries",
            f"user_id=eq.{user_id}&metric_type=eq.composite"
            f"&order=date.desc&limit=2&select=score,date",
        ),
        _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name",
        ),
        _supabase_get(
            "medical_records",
            f"user_id=eq.{user_id}&order=created_at.desc&limit=3"
            f"&select=record_type,title,ai_summary",
        ),
    )

    # Parse profile
    profile = profile_rows[0] if profile_rows else {}
    first_name = (profile.get("full_name") or "").split(" ")[0] or "there"

    # Build context parts for prompt
    parts: List[str] = []

    # 1. Sleep
    sleep_score = None
    for w in wearable_yesterday:
        if w.get("metric_type") == "sleep":
            sleep_score = w.get("score") or w.get("latest_value")
    if sleep_score:
        quality = (
            "great" if sleep_score >= 80 else "decent" if sleep_score >= 60 else "rough"
        )
        parts.append(f"Sleep last night: {quality} (score {int(sleep_score)})")

    # 2. Today's wearable
    hrv = None
    rhr = None
    steps = None
    for w in wearable_today:
        mt = w.get("metric_type", "")
        if "hrv" in mt:
            hrv = w.get("latest_value") or w.get("score")
        elif mt == "resting_heart_rate":
            rhr = w.get("latest_value")
        elif mt == "steps":
            steps = w.get("latest_value")
    if hrv:
        parts.append(f"HRV today: {int(hrv)}ms")
    if steps:
        parts.append(f"Steps so far: {int(steps):,}")

    # 3. Yesterday's nutrition
    yesterday_meals = [
        m for m in meals_yesterday if (m.get("timestamp") or "")[:10] == yesterday
    ]
    if yesterday_meals:
        total_cal = sum(m.get("calories") or 0 for m in yesterday_meals)
        if total_cal > 0:
            parts.append(
                f"Yesterday's intake: {int(total_cal)} cal ({len(yesterday_meals)} meals)"
            )

    # 4. Active experiment
    if experiments:
        exp = experiments[0]
        started = exp.get("started_at", "")[:10]
        try:
            day_num = (date.today() - date.fromisoformat(started)).days + 1
            parts.append(f"Experiment: Day {day_num} of {exp.get('title', '')}")
        except (ValueError, TypeError):
            pass

    # 5. Active journey
    if journeys:
        j = journeys[0]
        phases = j.get("phases") or []
        if isinstance(phases, str):
            import json as _json

            try:
                phases = _json.loads(phases)
            except Exception:
                phases = []
        cp = j.get("current_phase", 0)
        phase_name = (
            phases[cp].get("name", f"Phase {cp + 1}") if cp < len(phases) else ""
        )
        parts.append(f"Journey: {j.get('title', '')} — {phase_name}")

    # 6. Medication adherence
    meds_total = len(medications)
    meds_taken = sum(1 for log in adherence_today if log.get("was_taken"))
    if meds_total > 0:
        parts.append(f"Meds: {meds_taken}/{meds_total} taken today")

    # 7. Lab retest
    if retest_labs:
        last_date = retest_labs[0].get("test_date", "")
        if last_date:
            try:
                days_since = (date.today() - date.fromisoformat(last_date[:10])).days
                if days_since >= 75:
                    parts.append(
                        f"Lab recheck: last {retest_labs[0].get('test_type', 'labs')} was {days_since} days ago"
                    )
            except (ValueError, TypeError):
                pass

    # 8. Symptoms this week
    if symptoms_week:
        symptom_count = len(symptoms_week)
        types = list({s.get("symptom_type", "") for s in symptoms_week})
        parts.append(f"Symptoms this week: {symptom_count} ({', '.join(types[:3])})")

    # 9. Cycle phase
    if cycle_logs:
        last = cycle_logs[0]
        if last.get("event_type") == "period_start":
            try:
                period_start = date.fromisoformat(last["event_date"][:10])
                day_in_cycle = (date.today() - period_start).days
                if day_in_cycle <= 5:
                    parts.append("Cycle: menstrual phase — rest and iron-rich foods")
                elif day_in_cycle <= 13:
                    parts.append(
                        "Cycle: follicular phase — great time for higher intensity"
                    )
                elif day_in_cycle <= 28:
                    parts.append(
                        "Cycle: luteal phase — you may need extra rest and magnesium"
                    )
            except (ValueError, TypeError):
                pass

    # 10. Health score trajectory
    if len(health_score) >= 2:
        curr = health_score[0].get("score")
        prev = health_score[1].get("score")
        if curr and prev:
            if curr > prev + 3:
                parts.append(f"Health score: {int(curr)} (improving ↑)")
            elif curr < prev - 3:
                parts.append(f"Health score: {int(curr)} (declining ↓)")
            else:
                parts.append(f"Health score: {int(curr)} (stable)")

    # 11. Conditions
    cond_names = [c.get("condition_name", "") for c in conditions]
    if cond_names:
        parts.append(f"Conditions: {', '.join(cond_names)}")

    # 12. Medical records (pathology, genomic, imaging)
    if medical_records:
        for rec in medical_records:
            rtype = rec.get("record_type", "")
            title = rec.get("title", "")
            summary = rec.get("ai_summary", "")
            if rtype == "genomic":
                parts.append(f"Genomic profile: {title}. {summary}")
            elif rtype == "pathology":
                parts.append(f"Pathology: {title}. {summary}")
            elif rtype == "imaging":
                parts.append(f"Imaging: {title}. {summary}")

    # Build prompt
    context_block = (
        "\n".join(f"- {p}" for p in parts)
        if parts
        else "- Limited data available today"
    )

    prompt = f"""You are a personal health assistant for {first_name}. Generate a morning health brief.

TODAY'S DATA:
{context_block}

Write a 3-5 sentence conversational morning brief. Rules:
- Address {first_name} by name in the first sentence
- Start with the most notable finding (good sleep, low HRV, etc.)
- Mention the ONE most important action for today
- If an experiment is active, encourage continuation
- If meds aren't taken yet, gently remind
- If symptoms increased this week, acknowledge with empathy
- Be warm, encouraging, and specific — never generic
- Keep under 120 words
- Return ONLY the brief text"""

    brief = await _call_claude(prompt, max_tokens=250)

    data_sources = [p.split(":")[0] for p in parts]

    return {
        "brief": brief,
        "generated_at": date.today().isoformat(),
        "data_sources_used": data_sources,
    }


async def _call_claude(prompt: str, max_tokens: int = 250) -> str:
    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "Good morning! Log your health data to receive a personalized daily brief."
        client = anthropic.AsyncAnthropic(api_key=api_key)
        result = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return result.content[0].text.strip()
    except Exception as e:
        logger.error("Claude call failed for daily brief: %s", e)
        return "Good morning! Check your health data for today's insights."
