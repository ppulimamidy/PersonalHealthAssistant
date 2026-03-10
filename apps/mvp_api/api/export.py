"""
Data Export API — generates a full health history PDF and FHIR R4 bundle.
Uses ReportLab (already in requirements.txt).
"""

import io
import json
import uuid as _uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get

logger = get_logger(__name__)
router = APIRouter()


def _fmt_date(s: Optional[str]) -> str:
    if not s:
        return "—"
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%b %d, %Y")
    except Exception:
        return str(s)[:10]


def _build_pdf(
    user: dict,
    profile: dict,
    meds: list,
    supplements: list,
    lab_results: list,
    symptoms: list,
    insights: list,
    health_scores: list,
    adherence_stats: dict,
) -> bytes:
    """Build the full health history PDF and return bytes."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
            HRFlowable,
            PageBreak,
        )
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
    except ImportError:
        raise RuntimeError("reportlab is not installed")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    TEAL = colors.HexColor("#00D4AA")
    DARK = colors.HexColor("#1A2332")
    MUTED = colors.HexColor("#526380")

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=20,
        textColor=DARK,
        spaceAfter=4,
    )
    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=TEAL,
        spaceBefore=14,
        spaceAfter=4,
    )
    h3_style = ParagraphStyle(
        "H3",
        parent=styles["Heading3"],
        fontSize=11,
        textColor=DARK,
        spaceBefore=8,
        spaceAfter=2,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9,
        textColor=DARK,
        leading=13,
    )
    muted_style = ParagraphStyle(
        "Muted",
        parent=styles["Normal"],
        fontSize=8,
        textColor=MUTED,
        leading=11,
    )

    def hr():
        return HRFlowable(
            width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=6
        )

    def tbl(data, col_widths, bold_header=True):
        t = Table(data, colWidths=col_widths)
        style_cmds = [
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            (
                "ROWBACKGROUNDS",
                (0, 0),
                (-1, -1),
                [colors.white, colors.HexColor("#F8FAFC")],
            ),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
        if bold_header:
            style_cmds += [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        t.setStyle(TableStyle(style_cmds))
        return t

    story = []
    name = user.get("name", user.get("email", "Unknown"))
    generated_at = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

    # ── Cover / Header ────────────────────────────────────────────────────────
    story.append(Paragraph("Personal Health Export", title_style))
    story.append(Paragraph(f"Prepared for: <b>{name}</b>", body_style))
    story.append(Paragraph(f"Generated: {generated_at}", muted_style))
    story.append(Spacer(1, 10))
    story.append(hr())

    # ── Page 1: Profile & Active Treatments ──────────────────────────────────
    story.append(Paragraph("Profile & Active Treatments", h2_style))

    # Profile stats
    dob = profile.get("date_of_birth", "")
    age_str = ""
    if dob:
        try:
            dob_dt = datetime.strptime(dob, "%Y-%m-%d")
            age_str = f"{(datetime.now() - dob_dt).days // 365} yrs"
        except Exception:
            pass

    weight = profile.get("weight_kg")
    height = profile.get("height_cm")
    bmi_str = ""
    if weight and height:
        bmi = weight / ((height / 100) ** 2)
        bmi_str = f"{bmi:.1f}"

    profile_rows = [
        ["Field", "Value"],
        ["Name", name],
        ["Date of Birth", _fmt_date(dob) + (f" ({age_str})" if age_str else "")],
        [
            "Biological Sex",
            (profile.get("biological_sex") or "—").replace("_", " ").title(),
        ],
        ["Weight", f"{weight} kg" if weight else "—"],
        ["Height", f"{height} cm" if height else "—"],
        ["BMI", bmi_str or "—"],
    ]
    story.append(tbl(profile_rows, [2 * inch, 4 * inch]))
    story.append(Spacer(1, 10))

    # Active Medications
    active_meds = [m for m in meds if m.get("is_active", True)]
    if active_meds:
        story.append(Paragraph("Active Medications", h3_style))
        med_rows = [["Medication", "Dosage", "Frequency", "Since"]]
        for m in active_meds:
            med_rows.append(
                [
                    m.get("medication_name", "—"),
                    m.get("dosage", "—"),
                    m.get("frequency", "—"),
                    _fmt_date(m.get("start_date")),
                ]
            )
        story.append(tbl(med_rows, [2.2 * inch, 1.3 * inch, 1.5 * inch, 1.2 * inch]))
        story.append(Spacer(1, 6))

    # Active Supplements
    active_supps = [s for s in supplements if s.get("is_active", True)]
    if active_supps:
        story.append(Paragraph("Active Supplements", h3_style))
        supp_rows = [["Supplement", "Dosage", "Frequency"]]
        for s in active_supps:
            supp_rows.append(
                [
                    s.get("supplement_name", "—"),
                    s.get("dosage", "—"),
                    s.get("frequency", "—"),
                ]
            )
        story.append(tbl(supp_rows, [2.5 * inch, 1.5 * inch, 2.2 * inch]))
        story.append(Spacer(1, 6))

    # Adherence summary
    if adherence_stats.get("total_scheduled", 0) > 0:
        rate = adherence_stats.get("adherence_rate", 0)
        story.append(
            Paragraph(
                f"Medication Adherence (30 days): <b>{rate:.0f}%</b> "
                f"({adherence_stats.get('total_taken', 0)}/{adherence_stats.get('total_scheduled', 0)} doses)",
                body_style,
            )
        )
        story.append(Spacer(1, 6))

    story.append(PageBreak())

    # ── Page 2: Lab Results ───────────────────────────────────────────────────
    story.append(Paragraph("Lab Results (Last 12 Months)", h2_style))
    if not lab_results:
        story.append(Paragraph("No lab results recorded.", muted_style))
    else:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=365)).date().isoformat()
        recent_labs = [r for r in lab_results if (r.get("test_date") or "") >= cutoff]
        if not recent_labs:
            story.append(
                Paragraph("No lab results in the past 12 months.", muted_style)
            )
        else:
            for lab in recent_labs:
                story.append(
                    Paragraph(
                        f"{lab.get('test_type', 'Lab Test')} — {_fmt_date(lab.get('test_date'))}",
                        h3_style,
                    )
                )
                biomarkers = lab.get("biomarkers", [])
                if biomarkers:
                    b_rows = [["Biomarker", "Value", "Unit", "Status"]]
                    for b in biomarkers:
                        status = b.get("status", "normal")
                        b_rows.append(
                            [
                                b.get("biomarker_name", "—"),
                                str(b.get("value", "—")),
                                b.get("unit", "—"),
                                status.upper()
                                if status not in ("normal",)
                                else status.title(),
                            ]
                        )
                    story.append(
                        tbl(b_rows, [2.5 * inch, 1 * inch, 1 * inch, 1.2 * inch])
                    )
                story.append(Spacer(1, 8))

    story.append(PageBreak())

    # ── Page 3: Symptom Timeline ──────────────────────────────────────────────
    story.append(Paragraph("Symptom Timeline (Last 90 Days)", h2_style))
    if not symptoms:
        story.append(Paragraph("No symptoms logged.", muted_style))
    else:
        sym_rows = [["Date", "Type", "Severity", "Notes"]]
        for sym in symptoms[:25]:
            sym_rows.append(
                [
                    _fmt_date(sym.get("symptom_date")),
                    str(sym.get("symptom_type", "—")).title(),
                    f"{sym.get('severity', '—')}/10",
                    (sym.get("notes") or "")[:60],
                ]
            )
        story.append(tbl(sym_rows, [1.2 * inch, 1.3 * inch, 0.8 * inch, 2.9 * inch]))

    story.append(PageBreak())

    # ── Page 4: AI Insights ───────────────────────────────────────────────────
    story.append(Paragraph("Recent AI Insights", h2_style))
    if not insights:
        story.append(Paragraph("No AI insights generated yet.", muted_style))
    else:
        for ins in insights[:5]:
            story.append(Paragraph(ins.get("title", "Insight"), h3_style))
            story.append(Paragraph(ins.get("summary", ""), body_style))
            story.append(Paragraph(_fmt_date(ins.get("created_at")), muted_style))
            story.append(Spacer(1, 6))

    # ── Page 5: Health Scores ─────────────────────────────────────────────────
    if health_scores:
        story.append(PageBreak())
        story.append(Paragraph("Health Scores (7-Day Averages)", h2_style))
        score_rows = [["Date", "Sleep", "Activity", "Readiness", "Overall"]]
        for day in health_scores[-7:]:
            score_rows.append(
                [
                    _fmt_date(day.get("date")),
                    str(
                        day.get("sleep", {}).get("sleep_score", "—")
                        if isinstance(day.get("sleep"), dict)
                        else "—"
                    ),
                    str(
                        day.get("activity", {}).get("activity_score", "—")
                        if isinstance(day.get("activity"), dict)
                        else "—"
                    ),
                    str(
                        day.get("readiness", {}).get("readiness_score", "—")
                        if isinstance(day.get("readiness"), dict)
                        else "—"
                    ),
                    "—",
                ]
            )
        story.append(
            tbl(
                score_rows, [1.3 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch]
            )
        )

    doc.build(story)
    return buf.getvalue()


@router.get("/pdf")
async def export_health_pdf(
    current_user: dict = Depends(get_current_user),
):
    """
    Generate and download a full health history PDF.
    Includes profile, treatments, lab results, symptoms, AI insights, and health scores.
    """
    user_id = current_user["id"]

    # Collect all data in parallel-ish (sequential is fine for PDF generation)
    profile_rows = await _supabase_get(
        "profiles",
        f"id=eq.{user_id}&select=date_of_birth,biological_sex,weight_kg,height_cm&limit=1",
    )
    profile = (profile_rows or [{}])[0]

    meds = (
        await _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&select=*&order=created_at.desc",
        )
        or []
    )

    supplements = (
        await _supabase_get(
            "supplements",
            f"user_id=eq.{user_id}&select=*&order=created_at.desc",
        )
        or []
    )

    cutoff_90d = (datetime.now(timezone.utc) - timedelta(days=90)).date().isoformat()
    symptoms = (
        await _supabase_get(
            "symptom_journal",
            f"user_id=eq.{user_id}&symptom_date=gte.{cutoff_90d}&select=*&order=symptom_date.desc&limit=25",
        )
        or []
    )

    insights = (
        await _supabase_get(
            "ai_insights",
            f"user_id=eq.{user_id}&select=*&order=created_at.desc&limit=5",
        )
        or []
    )

    lab_results = (
        await _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&select=*&order=test_date.desc&limit=20",
        )
        or []
    )

    # Try to get health scores via timeline data if Oura connected
    health_scores: list = []
    try:
        from .timeline import get_timeline

        mock_user = {
            "id": user_id,
            "email": current_user.get("email", ""),
            "user_type": "system",
        }
        timeline = await get_timeline(days=7, current_user=mock_user)
        if timeline:
            health_scores = timeline
    except Exception:
        pass

    # Adherence stats (30 days)
    adherence_stats: dict = {}
    try:
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        adh_rows = (
            await _supabase_get(
                "medication_adherence_log",
                f"user_id=eq.{user_id}&scheduled_time=gte.{start_date}&select=was_taken&limit=500",
            )
            or []
        )
        if adh_rows:
            total = len(adh_rows)
            taken = sum(1 for r in adh_rows if r.get("was_taken"))
            adherence_stats = {
                "total_scheduled": total,
                "total_taken": taken,
                "adherence_rate": round(taken / total * 100, 1) if total > 0 else 0,
            }
    except Exception:
        pass

    try:
        pdf_bytes = _build_pdf(
            user=current_user,
            profile=profile,
            meds=meds,
            supplements=supplements,
            lab_results=lab_results,
            symptoms=symptoms,
            insights=insights,
            health_scores=health_scores,
            adherence_stats=adherence_stats,
        )
    except Exception as exc:
        logger.error(f"PDF generation failed for user {user_id}: {exc}")
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=health_export.pdf"},
    )


@router.get("/fhir")
async def export_fhir(
    current_user: dict = Depends(get_current_user),
):
    """
    Export health data as a FHIR R4 Bundle (application/fhir+json).
    Includes Condition, MedicationStatement, Observation (vitals/labs),
    and DiagnosticReport resources.
    """
    user_id = current_user["id"]
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    patient_ref = f"urn:uuid:{user_id}"

    entries: List[dict] = []

    # ── Patient resource ─────────────────────────────────────────────────────
    profile_rows = await _supabase_get(
        "profiles",
        f"id=eq.{user_id}&select=date_of_birth,biological_sex,weight_kg,height_cm&limit=1",
    )
    profile = (profile_rows or [{}])[0]

    gender_map = {
        "male": "male",
        "female": "female",
        "other": "other",
        "unknown": "unknown",
    }
    gender = gender_map.get(
        (profile.get("biological_sex") or "unknown").lower(), "unknown"
    )

    patient_resource: dict = {
        "resourceType": "Patient",
        "id": user_id,
        "gender": gender,
    }
    if profile.get("date_of_birth"):
        patient_resource["birthDate"] = profile["date_of_birth"][:10]

    entries.append(
        {
            "fullUrl": patient_ref,
            "resource": patient_resource,
            "request": {"method": "PUT", "url": f"Patient/{user_id}"},
        }
    )

    # ── Condition resources ───────────────────────────────────────────────────
    conditions = (
        await _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true&select=id,condition_name,severity,created_at",
        )
        or []
    )

    for cond in conditions:
        severity_map = {
            "mild": "255604002",
            "moderate": "6736007",
            "severe": "24484000",
        }
        sev_code = severity_map.get(
            (cond.get("severity") or "moderate").lower(), "6736007"
        )
        condition_res = {
            "resourceType": "Condition",
            "id": str(cond.get("id", _uuid.uuid4())),
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                    }
                ]
            },
            "subject": {"reference": patient_ref},
            "code": {"text": cond.get("condition_name", "Unknown condition")},
            "severity": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": sev_code,
                        "display": (cond.get("severity") or "moderate").capitalize(),
                    }
                ]
            },
            "recordedDate": (cond.get("created_at") or now_iso)[:10],
        }
        entries.append(
            {
                "fullUrl": f"urn:uuid:{cond.get('id')}",
                "resource": condition_res,
                "request": {"method": "PUT", "url": f"Condition/{cond.get('id')}"},
            }
        )

    # ── MedicationStatement resources ─────────────────────────────────────────
    meds = (
        await _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true&select=id,medication_name,dosage,frequency,start_date",
        )
        or []
    )

    for med in meds:
        med_id = str(med.get("id", _uuid.uuid4()))
        med_res = {
            "resourceType": "MedicationStatement",
            "id": med_id,
            "status": "active",
            "subject": {"reference": patient_ref},
            "medicationCodeableConcept": {
                "text": med.get("medication_name", "Unknown medication")
            },
            "dosage": [
                {
                    "text": " ".join(
                        filter(
                            None,
                            [
                                med.get("dosage"),
                                med.get("frequency"),
                            ],
                        )
                    )
                    or "as directed"
                }
            ],
        }
        if med.get("start_date"):
            med_res["effectivePeriod"] = {"start": med["start_date"][:10]}
        entries.append(
            {
                "fullUrl": f"urn:uuid:{med_id}",
                "resource": med_res,
                "request": {"method": "PUT", "url": f"MedicationStatement/{med_id}"},
            }
        )

    # ── Observation resources — weight + BMI from profile ────────────────────
    weight = profile.get("weight_kg")
    height = profile.get("height_cm")

    if weight:
        obs_id = str(_uuid.uuid4())
        entries.append(
            {
                "fullUrl": f"urn:uuid:{obs_id}",
                "resource": {
                    "resourceType": "Observation",
                    "id": obs_id,
                    "status": "final",
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "29463-7",
                                "display": "Body weight",
                            }
                        ]
                    },
                    "subject": {"reference": patient_ref},
                    "effectiveDateTime": now_iso,
                    "valueQuantity": {
                        "value": weight,
                        "unit": "kg",
                        "system": "http://unitsofmeasure.org",
                        "code": "kg",
                    },
                },
                "request": {"method": "POST", "url": "Observation"},
            }
        )

    if weight and height:
        bmi = round(weight / ((height / 100) ** 2), 1)
        obs_id = str(_uuid.uuid4())
        entries.append(
            {
                "fullUrl": f"urn:uuid:{obs_id}",
                "resource": {
                    "resourceType": "Observation",
                    "id": obs_id,
                    "status": "final",
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "39156-5",
                                "display": "Body mass index (BMI)",
                            }
                        ]
                    },
                    "subject": {"reference": patient_ref},
                    "effectiveDateTime": now_iso,
                    "valueQuantity": {
                        "value": bmi,
                        "unit": "kg/m2",
                        "system": "http://unitsofmeasure.org",
                        "code": "kg/m2",
                    },
                },
                "request": {"method": "POST", "url": "Observation"},
            }
        )

    # ── DiagnosticReport + Observation resources — lab results ────────────────
    cutoff_1yr = (datetime.now(timezone.utc) - timedelta(days=365)).date().isoformat()
    lab_results = (
        await _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&test_date=gte.{cutoff_1yr}&select=*&order=test_date.desc&limit=20",
        )
        or []
    )

    # LOINC codes for common biomarkers
    _LOINC: dict = {
        "glucose": "2345-7",
        "hemoglobin": "718-7",
        "hba1c": "4548-4",
        "cholesterol": "2093-3",
        "ldl": "13457-7",
        "hdl": "2085-9",
        "triglycerides": "2571-8",
        "creatinine": "2160-0",
        "egfr": "33914-3",
        "sodium": "2951-2",
        "potassium": "2823-3",
        "calcium": "17861-6",
        "alt": "1742-6",
        "ast": "1920-8",
        "tsh": "3016-3",
        "vitamin_d": "1989-3",
        "iron": "2498-4",
        "ferritin": "2276-4",
    }

    for lab in lab_results:
        lab_id = str(lab.get("id", _uuid.uuid4()))
        test_date = lab.get("test_date") or now_iso[:10]
        biomarkers = lab.get("biomarkers") or []
        obs_refs = []

        for b in biomarkers:
            b_name = (b.get("biomarker_name") or "").lower().replace(" ", "_")
            loinc = _LOINC.get(b_name)
            obs_id = str(_uuid.uuid4())
            obs_res: dict = {
                "resourceType": "Observation",
                "id": obs_id,
                "status": "final",
                "subject": {"reference": patient_ref},
                "effectiveDateTime": f"{test_date}T00:00:00Z",
                "valueQuantity": {
                    "value": b.get("value"),
                    "unit": b.get("unit", ""),
                },
                "code": {
                    "text": b.get("biomarker_name", "Biomarker"),
                },
            }
            if loinc:
                obs_res["code"]["coding"] = [
                    {
                        "system": "http://loinc.org",
                        "code": loinc,
                        "display": b.get("biomarker_name"),
                    }
                ]
            interp = b.get("status", "normal")
            if interp in ("abnormal", "critical"):
                obs_res["interpretation"] = [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                                "code": "A" if interp == "abnormal" else "LL",
                                "display": interp.capitalize(),
                            }
                        ]
                    }
                ]
            entries.append(
                {
                    "fullUrl": f"urn:uuid:{obs_id}",
                    "resource": obs_res,
                    "request": {"method": "POST", "url": "Observation"},
                }
            )
            obs_refs.append({"reference": f"urn:uuid:{obs_id}"})

        if obs_refs:
            diag_res = {
                "resourceType": "DiagnosticReport",
                "id": lab_id,
                "status": "final",
                "code": {"text": lab.get("test_type", "Lab Test")},
                "subject": {"reference": patient_ref},
                "effectiveDateTime": f"{test_date}T00:00:00Z",
                "result": obs_refs,
            }
            entries.append(
                {
                    "fullUrl": f"urn:uuid:{lab_id}",
                    "resource": diag_res,
                    "request": {"method": "POST", "url": f"DiagnosticReport/{lab_id}"},
                }
            )

    # ── Build FHIR R4 Bundle ──────────────────────────────────────────────────
    bundle = {
        "resourceType": "Bundle",
        "id": str(_uuid.uuid4()),
        "meta": {"lastUpdated": now_iso},
        "type": "collection",
        "timestamp": now_iso,
        "entry": entries,
    }

    return Response(
        content=json.dumps(bundle, indent=2),
        media_type="application/fhir+json",
        headers={"Content-Disposition": "attachment; filename=health_fhir.json"},
    )
