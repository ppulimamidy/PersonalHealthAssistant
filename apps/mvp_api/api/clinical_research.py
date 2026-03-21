"""
Clinical Research API — multi-source clinical intelligence engine.

Searches PubMed, synthesizes treatment options, generates drug profiles,
and references clinical practice guidelines personalized to user's conditions.
"""

import asyncio
import json
import os
from datetime import date
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..dependencies.usage_gate import _supabase_get

logger = get_logger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Condition → Guideline Mapping
# ---------------------------------------------------------------------------

CONDITION_GUIDELINES_MAP: Dict[str, List[Dict[str, str]]] = {
    "type_2_diabetes": [
        {
            "authority": "ADA",
            "name": "ADA Standards of Care 2026",
            "focus": "A1C targets, medication algorithms",
        },
        {
            "authority": "AACE",
            "name": "AACE Comprehensive Diabetes Algorithm",
            "focus": "Treatment intensification",
        },
    ],
    "pcos": [
        {
            "authority": "Endocrine Society",
            "name": "PCOS Clinical Practice Guideline",
            "focus": "Diagnosis, treatment, metabolic management",
        },
        {
            "authority": "ADA",
            "name": "ADA Standards (insulin resistance)",
            "focus": "Metformin, GLP-1 agonists",
        },
    ],
    "hypertension": [
        {
            "authority": "ACC/AHA",
            "name": "ACC/AHA Blood Pressure Guidelines",
            "focus": "BP targets, medication classes",
        },
    ],
    "high_cholesterol": [
        {
            "authority": "ACC/AHA",
            "name": "ACC/AHA Cholesterol Management Guidelines",
            "focus": "Statin therapy, ASCVD risk",
        },
    ],
    "hypothyroidism": [
        {
            "authority": "ATA",
            "name": "ATA Thyroid Guidelines",
            "focus": "TSH targets, levothyroxine dosing",
        },
    ],
    "heart_failure": [
        {
            "authority": "ACC/AHA",
            "name": "ACC/AHA Heart Failure Guidelines",
            "focus": "GDMT, device therapy",
        },
    ],
    "breast_cancer": [
        {
            "authority": "NCCN",
            "name": "NCCN Breast Cancer Guidelines",
            "focus": "Staging, treatment algorithms, biomarker-guided therapy",
        },
        {
            "authority": "ASCO",
            "name": "ASCO Clinical Practice Guidelines",
            "focus": "Adjuvant therapy, survivorship",
        },
    ],
    "lung_cancer": [
        {
            "authority": "NCCN",
            "name": "NCCN Lung Cancer Guidelines",
            "focus": "NSCLC/SCLC treatment, immunotherapy",
        },
    ],
    "depression": [
        {
            "authority": "APA",
            "name": "APA Practice Guidelines for Depression",
            "focus": "Medication algorithms, psychotherapy",
        },
    ],
    "rheumatoid_arthritis": [
        {
            "authority": "ACR",
            "name": "ACR Guideline for RA",
            "focus": "DMARD therapy, biologic selection",
        },
        {
            "authority": "EULAR",
            "name": "EULAR RA Management Recommendations",
            "focus": "Treat-to-target strategy",
        },
    ],
    "asthma": [
        {
            "authority": "GINA",
            "name": "GINA Asthma Strategy",
            "focus": "Step therapy, controller medications",
        },
    ],
    "copd": [
        {
            "authority": "GOLD",
            "name": "GOLD COPD Guidelines",
            "focus": "Staging, inhaler selection",
        },
    ],
    "ibd": [
        {
            "authority": "AGA",
            "name": "AGA IBD Management Guidelines",
            "focus": "Treatment ladders for UC and Crohn's",
        },
    ],
    "migraine": [
        {
            "authority": "AAN",
            "name": "AAN Migraine Prevention Guidelines",
            "focus": "Preventive medication selection",
        },
    ],
    "ckd": [
        {
            "authority": "KDIGO",
            "name": "KDIGO CKD Guidelines",
            "focus": "Staging by eGFR, BP targets",
        },
    ],
    "osteoporosis": [
        {
            "authority": "Endocrine Society",
            "name": "Endocrine Society Osteoporosis Guidelines",
            "focus": "Bisphosphonates, denosumab, DEXA intervals",
        },
        {
            "authority": "USPSTF",
            "name": "USPSTF Osteoporosis Screening",
            "focus": "Screening age/sex criteria",
        },
    ],
}

TREATMENT_LADDERS: Dict[str, List[Dict[str, str]]] = {
    "type_2_diabetes": [
        {"step": "1st line", "treatment": "Metformin", "guideline": "ADA 2026"},
        {
            "step": "2nd line (with CV risk)",
            "treatment": "GLP-1 agonist (semaglutide) or SGLT2 inhibitor",
            "guideline": "ADA 2026",
        },
        {
            "step": "2nd line (without CV risk)",
            "treatment": "GLP-1, SGLT2, DPP-4, or TZD",
            "guideline": "ADA 2026",
        },
        {
            "step": "3rd line",
            "treatment": "Add basal insulin or combination",
            "guideline": "ADA 2026",
        },
    ],
    "rheumatoid_arthritis": [
        {"step": "1st line", "treatment": "Methotrexate", "guideline": "ACR 2023"},
        {
            "step": "2nd line",
            "treatment": "Add biologic (TNF or IL-6 inhibitor)",
            "guideline": "ACR 2023",
        },
        {
            "step": "3rd line",
            "treatment": "Switch biologic class or JAK inhibitor",
            "guideline": "ACR 2023",
        },
    ],
    "depression": [
        {
            "step": "1st line",
            "treatment": "SSRI (sertraline, escitalopram)",
            "guideline": "APA",
        },
        {
            "step": "2nd line",
            "treatment": "Switch SSRI or try SNRI (venlafaxine, duloxetine)",
            "guideline": "APA",
        },
        {
            "step": "3rd line",
            "treatment": "Augment with atypical antipsychotic or lithium",
            "guideline": "APA",
        },
    ],
    "asthma": [
        {"step": "Step 1", "treatment": "SABA as needed", "guideline": "GINA 2026"},
        {"step": "Step 2", "treatment": "Low-dose ICS", "guideline": "GINA 2026"},
        {"step": "Step 3", "treatment": "Low-dose ICS/LABA", "guideline": "GINA 2026"},
        {
            "step": "Step 4",
            "treatment": "Medium/high-dose ICS/LABA",
            "guideline": "GINA 2026",
        },
        {
            "step": "Step 5",
            "treatment": "Add biologic (omalizumab, dupilumab)",
            "guideline": "GINA 2026",
        },
    ],
    "hypertension": [
        {
            "step": "1st line",
            "treatment": "ACE inhibitor/ARB or CCB or thiazide",
            "guideline": "ACC/AHA",
        },
        {
            "step": "2nd line",
            "treatment": "Combination of two 1st-line classes",
            "guideline": "ACC/AHA",
        },
        {
            "step": "Resistant",
            "treatment": "Add spironolactone",
            "guideline": "ACC/AHA",
        },
    ],
}

# USPSTF Screening Recommendations
USPSTF_SCREENINGS: List[Dict[str, Any]] = [
    {
        "name": "Colorectal Cancer",
        "age_min": 45,
        "age_max": 75,
        "sex": "all",
        "grade": "A",
        "interval": "varies by method",
    },
    {
        "name": "Breast Cancer (Mammography)",
        "age_min": 40,
        "age_max": 74,
        "sex": "female",
        "grade": "B",
        "interval": "every 2 years",
    },
    {
        "name": "Cervical Cancer",
        "age_min": 21,
        "age_max": 65,
        "sex": "female",
        "grade": "A",
        "interval": "every 3-5 years",
    },
    {
        "name": "Lung Cancer (CT)",
        "age_min": 50,
        "age_max": 80,
        "sex": "all",
        "grade": "B",
        "interval": "annually",
        "note": "20+ pack-year smoking history",
    },
    {
        "name": "Diabetes (A1C/Glucose)",
        "age_min": 35,
        "age_max": 70,
        "sex": "all",
        "grade": "B",
        "interval": "every 3 years",
        "note": "overweight/obese adults",
    },
    {
        "name": "Hepatitis C",
        "age_min": 18,
        "age_max": 79,
        "sex": "all",
        "grade": "B",
        "interval": "one-time",
    },
    {
        "name": "HIV",
        "age_min": 15,
        "age_max": 65,
        "sex": "all",
        "grade": "A",
        "interval": "at least once",
    },
    {
        "name": "Depression",
        "age_min": 12,
        "age_max": 999,
        "sex": "all",
        "grade": "B",
        "interval": "periodic",
    },
    {
        "name": "Osteoporosis (DEXA)",
        "age_min": 65,
        "sex": "female",
        "grade": "B",
        "interval": "varies",
    },
    {
        "name": "Abdominal Aortic Aneurysm",
        "age_min": 65,
        "age_max": 75,
        "sex": "male",
        "grade": "B",
        "interval": "one-time",
        "note": "ever-smokers",
    },
    {
        "name": "Statin for CVD Prevention",
        "age_min": 40,
        "age_max": 75,
        "sex": "all",
        "grade": "B",
        "interval": "ongoing",
        "note": "ASCVD risk ≥10%",
    },
]


# ---------------------------------------------------------------------------
# Context Gathering
# ---------------------------------------------------------------------------


async def _gather_research_context(user_id: str) -> Dict[str, Any]:
    """Gather user context for personalized research."""
    (
        conditions,
        medications,
        supplements,
        labs,
        profile_rows,
        genomic_records,
    ) = await asyncio.gather(
        _supabase_get(
            "health_conditions",
            f"user_id=eq.{user_id}&is_active=eq.true&select=condition_name",
        ),
        _supabase_get(
            "medications",
            f"user_id=eq.{user_id}&is_active=eq.true&select=medication_name,dosage,start_date,indication",
        ),
        _supabase_get(
            "supplements",
            f"user_id=eq.{user_id}&is_active=eq.true&select=supplement_name,dosage",
        ),
        _supabase_get(
            "lab_results",
            f"user_id=eq.{user_id}&order=test_date.desc&limit=3&select=test_type,test_date,biomarkers",
        ),
        _supabase_get(
            "profiles", f"id=eq.{user_id}&select=full_name,date_of_birth,biological_sex"
        ),
        _supabase_get(
            "medical_records",
            f"user_id=eq.{user_id}&record_type=eq.genomic&order=created_at.desc&limit=3&select=extracted_data,report_date",
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

    # Parse lab biomarkers
    abnormal_labs: List[str] = []
    for lab in labs:
        bms = lab.get("biomarkers") or []
        if isinstance(bms, str):
            try:
                bms = json.loads(bms)
            except Exception:
                bms = []
        for bm in bms:
            if isinstance(bm, dict) and bm.get("status") in (
                "abnormal",
                "critical",
                "borderline",
            ):
                abnormal_labs.append(
                    f"{bm.get('name', '?')}: {bm.get('value', '?')} {bm.get('unit', '')} ({bm.get('status')})"
                )

    # Map conditions to guidelines
    condition_names = [c.get("condition_name", "") for c in conditions]
    relevant_guidelines: List[Dict[str, str]] = []
    relevant_ladders: List[Dict[str, Any]] = []
    for cond in condition_names:
        norm = cond.lower().replace(" ", "_").replace("'", "")
        for key, guides in CONDITION_GUIDELINES_MAP.items():
            if key in norm or norm in key:
                relevant_guidelines.extend(guides)
        if norm in TREATMENT_LADDERS:
            relevant_ladders.append(
                {"condition": cond, "ladder": TREATMENT_LADDERS[norm]}
            )

    return {
        "first_name": first_name,
        "age": age,
        "sex": profile.get("biological_sex"),
        "conditions": condition_names,
        "medications": [
            {
                "name": m.get("medication_name", ""),
                "dosage": m.get("dosage", ""),
                "indication": m.get("indication", ""),
            }
            for m in medications
        ],
        "supplements": [s.get("supplement_name", "") for s in supplements],
        "abnormal_labs": abnormal_labs[:5],
        "guidelines": relevant_guidelines,
        "treatment_ladders": relevant_ladders,
        "genomic_mutations": _extract_mutations(genomic_records),
    }


def _extract_mutations(genomic_records: list) -> List[Dict[str, Any]]:
    """Extract mutations from genomic medical records."""
    mutations: List[Dict[str, Any]] = []
    for rec in genomic_records:
        ed = rec.get("extracted_data") or {}
        if isinstance(ed, str):
            try:
                ed = json.loads(ed)
            except Exception:
                continue
        for m in ed.get("mutations", []):
            if isinstance(m, dict):
                mutations.append(
                    {
                        "gene": m.get("gene", ""),
                        "variant": m.get("protein_change") or m.get("variant", ""),
                        "tier": m.get("classification", {}).get("tier", "")
                        if isinstance(m.get("classification"), dict)
                        else "",
                        "sensitivity": m.get("sensitivity", ""),
                        "therapies": m.get("sensitive_therapies", []),
                    }
                )
    return mutations


def _format_context(ctx: Dict[str, Any]) -> str:
    """Format research context for AI prompt."""
    parts = []
    if ctx.get("first_name"):
        parts.append(
            f"Patient: {ctx['first_name']}, {ctx.get('age', '?')}yo {ctx.get('sex', '?')}"
        )
    if ctx.get("conditions"):
        parts.append(f"Conditions: {', '.join(ctx['conditions'])}")
    if ctx.get("medications"):
        meds = [f"{m['name']} {m['dosage']}" for m in ctx["medications"]]
        parts.append(f"Current medications: {', '.join(meds)}")
    if ctx.get("supplements"):
        parts.append(f"Supplements: {', '.join(ctx['supplements'])}")
    if ctx.get("abnormal_labs"):
        parts.append(f"Abnormal labs: {', '.join(ctx['abnormal_labs'][:3])}")
    if ctx.get("guidelines"):
        guide_names = list({g["name"] for g in ctx["guidelines"]})
        parts.append(f"Relevant guidelines: {', '.join(guide_names)}")
    if ctx.get("treatment_ladders"):
        for ladder in ctx["treatment_ladders"]:
            steps = " → ".join(
                f"{s['step']}: {s['treatment']}" for s in ladder["ladder"]
            )
            parts.append(f"Treatment ladder ({ladder['condition']}): {steps}")
    if ctx.get("genomic_mutations"):
        mut_strs = []
        for m in ctx["genomic_mutations"]:
            therapies = ", ".join(m.get("therapies", [])[:3])
            mut_strs.append(
                f"{m.get('gene', '?')} {m.get('variant', '')}"
                f" [{m.get('tier', '')}] — {m.get('sensitivity', '')}"
                f"{f' → {therapies}' if therapies else ''}"
            )
        parts.append(f"MOLECULAR PROFILE:\n" + "\n".join(f"  • {s}" for s in mut_strs))
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


class ClinicalSearchRequest(BaseModel):
    query: str
    search_type: str = "all"  # all, treatments, drugs, trials


@router.post("/clinical-search")
async def clinical_search(
    body: ClinicalSearchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Multi-source clinical search with AI synthesis."""
    user_id = current_user["id"]
    ctx = await _gather_research_context(user_id)
    context_text = _format_context(ctx)
    first_name = ctx.get("first_name") or "there"

    # PubMed search (existing endpoint internally)
    articles = []
    try:
        from .medical_literature import _pubmed_search, _pubmed_fetch_articles

        pmids = await _pubmed_search(body.query, max_results=10)
        if pmids:
            article_data = await _pubmed_fetch_articles(pmids[:10])
            articles = [
                {
                    "title": a.get("title", ""),
                    "journal": a.get("journal", ""),
                    "publication_date": a.get("publication_date", ""),
                    "evidence_level": a.get("evidence_level", "other"),
                    "pubmed_id": a.get("pubmed_id", ""),
                    "authors": a.get("authors", [])[:3],
                }
                for a in article_data
            ]
    except Exception as e:
        logger.warning("PubMed search failed: %s", e)

    # Phase 1: Fast AI synthesis (plain text, no JSON — renders immediately)
    synthesis_prompt = f"""You are a clinical research analyst for {first_name}.

QUERY: {body.query}

PATIENT CONTEXT:
{context_text}

Write a 3-5 sentence evidence-based synthesis addressing this query, personalized to this patient.
Reference specific clinical practice guidelines (ADA, ACC/AHA, NCCN, etc.) with year.
Mention relevant drug interactions with the patient's current medications.
Be specific with efficacy numbers. Return ONLY the synthesis text, no JSON."""

    ai_synthesis = await _call_claude(synthesis_prompt, max_tokens=600)

    return {
        "ai_synthesis": ai_synthesis,
        "treatment_report": None,
        "drugs_mentioned": [],
        "articles": [
            {
                "title": a.get("title", ""),
                "journal": a.get("journal", ""),
                "publication_date": a.get("publication_date", ""),
                "evidence_level": a.get("evidence_level", "other"),
                "pubmed_id": a.get("pubmed_id", ""),
            }
            for a in articles[:10]
        ]
        if articles
        else [],
    }


@router.post("/clinical-search/details")
async def clinical_search_details(
    body: ClinicalSearchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Phase 2: Structured treatment options, drug profiles, and doctor questions."""
    user_id = current_user["id"]
    ctx = await _gather_research_context(user_id)
    context_text = _format_context(ctx)
    first_name = ctx.get("first_name") or "there"

    prompt = f"""You are a clinical research analyst for {first_name}.

QUERY: {body.query}

PATIENT CONTEXT:
{context_text}

Return ONLY valid JSON (no markdown fences, no extra text):
{{
  "treatment_report": {{
    "condition": "condition",
    "guidelines_referenced": ["guideline1"],
    "treatment_options": [
      {{"name": "Treatment", "type": "medication", "evidence_level": "strong", "efficacy": "data", "guideline_position": "First-line per X", "side_effects": "effects", "compatibility": "status", "notes": "personalized note"}}
    ],
    "doctor_questions": ["question1", "question2", "question3"]
  }},
  "drugs_mentioned": [
    {{"name": "Drug", "drug_class": "class", "mechanism": "how it works", "approved_indications": ["indication"], "efficacy_summary": "data", "side_effects": {{"common": ["effect"], "serious": ["effect"]}}, "interactions_with_user_meds": [], "cost_range": "range", "guideline_position": "position"}}
  ]
}}

Rules: max 3 treatment options, 2 drugs, 3 doctor questions. Be concise. Reference guidelines."""

    raw = await _call_claude(prompt, max_tokens=2000)

    parsed = _parse_json_robust(raw)
    if not parsed:
        parsed = {"treatment_report": None, "drugs_mentioned": []}

    return {
        "treatment_report": parsed.get("treatment_report"),
        "drugs_mentioned": parsed.get("drugs_mentioned", []),
    }


def _parse_json_robust(raw: str) -> Optional[Dict[str, Any]]:
    """Robust JSON extraction from Claude response."""
    try:
        clean = raw
        if "```json" in clean:
            clean = clean[clean.find("```json") + 7 :]
            if "```" in clean:
                clean = clean[: clean.find("```")]
        elif "```" in clean:
            clean = clean[clean.find("```") + 3 :]
            if "```" in clean:
                clean = clean[: clean.find("```")]
        clean = clean.strip()

        if clean.startswith("{"):
            depth = 0
            end_idx = -1
            for i, ch in enumerate(clean):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end_idx = i
                        break
            if end_idx > 0:
                return json.loads(clean[: end_idx + 1])
            return json.loads(clean)
        return json.loads(clean)
    except (json.JSONDecodeError, ValueError):
        logger.warning("JSON parse failed: %s", raw[:100])
        return None


@router.get("/drug-profile/{drug_name}")
async def drug_profile(
    drug_name: str,
    current_user: dict = Depends(get_current_user),
):
    """Comprehensive drug intelligence personalized to user."""
    user_id = current_user["id"]
    ctx = await _gather_research_context(user_id)
    context_text = _format_context(ctx)
    first_name = ctx.get("first_name") or "there"

    prompt = f"""Generate a comprehensive drug profile for "{drug_name}" personalized for {first_name}.

PATIENT CONTEXT:
{context_text}

Return ONLY valid JSON:
{{
  "name": "{drug_name}",
  "generic_name": "generic name",
  "brand_names": ["brand1"],
  "drug_class": "class",
  "mechanism": "Plain language mechanism of action (2 sentences max)",
  "approved_indications": ["indication1"],
  "off_label_uses": ["off-label use with evidence level"],
  "efficacy_summary": "Key efficacy data from meta-analyses",
  "dosing": "Typical dosing range",
  "side_effects": {{"common": ["list"], "uncommon": ["list"], "serious": ["list"]}},
  "interactions_with_user_meds": ["specific interactions with patient's current medications"],
  "nutrient_depletions": ["nutrients this drug depletes"],
  "cost_range": "Generic vs brand cost estimate",
  "guideline_position": "Where this drug sits in treatment guidelines",
  "monitoring_required": "Labs or monitoring needed",
  "patient_specific_notes": "Personalized notes for this patient based on their conditions and labs"
}}"""

    raw = await _call_claude(prompt, max_tokens=1500)
    try:
        if "```" in raw:
            raw = raw[raw.find("{") : raw.rfind("}") + 1]
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {"name": drug_name, "error": "Unable to generate drug profile"}


@router.post("/drug-compare")
async def drug_compare(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """Head-to-head drug comparison."""
    user_id = current_user["id"]
    ctx = await _gather_research_context(user_id)
    drugs = body.get("drugs", [])
    if len(drugs) < 2:
        return {"error": "Provide at least 2 drugs to compare"}

    prompt = f"""Compare these drugs head-to-head: {', '.join(drugs)}

PATIENT CONTEXT:
{_format_context(ctx)}

Return ONLY valid JSON:
{{
  "comparison": {{
    "metrics": ["efficacy", "side_effects", "cost", "evidence_quality", "guideline_position"],
    "drugs": [
      {{
        "name": "drug name",
        "efficacy": "specific data",
        "side_effects": "profile summary",
        "cost": "monthly estimate",
        "evidence_quality": "strong/moderate/limited",
        "guideline_position": "per [authority]",
        "compatibility": "with patient's current meds"
      }}
    ]
  }},
  "recommendation": "Personalized recommendation based on patient profile",
  "guideline_preferred": "Which drug guidelines prefer and why"
}}"""

    raw = await _call_claude(prompt, max_tokens=1500)
    try:
        if "```" in raw:
            raw = raw[raw.find("{") : raw.rfind("}") + 1]
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {"error": "Unable to generate comparison"}


@router.get("/guidelines/{condition}")
async def get_guidelines(
    condition: str,
    current_user: dict = Depends(get_current_user),
):
    """Get relevant clinical practice guidelines for a condition."""
    norm = condition.lower().replace(" ", "_")

    guidelines: List[Dict[str, str]] = []
    ladder: List[Dict[str, str]] = []

    for key, guides in CONDITION_GUIDELINES_MAP.items():
        if key in norm or norm in key:
            guidelines.extend(guides)

    if norm in TREATMENT_LADDERS:
        ladder = TREATMENT_LADDERS[norm]

    return {
        "condition": condition,
        "guidelines": guidelines,
        "treatment_ladder": ladder,
    }


@router.get("/screening-schedule")
async def screening_schedule(
    current_user: dict = Depends(get_current_user),
):
    """USPSTF-based preventive screening recommendations."""
    user_id = current_user["id"]
    ctx = await _gather_research_context(user_id)
    age = ctx.get("age") or 30
    sex = ctx.get("sex") or "all"

    applicable: List[Dict[str, Any]] = []
    for s in USPSTF_SCREENINGS:
        if age < s.get("age_min", 0):
            continue
        if s.get("age_max") and age > s["age_max"]:
            continue
        if s.get("sex", "all") != "all" and s["sex"] != sex:
            continue
        applicable.append(
            {
                "name": s["name"],
                "grade": s["grade"],
                "interval": s["interval"],
                "note": s.get("note"),
            }
        )

    return {
        "profile": f"{age}yo {sex}",
        "screenings": applicable,
    }


# ---------------------------------------------------------------------------
# Session 5: ClinicalTrials.gov Integration
# ---------------------------------------------------------------------------

CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"


@router.get("/trials")
async def search_trials(
    condition: str = Query(..., min_length=2),
    status: str = Query(default="RECRUITING"),
    phase: str = Query(default="PHASE2,PHASE3"),
    max_results: int = Query(default=10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """Search ClinicalTrials.gov for relevant trials."""
    import certifi
    import ssl

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())

    params: Dict[str, str] = {
        "query.cond": condition,
        "pageSize": str(max_results),
        "format": "json",
    }
    if status:
        params["filter.overallStatus"] = status
    if phase:
        params["filter.phase"] = phase

    trials: List[Dict[str, Any]] = []
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        async with aiohttp.ClientSession(
            timeout=timeout, connector=connector
        ) as session:
            async with session.get(CLINICALTRIALS_API, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    studies = data.get("studies", [])
                    for study in studies:
                        proto = study.get("protocolSection", {})
                        ident = proto.get("identificationModule", {})
                        status_mod = proto.get("statusModule", {})
                        design = proto.get("designModule", {})
                        desc = proto.get("descriptionModule", {})
                        sponsor = proto.get("sponsorCollaboratorsModule", {})
                        eligibility = proto.get("eligibilityModule", {})
                        locations = proto.get("contactsLocationsModule", {}).get(
                            "locations", []
                        )

                        loc_strs: List[str] = []
                        for loc in locations[:3]:
                            city = loc.get("city", "")
                            state = loc.get("state", "")
                            country = loc.get("country", "")
                            loc_strs.append(f"{city}, {state} {country}".strip(", "))

                        trials.append(
                            {
                                "nct_id": ident.get("nctId", ""),
                                "title": ident.get("briefTitle", ""),
                                "phase": ",".join(design.get("phases", [])),
                                "status": status_mod.get("overallStatus", ""),
                                "summary": desc.get("briefSummary", "")[:300],
                                "sponsor": sponsor.get("leadSponsor", {}).get(
                                    "name", ""
                                ),
                                "enrollment": design.get("enrollmentInfo", {}).get(
                                    "count"
                                ),
                                "locations": loc_strs,
                                "eligibility_criteria": (
                                    eligibility.get("eligibilityCriteria") or ""
                                )[:500],
                                "start_date": status_mod.get("startDateStruct", {}).get(
                                    "date"
                                ),
                                "completion_date": status_mod.get(
                                    "completionDateStruct", {}
                                ).get("date"),
                            }
                        )
                else:
                    logger.warning("ClinicalTrials.gov returned %d", resp.status)
    except Exception as e:
        logger.warning("ClinicalTrials.gov search failed: %s", e)

    return {"condition": condition, "trials": trials, "total": len(trials)}


@router.post("/trials/{nct_id}/eligibility")
async def check_trial_eligibility(
    nct_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Check if user likely qualifies for a clinical trial."""
    user_id = current_user["id"]
    ctx = await _gather_research_context(user_id)

    # Fetch trial details
    trial_data = await search_trials(
        condition="", status="", phase="", max_results=1, current_user=current_user
    )
    # Find by NCT ID from cached or re-fetch
    # For now, use AI to assess eligibility based on user profile
    prompt = f"""A patient wants to know if they might qualify for clinical trial {nct_id}.

PATIENT PROFILE:
{_format_context(ctx)}

Based on typical eligibility criteria for clinical trials and this patient's profile,
assess eligibility. Return ONLY valid JSON:
{{
  "likely_eligible": true/false,
  "confidence": "high/medium/low",
  "matching_criteria": ["criterion that the patient likely meets"],
  "potential_exclusions": ["criterion that might exclude the patient"],
  "recommendation": "One sentence recommendation"
}}"""

    raw = await _call_claude(prompt, max_tokens=500)
    try:
        if "```" in raw:
            raw = raw[raw.find("{") : raw.rfind("}") + 1]
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {"likely_eligible": None, "recommendation": "Discuss with your doctor."}


# ---------------------------------------------------------------------------
# Session 6: Saved Reports + Cancer Enhancement
# ---------------------------------------------------------------------------


@router.post("/reports/save")
async def save_report(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """Save a clinical research report for later reference."""
    from ..dependencies.usage_gate import _supabase_upsert
    import uuid

    user_id = current_user["id"]
    report_id = str(uuid.uuid4())

    await _supabase_upsert(
        "saved_research_reports",
        {
            "id": report_id,
            "user_id": user_id,
            "query": body.get("query", ""),
            "report_data": json.dumps(body.get("report_data", {})),
            "created_at": date.today().isoformat(),
        },
    )

    return {"id": report_id, "saved": True}


@router.get("/reports")
async def list_reports(
    current_user: dict = Depends(get_current_user),
):
    """List saved research reports."""
    user_id = current_user["id"]
    rows = await _supabase_get(
        "saved_research_reports",
        f"user_id=eq.{user_id}&order=created_at.desc&limit=20"
        f"&select=id,query,created_at",
    )
    return {"reports": rows}


@router.post("/cancer-pathways")
async def cancer_pathways(
    body: dict,
    current_user: dict = Depends(get_current_user),
):
    """
    Cancer-specific treatment intelligence.
    Includes staging, biomarker-guided therapy, immunotherapy, supportive care.
    """
    user_id = current_user["id"]
    ctx = await _gather_research_context(user_id)
    context_text = _format_context(ctx)
    first_name = ctx.get("first_name") or "there"

    cancer_type = body.get("cancer_type", "cancer")
    stage = body.get("stage", "")
    biomarkers = body.get("biomarkers", [])

    biomarker_text = f"\nBiomarkers: {', '.join(biomarkers)}" if biomarkers else ""
    stage_text = f"\nStage: {stage}" if stage else ""

    prompt = f"""You are a clinical oncology research analyst for {first_name}.

CANCER TYPE: {cancer_type}{stage_text}{biomarker_text}

PATIENT CONTEXT:
{context_text}

Generate a comprehensive cancer treatment pathway. Return ONLY valid JSON:
{{
  "cancer_type": "{cancer_type}",
  "stage": "{stage or 'unspecified'}",
  "guidelines_referenced": ["NCCN 2026", "ASCO"],
  "standard_of_care": {{
    "primary_treatment": "Surgery/chemo/radiation recommendation",
    "adjuvant_therapy": "Post-primary treatment if applicable",
    "maintenance": "Long-term management"
  }},
  "treatment_options": [
    {{
      "name": "Treatment name",
      "type": "surgery|chemotherapy|immunotherapy|targeted_therapy|radiation|hormone_therapy",
      "evidence_level": "strong|moderate",
      "efficacy": "Survival/response rates",
      "guideline_position": "Per NCCN/ASCO",
      "biomarker_requirement": "Required biomarker status or null",
      "side_effects": "Key side effects"
    }}
  ],
  "immunotherapy_options": [
    {{
      "name": "Drug name",
      "target": "PD-1/PD-L1/CTLA-4/etc",
      "approved_for": "Specific indication",
      "biomarker_required": "PD-L1 ≥50%, MSI-H, etc.",
      "efficacy": "Response rate / survival data"
    }}
  ],
  "clinical_trials": "Recommend searching ClinicalTrials.gov for [specific trial types]",
  "supportive_care": [
    "Pain management recommendations",
    "Nutrition guidance for cancer patients",
    "Mental health support resources"
  ],
  "biomarker_tests_to_request": [
    "Specific biomarker tests that could guide therapy selection"
  ],
  "doctor_questions": [
    "Stage-specific questions for oncologist"
  ],
  "financial_resources": [
    "Patient assistance programs",
    "Foundation support"
  ],
  "disclaimer": "This is not medical advice. Cancer treatment decisions should be made with your oncology team."
}}

Rules:
- Reference NCCN and ASCO guidelines specifically
- Include biomarker-guided therapy options (HER2, BRCA, PD-L1, MSI, etc.)
- Include immunotherapy landscape for this cancer type
- Mention clinical trial options
- Include supportive care recommendations
- Be sensitive with survival statistics — present with context
- Generate specific oncologist questions"""

    raw = await _call_claude(prompt, max_tokens=3000)
    try:
        if "```" in raw:
            raw = raw[raw.find("{") : raw.rfind("}") + 1]
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {
            "cancer_type": cancer_type,
            "error": "Unable to generate cancer pathway",
            "recommendation": "Please consult with your oncology team for personalized treatment planning.",
        }


# ---------------------------------------------------------------------------
# Claude helper
# ---------------------------------------------------------------------------


async def _call_claude(prompt: str, max_tokens: int = 2000) -> str:
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
        logger.error("Claude call failed for clinical research: %s", e)
        return "{}"
