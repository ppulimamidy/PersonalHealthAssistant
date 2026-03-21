"""
Medical Records API — handles pathology, genomic/molecular, and imaging reports
in addition to existing blood labs.

Supports AI extraction from PDF/image uploads with type-specific prompts.
"""

import asyncio
import base64
import json
import os
import uuid
from datetime import date
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get, _supabase_upsert, _supabase_delete

logger = get_logger(__name__)
router = APIRouter()

VALID_RECORD_TYPES = {"pathology", "genomic", "imaging"}

# ---------------------------------------------------------------------------
# AI Extraction Prompts
# ---------------------------------------------------------------------------

PATHOLOGY_PROMPT = """Extract structured data from this pathology/biopsy report.
Return ONLY valid JSON (no markdown fences):
{
  "specimen": "tissue type and collection site",
  "diagnosis": "primary diagnosis",
  "histological_subtype": "e.g., adenocarcinoma, squamous cell",
  "stage": { "T": "T value or null", "N": "N value or null", "M": "M value or null", "overall": "overall stage or null" },
  "grade": "differentiation grade or Gleason or null",
  "margins": { "status": "clear/positive/close/null", "distance_mm": null },
  "receptor_status": {},
  "lymphovascular_invasion": "present/absent/not assessed",
  "perineural_invasion": "present/absent/not assessed",
  "additional_findings": [],
  "pathologist": "name or null",
  "lab": "facility name or null",
  "report_date": "YYYY-MM-DD or null"
}
If a field is not found in the report, use null. Extract everything available."""

GENOMIC_PROMPT = """Extract structured data from this genomic/molecular/NGS report.
Return ONLY valid JSON (no markdown fences):
{
  "test_type": "NGS/PCR/FISH/IHC/etc",
  "specimen": "tissue source",
  "mutations": [
    {
      "gene": "gene name (e.g., EGFR)",
      "exon": "exon number or null",
      "variant": "nucleotide change (e.g., c.2573T>G)",
      "protein_change": "amino acid change (e.g., p.Leu858Arg)",
      "vaf": "variant allele frequency % or null",
      "classification": { "tier": "Tier I/II/III/IV", "level": "Level A/B/C/D" },
      "clinical_significance": "Pathogenic/Likely Pathogenic/VUS/Benign",
      "sensitive_therapies": ["drug1", "drug2"],
      "resistant_therapies": [],
      "sensitivity": "Sensitive/Resistant/Unknown"
    }
  ],
  "genes_tested_negative": ["gene1", "gene2"],
  "tumor_mutational_burden": "value or null",
  "microsatellite_instability": "MSS/MSI-H/MSI-L or null",
  "pd_l1_tps": "percentage or null",
  "lab": "facility or null",
  "pathologist": "name or null",
  "genomics_consultant": "name or null",
  "report_date": "YYYY-MM-DD or null"
}
Extract ALL mutations found. For each mutation, list ALL targeted therapies mentioned."""

IMAGING_PROMPT = """Extract structured data from this imaging/radiology report.
Return ONLY valid JSON (no markdown fences):
{
  "modality": "CT/MRI/PET/X-ray/Ultrasound/Mammogram",
  "body_region": "chest/abdomen/brain/breast/etc",
  "date": "YYYY-MM-DD or null",
  "findings": [
    { "location": "anatomical location", "description": "finding description", "measurement_cm": null }
  ],
  "impression": "overall impression/conclusion",
  "comparison": "comparison to prior imaging or null",
  "scoring": "BIRADS/TIRADS/Lung-RADS score or null",
  "recommendations": "follow-up recommendations or null",
  "radiologist": "name or null"
}
Extract ALL findings with measurements when available."""

RECORD_TYPE_PROMPTS = {
    "pathology": PATHOLOGY_PROMPT,
    "genomic": GENOMIC_PROMPT,
    "imaging": IMAGING_PROMPT,
}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


class CreateRecordRequest(BaseModel):
    record_type: str
    title: Optional[str] = None
    report_date: Optional[str] = None
    provider_name: Optional[str] = None
    facility_name: Optional[str] = None
    extracted_data: Dict[str, Any] = {}
    tags: List[str] = []


@router.post("")
async def create_record(
    body: CreateRecordRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a medical record with pre-extracted data."""
    if body.record_type not in VALID_RECORD_TYPES:
        return {"error": f"Invalid record type. Valid: {VALID_RECORD_TYPES}"}

    user_id = current_user["id"]
    record_id = str(uuid.uuid4())

    # Generate AI summary
    ai_summary = await _generate_record_summary(
        body.record_type, body.extracted_data, user_id
    )

    result = await _supabase_upsert(
        "medical_records",
        {
            "id": record_id,
            "user_id": user_id,
            "record_type": body.record_type,
            "title": body.title or _auto_title(body.record_type, body.extracted_data),
            "report_date": body.report_date,
            "provider_name": body.provider_name,
            "facility_name": body.facility_name,
            "extracted_data": json.dumps(body.extracted_data),
            "ai_summary": ai_summary,
            "tags": json.dumps(body.tags),
            "created_at": date.today().isoformat(),
            "updated_at": date.today().isoformat(),
        },
    )

    return {"id": record_id, "ai_summary": ai_summary, "saved": True}


@router.get("")
async def list_records(
    record_type: Optional[str] = Query(default=None),
    current_user: dict = Depends(get_current_user),
):
    """List medical records, optionally filtered by type."""
    user_id = current_user["id"]
    params = f"user_id=eq.{user_id}&order=report_date.desc,created_at.desc&limit=50"
    if record_type and record_type in VALID_RECORD_TYPES:
        params += f"&record_type=eq.{record_type}"
    params += "&select=id,record_type,title,report_date,provider_name,facility_name,ai_summary,tags,created_at"

    rows = await _supabase_get("medical_records", params)

    return {"records": rows}


@router.get("/{record_id}")
async def get_record(
    record_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single medical record with full extracted data."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "medical_records",
        f"id=eq.{record_id}&user_id=eq.{user_id}&limit=1",
    )
    if not rows:
        return {"error": "Record not found"}

    record = rows[0]
    # Parse JSONB fields
    ed = record.get("extracted_data")
    if isinstance(ed, str):
        try:
            record["extracted_data"] = json.loads(ed)
        except Exception:
            record["extracted_data"] = {}

    tags = record.get("tags")
    if isinstance(tags, str):
        try:
            record["tags"] = json.loads(tags)
        except Exception:
            record["tags"] = []

    return record


@router.delete("/{record_id}")
async def delete_record(
    record_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a medical record."""
    user_id = current_user["id"]
    await _supabase_delete(
        "medical_records",
        f"id=eq.{record_id}&user_id=eq.{user_id}",
    )
    return {"deleted": True}


@router.post("/scan")
async def scan_record(
    image: UploadFile = File(...),
    record_type: str = Form(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload a file (PDF/image) and extract structured data using AI."""
    if record_type not in VALID_RECORD_TYPES:
        return {"error": f"Invalid record type. Valid: {VALID_RECORD_TYPES}"}

    image_bytes = await image.read()
    prompt = RECORD_TYPE_PROMPTS[record_type]

    # Determine content type
    filename = (image.filename or "").lower()
    is_pdf = filename.endswith(".pdf") or image.content_type == "application/pdf"

    extracted = await _extract_with_claude(image_bytes, prompt, is_pdf)

    return {
        "record_type": record_type,
        "extracted_data": extracted,
        "confidence": 0.85 if extracted else 0.0,
    }


SMART_CLASSIFY_PROMPT = """Analyze this medical document and:
1. Classify it as one of: "pathology" (biopsy, tissue, surgical pathology), "genomic" (NGS, mutation panel, molecular testing, EGFR/BRCA/KRAS), or "imaging" (CT, MRI, PET, X-ray, ultrasound)
2. Extract the structured data appropriate for that type

Return ONLY valid JSON (no markdown fences):
{
  "detected_type": "pathology" or "genomic" or "imaging",
  "confidence": 0.0-1.0,
  ...all fields appropriate for the detected type...
}

For pathology: include specimen, diagnosis, histological_subtype, stage, grade, margins, receptor_status, pathologist, lab, report_date
For genomic: include test_type, specimen, mutations (array with gene, exon, variant, protein_change, vaf, classification, sensitive_therapies, sensitivity), genes_tested_negative, lab, report_date
For imaging: include modality, body_region, date, findings (array), impression, scoring, radiologist"""


@router.post("/smart-scan")
async def smart_scan(
    image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload a file — AI auto-classifies the record type and extracts data."""
    image_bytes = await image.read()
    filename = (image.filename or "").lower()
    is_pdf = filename.endswith(".pdf") or image.content_type == "application/pdf"

    extracted = await _extract_with_claude(image_bytes, SMART_CLASSIFY_PROMPT, is_pdf)

    detected_type = extracted.pop("detected_type", None)
    confidence = extracted.pop("confidence", 0.5)

    # Validate detected type
    if detected_type not in VALID_RECORD_TYPES:
        # Try to infer from content
        if any(
            k in extracted for k in ("mutations", "test_type", "genes_tested_negative")
        ):
            detected_type = "genomic"
        elif any(k in extracted for k in ("diagnosis", "stage", "margins", "specimen")):
            detected_type = "pathology"
        elif any(
            k in extracted
            for k in ("modality", "findings", "impression", "radiologist")
        ):
            detected_type = "imaging"
        else:
            detected_type = "pathology"  # default fallback

    return {
        "record_type": detected_type,
        "extracted_data": extracted,
        "confidence": confidence,
    }


@router.post("/{record_id}/insight")
async def record_insight(
    record_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Generate AI insight for a medical record, cross-referencing user data."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "medical_records",
        f"id=eq.{record_id}&user_id=eq.{user_id}&limit=1",
    )
    if not rows:
        return {"insight": "Record not found."}

    record = rows[0]
    ed = record.get("extracted_data")
    if isinstance(ed, str):
        try:
            ed = json.loads(ed)
        except Exception:
            ed = {}

    record_type = record.get("record_type", "")

    # Gather user context
    conditions, medications = await asyncio.gather(
        _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name",
        ),
        _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true&select=medication_name,dosage",
        ),
    )

    ctx_parts = []
    if conditions:
        ctx_parts.append(
            f"Conditions: {', '.join(c.get('condition_name', '') for c in conditions)}"
        )
    if medications:
        med_strs = [
            m.get("medication_name", "") + " " + m.get("dosage", "")
            for m in medications
        ]
        ctx_parts.append(f"Medications: {', '.join(med_strs)}")

    if record_type == "genomic":
        mutations = ed.get("mutations", [])
        mutation_text = "\n".join(
            f"- {m.get('gene', '?')} {m.get('protein_change', '')}: {m.get('classification', {}).get('tier', '?')} "
            f"— Sensitive to: {', '.join(m.get('sensitive_therapies', []))}"
            for m in mutations
        )
        prompt = f"""You are an oncology specialist. Analyze this genomic profile:

{mutation_text}

Patient context: {'; '.join(ctx_parts) or 'None'}

Generate a 3-4 sentence clinical interpretation:
- What the mutations mean for treatment selection
- Reference NCCN guidelines for this molecular profile
- Flag if any current medication is a targeted therapy match
- Suggest clinical trial search if applicable
Return ONLY the interpretation text."""

    elif record_type == "pathology":
        diagnosis = ed.get("diagnosis", "Unknown")
        stage = ed.get("stage", {})
        grade = ed.get("grade", "")
        prompt = f"""You are a pathology specialist. Interpret this biopsy result:

Diagnosis: {diagnosis}
Stage: {json.dumps(stage)}
Grade: {grade}
Receptor status: {json.dumps(ed.get('receptor_status', {}))}

Patient context: {'; '.join(ctx_parts) or 'None'}

Generate a 3-4 sentence interpretation:
- What the diagnosis and staging mean
- Reference NCCN or relevant guidelines for treatment approach
- Note any receptor-guided therapy options
Return ONLY the interpretation text."""

    elif record_type == "imaging":
        findings = ed.get("findings", [])
        impression = ed.get("impression", "")
        prompt = f"""You are a radiologist. Interpret these imaging findings:

Impression: {impression}
Findings: {json.dumps(findings)}

Patient context: {'; '.join(ctx_parts) or 'None'}

Generate a 2-3 sentence interpretation:
- What the findings suggest
- Recommended follow-up
Return ONLY the interpretation text."""
    else:
        return {"insight": "Unknown record type."}

    insight = await _call_claude_text(prompt)
    return {"insight": insight}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auto_title(record_type: str, data: dict) -> str:
    """Generate a title from extracted data."""
    if record_type == "pathology":
        return data.get("diagnosis") or "Pathology Report"
    elif record_type == "genomic":
        mutations = data.get("mutations", [])
        genes = [m.get("gene", "?") for m in mutations[:3]]
        return f"Genomic: {', '.join(genes)}" if genes else "Genomic Report"
    elif record_type == "imaging":
        return f"{data.get('modality', 'Imaging')}: {data.get('body_region', 'Report')}"
    return "Medical Record"


async def _generate_record_summary(record_type: str, data: dict, user_id: str) -> str:
    """Generate a brief AI summary for the record."""
    if record_type == "genomic":
        mutations = data.get("mutations", [])
        if mutations:
            genes = [
                f"{m.get('gene', '?')} {m.get('protein_change', '')}" for m in mutations
            ]
            therapies = []
            for m in mutations:
                therapies.extend(m.get("sensitive_therapies", []))
            unique_therapies = list(dict.fromkeys(therapies))[:5]
            return (
                f"Detected {len(mutations)} mutation(s): {', '.join(genes)}. "
                f"Sensitive to: {', '.join(unique_therapies)}."
            )
    elif record_type == "pathology":
        diagnosis = data.get("diagnosis", "")
        stage = data.get("stage", {})
        stage_str = stage.get("overall", "") if isinstance(stage, dict) else ""
        return f"{diagnosis}{f' — {stage_str}' if stage_str else ''}"
    elif record_type == "imaging":
        impression = data.get("impression", "")
        return impression[:200] if impression else "Imaging report uploaded"
    return "Medical record uploaded"


async def _extract_with_claude(file_bytes: bytes, prompt: str, is_pdf: bool) -> dict:
    """Extract structured data from file using Claude."""
    try:
        import anthropic
        import certifi
        import ssl

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {}

        client = anthropic.AsyncAnthropic(api_key=api_key)

        if is_pdf:
            b64 = base64.b64encode(file_bytes).decode("utf-8")
            content = [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": b64,
                    },
                },
                {"type": "text", "text": prompt},
            ]
            result = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                messages=[{"role": "user", "content": content}],
                extra_headers={"anthropic-beta": "pdfs-2024-09-25"},
            )
        else:
            # Compress if needed
            if len(file_bytes) > 4_500_000:
                try:
                    from PIL import Image
                    import io

                    img = Image.open(io.BytesIO(file_bytes))
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=70)
                    file_bytes = buf.getvalue()
                except Exception:
                    pass

            b64 = base64.b64encode(file_bytes).decode("utf-8")
            media_type = "image/jpeg"
            if file_bytes[:4] == b"\x89PNG":
                media_type = "image/png"
            elif file_bytes[:4] == b"RIFF":
                media_type = "image/webp"

            content = [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": b64},
                },
                {"type": "text", "text": prompt},
            ]
            result = await client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                messages=[{"role": "user", "content": content}],
            )

        raw = result.content[0].text.strip()

        # Parse JSON
        if "```json" in raw:
            raw = raw[raw.find("```json") + 7 :]
            if "```" in raw:
                raw = raw[: raw.find("```")]
        elif "```" in raw:
            raw = raw[raw.find("```") + 3 :]
            if "```" in raw:
                raw = raw[: raw.find("```")]

        return json.loads(raw.strip())

    except Exception as e:
        logger.error("Claude extraction failed: %s", e)
        return {}


async def _call_claude_text(prompt: str, max_tokens: int = 500) -> str:
    """Call Claude for plain text response."""
    try:
        import anthropic

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "Upload processed. Review the extracted data below."
        client = anthropic.AsyncAnthropic(api_key=api_key)
        result = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return result.content[0].text.strip()
    except Exception as e:
        logger.error("Claude text call failed: %s", e)
        return "Record saved. Review the details below."
