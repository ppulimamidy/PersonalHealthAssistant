"""
Symptom Journal API

Pro/Pro+ feature for tracking symptoms, identifying patterns, and
correlating with nutrition, medications, sleep, etc.

Phase 1 of Health Intelligence Features
"""

from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import date, time, datetime, timezone, timedelta
import uuid
import json

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
    RateLimit,
    UsageGate,
    _supabase_get,
    _supabase_upsert,
    _supabase_patch,
    _supabase_delete,
)

logger = get_logger(__name__)
router = APIRouter()

# ============================================================================
# PYDANTIC MODELS - SYMPTOM JOURNAL
# ============================================================================


class SymptomJournalCreate(BaseModel):
    symptom_date: date
    symptom_time: Optional[time] = None
    symptom_type: str = Field(..., min_length=1, max_length=100)
    severity: int = Field(..., ge=1, le=10)
    location: Optional[str] = Field(None, max_length=200)
    duration_minutes: Optional[int] = Field(None, ge=0)
    triggers: List[str] = []
    associated_symptoms: List[str] = []
    medications_taken: List[str] = []
    notes: Optional[str] = None
    mood: Optional[str] = Field(None, max_length=50)
    weather_conditions: Optional[str] = Field(None, max_length=100)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    sleep_hours_previous_night: Optional[float] = Field(None, ge=0, le=24)
    photo_url: Optional[str] = None


class SymptomJournalUpdate(BaseModel):
    symptom_date: Optional[date] = None
    symptom_time: Optional[time] = None
    symptom_type: Optional[str] = Field(None, min_length=1, max_length=100)
    severity: Optional[int] = Field(None, ge=1, le=10)
    location: Optional[str] = Field(None, max_length=200)
    duration_minutes: Optional[int] = Field(None, ge=0)
    triggers: Optional[List[str]] = None
    associated_symptoms: Optional[List[str]] = None
    medications_taken: Optional[List[str]] = None
    notes: Optional[str] = None
    mood: Optional[str] = Field(None, max_length=50)
    weather_conditions: Optional[str] = Field(None, max_length=100)
    stress_level: Optional[int] = Field(None, ge=1, le=10)
    sleep_hours_previous_night: Optional[float] = Field(None, ge=0, le=24)
    photo_url: Optional[str] = None


class SymptomJournalResponse(SymptomJournalCreate):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


# ============================================================================
# PYDANTIC MODELS - SYMPTOM PATTERNS
# ============================================================================


class SymptomPattern(BaseModel):
    id: str
    user_id: str
    pattern_type: str
    symptom_type: str
    pattern_description: str
    confidence_score: float
    supporting_entry_count: int
    recommendations: List[str]
    detected_at: datetime
    is_active: bool


class SymptomAnalytics(BaseModel):
    total_entries: int
    date_range_days: int
    most_common_symptom: Optional[str]
    average_severity: float
    patterns_detected: List[SymptomPattern]
    symptom_frequency_by_type: dict
    severity_distribution: dict
    mood_correlation: Optional[dict] = None
    stress_correlation: Optional[dict] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _symptom_row_to_response(row: dict) -> SymptomJournalResponse:
    """Convert database row to SymptomJournalResponse"""
    # Parse JSONB fields if stored as strings
    triggers = row.get("triggers", [])
    if isinstance(triggers, str):
        try:
            triggers = json.loads(triggers)
        except (json.JSONDecodeError, TypeError):
            triggers = []

    associated = row.get("associated_symptoms", [])
    if isinstance(associated, str):
        try:
            associated = json.loads(associated)
        except (json.JSONDecodeError, TypeError):
            associated = []

    medications = row.get("medications_taken", [])
    if isinstance(medications, str):
        try:
            medications = json.loads(medications)
        except (json.JSONDecodeError, TypeError):
            medications = []

    return SymptomJournalResponse(
        id=row["id"],
        user_id=row["user_id"],
        symptom_date=row["symptom_date"],
        symptom_time=row.get("symptom_time"),
        symptom_type=row["symptom_type"],
        severity=row["severity"],
        location=row.get("location"),
        duration_minutes=row.get("duration_minutes"),
        triggers=triggers,
        associated_symptoms=associated,
        medications_taken=medications,
        notes=row.get("notes"),
        mood=row.get("mood"),
        weather_conditions=row.get("weather_conditions"),
        stress_level=row.get("stress_level"),
        sleep_hours_previous_night=row.get("sleep_hours_previous_night"),
        photo_url=row.get("photo_url"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _pattern_row_to_response(row: dict) -> SymptomPattern:
    """Convert database row to SymptomPattern"""
    recommendations = row.get("recommendations", [])
    if isinstance(recommendations, str):
        try:
            recommendations = json.loads(recommendations)
        except (json.JSONDecodeError, TypeError):
            recommendations = []

    supporting_entries = row.get("supporting_entries", [])
    if isinstance(supporting_entries, str):
        try:
            supporting_entries = json.loads(supporting_entries)
        except (json.JSONDecodeError, TypeError):
            supporting_entries = []

    return SymptomPattern(
        id=row["id"],
        user_id=row["user_id"],
        pattern_type=row["pattern_type"],
        symptom_type=row["symptom_type"],
        pattern_description=row.get("pattern_description", ""),
        confidence_score=row.get("confidence_score", 0.0),
        supporting_entry_count=len(supporting_entries),
        recommendations=recommendations,
        detected_at=row["detected_at"],
        is_active=row.get("is_active", True),
    )


# ============================================================================
# SYMPTOM JOURNAL ENDPOINTS
# ============================================================================


@router.post("/journal", response_model=SymptomJournalResponse, status_code=201)
async def log_symptom(
    body: SymptomJournalCreate,
    current_user: dict = Depends(UsageGate("symptom_journal")),
):
    """
    Log a new symptom entry.

    - **Pro tier**: 3 entries per week
    - **Pro+ tier**: Unlimited entries
    """
    user_id = current_user["id"]

    body_dict = body.dict(
        exclude={"triggers", "associated_symptoms", "medications_taken"}
    )
    # Convert date/time objects to ISO strings for JSON serialization
    if isinstance(body_dict.get("symptom_date"), date):
        body_dict["symptom_date"] = body_dict["symptom_date"].isoformat()
    if body_dict.get("symptom_time") is not None:
        body_dict["symptom_time"] = str(body_dict["symptom_time"])

    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        **body_dict,
        "triggers": json.dumps(body.triggers),
        "associated_symptoms": json.dumps(body.associated_symptoms),
        "medications_taken": json.dumps(body.medications_taken),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await _supabase_upsert("symptom_journal", data)
    if not result:
        logger.error(f"Failed to save symptom entry for user {user_id}")
        raise HTTPException(status_code=500, detail="Failed to save symptom entry")

    logger.info(
        f"Symptom logged: {result['id']} ({body.symptom_type}, severity {body.severity}) for user {user_id}"
    )
    return _symptom_row_to_response(result)


@router.get("/journal", response_model=List[SymptomJournalResponse])
async def list_symptoms(
    days: int = Query(default=30, ge=1, le=365),
    since_timestamp: Optional[str] = Query(
        default=None,
        description="ISO 8601 timestamp — return only entries created on or after this "
        "date (use for incremental mobile sync to avoid re-downloading all entries)",
    ),
    symptom_type: Optional[str] = Query(default=None),
    min_severity: Optional[int] = Query(default=None, ge=1, le=10),
    current_user: dict = Depends(get_current_user),
):
    """
    List symptom journal entries.

    - **days**: Number of days to retrieve (default: 30, max: 365)
    - **since_timestamp**: ISO 8601 anchor for incremental sync — only entries created on/after
    - **symptom_type**: Filter by symptom type (optional)
    - **min_severity**: Minimum severity to include (optional)
    """
    user_id = current_user["id"]
    start_date = (date.today() - timedelta(days=days)).isoformat()

    params = f"user_id=eq.{user_id}&symptom_date=gte.{start_date}&select=*&order=symptom_date.desc,symptom_time.desc"

    if since_timestamp:
        try:
            datetime.fromisoformat(since_timestamp.replace("Z", "+00:00"))  # validate
            params += f"&created_at=gte.{since_timestamp.replace('Z', '+00:00')}"
        except ValueError:
            pass  # Invalid format — ignore

    if symptom_type:
        params += f"&symptom_type=eq.{symptom_type}"
    if min_severity:
        params += f"&severity=gte.{min_severity}"

    rows = await _supabase_get("symptom_journal", params)
    if not rows:
        return []

    return [_symptom_row_to_response(row) for row in rows]


@router.get("/journal/{entry_id}", response_model=SymptomJournalResponse)
async def get_symptom_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single symptom journal entry by ID."""
    user_id = current_user["id"]

    rows = await _supabase_get(
        "symptom_journal", f"id=eq.{entry_id}&user_id=eq.{user_id}&select=*&limit=1"
    )

    if not rows or not rows[0]:
        raise HTTPException(status_code=404, detail="Symptom entry not found")

    return _symptom_row_to_response(rows[0])


@router.put("/journal/{entry_id}", response_model=SymptomJournalResponse)
async def update_symptom_entry(
    entry_id: str,
    body: SymptomJournalUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a symptom journal entry."""
    user_id = current_user["id"]

    # Verify ownership
    rows = await _supabase_get(
        "symptom_journal", f"id=eq.{entry_id}&user_id=eq.{user_id}&select=*&limit=1"
    )
    if not rows or not rows[0]:
        raise HTTPException(status_code=404, detail="Symptom entry not found")

    # Build update dict (only include provided fields)
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}

    for field, value in body.dict(exclude_unset=True).items():
        if value is not None:
            if field in ("triggers", "associated_symptoms", "medications_taken"):
                updates[field] = json.dumps(value)
            else:
                updates[field] = value

    result = await _supabase_patch(
        "symptom_journal", f"id=eq.{entry_id}&user_id=eq.{user_id}", updates
    )
    if not result:
        logger.error(f"Failed to update symptom entry {entry_id} for user {user_id}")
        raise HTTPException(status_code=500, detail="Failed to update symptom entry")

    logger.info(f"Symptom entry updated: {entry_id} for user {user_id}")
    return _symptom_row_to_response(result)


@router.delete("/journal/{entry_id}", status_code=204)
async def delete_symptom_entry(
    entry_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a symptom journal entry."""
    user_id = current_user["id"]

    # Verify ownership
    rows = await _supabase_get(
        "symptom_journal", f"id=eq.{entry_id}&user_id=eq.{user_id}&select=id&limit=1"
    )
    if not rows or not rows[0]:
        raise HTTPException(status_code=404, detail="Symptom entry not found")

    success = await _supabase_delete(
        "symptom_journal", f"id=eq.{entry_id}&user_id=eq.{user_id}"
    )
    if not success:
        logger.error(f"Failed to delete symptom entry {entry_id} for user {user_id}")
        raise HTTPException(status_code=500, detail="Failed to delete symptom entry")

    logger.info(f"Symptom entry deleted: {entry_id} for user {user_id}")


# ============================================================================
# SYMPTOM ANALYTICS ENDPOINTS
# ============================================================================


@router.get("/analytics", response_model=SymptomAnalytics)
async def get_symptom_analytics(
    days: int = Query(default=90, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
):
    """
    Get symptom analytics and statistics.

    - **days**: Number of days to analyze (default: 90, max: 365)
    """
    user_id = current_user["id"]
    start_date = (date.today() - timedelta(days=days)).isoformat()

    # Fetch symptom entries
    entries = await _supabase_get(
        "symptom_journal",
        f"user_id=eq.{user_id}&symptom_date=gte.{start_date}&select=*",
    )

    # Fetch detected patterns
    patterns = await _supabase_get(
        "symptom_patterns", f"user_id=eq.{user_id}&is_active=eq.true&select=*"
    )

    # Compute analytics
    if not entries:
        return SymptomAnalytics(
            total_entries=0,
            date_range_days=days,
            most_common_symptom=None,
            average_severity=0.0,
            patterns_detected=[],
            symptom_frequency_by_type={},
            severity_distribution={},
        )

    total_entries = len(entries)
    avg_severity = sum(e.get("severity", 0) for e in entries) / total_entries

    # Count symptom types
    type_counts: Dict[str, int] = {}
    for e in entries:
        stype = e.get("symptom_type", "unknown")
        type_counts[stype] = type_counts.get(stype, 0) + 1

    most_common = (
        max(type_counts.keys(), key=lambda k: type_counts[k]) if type_counts else None
    )

    # Severity distribution
    severity_dist: Dict[str, int] = {}
    for e in entries:
        severity = e.get("severity", 0)
        severity_dist[str(severity)] = severity_dist.get(str(severity), 0) + 1

    # Mood correlation (basic)
    mood_entries = [e for e in entries if e.get("mood")]
    mood_correlation = None
    if mood_entries:
        mood_counts: Dict[str, int] = {}
        mood_severities: Dict[str, List[int]] = {}
        for e in mood_entries:
            mood = e["mood"]
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
            if mood not in mood_severities:
                mood_severities[mood] = []
            mood_severities[mood].append(e.get("severity", 0))

        mood_correlation = {
            mood: {
                "count": mood_counts[mood],
                "avg_severity": round(
                    sum(mood_severities[mood]) / len(mood_severities[mood]), 1
                ),
            }
            for mood in mood_counts
        }

    # Stress correlation (basic)
    stress_entries = [e for e in entries if e.get("stress_level")]
    stress_correlation = None
    if stress_entries:
        stress_levels: Dict[int, List[int]] = {}
        for e in stress_entries:
            stress = e["stress_level"]
            if stress not in stress_levels:
                stress_levels[stress] = []
            stress_levels[stress].append(e.get("severity", 0))

        stress_correlation = {
            f"stress_{level}": {
                "count": len(severities),
                "avg_severity": round(sum(severities) / len(severities), 1),
            }
            for level, severities in stress_levels.items()
        }

    return SymptomAnalytics(
        total_entries=total_entries,
        date_range_days=days,
        most_common_symptom=most_common,
        average_severity=round(avg_severity, 1),
        patterns_detected=[_pattern_row_to_response(p) for p in patterns]
        if patterns
        else [],
        symptom_frequency_by_type=type_counts,
        severity_distribution=severity_dist,
        mood_correlation=mood_correlation,
        stress_correlation=stress_correlation,
    )


@router.get("/patterns", response_model=List[SymptomPattern])
async def list_symptom_patterns(
    active_only: bool = Query(default=True),
    current_user: dict = Depends(get_current_user),
):
    """
    List detected symptom patterns.

    - **active_only**: Only return active patterns (default: True)
    """
    user_id = current_user["id"]

    params = f"user_id=eq.{user_id}&select=*&order=detected_at.desc"
    if active_only:
        params += "&is_active=eq.true"

    rows = await _supabase_get("symptom_patterns", params)
    if not rows:
        return []

    return [_pattern_row_to_response(row) for row in rows]


@router.post("/patterns/detect", response_model=List[SymptomPattern])
async def detect_symptom_patterns(
    _rl: None = Depends(RateLimit("symptom_pattern_detect", max_per_minute=5)),
    current_user: dict = Depends(UsageGate("health_conditions")),  # Pro+ only
):
    """
    Statistical pattern detection across 90 days of symptom history (Pro+ only).

    Detects:
    - High-frequency symptoms (recurring ≥ 2×/week)
    - Time-of-day patterns (≥ 50% of occurrences at same time block)
    - Trigger correlations (a trigger present in ≥ 30% of entries)
    - Severity trends (worsening or improving over time)
    """
    user_id = current_user["id"]
    logger.info("Pattern detection requested for user %s", user_id)

    start = (date.today() - timedelta(days=90)).isoformat()
    params = (
        f"user_id=eq.{user_id}&symptom_date=gte.{start}"
        f"&select=*&order=symptom_date.asc,symptom_time.asc"
    )
    rows = await _supabase_get("symptom_journal", params)

    if not rows or len(rows) < 3:
        return []

    now = datetime.now(timezone.utc)
    WEEKS_SPAN = 90.0 / 7.0  # ~12.9 weeks

    # Group entries by symptom type
    by_type: Dict[str, List[dict]] = defaultdict(list)
    for row in rows:
        by_type[row["symptom_type"]].append(row)

    detected: List[SymptomPattern] = []

    for symptom_type, entries in by_type.items():
        if len(entries) < 3:
            continue

        # ── 1. Frequency pattern ──────────────────────────────────────────
        freq_per_week = len(entries) / WEEKS_SPAN
        if freq_per_week >= 2.0:
            rec = ["Discuss recurrence pattern with your healthcare provider."]
            if freq_per_week >= 4:
                rec.insert(
                    0, "This symptom occurs very frequently — consider a symptom diary."
                )
            pattern_id = str(uuid.uuid4())
            row_data = {
                "id": pattern_id,
                "user_id": user_id,
                "pattern_type": "frequency",
                "symptom_type": symptom_type,
                "pattern_description": (
                    f"'{symptom_type.replace('_', ' ').title()}' occurs approximately "
                    f"{freq_per_week:.1f}× per week over the last 90 days."
                ),
                "confidence_score": min(0.9, 0.5 + len(entries) / 60),
                "supporting_entries": json.dumps([e["id"] for e in entries[:20]]),
                "recommendations": json.dumps(rec),
                "detected_at": now.isoformat(),
                "is_active": True,
            }
            await _supabase_upsert("symptom_patterns", row_data)
            detected.append(
                SymptomPattern(
                    id=pattern_id,
                    user_id=user_id,
                    pattern_type="frequency",
                    symptom_type=symptom_type,
                    pattern_description=row_data["pattern_description"],
                    confidence_score=row_data["confidence_score"],
                    supporting_entry_count=min(20, len(entries)),
                    recommendations=rec,
                    detected_at=now,
                    is_active=True,
                )
            )

        # ── 2. Time-of-day pattern ────────────────────────────────────────
        timed = [e for e in entries if e.get("symptom_time")]
        if len(timed) >= 3:
            bucket_counts: Dict[str, int] = defaultdict(int)
            for e in timed:
                t = e["symptom_time"]
                hour: Optional[int] = None
                if isinstance(t, str) and len(t) >= 2:
                    try:
                        hour = int(t[:2])
                    except ValueError:
                        pass
                elif hasattr(t, "hour"):
                    hour = t.hour
                if hour is None:
                    continue
                if 5 <= hour < 12:
                    bucket_counts["morning"] += 1
                elif 12 <= hour < 17:
                    bucket_counts["afternoon"] += 1
                elif 17 <= hour < 21:
                    bucket_counts["evening"] += 1
                else:
                    bucket_counts["night"] += 1

            if bucket_counts:
                total_timed = sum(bucket_counts.values())
                peak_bucket, peak_cnt = max(bucket_counts.items(), key=lambda x: x[1])
                if total_timed >= 3 and peak_cnt / total_timed >= 0.5:
                    rec = [
                        f"Track what you do before {peak_bucket} to identify potential triggers.",
                        "Mention this timing pattern to your doctor.",
                    ]
                    pattern_id = str(uuid.uuid4())
                    confidence = min(0.85, 0.4 + (peak_cnt / total_timed) * 0.5)
                    row_data = {
                        "id": pattern_id,
                        "user_id": user_id,
                        "pattern_type": "time_of_day",
                        "symptom_type": symptom_type,
                        "pattern_description": (
                            f"'{symptom_type.replace('_', ' ').title()}' occurs most often in the "
                            f"{peak_bucket} ({peak_cnt/total_timed*100:.0f}% of timed entries)."
                        ),
                        "confidence_score": confidence,
                        "supporting_entries": json.dumps([e["id"] for e in timed[:20]]),
                        "recommendations": json.dumps(rec),
                        "detected_at": now.isoformat(),
                        "is_active": True,
                    }
                    await _supabase_upsert("symptom_patterns", row_data)
                    detected.append(
                        SymptomPattern(
                            id=pattern_id,
                            user_id=user_id,
                            pattern_type="time_of_day",
                            symptom_type=symptom_type,
                            pattern_description=row_data["pattern_description"],
                            confidence_score=confidence,
                            supporting_entry_count=min(20, len(timed)),
                            recommendations=rec,
                            detected_at=now,
                            is_active=True,
                        )
                    )

        # ── 3. Trigger correlation ────────────────────────────────────────
        trigger_counts: Dict[str, int] = defaultdict(int)
        entries_with_triggers = []
        for e in entries:
            triggers = e.get("triggers", [])
            if isinstance(triggers, str):
                try:
                    triggers = json.loads(triggers)
                except Exception:
                    triggers = []
            if triggers:
                entries_with_triggers.append(e)
                for t in triggers:
                    if t:
                        trigger_counts[str(t).lower().strip()] += 1

        if trigger_counts and len(entries_with_triggers) >= 3:
            top_trigger, top_cnt = max(trigger_counts.items(), key=lambda x: x[1])
            threshold = max(3, len(entries_with_triggers) * 0.3)
            if top_cnt >= threshold:
                rec = [
                    f"Try avoiding or reducing '{top_trigger}' to see if symptoms improve.",
                    "Log this correlation with your healthcare provider.",
                ]
                pattern_id = str(uuid.uuid4())
                confidence = min(0.8, 0.3 + (top_cnt / max(len(entries), 10)) * 1.5)
                row_data = {
                    "id": pattern_id,
                    "user_id": user_id,
                    "pattern_type": "trigger_correlation",
                    "symptom_type": symptom_type,
                    "pattern_description": (
                        f"'{top_trigger.title()}' appears as a trigger in {top_cnt} of "
                        f"{len(entries_with_triggers)} entries for "
                        f"'{symptom_type.replace('_', ' ').title()}'."
                    ),
                    "confidence_score": confidence,
                    "supporting_entries": json.dumps(
                        [e["id"] for e in entries_with_triggers[:20]]
                    ),
                    "recommendations": json.dumps(rec),
                    "detected_at": now.isoformat(),
                    "is_active": True,
                }
                await _supabase_upsert("symptom_patterns", row_data)
                detected.append(
                    SymptomPattern(
                        id=pattern_id,
                        user_id=user_id,
                        pattern_type="trigger_correlation",
                        symptom_type=symptom_type,
                        pattern_description=row_data["pattern_description"],
                        confidence_score=confidence,
                        supporting_entry_count=min(20, len(entries_with_triggers)),
                        recommendations=rec,
                        detected_at=now,
                        is_active=True,
                    )
                )

        # ── 4. Severity trend ─────────────────────────────────────────────
        if len(entries) >= 5:
            severities = [int(e.get("severity") or 5) for e in entries]
            n = len(severities)
            mean_x = (n - 1) / 2.0
            mean_y = sum(severities) / n
            num = sum((i - mean_x) * (severities[i] - mean_y) for i in range(n))
            den = sum((i - mean_x) ** 2 for i in range(n))
            slope = num / den if den != 0 else 0.0

            if abs(slope) > 0.05:
                direction = "worsening" if slope > 0 else "improving"
                avg_recent = sum(severities[-5:]) / 5
                rec = []
                if direction == "worsening":
                    rec = [
                        f"Severity of '{symptom_type}' is trending upward — consult your healthcare provider.",
                        "Review recent changes in diet, medications, or activities.",
                    ]
                else:
                    rec = [
                        f"Severity of '{symptom_type}' is trending downward — keep doing what's working.",
                    ]
                pattern_id = str(uuid.uuid4())
                confidence = min(0.8, 0.4 + abs(slope) * 2)
                row_data = {
                    "id": pattern_id,
                    "user_id": user_id,
                    "pattern_type": "severity_trend",
                    "symptom_type": symptom_type,
                    "pattern_description": (
                        f"'{symptom_type.replace('_', ' ').title()}' is {direction} "
                        f"(recent average severity: {avg_recent:.1f}/10)."
                    ),
                    "confidence_score": confidence,
                    "supporting_entries": json.dumps([e["id"] for e in entries[-20:]]),
                    "recommendations": json.dumps(rec),
                    "detected_at": now.isoformat(),
                    "is_active": True,
                }
                await _supabase_upsert("symptom_patterns", row_data)
                detected.append(
                    SymptomPattern(
                        id=pattern_id,
                        user_id=user_id,
                        pattern_type="severity_trend",
                        symptom_type=symptom_type,
                        pattern_description=row_data["pattern_description"],
                        confidence_score=confidence,
                        supporting_entry_count=min(20, len(entries)),
                        recommendations=rec,
                        detected_at=now,
                        is_active=True,
                    )
                )

    logger.info(
        "Pattern detection for user %s: %d patterns from %d entries",
        user_id,
        len(detected),
        len(rows),
    )
    return detected
