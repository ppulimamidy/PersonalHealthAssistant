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
    (conditions, medications, supplements, labs, profile_rows,) = await asyncio.gather(
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
    }


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
        from .medical_literature import _search_pubmed

        articles = await _search_pubmed(body.query, max_results=10)
    except Exception as e:
        logger.warning("PubMed search failed: %s", e)

    # AI synthesis with treatment report
    prompt = f"""You are a clinical research analyst for {first_name}.

QUERY: {body.query}

PATIENT CONTEXT:
{context_text}

Generate a comprehensive clinical research response. Return ONLY valid JSON (no markdown):
{{
  "ai_synthesis": "3-5 sentence synthesis of the latest evidence addressing the query, personalized to this patient. Reference specific guidelines when applicable.",
  "treatment_report": {{
    "condition": "the condition being researched",
    "guidelines_referenced": ["ADA 2026", "ACC/AHA 2023"],
    "treatment_options": [
      {{
        "name": "Treatment name",
        "type": "medication|procedure|lifestyle|supplement",
        "evidence_level": "strong|moderate|limited",
        "efficacy": "Specific efficacy data (e.g., A1C reduction 0.5-1.0%)",
        "guideline_position": "First-line per ADA 2026",
        "side_effects": "Common side effects",
        "compatibility": "Compatible with current meds / Interaction concern",
        "notes": "Personalized note for this patient"
      }}
    ],
    "doctor_questions": [
      "Specific, guideline-informed question for the doctor"
    ],
    "disclaimer": "This is not medical advice. Discuss all findings with your healthcare provider."
  }},
  "drugs_mentioned": [
    {{
      "name": "Drug name",
      "drug_class": "Class",
      "mechanism": "Plain language mechanism",
      "approved_indications": ["indication1"],
      "efficacy_summary": "Key efficacy data",
      "side_effects": {{"common": ["nausea", "headache"], "serious": ["pancreatitis"]}},
      "interactions_with_user_meds": ["interaction with X"],
      "cost_range": "$10-50/month generic",
      "guideline_position": "First-line per [authority]"
    }}
  ]
}}

Rules:
- Reference specific clinical practice guidelines (ACC/AHA, NCCN, ADA, etc.)
- Include guideline year in citations
- Rank treatment options by evidence strength and guideline position
- Check drug interactions against patient's current medications
- For cancer queries: include staging, biomarker-guided therapy, immunotherapy options
- Be specific with efficacy numbers (NNT, reduction percentages, survival rates)
- Generate 3-5 informed doctor discussion questions referencing guidelines and patient data
- Maximum 4 treatment options, 3 drugs, 5 doctor questions"""

    raw = await _call_claude(prompt, max_tokens=3000)

    # Parse response
    try:
        if "```" in raw:
            raw = raw[raw.find("{") : raw.rfind("}") + 1]
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        parsed = {
            "ai_synthesis": raw[:500] if raw else "Unable to generate synthesis.",
            "treatment_report": None,
            "drugs_mentioned": [],
        }

    return {
        "ai_synthesis": parsed.get("ai_synthesis", ""),
        "treatment_report": parsed.get("treatment_report"),
        "drugs_mentioned": parsed.get("drugs_mentioned", []),
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
