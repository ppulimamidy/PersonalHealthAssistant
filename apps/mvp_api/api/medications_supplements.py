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
    body: MedicationCreate, current_user: dict = Depends(UsageGate("health_conditions"))
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
    body: SupplementCreate, current_user: dict = Depends(UsageGate("health_conditions"))
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
# PRESCRIPTION / SUPPLEMENT BOTTLE IMAGE SCAN
# ============================================================================

class PrescriptionScanResult(BaseModel):
    """Extracted medication or supplement data from a scanned image."""
    is_supplement: bool = False
    image_type: str = "unknown"          # prescription_label | bottle | strip | handwritten | other
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
        media_type = {"JPEG": "image/jpeg", "PNG": "image/png",
                      "GIF": "image/gif", "WEBP": "image/webp"}.get(fmt, "image/jpeg")
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
            content = content[content.find("```json") + 7: content.rfind("```")].strip()
        elif "```" in content:
            content = content[content.find("```") + 3: content.rfind("```")].strip()

        extracted: Dict[str, Any] = json.loads(content)
        return PrescriptionScanResult(**{k: v for k, v in extracted.items()
                                         if k in PrescriptionScanResult.model_fields})

    except json.JSONDecodeError as e:
        logger.warning(f"Prescription scan: Claude returned non-JSON: {e}")
        raise HTTPException(status_code=422, detail="Could not parse AI response. Please try a clearer image.")
    except Exception as e:
        logger.error(f"Prescription scan failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
