"""
Symptom Journal API

Pro/Pro+ feature for tracking symptoms, identifying patterns, and
correlating with nutrition, medications, sleep, etc.

Phase 1 of Health Intelligence Features
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import date, time, datetime, timezone, timedelta
import uuid
import json

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import (
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

    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        **body.dict(exclude={"triggers", "associated_symptoms", "medications_taken"}),
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
    symptom_type: Optional[str] = Query(default=None),
    min_severity: Optional[int] = Query(default=None, ge=1, le=10),
    current_user: dict = Depends(get_current_user),
):
    """
    List symptom journal entries.

    - **days**: Number of days to retrieve (default: 30, max: 365)
    - **symptom_type**: Filter by symptom type (optional)
    - **min_severity**: Minimum severity to include (optional)
    """
    user_id = current_user["id"]
    start_date = (date.today() - timedelta(days=days)).isoformat()

    params = f"user_id=eq.{user_id}&symptom_date=gte.{start_date}&select=*&order=symptom_date.desc,symptom_time.desc"

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


@router.post("/patterns/detect")
async def detect_symptom_patterns(
    current_user: dict = Depends(UsageGate("health_conditions")),  # Pro+ only
):
    """
    Trigger AI-powered pattern detection (Pro+ only).

    This endpoint will be implemented in Phase 2 with the AI agent system.
    For now, it returns a placeholder response.
    """
    user_id = current_user["id"]

    logger.info(f"Pattern detection requested for user {user_id}")

    # TODO: Implement AI pattern detection
    # This will analyze symptom history and detect:
    # - Time-based patterns (symptoms at certain times/days)
    # - Trigger-based patterns (symptoms after certain foods/activities)
    # - Cyclic patterns (monthly, seasonal)
    # - Correlations with other health metrics

    return {
        "message": "Pattern detection is under development. Will be available in Phase 2.",
        "status": "pending_implementation",
    }
