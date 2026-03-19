"""
Medications & Supplements Tracker API

Pro+ feature for tracking medications, supplements, and adherence.
Includes drug interaction warnings, refill reminders, and adherence analytics.

Phase 1 of Health Intelligence Features
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import date, datetime, timezone, timedelta
import uuid
import json
import base64
import io

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
# PYDANTIC MODELS - MEDICATIONS
# ============================================================================


class MedicationBase(BaseModel):
    medication_name: str = Field(..., min_length=1, max_length=200)
    generic_name: Optional[str] = Field(None, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    route: str = Field(default="oral", max_length=50)
    indication: Optional[str] = Field(None, max_length=500)
    prescribing_doctor: Optional[str] = Field(None, max_length=200)
    pharmacy: Optional[str] = Field(None, max_length=200)
    prescription_number: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True
    refill_reminder_enabled: bool = False
    refill_reminder_days_before: int = Field(default=7, ge=1, le=30)
    side_effects_experienced: List[str] = []
    notes: Optional[str] = None


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(BaseModel):
    medication_name: Optional[str] = Field(None, min_length=1, max_length=200)
    generic_name: Optional[str] = Field(None, max_length=200)
    dosage: Optional[str] = Field(None, min_length=1, max_length=100)
    frequency: Optional[str] = Field(None, min_length=1, max_length=100)
    route: Optional[str] = Field(None, max_length=50)
    indication: Optional[str] = Field(None, max_length=500)
    prescribing_doctor: Optional[str] = Field(None, max_length=200)
    pharmacy: Optional[str] = Field(None, max_length=200)
    prescription_number: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    refill_reminder_enabled: Optional[bool] = None
    refill_reminder_days_before: Optional[int] = Field(None, ge=1, le=30)
    side_effects_experienced: Optional[List[str]] = None
    notes: Optional[str] = None


class MedicationResponse(MedicationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


# ============================================================================
# PYDANTIC MODELS - SUPPLEMENTS
# ============================================================================


class SupplementBase(BaseModel):
    supplement_name: str = Field(..., min_length=1, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    form: str = Field(default="capsule", max_length=50)
    purpose: Optional[str] = Field(None, max_length=500)
    taken_with_food: Optional[bool] = None
    time_of_day: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = True
    notes: Optional[str] = None


class SupplementCreate(SupplementBase):
    pass


class SupplementUpdate(BaseModel):
    supplement_name: Optional[str] = Field(None, min_length=1, max_length=200)
    brand: Optional[str] = Field(None, max_length=100)
    dosage: Optional[str] = Field(None, min_length=1, max_length=100)
    frequency: Optional[str] = Field(None, min_length=1, max_length=100)
    form: Optional[str] = Field(None, max_length=50)
    purpose: Optional[str] = Field(None, max_length=500)
    taken_with_food: Optional[bool] = None
    time_of_day: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class SupplementResponse(SupplementBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


# ============================================================================
# PYDANTIC MODELS - ADHERENCE
# ============================================================================


class AdherenceLogEntry(BaseModel):
    id: str
    user_id: str
    medication_id: Optional[str]
    supplement_id: Optional[str]
    scheduled_time: datetime
    taken_time: Optional[datetime]
    was_taken: bool
    missed_reason: Optional[str]
    side_effects_noted: Optional[str]
    created_at: datetime


class AdherenceStats(BaseModel):
    total_scheduled: int
    total_taken: int
    missed: int
    adherence_rate: float
    recent_entries: List[AdherenceLogEntry]
    by_medication: Optional[dict] = None
    by_supplement: Optional[dict] = None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _medication_row_to_response(row: dict) -> MedicationResponse:
    """Convert database row to MedicationResponse"""
    # Parse side effects if stored as string
    side_effects = row.get("side_effects_experienced", [])
    if isinstance(side_effects, str):
        try:
            side_effects = json.loads(side_effects)
        except (json.JSONDecodeError, TypeError):
            side_effects = []

    return MedicationResponse(
        id=row["id"],
        user_id=row["user_id"],
        medication_name=row["medication_name"],
        generic_name=row.get("generic_name"),
        dosage=row["dosage"],
        frequency=row["frequency"],
        route=row.get("route", "oral"),
        indication=row.get("indication"),
        prescribing_doctor=row.get("prescribing_doctor"),
        pharmacy=row.get("pharmacy"),
        prescription_number=row.get("prescription_number"),
        start_date=row.get("start_date"),
        end_date=row.get("end_date"),
        is_active=row.get("is_active", True),
        refill_reminder_enabled=row.get("refill_reminder_enabled", False),
        refill_reminder_days_before=row.get("refill_reminder_days_before", 7),
        side_effects_experienced=side_effects,
        notes=row.get("notes"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _supplement_row_to_response(row: dict) -> SupplementResponse:
    """Convert database row to SupplementResponse"""
    return SupplementResponse(
        id=row["id"],
        user_id=row["user_id"],
        supplement_name=row["supplement_name"],
        brand=row.get("brand"),
        dosage=row["dosage"],
        frequency=row["frequency"],
        form=row.get("form", "capsule"),
        purpose=row.get("purpose"),
        taken_with_food=row.get("taken_with_food"),
        time_of_day=row.get("time_of_day"),
        start_date=row.get("start_date"),
        end_date=row.get("end_date"),
        is_active=row.get("is_active", True),
        notes=row.get("notes"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ============================================================================
# MEDICATIONS ENDPOINTS
# ============================================================================


@router.get("/medications", response_model=List[MedicationResponse])
async def list_medications(
    active_only: bool = Query(default=True),
    current_user: dict = Depends(get_current_user),
):
    """
    List user's medications.

    - **active_only**: Only return active medications (default: True)
    """
    user_id = current_user["id"]

    params = f"user_id=eq.{user_id}&select=*&order=created_at.desc"
    if active_only:
        params += "&is_active=eq.true"

    rows = await _supabase_get("medications", params)
    if not rows:
        return []

    return [_medication_row_to_response(row) for row in rows]


@router.post("/medications", response_model=MedicationResponse, status_code=201)
async def add_medication(
    body: MedicationCreate, current_user: dict = Depends(get_current_user)
):
    """
    Add a new medication (Pro+ only).

    Requires Pro+ subscription tier.
    """
    user_id = current_user["id"]

    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        **body.dict(exclude={"side_effects_experienced"}),
        "side_effects_experienced": json.dumps(body.side_effects_experienced),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await _supabase_upsert("medications", data)
    if not result:
        logger.error(f"Failed to save medication for user {user_id}")
        raise HTTPException(status_code=500, detail="Failed to save medication")

    logger.info(f"Medication added: {result['id']} for user {user_id}")
    return _medication_row_to_response(result)


@router.put("/medications/{med_id}", response_model=MedicationResponse)
async def update_medication(
    med_id: str,
    body: MedicationUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing medication."""
    user_id = current_user["id"]

    # Verify ownership
    rows = await _supabase_get(
        "medications", f"id=eq.{med_id}&user_id=eq.{user_id}&select=*&limit=1"
    )
    if not rows or not rows[0]:
        raise HTTPException(status_code=404, detail="Medication not found")

    # Build update dict (only include provided fields)
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}

    for field, value in body.dict(exclude_unset=True).items():
        if field == "side_effects_experienced" and value is not None:
            updates[field] = json.dumps(value)
        elif value is not None:
            updates[field] = value

    result = await _supabase_patch(
        "medications", f"id=eq.{med_id}&user_id=eq.{user_id}", updates
    )
    if not result:
        logger.error(f"Failed to update medication {med_id} for user {user_id}")
        raise HTTPException(status_code=500, detail="Failed to update medication")

    logger.info(f"Medication updated: {med_id} for user {user_id}")
    return _medication_row_to_response(result)


@router.delete("/medications/{med_id}", status_code=204)
async def delete_medication(
    med_id: str, current_user: dict = Depends(get_current_user)
):
    """Delete a medication."""
    user_id = current_user["id"]

    # Verify ownership
    rows = await _supabase_get(
        "medications", f"id=eq.{med_id}&user_id=eq.{user_id}&select=id&limit=1"
    )
    if not rows or not rows[0]:
        raise HTTPException(status_code=404, detail="Medication not found")

    success = await _supabase_delete(
        "medications", f"id=eq.{med_id}&user_id=eq.{user_id}"
    )
    if not success:
        logger.error(f"Failed to delete medication {med_id} for user {user_id}")
        raise HTTPException(status_code=500, detail="Failed to delete medication")

    logger.info(f"Medication deleted: {med_id} for user {user_id}")


# ============================================================================
# SUPPLEMENTS ENDPOINTS
# ============================================================================


@router.get("/supplements", response_model=List[SupplementResponse])
async def list_supplements(
    active_only: bool = Query(default=True),
    current_user: dict = Depends(get_current_user),
):
    """
    List user's supplements.

    - **active_only**: Only return active supplements (default: True)
    """
    user_id = current_user["id"]

    params = f"user_id=eq.{user_id}&select=*&order=created_at.desc"
    if active_only:
        params += "&is_active=eq.true"

    rows = await _supabase_get("supplements", params)
    if not rows:
        return []

    return [_supplement_row_to_response(row) for row in rows]


@router.post("/supplements", response_model=SupplementResponse, status_code=201)
async def add_supplement(
    body: SupplementCreate, current_user: dict = Depends(get_current_user)
):
    """
    Add a new supplement (Pro+ only).

    Requires Pro+ subscription tier.
    """
    user_id = current_user["id"]

    data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        **body.dict(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = await _supabase_upsert("supplements", data)
    if not result:
        logger.error(f"Failed to save supplement for user {user_id}")
        raise HTTPException(status_code=500, detail="Failed to save supplement")

    logger.info(f"Supplement added: {result['id']} for user {user_id}")
    return _supplement_row_to_response(result)


@router.put("/supplements/{supp_id}", response_model=SupplementResponse)
async def update_supplement(
    supp_id: str,
    body: SupplementUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an existing supplement."""
    user_id = current_user["id"]

    # Verify ownership
    rows = await _supabase_get(
        "supplements", f"id=eq.{supp_id}&user_id=eq.{user_id}&select=*&limit=1"
    )
    if not rows or not rows[0]:
        raise HTTPException(status_code=404, detail="Supplement not found")

    # Build update dict (only include provided fields)
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}

    for field, value in body.dict(exclude_unset=True).items():
        if value is not None:
            updates[field] = value

    result = await _supabase_patch(
        "supplements", f"id=eq.{supp_id}&user_id=eq.{user_id}", updates
    )
    if not result:
        logger.error(f"Failed to update supplement {supp_id} for user {user_id}")
        raise HTTPException(status_code=500, detail="Failed to update supplement")

    logger.info(f"Supplement updated: {supp_id} for user {user_id}")
    return _supplement_row_to_response(result)


@router.delete("/supplements/{supp_id}", status_code=204)
async def delete_supplement(
    supp_id: str, current_user: dict = Depends(get_current_user)
):
    """Delete a supplement."""
    user_id = current_user["id"]

    # Verify ownership
    rows = await _supabase_get(
        "supplements", f"id=eq.{supp_id}&user_id=eq.{user_id}&select=id&limit=1"
    )
    if not rows or not rows[0]:
        raise HTTPException(status_code=404, detail="Supplement not found")

    success = await _supabase_delete(
        "supplements", f"id=eq.{supp_id}&user_id=eq.{user_id}"
    )
    if not success:
        logger.error(f"Failed to delete supplement {supp_id} for user {user_id}")
        raise HTTPException(status_code=500, detail="Failed to delete supplement")

    logger.info(f"Supplement deleted: {supp_id} for user {user_id}")


# ============================================================================
# ADHERENCE ENDPOINTS
# ============================================================================


@router.get("/adherence/stats", response_model=AdherenceStats)
async def get_adherence_stats(
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
):
    """
    Calculate adherence statistics for the last N days.

    - **days**: Number of days to analyze (default: 30, max: 365)
    """
    user_id = current_user["id"]
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    rows = await _supabase_get(
        "medication_adherence_log",
        f"user_id=eq.{user_id}&scheduled_time=gte.{start_date}&select=*&order=scheduled_time.desc&limit=1000",
    )

    if not rows:
        return AdherenceStats(
            total_scheduled=0,
            total_taken=0,
            missed=0,
            adherence_rate=0.0,
            recent_entries=[],
        )

    total_scheduled = len(rows)
    total_taken = sum(1 for r in rows if r.get("was_taken"))
    missed = total_scheduled - total_taken
    adherence_rate = (
        (total_taken / total_scheduled * 100) if total_scheduled > 0 else 0.0
    )

    # Convert recent entries
    recent_entries = [
        AdherenceLogEntry(
            id=r["id"],
            user_id=r["user_id"],
            medication_id=r.get("medication_id"),
            supplement_id=r.get("supplement_id"),
            scheduled_time=r["scheduled_time"],
            taken_time=r.get("taken_time"),
            was_taken=r.get("was_taken", False),
            missed_reason=r.get("missed_reason"),
            side_effects_noted=r.get("side_effects_noted"),
            created_at=r["created_at"],
        )
        for r in rows[:10]
    ]

    return AdherenceStats(
        total_scheduled=total_scheduled,
        total_taken=total_taken,
        missed=missed,
        adherence_rate=round(adherence_rate, 1),
        recent_entries=recent_entries,
    )


# ============================================================================
# ADHERENCE DAILY CHECK-IN ENDPOINTS
# ============================================================================


def _parse_doses_per_day(f: str) -> int:
    """Parse frequency string into daily dose count (0 = skip from daily schedule)."""
    f = f.lower()
    if any(x in f for x in ["as needed", "prn", "when needed"]):
        return 0
    if any(x in f for x in ["twice", "bid", "2x", "2 time"]):
        return 2
    if any(x in f for x in ["three", "tid", "3x", "3 time"]):
        return 3
    if any(x in f for x in ["four", "qid", "4x", "4 time"]):
        return 4
    if any(x in f for x in ["weekly", "once a week"]):
        return 0
    return 1


class TodayMedication(BaseModel):
    medication_id: str
    medication_name: str
    dosage: str
    doses_today: int
    logs: List[dict]


class TodayAdherenceResponse(BaseModel):
    medications: List[TodayMedication]


class LogAdherenceRequest(BaseModel):
    medication_id: Optional[str] = None
    supplement_id: Optional[str] = None
    was_taken: bool
    scheduled_slot: int = 1
    date: Optional[date] = None


# Slot → hour offset
_SLOT_HOURS = {1: 8, 2: 14, 3: 20}


@router.get("/adherence/today", response_model=TodayAdherenceResponse)
async def get_today_adherence(
    current_user: dict = Depends(get_current_user),
):
    """Return today's medication schedule with logged doses."""
    user_id = current_user["id"]

    meds = await _supabase_get(
        "medications",
        f"user_id=eq.{user_id}&is_active=eq.true&select=id,medication_name,dosage,frequency",
    )
    if not meds:
        return TodayAdherenceResponse(medications=[])

    today = date.today()
    # Use naive datetime strings (no +00:00) to avoid URL encoding issues with '+'
    day_start = f"{today}T00:00:00"
    day_end = f"{today}T23:59:59"

    logs = (
        await _supabase_get(
            "medication_adherence_log",
            f"user_id=eq.{user_id}&scheduled_time=gte.{day_start}&scheduled_time=lte.{day_end}&select=*",
        )
        or []
    )

    result = []
    for med in meds:
        dpd = _parse_doses_per_day(med.get("frequency", "once daily"))
        if dpd == 0:
            continue
        med_logs = [lg for lg in logs if lg.get("medication_id") == med["id"]]
        result.append(
            TodayMedication(
                medication_id=med["id"],
                medication_name=med["medication_name"],
                dosage=med.get("dosage", ""),
                doses_today=dpd,
                logs=med_logs,
            )
        )

    return TodayAdherenceResponse(medications=result)


@router.post("/adherence/log", response_model=AdherenceLogEntry, status_code=201)
async def log_adherence(
    body: LogAdherenceRequest,
    current_user: dict = Depends(get_current_user),
):
    """Log a medication dose taken/missed for today."""
    user_id = current_user["id"]
    log_date = body.date or date.today()
    slot_hour = _SLOT_HOURS.get(body.scheduled_slot, 8)
    scheduled_time = datetime(
        log_date.year,
        log_date.month,
        log_date.day,
        slot_hour,
        0,
        0,
        tzinfo=timezone.utc,
    )

    # Dedup: check if a log already exists for this med + date + slot
    med_filter = (
        f"medication_id=eq.{body.medication_id}"
        if body.medication_id
        else "supplement_id=eq." + (body.supplement_id or "null")
    )
    existing = await _supabase_get(
        "medication_adherence_log",
        f"user_id=eq.{user_id}&{med_filter}&scheduled_time=eq.{scheduled_time.isoformat()}&select=id&limit=1",
    )

    entry_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()

    data = {
        "id": entry_id,
        "user_id": user_id,
        "medication_id": body.medication_id,
        "supplement_id": body.supplement_id,
        "scheduled_time": scheduled_time.isoformat(),
        "taken_time": now_iso if body.was_taken else None,
        "was_taken": body.was_taken,
        "created_at": now_iso,
    }

    if existing and existing[0]:
        # Update existing record
        entry_id = existing[0]["id"]
        updated = await _supabase_patch(
            "medication_adherence_log",
            f"id=eq.{entry_id}&user_id=eq.{user_id}",
            {"was_taken": body.was_taken, "taken_time": data["taken_time"]},
        )
        row = updated or data
    else:
        row = await _supabase_upsert("medication_adherence_log", data)
        if not row:
            row = data

    return AdherenceLogEntry(
        id=row.get("id", entry_id),
        user_id=user_id,
        medication_id=row.get("medication_id"),
        supplement_id=row.get("supplement_id"),
        scheduled_time=row.get("scheduled_time", scheduled_time.isoformat()),
        taken_time=row.get("taken_time"),
        was_taken=row.get("was_taken", body.was_taken),
        missed_reason=row.get("missed_reason"),
        side_effects_noted=row.get("side_effects_noted"),
        created_at=row.get("created_at", now_iso),
    )


# ============================================================================
# ADHERENCE HISTORY
# ============================================================================


class DayAdherence(BaseModel):
    scheduled: int
    taken: int


class MedAdherenceHistory(BaseModel):
    medication_id: Optional[str]
    medication_name: str
    doses_per_day: int
    days: dict  # date string → DayAdherence dict


class AdherenceHistoryResponse(BaseModel):
    dates: List[str]  # chronological YYYY-MM-DD strings
    medications: List[MedAdherenceHistory]


@router.get("/adherence/history", response_model=AdherenceHistoryResponse)
async def get_adherence_history(
    days: int = Query(default=7, ge=1, le=30),
    current_user: dict = Depends(get_current_user),
):
    """Return per-day, per-medication adherence logs for the last N days."""
    from collections import defaultdict

    user_id = current_user["id"]
    today = datetime.now(timezone.utc).date()

    # Build chronological date list
    dates = [(today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]

    # Fetch active medications
    meds = (
        await _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true&select=id,medication_name,frequency",
        )
        or []
    )

    if not meds:
        return AdherenceHistoryResponse(dates=dates, medications=[])

    # Fetch adherence logs for the period
    start_dt = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    logs = (
        await _supabase_get(
            "medication_adherence_log",
            f"user_id=eq.{user_id}&scheduled_time=gte.{start_dt}"
            f"&select=medication_id,scheduled_time,was_taken&limit=1000",
        )
        or []
    )

    # Group logs by medication_id → date → [was_taken, ...]
    logs_by_med_date: dict[str, dict[str, list]] = defaultdict(
        lambda: defaultdict(list)
    )
    for log in logs:
        mid = log.get("medication_id")
        if mid:
            date_key = log["scheduled_time"][:10]
            logs_by_med_date[mid][date_key].append(log.get("was_taken", False))

    result = []
    for med in meds:
        mid = med["id"]
        dpd = _parse_doses_per_day(med.get("frequency") or "")
        if dpd == 0:
            continue  # skip as-needed / weekly

        days_dict = {}
        for d in dates:
            taken_list = logs_by_med_date[mid].get(d, [])
            taken = sum(1 for t in taken_list if t)
            days_dict[d] = {"scheduled": dpd, "taken": taken}

        result.append(
            MedAdherenceHistory(
                medication_id=mid,
                medication_name=med.get("medication_name", "Unknown"),
                doses_per_day=dpd,
                days=days_dict,
            )
        )

    return AdherenceHistoryResponse(dates=dates, medications=result)


# ============================================================================
# ADHERENCE STREAKS + MISSED-DOSE PATTERNS
# ============================================================================


class MedStreakData(BaseModel):
    medication_id: str
    medication_name: str
    current_streak: int  # consecutive days taken (ending today)
    longest_streak: int  # all-time best streak
    total_days_logged: int
    total_days_taken: int
    missed_days_of_week: List[
        str
    ]  # day names most commonly skipped, e.g. ["Saturday", "Sunday"]


class StreaksResponse(BaseModel):
    medications: List[MedStreakData]
    overall_current_streak: int  # days where ALL scheduled meds were taken
    overall_longest_streak: int


@router.get("/adherence/streaks", response_model=StreaksResponse)
async def get_adherence_streaks(
    days: int = Query(default=90, ge=7, le=365),
    current_user: dict = Depends(get_current_user),
):
    """
    Compute current and longest adherence streak per medication,
    plus which days-of-week are most often missed.
    """
    from collections import defaultdict

    user_id = current_user["id"]
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=days - 1)

    # All dates in window (oldest → newest)
    date_range = [(start + timedelta(days=i)) for i in range(days)]

    meds = (
        await _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true&select=id,medication_name,frequency",
        )
        or []
    )
    if not meds:
        return StreaksResponse(
            medications=[], overall_current_streak=0, overall_longest_streak=0
        )

    start_dt = start.isoformat()
    logs = (
        await _supabase_get(
            "medication_adherence_log",
            f"user_id=eq.{user_id}&scheduled_time=gte.{start_dt}"
            f"&select=medication_id,scheduled_time,was_taken&limit=5000",
        )
        or []
    )

    # Group: med_id -> date_str -> any taken
    taken_by_med_date: dict[str, dict[str, bool]] = defaultdict(dict)
    for log in logs:
        mid = log.get("medication_id")
        if mid:
            d = log["scheduled_time"][:10]
            # If any log for that day is taken, mark the day taken
            taken_by_med_date[mid][d] = taken_by_med_date[mid].get(d, False) or bool(
                log.get("was_taken")
            )

    DAY_NAMES = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    def _compute_streaks(taken_map: dict) -> tuple[int, int]:
        """Returns (current_streak, longest_streak) from date_str -> bool map."""
        current = 0
        longest = 0
        run = 0
        for d in date_range:
            ds = d.isoformat()
            if taken_map.get(ds, False):
                run += 1
                longest = max(longest, run)
            else:
                run = 0
        # Current streak: count backwards from today
        for d in reversed(date_range):
            ds = d.isoformat()
            if taken_map.get(ds, False):
                current += 1
            else:
                break
        return current, longest

    def _missed_days_of_week(med_id: str) -> list[str]:
        """Return up to 2 day names most commonly missed (> 50% miss rate on that day)."""
        day_missed: dict[str, int] = defaultdict(int)
        day_total: dict[str, int] = defaultdict(int)
        for d in date_range:
            ds = d.isoformat()
            if ds in taken_by_med_date[med_id]:
                dow = DAY_NAMES[d.weekday()]
                day_total[dow] += 1
                if not taken_by_med_date[med_id][ds]:
                    day_missed[dow] += 1
        # Days where miss rate > 50%
        bad_days = [
            day
            for day in DAY_NAMES
            if day_total.get(day, 0) >= 2
            and day_missed.get(day, 0) / day_total[day] > 0.5
        ]
        return bad_days[:2]

    med_results = []
    for med in meds:
        mid = med["id"]
        dpd = _parse_doses_per_day(med.get("frequency") or "")
        if dpd == 0:
            continue
        tm = taken_by_med_date[mid]
        cs, ls = _compute_streaks(tm)
        total_logged = len(tm)
        total_taken = sum(1 for v in tm.values() if v)
        med_results.append(
            MedStreakData(
                medication_id=mid,
                medication_name=med.get("medication_name", "Unknown"),
                current_streak=cs,
                longest_streak=ls,
                total_days_logged=total_logged,
                total_days_taken=total_taken,
                missed_days_of_week=_missed_days_of_week(mid),
            )
        )

    # Overall streak: days where every scheduled med was taken
    if med_results:
        scheduled_ids = {m.medication_id for m in med_results}
        overall_taken: dict[str, bool] = {}
        for d in date_range:
            ds = d.isoformat()
            overall_taken[ds] = all(
                taken_by_med_date[mid].get(ds, False) for mid in scheduled_ids
            )
        ocs, ols = _compute_streaks(overall_taken)
    else:
        ocs, ols = 0, 0

    return StreaksResponse(
        medications=med_results,
        overall_current_streak=ocs,
        overall_longest_streak=ols,
    )


# ============================================================================
# PRESCRIPTION / SUPPLEMENT BOTTLE IMAGE SCAN
# ============================================================================


class PrescriptionScanResult(BaseModel):
    """Extracted medication or supplement data from a scanned image."""

    is_supplement: bool = False
    image_type: str = (
        "unknown"  # prescription_label | bottle | strip | handwritten | other
    )
    medication_name: Optional[str] = None
    generic_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    indication: Optional[str] = None
    prescribing_doctor: Optional[str] = None
    pharmacy: Optional[str] = None
    prescription_number: Optional[str] = None
    start_date: Optional[str] = None
    notes: Optional[str] = None
    # Supplement-specific
    brand: Optional[str] = None
    form: Optional[str] = None
    purpose: Optional[str] = None
    # Meta
    confidence: float = 0.0
    raw_text: Optional[str] = None


def _compress_image(image_bytes: bytes, max_bytes: int = 4_500_000) -> bytes:
    """Compress image to stay under Anthropic's 5 MB limit."""
    if len(image_bytes) <= max_bytes:
        return image_bytes
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        quality = 85
        scale = 1.0
        while True:
            buf = io.BytesIO()
            w = int(img.width * scale)
            h = int(img.height * scale)
            out = img.resize((w, h), Image.LANCZOS) if scale < 1.0 else img
            out.save(buf, format="JPEG", quality=quality, optimize=True)
            compressed = buf.getvalue()
            if len(compressed) <= max_bytes:
                return compressed
            if quality > 60:
                quality -= 10
            else:
                scale *= 0.75
            if scale < 0.1:
                return compressed
    except Exception:
        return image_bytes


@router.post("/medications/scan-prescription", response_model=PrescriptionScanResult)
async def scan_prescription_image(
    image: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> PrescriptionScanResult:
    """
    Extract medication or supplement details from a photo of a prescription label,
    supplement bottle, pill strip, or handwritten doctor prescription using
    Claude Vision AI.
    """
    import anthropic
    import os

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI vision service not configured")

    image_bytes = await image.read()
    image_bytes = _compress_image(image_bytes)

    # Detect MIME type
    media_type = "image/jpeg"
    try:
        from PIL import Image as PILImage

        img = PILImage.open(io.BytesIO(image_bytes))
        fmt = (img.format or "JPEG").upper()
        media_type = {
            "JPEG": "image/jpeg",
            "PNG": "image/png",
            "GIF": "image/gif",
            "WEBP": "image/webp",
        }.get(fmt, "image/jpeg")
    except Exception:
        pass

    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    prompt = """You are analyzing an image of a medication prescription, supplement bottle, pill strip, or handwritten doctor prescription.

Extract ALL medication or supplement information visible in the image.

Return ONLY a valid JSON object with these fields. Omit any field you cannot confidently determine — do NOT guess or invent values:
{
  "is_supplement": false,
  "image_type": "prescription_label|bottle|strip|handwritten|other",
  "medication_name": "brand name of the drug or supplement",
  "generic_name": "INN/generic name if different from brand (e.g. atorvastatin for Lipitor)",
  "dosage": "strength with units e.g. 10mg, 500mg, 1000 IU, 2.5mcg",
  "frequency": "how often e.g. once daily, twice daily, every 8 hours, take as directed",
  "route": "oral|topical|injection|inhaled",
  "indication": "condition it treats e.g. hypertension, Type 2 diabetes, vitamin D deficiency",
  "prescribing_doctor": "Dr. Full Name if visible on prescription",
  "pharmacy": "pharmacy name if visible on label",
  "prescription_number": "Rx number if visible",
  "start_date": "YYYY-MM-DD format if a fill or start date is visible",
  "notes": "important warnings, special instructions, food or drug interactions, storage notes",
  "brand": "brand name if this is a supplement",
  "form": "capsule|tablet|powder|liquid|gummy — if this is a supplement",
  "purpose": "what the supplement is for e.g. immune support, bone health",
  "confidence": 0.90,
  "raw_text": "all legible text extracted from the image verbatim"
}

Rules:
- Set is_supplement to true for vitamins, minerals, herbal products, or dietary supplements
- Set is_supplement to false for prescription drugs and OTC medications
- confidence should reflect how clearly the image and text were visible (0.0 to 1.0)
- Return the JSON object only, no markdown fences or extra text"""

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        result = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1200,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        content = result.content[0].text.strip()
        # Strip markdown fences if Claude adds them despite instructions
        if "```json" in content:
            content = content[
                content.find("```json") + 7 : content.rfind("```")
            ].strip()
        elif "```" in content:
            content = content[content.find("```") + 3 : content.rfind("```")].strip()

        extracted: Dict[str, Any] = json.loads(content)
        return PrescriptionScanResult(
            **{
                k: v
                for k, v in extracted.items()
                if k in PrescriptionScanResult.model_fields
            }
        )

    except json.JSONDecodeError as e:
        logger.warning(f"Prescription scan: Claude returned non-JSON: {e}")
        raise HTTPException(
            status_code=422,
            detail="Could not parse AI response. Please try a clearer image.",
        )
    except Exception as e:
        logger.error(f"Prescription scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
