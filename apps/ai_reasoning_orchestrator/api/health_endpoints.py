"""
Health composite endpoints router for AI Reasoning Orchestrator.
Handles the health-prefixed endpoints: unified-dashboard, daily-summary,
analyze-symptoms, query, and doctor-report.
"""

import time
import os
import json
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Depends

from common.middleware.auth import get_current_user
from common.utils.logging import get_logger
from ..models.reasoning_models import ReasoningRequest
from .reasoning import perform_reasoning

logger = get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Unified dashboard endpoint
# ---------------------------------------------------------------------------
@router.get("/health/unified-dashboard")
async def get_unified_dashboard(
    request: Request, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Unified health dashboard endpoint.

    Provides a comprehensive view of the user's health status,
    combining data from multiple services into a single dashboard view.
    """
    try:
        user_id = current_user["id"]
        logger.info(f"🔄 Generating unified dashboard for user {user_id}")

        # Create reasoning request for unified dashboard
        reasoning_request = ReasoningRequest(
            query="Generate comprehensive health dashboard with current status, trends, and recommendations",
            reasoning_type="dashboard_summary",
            time_window="7d",  # Show 7 days of data for trends
            data_types=[
                "vitals",
                "symptoms",
                "medications",
                "nutrition",
                "sleep",
                "activity",
                "lab_results",
                "medical_records",
            ],
        )

        # Use the core reasoning function
        dashboard_result = await perform_reasoning(
            request, reasoning_request, current_user
        )

        # Enhance with additional dashboard-specific data
        unified_dashboard = {
            "user_id": user_id,
            "dashboard_type": "unified_health",
            "generated_at": datetime.utcnow().isoformat(),
            "time_window": "7d",
            "summary": dashboard_result.reasoning,
            "key_metrics": {
                "health_score": 85.0,  # Placeholder - would be calculated from data
                "data_completeness": 78.0,  # Placeholder - would be calculated from data
                "risk_level": "low",
                "trend_direction": "improving",
            },
            "insights": dashboard_result.insights,
            "recommendations": dashboard_result.recommendations,
            "recent_activity": {
                "last_vital_recorded": "2025-08-08T10:30:00Z",
                "last_symptom_logged": "2025-08-08T09:15:00Z",
                "last_medication_taken": "2025-08-08T08:00:00Z",
            },
            "alerts": [
                {
                    "id": "alert-001",
                    "type": "info",
                    "message": "Consider logging more sleep data for better insights",
                    "priority": "medium",
                    "actionable": True,
                }
            ],
            "data_sources": dashboard_result.data_sources,
            "confidence": dashboard_result.confidence,
        }

        logger.info(f"✅ Unified dashboard generated successfully for user {user_id}")
        return unified_dashboard

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unified dashboard generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Dashboard generation failed: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Daily summary endpoint (health path)
# ---------------------------------------------------------------------------
@router.get("/health/daily-summary")
async def get_daily_summary_health(
    request: Request, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Daily summary endpoint accessible via /health/daily-summary path.

    Provides a daily health summary for the user.
    """
    try:
        user_id = current_user["id"]
        logger.info(f"🔄 Generating daily summary for user {user_id}")

        # Create reasoning request for daily summary
        reasoning_request = ReasoningRequest(
            query="Generate daily health summary and insights",
            reasoning_type="daily_summary",
            time_window="24h",
            data_types=[
                "vitals",
                "symptoms",
                "medications",
                "nutrition",
                "sleep",
                "activity",
            ],
        )

        # Use the core reasoning function
        daily_result = await perform_reasoning(request, reasoning_request, current_user)

        # Return daily summary data
        daily_summary = {
            "user_id": user_id,
            "date": datetime.utcnow().isoformat(),
            "summary": daily_result.reasoning,
            "key_insights": daily_result.insights,
            "recommendations": daily_result.recommendations,
            "health_score": 85.0,
            "data_quality_score": 78.0,
            "trends": [],
            "anomalies": [],
            "data_sources": daily_result.data_sources,
            "confidence": daily_result.confidence,
        }

        logger.info(f"✅ Daily summary generated successfully for user {user_id}")
        return daily_summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Daily summary generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Daily summary failed: {str(e)}")


# ---------------------------------------------------------------------------
# Enhanced symptom analysis endpoint
# ---------------------------------------------------------------------------
@router.post("/health/analyze-symptoms")
async def analyze_symptoms(
    request: Request, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Enhanced symptom analysis endpoint accessible via /health/analyze-symptoms path.

    Provides physician-like interactive analysis with follow-up questions and multi-model synthesis.
    """
    try:
        # Parse the request body
        body = await request.json()
        symptoms = body.get("symptoms", [])
        severity = body.get("severity", "medium")
        duration = body.get("duration", "unknown")
        additional_context = body.get("context", "")
        include_vitals = body.get("include_vitals", True)
        include_medications = body.get("include_medications", True)

        user_id = current_user["id"]

        logger.info(f"🔄 Enhanced symptom analysis for user {user_id}: {symptoms}")

        # Analyze the specific query for context
        query_analysis = await _analyze_symptom_query(symptoms, additional_context)

        # Generate follow-up questions based on the symptom and context
        logger.info(f"🔍 Generating follow-up questions for symptoms: {symptoms}")
        follow_up_questions = await _generate_follow_up_questions(
            symptoms, query_analysis, include_vitals, include_medications
        )
        logger.info(f"✅ Generated {len(follow_up_questions)} follow-up questions")

        # Generate multi-model insights using AI
        multi_model_insights = await _generate_multi_model_insights(
            symptoms, query_analysis, include_vitals, include_medications
        )

        # Calculate urgency level based on symptoms and context
        urgency_level = await _calculate_urgency_level(
            symptoms, severity, duration, query_analysis
        )

        # Generate personalized recommendations using AI
        personalized_recommendations = await _generate_personalized_recommendations(
            symptoms, query_analysis, urgency_level, include_vitals, include_medications
        )

        # Generate basic analysis text (bypassing the reasoning engine for now)
        analysis_text = f"Analysis based on available data. Query: Analyze symptoms with medical context: {', '.join(symptoms)}. Query context: {query_analysis['query_type']}. Severity: {severity}, Duration: {duration}. Additional context: {additional_context}"

        # Create a simple analysis result structure
        analysis_result = type(
            "AnalysisResult",
            (),
            {
                "reasoning": analysis_text,
                "data_sources": [
                    "vitals",
                    "symptoms",
                    "medications",
                    "nutrition",
                    "sleep",
                    "activity",
                    "medical_records",
                    "lab_results",
                ],
                "confidence": "medium",
            },
        )()

        # Return enhanced symptom analysis data
        symptom_analysis = {
            "user_id": user_id,
            "analyzed_at": datetime.utcnow().isoformat(),
            "symptoms_analyzed": symptoms,
            "severity": severity,
            "duration": duration,
            "query_analysis": query_analysis,
            "analysis": analysis_result.reasoning,
            "key_insights": multi_model_insights["insights"],
            "recommendations": personalized_recommendations,
            "possible_causes": multi_model_insights["possible_causes"],
            "urgency_level": urgency_level["level"],
            "urgency_reasoning": urgency_level["reasoning"],
            "follow_up_questions": follow_up_questions,
            "next_steps": urgency_level["next_steps"],
            "medical_context": multi_model_insights["medical_context"],
            "data_sources": analysis_result.data_sources,
            "confidence": analysis_result.confidence,
            "interaction_required": len(follow_up_questions) > 0,
            "session_id": f"session_{user_id}_{int(time.time())}",
        }

        logger.info(f"✅ Enhanced symptom analysis completed for user {user_id}")
        return symptom_analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Enhanced symptom analysis failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Symptom analysis failed: {str(e)}"
        )


# ---------------------------------------------------------------------------
# Enhanced health query endpoint
# ---------------------------------------------------------------------------
@router.post("/health/query")
async def health_query(
    request: Request, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Enhanced health query endpoint accessible via /health/query path.

    Accepts natural language health queries and provides intelligent, educational responses.
    Distinguishes between general health questions and symptom-specific queries.
    """
    try:
        # Parse the request body
        body = await request.json()
        query = body.get("query", "")
        context = body.get("context", "")
        user_id = current_user["id"]

        logger.info(f"🔄 Processing enhanced health query for user {user_id}: {query}")

        # Analyze query type to determine response approach
        query_analysis = await _analyze_health_query(query, context)

        # Create reasoning request for health query
        reasoning_request = ReasoningRequest(
            query=f"{query}. Context: {context}. Query type: {query_analysis['query_type']}",
            reasoning_type="real_time_insights",
            time_window="7d",
            data_types=[
                "vitals",
                "symptoms",
                "medications",
                "nutrition",
                "sleep",
                "activity",
                "medical_records",
                "lab_results",
            ],
        )

        # Use the core reasoning function
        query_result = await perform_reasoning(request, reasoning_request, current_user)

        # Generate educational content based on query type
        educational_content = await _generate_educational_content(query, query_analysis)

        # Determine if this should redirect to symptom analysis
        should_redirect_to_symptoms = query_analysis.get(
            "should_redirect_to_symptoms", False
        )

        # Return enhanced health query response
        health_query_response = {
            "user_id": user_id,
            "query": query,
            "context": context,
            "query_analysis": query_analysis,
            "answered_at": datetime.utcnow().isoformat(),
            "answer": query_result.reasoning,
            "educational_content": educational_content,
            "insights": query_result.insights,
            "recommendations": query_result.recommendations,
            "confidence": query_result.confidence,
            "data_sources": query_result.data_sources,
            "related_topics": educational_content.get("related_topics", []),
            "follow_up_questions": educational_content.get("follow_up_questions", []),
            "should_redirect_to_symptoms": should_redirect_to_symptoms,
            "redirect_reason": query_analysis.get("redirect_reason", ""),
            "query_category": query_analysis.get("category", "general"),
            "medical_entities": query_analysis.get("medical_entities", []),
        }

        logger.info(f"✅ Enhanced health query processed for user {user_id}")
        return health_query_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Enhanced health query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health query failed: {str(e)}")


# ---------------------------------------------------------------------------
# Doctor report endpoint
# ---------------------------------------------------------------------------
@router.post("/health/doctor-report")
async def doctor_report(
    request: Request, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Doctor report endpoint accessible via /health/doctor-report path.

    Generates comprehensive health reports suitable for healthcare providers.
    """
    try:
        # Parse the request body
        body = await request.json()
        report_type = body.get("report_type", "comprehensive")
        time_window = body.get("time_window", "30d")
        include_labs = body.get("include_labs", True)
        include_medications = body.get("include_medications", True)
        user_id = current_user["id"]

        logger.info(
            f"🔄 Generating doctor report for user {user_id}, type: {report_type}"
        )

        # Create reasoning request for doctor report
        reasoning_request = ReasoningRequest(
            query=f"Generate {report_type} doctor report for the last {time_window}. Include labs: {include_labs}, medications: {include_medications}",
            reasoning_type="doctor_report",
            time_window=time_window,
            data_types=[
                "vitals",
                "symptoms",
                "medications",
                "nutrition",
                "sleep",
                "activity",
                "medical_records",
                "lab_results",
            ],
        )

        # Use the core reasoning function
        report_result = await perform_reasoning(
            request, reasoning_request, current_user
        )

        # Return doctor report data
        doctor_report_response = {
            "user_id": user_id,
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "time_window": time_window,
            "patient_summary": {
                "age": 35,  # Placeholder - would come from user profile
                "gender": "Not specified",
                "primary_concerns": ["Fatigue", "Sleep issues"],
                "current_medications": ["Vitamin D", "Iron supplement"],
                "allergies": ["None reported"],
                "family_history": ["Diabetes", "Hypertension"],
            },
            "vital_signs_summary": {
                "blood_pressure": "120/80 mmHg",
                "heart_rate": "72 bpm",
                "temperature": "98.6°F",
                "weight": "70 kg",
                "trends": "Stable over the last 30 days",
            },
            "symptom_analysis": {
                "primary_symptoms": ["Fatigue", "Poor sleep quality"],
                "severity": "Mild to moderate",
                "duration": "2-3 weeks",
                "triggers": ["Stress", "Poor sleep hygiene"],
                "impact": "Affecting daily activities and work performance",
            },
            "lifestyle_factors": {
                "sleep_patterns": "Irregular, 6-7 hours average",
                "exercise": "Minimal, mostly sedentary",
                "diet": "Generally healthy, but irregular meal times",
                "stress_levels": "High due to work demands",
            },
            "recommendations": report_result.recommendations,
            "insights": report_result.insights,
            "clinical_notes": report_result.reasoning,
            "next_steps": [
                "Schedule follow-up appointment in 2 weeks",
                "Consider sleep study if symptoms persist",
                "Monitor stress levels and implement stress management techniques",
                "Review medication adherence and side effects",
            ],
            "risk_factors": [
                {
                    "factor": "Sedentary lifestyle",
                    "risk_level": "Medium",
                    "recommendation": "Increase physical activity",
                },
                {
                    "factor": "High stress levels",
                    "risk_level": "High",
                    "recommendation": "Implement stress management strategies",
                },
            ],
            "data_sources": report_result.data_sources,
            "confidence": report_result.confidence,
            "report_metadata": {
                "generated_by": "AI Reasoning Orchestrator",
                "data_completeness": "78%",
                "last_data_update": "2025-08-08T20:00:00Z",
            },
        }

        logger.info(f"✅ Doctor report generated for user {user_id}")
        return doctor_report_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Doctor report generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Doctor report generation failed: {str(e)}"
        )


# ===========================================================================
# Helper functions for symptom analysis and health queries
# ===========================================================================


async def _analyze_symptom_query(symptoms: List[str], context: str) -> Dict[str, Any]:
    """Analyze the specific symptom query to understand user intent and context"""
    try:
        # Analyze if this is a question about causation, diagnosis, or general inquiry
        query_text = " ".join(symptoms) + " " + context
        query_lower = query_text.lower()

        query_analysis = {
            "query_type": "general_inquiry",
            "medical_entities": [],
            "intent": "information_seeking",
            "specific_concerns": [],
            "requires_follow_up": True,
        }

        # Enhanced query type detection
        if any(
            word in query_lower
            for word in [
                "cause",
                "causes",
                "causing",
                "can cause",
                "lead to",
                "why",
                "reason",
            ]
        ):
            query_analysis["query_type"] = "causation_inquiry"
            query_analysis["intent"] = "understanding_causes"
        elif any(
            word in query_lower
            for word in [
                "diagnosis",
                "diagnose",
                "what is",
                "could be",
                "condition",
                "disease",
            ]
        ):
            query_analysis["query_type"] = "diagnostic_inquiry"
            query_analysis["intent"] = "seeking_diagnosis"
        elif any(
            word in query_lower
            for word in ["treatment", "cure", "fix", "help", "solution", "remedy"]
        ):
            query_analysis["query_type"] = "treatment_inquiry"
            query_analysis["intent"] = "seeking_treatment"
        elif any(
            word in query_lower
            for word in [
                "weight",
                "belly",
                "fat",
                "diet",
                "nutrition",
                "exercise",
                "calorie",
                "carb",
                "carbs",
                "low carb",
                "keto",
            ]
        ):
            query_analysis["query_type"] = "lifestyle_inquiry"
            query_analysis["intent"] = "lifestyle_optimization"

        # Enhanced medical entity extraction
        medical_entities = []

        # Weight and body composition related
        if any(
            word in query_lower for word in ["belly", "stomach", "abdomen", "waist"]
        ):
            medical_entities.append(
                {
                    "entity": "abdominal_fat",
                    "type": "body_composition",
                    "concern": "weight_distribution",
                }
            )
        if any(
            word in query_lower for word in ["weight", "fat", "obese", "overweight"]
        ):
            medical_entities.append(
                {
                    "entity": "weight_management",
                    "type": "lifestyle",
                    "concern": "body_composition",
                }
            )
        if any(word in query_lower for word in ["diet", "nutrition", "eating", "food"]):
            medical_entities.append(
                {
                    "entity": "nutrition",
                    "type": "lifestyle",
                    "concern": "dietary_habits",
                }
            )
        if any(
            word in query_lower
            for word in [
                "calorie",
                "calories",
                "restricted",
                "low carb",
                "keto",
                "carb",
                "carbs",
            ]
        ):
            medical_entities.append(
                {
                    "entity": "calorie_restriction",
                    "type": "diet",
                    "concern": "metabolic_response",
                }
            )

        # Common symptoms
        if "headache" in query_lower:
            medical_entities.append(
                {"entity": "headache", "type": "symptom", "severity": "variable"}
            )
        if "fatigue" in query_lower or "tired" in query_lower:
            medical_entities.append(
                {"entity": "fatigue", "type": "symptom", "severity": "variable"}
            )
        if "pain" in query_lower:
            medical_entities.append(
                {"entity": "pain", "type": "symptom", "severity": "variable"}
            )
        if "nausea" in query_lower:
            medical_entities.append(
                {"entity": "nausea", "type": "symptom", "severity": "variable"}
            )
        if "dizziness" in query_lower:
            medical_entities.append(
                {"entity": "dizziness", "type": "symptom", "severity": "variable"}
            )

        # Metabolic and endocrine
        if any(word in query_lower for word in ["sodium", "salt", "electrolyte"]):
            medical_entities.append(
                {"entity": "sodium", "type": "electrolyte", "concern": "deficiency"}
            )
        if any(word in query_lower for word in ["blood sugar", "glucose", "diabetes"]):
            medical_entities.append(
                {"entity": "blood_sugar", "type": "metabolic", "concern": "regulation"}
            )
        if any(word in query_lower for word in ["thyroid", "hormone"]):
            medical_entities.append(
                {"entity": "thyroid", "type": "endocrine", "concern": "function"}
            )

        # Digestive
        if any(
            word in query_lower
            for word in ["bloating", "gas", "digestion", "digestive"]
        ):
            medical_entities.append(
                {
                    "entity": "digestive_issues",
                    "type": "symptom",
                    "concern": "gastrointestinal",
                }
            )

        query_analysis["medical_entities"] = medical_entities
        query_analysis["specific_concerns"] = [
            entity["entity"] for entity in medical_entities
        ]

        return query_analysis

    except Exception as e:
        logger.error(f"Error analyzing symptom query: {e}")
        return {
            "query_type": "general_inquiry",
            "medical_entities": [],
            "intent": "information_seeking",
            "specific_concerns": [],
            "requires_follow_up": True,
        }


async def _generate_follow_up_questions(
    symptoms: List[str],
    query_analysis: Dict[str, Any],
    include_vitals: bool,
    include_medications: bool,
) -> List[Dict[str, Any]]:
    """Generate physician-like follow-up questions dynamically using AI models"""
    try:
        logger.info(
            f"🤖 Starting AI-powered follow-up question generation for: {symptoms}"
        )
        import openai

        # Base questions that are always relevant
        base_questions = [
            {
                "id": "duration",
                "question": "How long have you been experiencing these symptoms?",
                "type": "duration",
                "required": True,
                "options": [
                    "Less than 24 hours",
                    "1-3 days",
                    "1 week",
                    "2-4 weeks",
                    "More than 1 month",
                ],
            },
            {
                "id": "frequency",
                "question": "How often do these symptoms occur?",
                "type": "frequency",
                "required": True,
                "options": [
                    "Constant",
                    "Daily",
                    "Several times a week",
                    "Occasionally",
                    "Rarely",
                ],
            },
        ]

        # Generate symptom-specific questions using AI
        symptom_text = " ".join(symptoms)
        query_type = query_analysis.get("query_type", "general_inquiry")

        # Create prompt for AI to generate relevant follow-up questions
        prompt = f"""
        As a medical AI assistant, generate 3-5 relevant follow-up questions for a patient with the following symptoms: "{symptom_text}"

        Query type: {query_type}
        Include vitals data: {include_vitals}
        Include medications data: {include_medications}

        Generate questions that would help a physician understand:
        1. The nature and characteristics of the symptoms
        2. Potential triggers or aggravating factors
        3. Associated symptoms
        4. Relevant medical history context
        5. Impact on daily activities

        Return the questions in this exact JSON format:
        {{
            "questions": [
                {{
                    "id": "unique_identifier",
                    "question": "The question text",
                    "type": "question_category",
                    "required": true/false,
                    "options": ["option1", "option2", "option3", "option4", "option5"]
                }}
            ]
        }}

        Make sure the questions are:
        - Specific to the symptoms mentioned
        - Clinically relevant
        - Easy to understand
        - Include appropriate multiple choice options
        - Cover different aspects (location, severity, triggers, timing, etc.)
        """

        try:
            # Use OpenAI API to generate questions
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical AI assistant that generates relevant follow-up questions for symptom analysis. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            # Parse the AI response
            ai_response = response.choices[0].message.content.strip()

            # Extract JSON from the response (handle cases where there might be extra text)
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0]
            elif "```" in ai_response:
                ai_response = ai_response.split("```")[1]

            ai_questions_data = json.loads(ai_response)
            ai_questions = ai_questions_data.get("questions", [])

            logger.info(
                f"✅ Generated {len(ai_questions)} AI-powered follow-up questions for symptoms: {symptom_text}"
            )
            logger.info(f"🤖 AI questions: {ai_questions}")

        except Exception as ai_error:
            logger.error(f"Error generating AI questions: {ai_error}")
            # Generate dynamic fallback questions based on symptoms and query analysis
            ai_questions = _generate_dynamic_fallback_questions(
                symptoms, query_analysis
            )

        # Add data-specific questions based on available data
        data_questions = []

        if include_vitals:
            data_questions.append(
                {
                    "id": "vital_trends",
                    "question": "Have you noticed any changes in your blood pressure or heart rate?",
                    "type": "vitals",
                    "required": False,
                    "options": [
                        "Yes, higher",
                        "Yes, lower",
                        "No changes",
                        "Don't monitor",
                    ],
                }
            )

        if include_medications:
            data_questions.append(
                {
                    "id": "medication_changes",
                    "question": "Have you started, stopped, or changed any medications recently?",
                    "type": "medications",
                    "required": False,
                    "options": [
                        "Yes, new medication",
                        "Yes, stopped medication",
                        "Yes, changed dose",
                        "No changes",
                    ],
                }
            )

        # Combine all questions
        all_questions = base_questions + ai_questions + data_questions

        # Ensure unique IDs
        seen_ids = set()
        unique_questions = []
        for question in all_questions:
            if question["id"] not in seen_ids:
                seen_ids.add(question["id"])
                unique_questions.append(question)

        logger.info(f"Total follow-up questions generated: {len(unique_questions)}")
        return unique_questions

    except Exception as e:
        logger.error(f"Error generating follow-up questions: {e}")
        # Return dynamic fallback questions
        return _generate_dynamic_fallback_questions(symptoms, query_analysis)


def _generate_dynamic_fallback_questions(
    symptoms: List[str], query_analysis: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate dynamic fallback questions based on symptoms and query analysis"""
    questions = []
    symptom_text = " ".join(symptoms).lower()
    query_type = query_analysis.get("query_type", "general_inquiry")
    medical_entities = query_analysis.get("medical_entities", [])

    # Base questions that are always relevant
    questions.extend(
        [
            {
                "id": "duration",
                "question": "How long have you been experiencing these symptoms?",
                "type": "duration",
                "required": True,
                "options": [
                    "Less than 24 hours",
                    "1-3 days",
                    "1 week",
                    "2-4 weeks",
                    "More than 1 month",
                ],
            },
            {
                "id": "frequency",
                "question": "How often do these symptoms occur?",
                "type": "frequency",
                "required": True,
                "options": [
                    "Constant",
                    "Daily",
                    "Several times a week",
                    "Occasionally",
                    "Rarely",
                ],
            },
        ]
    )

    # Weight and body composition specific questions
    if any(
        word in symptom_text for word in ["belly", "stomach", "abdomen", "waist", "fat"]
    ):
        questions.extend(
            [
                {
                    "id": "weight_distribution",
                    "question": "Where specifically is the fat accumulating?",
                    "type": "body_composition",
                    "required": False,
                    "options": [
                        "Only belly/waist",
                        "All over body",
                        "Face and neck",
                        "Arms and legs",
                        "Mixed distribution",
                    ],
                },
                {
                    "id": "diet_consistency",
                    "question": "How strictly have you been following your calorie-restricted diet?",
                    "type": "lifestyle",
                    "required": False,
                    "options": [
                        "Very strictly",
                        "Mostly consistent",
                        "Sometimes cheat",
                        "Not very strict",
                        "Inconsistent",
                    ],
                },
                {
                    "id": "exercise_routine",
                    "question": "What type of exercise are you currently doing?",
                    "type": "lifestyle",
                    "required": False,
                    "options": [
                        "Cardio only",
                        "Strength training",
                        "Both cardio and strength",
                        "No exercise",
                        "Occasional walks",
                    ],
                },
            ]
        )

    # Diet and nutrition specific questions
    if any(
        word in symptom_text
        for word in ["diet", "nutrition", "eating", "calorie", "low carb"]
    ):
        questions.extend(
            [
                {
                    "id": "diet_type",
                    "question": "What type of diet are you following?",
                    "type": "nutrition",
                    "required": False,
                    "options": [
                        "Low carb/keto",
                        "Calorie restriction",
                        "Intermittent fasting",
                        "Mediterranean",
                        "Other",
                    ],
                },
                {
                    "id": "meal_timing",
                    "question": "How many meals do you eat per day?",
                    "type": "nutrition",
                    "required": False,
                    "options": [
                        "1-2 meals",
                        "3 meals",
                        "4-5 small meals",
                        "Grazing throughout day",
                        "Intermittent fasting",
                    ],
                },
                {
                    "id": "water_intake",
                    "question": "How much water do you drink daily?",
                    "type": "nutrition",
                    "required": False,
                    "options": [
                        "Less than 4 cups",
                        "4-6 cups",
                        "6-8 cups",
                        "More than 8 cups",
                        "Don't track",
                    ],
                },
            ]
        )

    # Metabolic and endocrine questions
    if any(
        word in symptom_text
        for word in ["metabolism", "thyroid", "hormone", "blood sugar"]
    ):
        questions.extend(
            [
                {
                    "id": "energy_levels",
                    "question": "How would you describe your energy levels throughout the day?",
                    "type": "metabolic",
                    "required": False,
                    "options": ["Very low", "Low", "Moderate", "Good", "Very high"],
                },
                {
                    "id": "sleep_quality",
                    "question": "How well do you sleep?",
                    "type": "lifestyle",
                    "required": False,
                    "options": ["Very poorly", "Poorly", "Fair", "Well", "Very well"],
                },
                {
                    "id": "stress_levels",
                    "question": "How would you rate your stress levels?",
                    "type": "lifestyle",
                    "required": False,
                    "options": ["Very high", "High", "Moderate", "Low", "Very low"],
                },
            ]
        )

    # Digestive questions
    if any(
        word in symptom_text
        for word in ["bloating", "gas", "digestion", "digestive", "stomach"]
    ):
        questions.extend(
            [
                {
                    "id": "digestive_symptoms",
                    "question": "Do you experience any digestive symptoms?",
                    "type": "digestive",
                    "required": False,
                    "options": [
                        "Bloating",
                        "Gas",
                        "Indigestion",
                        "Nausea",
                        "None of the above",
                    ],
                },
                {
                    "id": "food_triggers",
                    "question": "Do certain foods make your symptoms worse?",
                    "type": "digestive",
                    "required": False,
                    "options": [
                        "Dairy",
                        "Gluten",
                        "High fat foods",
                        "Spicy foods",
                        "No specific triggers",
                    ],
                },
            ]
        )

    # General health questions based on query type
    if query_type == "lifestyle_inquiry":
        questions.extend(
            [
                {
                    "id": "goal_clarity",
                    "question": "What is your primary health goal?",
                    "type": "lifestyle",
                    "required": False,
                    "options": [
                        "Weight loss",
                        "Better health",
                        "More energy",
                        "Better sleep",
                        "Other",
                    ],
                },
                {
                    "id": "previous_attempts",
                    "question": "Have you tried similar approaches before?",
                    "type": "lifestyle",
                    "required": False,
                    "options": [
                        "Yes, worked well",
                        "Yes, some success",
                        "Yes, no success",
                        "No previous attempts",
                        "Not sure",
                    ],
                },
            ]
        )

    return questions


def _generate_dynamic_fallback_insights(
    symptoms: List[str], query_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate dynamic fallback insights based on symptoms and query analysis"""
    symptom_text = " ".join(symptoms).lower()
    query_type = query_analysis.get("query_type", "general_inquiry")
    medical_entities = query_analysis.get("medical_entities", [])

    insights = []
    possible_causes = []
    medical_context = {
        "key_factors": [],
        "risk_factors": [],
        "diagnostic_considerations": [],
    }

    # Weight and body composition insights
    if any(
        word in symptom_text for word in ["belly", "stomach", "abdomen", "waist", "fat"]
    ):
        insights.append(
            {
                "type": "body_composition",
                "title": "Abdominal Fat Distribution",
                "description": "Abdominal fat can be particularly resistant to diet changes due to hormonal factors and metabolic differences.",
                "confidence": "medium",
                "source": "medical_knowledge",
            }
        )

        possible_causes.extend(
            [
                {
                    "cause": "Hormonal factors (cortisol, insulin)",
                    "confidence": "medium",
                    "evidence": "Stress and poor sleep can increase cortisol, leading to abdominal fat storage",
                    "medical_background": "Cortisol promotes fat storage in the abdominal area",
                },
                {
                    "cause": "Insulin resistance",
                    "confidence": "medium",
                    "evidence": "High carb diets can lead to insulin resistance, making fat loss difficult",
                    "medical_background": "Insulin resistance affects how the body stores and burns fat",
                },
            ]
        )

        medical_context["key_factors"].extend(
            ["Hormonal balance", "Insulin sensitivity", "Stress levels"]
        )
        medical_context["risk_factors"].extend(
            ["High stress", "Poor sleep", "Sedentary lifestyle"]
        )
        medical_context["diagnostic_considerations"].extend(
            ["Hormone levels", "Insulin resistance", "Metabolic health"]
        )

    # Diet and nutrition insights
    if any(
        word in symptom_text
        for word in ["diet", "nutrition", "eating", "calorie", "low carb"]
    ):
        insights.append(
            {
                "type": "nutrition",
                "title": "Diet Effectiveness",
                "description": "Calorie restriction and low-carb diets can be effective, but individual responses vary significantly.",
                "confidence": "medium",
                "source": "nutritional_science",
            }
        )

        possible_causes.extend(
            [
                {
                    "cause": "Metabolic adaptation",
                    "confidence": "medium",
                    "evidence": "The body may adapt to calorie restriction by slowing metabolism",
                    "medical_background": "Prolonged calorie restriction can trigger metabolic slowdown",
                },
                {
                    "cause": "Inadequate protein intake",
                    "confidence": "medium",
                    "evidence": "Low protein diets may not preserve muscle mass during weight loss",
                    "medical_background": "Protein is essential for maintaining muscle mass and metabolic rate",
                },
            ]
        )

        medical_context["key_factors"].extend(
            ["Protein intake", "Calorie deficit", "Nutrient timing"]
        )
        medical_context["risk_factors"].extend(
            ["Very low calorie diets", "Nutrient deficiencies"]
        )
        medical_context["diagnostic_considerations"].extend(
            ["Body composition", "Metabolic rate", "Nutrient status"]
        )

    # Exercise and lifestyle insights
    if any(
        word in symptom_text for word in ["exercise", "workout", "activity", "training"]
    ):
        insights.append(
            {
                "type": "lifestyle",
                "title": "Exercise Impact",
                "description": "Combining strength training with cardio can be more effective for fat loss than either alone.",
                "confidence": "high",
                "source": "exercise_science",
            }
        )

        possible_causes.append(
            {
                "cause": "Inadequate exercise variety",
                "confidence": "medium",
                "evidence": "Focusing only on cardio may not build enough muscle to boost metabolism",
                "medical_background": "Muscle tissue burns more calories at rest than fat tissue",
            }
        )

        medical_context["key_factors"].extend(
            ["Exercise type", "Intensity", "Consistency"]
        )
        medical_context["risk_factors"].extend(["Sedentary lifestyle", "Overtraining"])
        medical_context["diagnostic_considerations"].extend(
            ["Fitness level", "Recovery capacity"]
        )

    # General health insights
    if query_type == "lifestyle_inquiry":
        insights.append(
            {
                "type": "lifestyle",
                "title": "Holistic Approach",
                "description": "Sustainable weight loss requires addressing multiple factors including diet, exercise, sleep, and stress management.",
                "confidence": "high",
                "source": "lifestyle_medicine",
            }
        )

        medical_context["key_factors"].extend(
            ["Sleep quality", "Stress management", "Consistency"]
        )
        medical_context["risk_factors"].extend(
            ["Poor sleep", "High stress", "Inconsistent habits"]
        )
        medical_context["diagnostic_considerations"].extend(
            ["Lifestyle factors", "Behavioral patterns"]
        )

    return {
        "insights": insights,
        "possible_causes": possible_causes,
        "medical_context": medical_context,
    }


async def _generate_multi_model_insights(
    symptoms: List[str],
    query_analysis: Dict[str, Any],
    include_vitals: bool,
    include_medications: bool,
) -> Dict[str, Any]:
    """Generate insights using AI models and medical knowledge dynamically"""
    try:
        import openai

        # Generate insights using AI
        symptom_text = " ".join(symptoms)
        query_type = query_analysis.get("query_type", "general_inquiry")

        # Create prompt for AI to generate medical insights
        prompt = f"""
        As a medical AI assistant, analyze the following symptoms and provide comprehensive medical insights: "{symptom_text}"

        Query type: {query_type}
        Include vitals data: {include_vitals}
        Include medications data: {include_medications}

        Provide analysis in this exact JSON format:
        {{
            "insights": [
                {{
                    "type": "insight_type",
                    "title": "Insight title",
                    "description": "Detailed description of the insight",
                    "confidence": "high/medium/low",
                    "source": "source_of_information"
                }}
            ],
            "possible_causes": [
                {{
                    "cause": "Possible cause name",
                    "confidence": "high/medium/low",
                    "evidence": "Supporting evidence",
                    "medical_background": "Medical explanation"
                }}
            ],
            "medical_context": {{
                "key_factors": ["factor1", "factor2"],
                "risk_factors": ["risk1", "risk2"],
                "diagnostic_considerations": ["consideration1", "consideration2"]
            }}
        }}

        Focus on:
        1. Clinically relevant insights
        2. Evidence-based possible causes
        3. Important medical context and risk factors
        4. Diagnostic considerations
        5. Treatment implications
        """

        try:
            # Use OpenAI API to generate insights
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical AI assistant that provides evidence-based medical insights and analysis. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1500,
            )

            # Parse the AI response
            ai_response = response.choices[0].message.content.strip()

            # Extract JSON from the response
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0]
            elif "```" in ai_response:
                ai_response = ai_response.split("```")[1]

            ai_insights_data = json.loads(ai_response)

            insights = ai_insights_data.get("insights", [])
            possible_causes = ai_insights_data.get("possible_causes", [])
            medical_context = ai_insights_data.get("medical_context", {})

            logger.info(f"Generated AI-powered insights for symptoms: {symptom_text}")

        except Exception as ai_error:
            logger.error(f"Error generating AI insights: {ai_error}")
            # Generate dynamic fallback insights based on symptoms and query analysis
            fallback_data = _generate_dynamic_fallback_insights(
                symptoms, query_analysis
            )
            insights = fallback_data["insights"]
            possible_causes = fallback_data["possible_causes"]
            medical_context = fallback_data["medical_context"]

        # Add fallback insights if AI didn't generate any
        if not insights:
            insights.append(
                {
                    "type": "general_analysis",
                    "title": "Symptom Analysis",
                    "description": "Based on the symptoms provided, a comprehensive medical evaluation may be needed to determine the underlying cause.",
                    "confidence": "low",
                    "source": "general_medical_knowledge",
                }
            )

        if not possible_causes:
            possible_causes.append(
                {
                    "cause": "Requires medical evaluation",
                    "confidence": "low",
                    "evidence": "Symptoms need professional assessment",
                    "medical_background": "Many conditions can present with similar symptoms",
                }
            )

        return {
            "insights": insights,
            "possible_causes": possible_causes,
            "medical_context": medical_context,
        }

    except Exception as e:
        logger.error(f"Error generating multi-model insights: {e}")
        return {"insights": [], "possible_causes": [], "medical_context": {}}


async def _calculate_urgency_level(
    symptoms: List[str], severity: str, duration: str, query_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Calculate urgency level based on symptoms and context"""
    try:
        query_text = " ".join(symptoms).lower()
        urgency_level = "low"
        reasoning = (
            "Based on current information, this appears to be a non-urgent situation."
        )
        next_steps = [
            "Monitor symptoms for 24-48 hours",
            "Consider logging additional context",
            "Consult healthcare provider if symptoms worsen",
        ]

        # Symptom-specific urgency assessment
        if (
            "sunrash" in query_text
            or "sun rash" in query_text
            or "sunburn" in query_text
        ):
            if (
                "severe" in query_text
                or "blisters" in query_text
                or "fever" in query_text
            ):
                urgency_level = "medium"
                reasoning = "Severe sunburn with blisters or fever may require medical attention to prevent complications."
                next_steps = [
                    "Seek medical attention if blisters are extensive",
                    "Monitor for signs of infection",
                    "Stay hydrated and avoid further sun exposure",
                ]
            else:
                urgency_level = "low"
                reasoning = "Mild to moderate sunburn can typically be managed at home with proper care."
                next_steps = [
                    "Apply cool compresses and moisturizer",
                    "Stay hydrated",
                    "Avoid further sun exposure",
                ]

        elif (
            "heartburn" in query_text
            or "acid reflux" in query_text
            or "indigestion" in query_text
        ):
            if (
                "severe" in query_text
                or "chest pain" in query_text
                or "difficulty swallowing" in query_text
            ):
                urgency_level = "medium"
                reasoning = "Severe heartburn with chest pain or difficulty swallowing may indicate complications requiring medical evaluation."
                next_steps = [
                    "Seek medical attention if chest pain is severe",
                    "Monitor for signs of complications",
                    "Consider over-the-counter antacids",
                ]
            else:
                urgency_level = "low"
                reasoning = "Mild to moderate heartburn can often be managed with lifestyle changes and over-the-counter medications."
                next_steps = [
                    "Try lifestyle modifications",
                    "Consider over-the-counter antacids",
                    "Monitor for worsening symptoms",
                ]

        elif "headache" in query_text:
            # Check for urgent headache symptoms
            urgent_headache_symptoms = [
                "severe headache",
                "sudden headache",
                "worst headache",
                "thunderclap headache",
                "headache with fever",
                "headache with confusion",
            ]
            if any(
                urgent_symptom in query_text
                for urgent_symptom in urgent_headache_symptoms
            ):
                urgency_level = "high"
                reasoning = "Sudden or severe headaches can indicate serious conditions requiring immediate medical attention."
                next_steps = [
                    "Seek immediate medical attention",
                    "Go to emergency room if symptoms are severe",
                    "Contact healthcare provider immediately",
                ]
            elif "severe" in query_text or "migraine" in query_text:
                urgency_level = "medium"
                reasoning = "Severe or migraine headaches may require medical evaluation and treatment."
                next_steps = [
                    "Schedule appointment with healthcare provider",
                    "Try over-the-counter pain relievers",
                    "Rest in a quiet, dark room",
                ]
            else:
                urgency_level = "low"
                reasoning = "Mild to moderate headaches can often be managed with rest and over-the-counter medications."
                next_steps = [
                    "Try over-the-counter pain relievers",
                    "Rest and stay hydrated",
                    "Monitor for worsening symptoms",
                ]

        elif "fever" in query_text or "temperature" in query_text:
            if (
                "high fever" in query_text
                or "above 103" in query_text
                or "fever with confusion" in query_text
            ):
                urgency_level = "high"
                reasoning = "High fever (above 103°F) or fever with confusion requires immediate medical attention."
                next_steps = [
                    "Seek immediate medical attention",
                    "Go to emergency room if fever is very high",
                    "Stay hydrated and rest",
                ]
            elif "fever" in query_text and (
                "persistent" in query_text or "more than 3 days" in query_text
            ):
                urgency_level = "medium"
                reasoning = "Persistent fever lasting more than 3 days may indicate a bacterial infection requiring medical evaluation."
                next_steps = [
                    "Schedule appointment with healthcare provider",
                    "Monitor temperature regularly",
                    "Stay hydrated and rest",
                ]
            else:
                urgency_level = "low"
                reasoning = "Mild fever is often due to viral infection and can be managed at home."
                next_steps = [
                    "Rest and stay hydrated",
                    "Monitor temperature",
                    "Seek care if fever persists or worsens",
                ]

        elif "cough" in query_text:
            if (
                "blood" in query_text
                or "shortness of breath" in query_text
                or "chest pain" in query_text
            ):
                urgency_level = "high"
                reasoning = "Cough with blood, shortness of breath, or chest pain requires immediate medical attention."
                next_steps = [
                    "Seek immediate medical attention",
                    "Go to emergency room if symptoms are severe",
                    "Avoid strenuous activity",
                ]
            elif "persistent cough" in query_text or "more than 3 weeks" in query_text:
                urgency_level = "medium"
                reasoning = "Persistent cough lasting more than 3 weeks may indicate underlying conditions requiring medical evaluation."
                next_steps = [
                    "Schedule appointment with healthcare provider",
                    "Monitor for other symptoms",
                    "Consider over-the-counter cough remedies",
                ]
            else:
                urgency_level = "low"
                reasoning = "Acute cough is usually due to viral infection and can be managed at home."
                next_steps = [
                    "Stay hydrated",
                    "Use humidifier",
                    "Monitor for worsening symptoms",
                ]

        elif "pain" in query_text:
            if (
                "severe pain" in query_text
                or "sudden pain" in query_text
                or "chest pain" in query_text
            ):
                urgency_level = "high"
                reasoning = "Severe or sudden pain, especially chest pain, requires immediate medical attention."
                next_steps = [
                    "Seek immediate medical attention",
                    "Go to emergency room if pain is severe",
                    "Avoid strenuous activity",
                ]
            elif "chronic pain" in query_text or "persistent pain" in query_text:
                urgency_level = "medium"
                reasoning = "Chronic or persistent pain may require medical evaluation and treatment."
                next_steps = [
                    "Schedule appointment with healthcare provider",
                    "Consider pain management strategies",
                    "Monitor for changes in pain pattern",
                ]
            else:
                urgency_level = "low"
                reasoning = "Mild to moderate pain can often be managed with rest and over-the-counter medications."
                next_steps = [
                    "Try over-the-counter pain relievers",
                    "Rest the affected area",
                    "Monitor for worsening symptoms",
                ]

        elif "rash" in query_text or "skin" in query_text:
            if (
                "severe rash" in query_text
                or "blisters" in query_text
                or "fever with rash" in query_text
            ):
                urgency_level = "medium"
                reasoning = "Severe rash with blisters or fever may indicate infection or allergic reaction requiring medical attention."
                next_steps = [
                    "Seek medical attention if rash is severe",
                    "Monitor for signs of infection",
                    "Avoid scratching the affected area",
                ]
            else:
                urgency_level = "low"
                reasoning = "Mild rash can often be managed with gentle skincare and avoiding triggers."
                next_steps = [
                    "Use gentle skincare products",
                    "Avoid known triggers",
                    "Monitor for worsening symptoms",
                ]

        elif "nausea" in query_text or "vomiting" in query_text:
            if (
                "severe nausea" in query_text
                or "blood in vomit" in query_text
                or "severe abdominal pain" in query_text
            ):
                urgency_level = "high"
                reasoning = "Severe nausea with blood in vomit or severe abdominal pain requires immediate medical attention."
                next_steps = [
                    "Seek immediate medical attention",
                    "Go to emergency room if symptoms are severe",
                    "Stay hydrated if possible",
                ]
            elif (
                "persistent vomiting" in query_text
                or "more than 24 hours" in query_text
            ):
                urgency_level = "medium"
                reasoning = "Persistent vomiting for more than 24 hours may lead to dehydration and requires medical evaluation."
                next_steps = [
                    "Seek medical attention",
                    "Stay hydrated with small sips",
                    "Monitor for signs of dehydration",
                ]
            else:
                urgency_level = "low"
                reasoning = "Mild nausea and vomiting can often be managed with rest and hydration."
                next_steps = [
                    "Stay hydrated with small sips",
                    "Eat bland foods",
                    "Monitor for worsening symptoms",
                ]

        elif "fatigue" in query_text or "tired" in query_text:
            if (
                "severe fatigue" in query_text
                or "extreme fatigue" in query_text
                or "fatigue with other symptoms" in query_text
            ):
                urgency_level = "medium"
                reasoning = "Severe or extreme fatigue, especially with other symptoms, may indicate underlying medical conditions."
                next_steps = [
                    "Schedule appointment with healthcare provider",
                    "Monitor for other symptoms",
                    "Ensure adequate rest and nutrition",
                ]
            else:
                urgency_level = "low"
                reasoning = (
                    "Mild fatigue is common and often related to lifestyle factors."
                )
                next_steps = [
                    "Ensure adequate sleep",
                    "Maintain healthy diet",
                    "Consider stress management techniques",
                ]

        # General severity-based assessment
        elif severity == "severe":
            urgency_level = "medium"
            reasoning = "Severe symptoms warrant medical evaluation."
            next_steps = [
                "Schedule appointment with healthcare provider",
                "Monitor symptoms closely",
                "Seek care if symptoms worsen",
            ]

        return {
            "level": urgency_level,
            "reasoning": reasoning,
            "next_steps": next_steps,
        }

    except Exception as e:
        logger.error(f"Error calculating urgency level: {e}")
        return {
            "level": "low",
            "reasoning": "Unable to determine urgency level",
            "next_steps": ["Consult healthcare provider"],
        }


async def _generate_personalized_recommendations(
    symptoms: List[str],
    query_analysis: Dict[str, Any],
    urgency_level: Dict[str, Any],
    include_vitals: bool,
    include_medications: bool,
) -> List[Dict[str, Any]]:
    """Generate personalized recommendations dynamically using AI models"""
    try:
        import openai

        # Base recommendations that are always relevant
        base_recommendations = [
            {
                "title": "Monitor Symptoms",
                "description": "Keep track of your symptoms, their frequency, and any triggers you notice.",
                "category": "monitoring",
                "priority": "high",
                "actionable": True,
                "evidence": ["Symptom tracking helps identify patterns"],
                "follow_up": "Log symptoms daily for the next week",
            }
        ]

        # Generate symptom-specific recommendations using AI
        symptom_text = " ".join(symptoms)
        query_type = query_analysis.get("query_type", "general_inquiry")
        urgency = urgency_level.get("level", "low")

        # Create prompt for AI to generate relevant recommendations
        prompt = f"""
        As a medical AI assistant, generate 3-5 personalized recommendations for a patient with the following symptoms: "{symptom_text}"

        Query type: {query_type}
        Urgency level: {urgency}
        Include vitals data: {include_vitals}
        Include medications data: {include_medications}

        Generate recommendations that:
        1. Are specific to the symptoms mentioned
        2. Include both immediate relief and long-term management strategies
        3. Are evidence-based and clinically sound
        4. Are actionable and practical
        5. Consider the urgency level appropriately

        Return the recommendations in this exact JSON format:
        {{
            "recommendations": [
                {{
                    "title": "Recommendation title",
                    "description": "Detailed description of the recommendation",
                    "category": "category_type",
                    "priority": "high/medium/low",
                    "actionable": true/false,
                    "evidence": ["evidence_point_1", "evidence_point_2"],
                    "follow_up": "Specific follow-up action"
                }}
            ]
        }}

        Categories can include: monitoring, lifestyle, symptom_relief, prevention, nutrition, hydration, medical, emergency
        Priorities should be: high (immediate action needed), medium (important but not urgent), low (general advice)
        """

        try:
            # Use OpenAI API to generate recommendations
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical AI assistant that generates personalized health recommendations. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            # Parse the AI response
            ai_response = response.choices[0].message.content.strip()

            # Extract JSON from the response
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0]
            elif "```" in ai_response:
                ai_response = ai_response.split("```")[1]

            ai_recommendations_data = json.loads(ai_response)
            ai_recommendations = ai_recommendations_data.get("recommendations", [])

            logger.info(
                f"Generated {len(ai_recommendations)} AI-powered recommendations for symptoms: {symptom_text}"
            )

        except Exception as ai_error:
            logger.error(f"Error generating AI recommendations: {ai_error}")
            # Fallback to basic recommendations if AI fails
            ai_recommendations = []

        # Add urgency-based recommendations
        urgency_recommendations = []
        if urgency_level["level"] == "high":
            urgency_recommendations.append(
                {
                    "title": "Seek Immediate Care",
                    "description": "This requires immediate medical attention. Please go to the emergency room or call emergency services.",
                    "category": "emergency",
                    "priority": "critical",
                    "actionable": True,
                    "evidence": ["Severe symptoms may indicate serious conditions"],
                    "follow_up": "Go to emergency room immediately",
                }
            )
        elif urgency_level["level"] == "medium":
            urgency_recommendations.append(
                {
                    "title": "Schedule Medical Evaluation",
                    "description": "These symptoms warrant medical evaluation. Please schedule an appointment with your healthcare provider.",
                    "category": "medical",
                    "priority": "high",
                    "actionable": True,
                    "evidence": [
                        "Medical evaluation can help identify underlying causes"
                    ],
                    "follow_up": "Schedule appointment within 1-2 weeks",
                }
            )

        # Combine all recommendations
        all_recommendations = (
            base_recommendations + ai_recommendations + urgency_recommendations
        )

        # Ensure unique titles
        seen_titles = set()
        unique_recommendations = []
        for recommendation in all_recommendations:
            if recommendation["title"] not in seen_titles:
                seen_titles.add(recommendation["title"])
                unique_recommendations.append(recommendation)

        logger.info(f"Total recommendations generated: {len(unique_recommendations)}")
        return unique_recommendations

    except Exception as e:
        logger.error(f"Error generating personalized recommendations: {e}")
        return [
            {
                "title": "Consult Healthcare Provider",
                "description": "Please consult with a healthcare provider for proper evaluation.",
                "category": "medical",
                "priority": "medium",
                "actionable": True,
                "evidence": [],
                "follow_up": "Schedule appointment with doctor",
            }
        ]


async def _analyze_health_query(query: str, context: str) -> Dict[str, Any]:
    """Analyze health query to determine type and appropriate response approach"""
    try:
        query_lower = (query + " " + context).lower()

        query_analysis = {
            "query_type": "general_inquiry",
            "category": "general",
            "medical_entities": [],
            "should_redirect_to_symptoms": False,
            "redirect_reason": "",
            "intent": "information_seeking",
        }

        # Check if this is a symptom-specific query that should use symptom analysis
        symptom_keywords = [
            "i have",
            "i'm experiencing",
            "i feel",
            "my",
            "suffering from",
            "having",
            "experiencing",
        ]
        if any(keyword in query_lower for keyword in symptom_keywords):
            query_analysis["query_type"] = "symptom_inquiry"
            query_analysis["category"] = "symptoms"
            query_analysis["should_redirect_to_symptoms"] = True
            query_analysis[
                "redirect_reason"
            ] = "This appears to be a symptom-specific query that would benefit from our comprehensive symptom analysis"
            query_analysis["intent"] = "symptom_assessment"

        # Check for specific query types
        elif any(
            word in query_lower
            for word in ["symptoms of", "signs of", "what are the symptoms"]
        ):
            query_analysis["query_type"] = "symptom_education"
            query_analysis["category"] = "education"
            query_analysis["intent"] = "learning_symptoms"
        elif any(
            word in query_lower for word in ["cause", "causes", "why", "what causes"]
        ):
            query_analysis["query_type"] = "causation_education"
            query_analysis["category"] = "education"
            query_analysis["intent"] = "understanding_causes"
        elif any(
            word in query_lower
            for word in ["treatment", "cure", "how to treat", "remedy"]
        ):
            query_analysis["query_type"] = "treatment_education"
            query_analysis["category"] = "education"
            query_analysis["intent"] = "seeking_treatment_info"
        elif any(
            word in query_lower
            for word in ["normal", "range", "what is normal", "healthy"]
        ):
            query_analysis["query_type"] = "normal_range_inquiry"
            query_analysis["category"] = "reference"
            query_analysis["intent"] = "understanding_norms"

        # Extract medical entities
        medical_entities = []
        if "diabetes" in query_lower:
            medical_entities.append(
                {"entity": "diabetes", "type": "condition", "category": "metabolic"}
            )
        if "blood pressure" in query_lower or "hypertension" in query_lower:
            medical_entities.append(
                {
                    "entity": "blood_pressure",
                    "type": "vital",
                    "category": "cardiovascular",
                }
            )
        if "heart rate" in query_lower or "pulse" in query_lower:
            medical_entities.append(
                {"entity": "heart_rate", "type": "vital", "category": "cardiovascular"}
            )
        if "headache" in query_lower:
            medical_entities.append(
                {"entity": "headache", "type": "symptom", "category": "neurological"}
            )

        query_analysis["medical_entities"] = medical_entities

        return query_analysis

    except Exception as e:
        logger.error(f"Error analyzing health query: {e}")
        return {
            "query_type": "general_inquiry",
            "category": "general",
            "medical_entities": [],
            "should_redirect_to_symptoms": False,
            "redirect_reason": "",
            "intent": "information_seeking",
        }


async def _generate_educational_content(
    query: str, query_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate educational content based on query type with dynamic AI-powered questions"""
    try:
        query_lower = query.lower()
        educational_content = {
            "related_topics": [],
            "follow_up_questions": [],
            "key_points": [],
            "resources": [],
        }

        # Generate dynamic follow-up questions using AI (this will be the default)
        dynamic_questions_generated = False
        logger.info(f"🔍 Starting dynamic question generation for query: '{query}'")
        if query.strip():  # Only generate questions if there's an actual query
            try:
                # Use the same dynamic question generation logic as symptom analysis
                symptoms = [
                    query
                ]  # Treat the query as a symptom for question generation
                include_vitals = True
                include_medications = True

                # Generate dynamic questions
                dynamic_questions = await _generate_follow_up_questions(
                    symptoms, query_analysis, include_vitals, include_medications
                )

                # Convert the structured questions to simple text format for educational content
                educational_content["follow_up_questions"] = [
                    question["question"]
                    for question in dynamic_questions[:5]  # Limit to 5 questions
                ]

                dynamic_questions_generated = True
                logger.info(
                    f"Generated {len(educational_content['follow_up_questions'])} dynamic questions for query: {query}"
                )

            except Exception as ai_error:
                logger.error(f"Error generating dynamic questions: {ai_error}")
                # Fallback to basic questions
                educational_content["follow_up_questions"] = [
                    "Would you like to learn more about this topic?",
                    "Do you have any specific concerns about your health?",
                    "Would you like to track your health data?",
                ]
        else:
            # If no query, use basic questions
            educational_content["follow_up_questions"] = [
                "Would you like to learn more about this topic?",
                "Do you have any specific concerns about your health?",
                "Would you like to track your health data?",
            ]

        # Generate content based on query type (but don't override dynamic questions)
        if query_analysis["query_type"] == "symptom_education":
            if "diabetes" in query_lower:
                educational_content["key_points"] = [
                    "Common symptoms include increased thirst, frequent urination, and fatigue",
                    "Early detection is crucial for effective management",
                    "Symptoms can develop gradually or appear suddenly",
                ]
                educational_content["related_topics"] = [
                    {
                        "topic": "Diabetes Management",
                        "relevance": "high",
                        "description": "Lifestyle changes and medical treatment options",
                    },
                    {
                        "topic": "Blood Sugar Monitoring",
                        "relevance": "high",
                        "description": "How to track and manage blood glucose levels",
                    },
                ]
                # Keep the dynamic questions that were generated above

        elif query_analysis["query_type"] == "normal_range_inquiry":
            if "blood pressure" in query_lower:
                educational_content["key_points"] = [
                    "Normal blood pressure is typically below 120/80 mmHg",
                    "Prehypertension ranges from 120-139/80-89 mmHg",
                    "Hypertension is 140/90 mmHg or higher",
                ]
                educational_content["related_topics"] = [
                    {
                        "topic": "Blood Pressure Management",
                        "relevance": "high",
                        "description": "Lifestyle changes to maintain healthy blood pressure",
                    }
                ]

        # Default educational content
        if not educational_content["key_points"]:
            educational_content["key_points"] = [
                "This information is for educational purposes only",
                "Consult with a healthcare provider for personalized medical advice",
                "Monitor your health regularly and report any concerns",
            ]
            educational_content["related_topics"] = [
                {
                    "topic": "Health Monitoring",
                    "relevance": "high",
                    "description": "Track your symptoms and vitals regularly",
                },
                {
                    "topic": "Lifestyle Factors",
                    "relevance": "medium",
                    "description": "Consider diet, exercise, and sleep patterns",
                },
            ]

        return educational_content

    except Exception as e:
        logger.error(f"Error generating educational content: {e}")
        return {
            "related_topics": [],
            "follow_up_questions": [
                "Would you like to learn more about this topic?",
                "Do you have any specific concerns about your health?",
                "Would you like to track your health data?",
            ],
            "key_points": [],
            "resources": [],
        }
