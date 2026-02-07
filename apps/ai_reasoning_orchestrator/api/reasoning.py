"""
Core reasoning router for AI Reasoning Orchestrator.
Handles the main reasoning endpoints: /api/v1/reason, /api/v1/query,
/api/v1/insights/daily-summary, and /api/v1/doctor-mode/report.
"""

import time
import json
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Depends

from common.middleware.auth import require_auth
from common.models.base import create_success_response
from common.utils.logging import get_logger
from ..models.reasoning_models import HealthQuery, ReasoningRequest, ReasoningResponse

logger = get_logger(__name__)

router = APIRouter()


async def perform_reasoning(
    request: Request, reasoning_request: ReasoningRequest, current_user: Dict[str, Any]
) -> ReasoningResponse:
    """
    Core reasoning function used by multiple endpoints.

    Aggregates data from all microservices, integrates medical knowledge,
    and provides explainable reasoning with actionable insights.
    """
    try:
        start_time = time.time()
        user_id = current_user["id"]

        logger.info(
            f"🧠 Processing reasoning request for user {user_id}: {reasoning_request.query}"
        )

        # Check Redis cache first
        redis_client = getattr(request.app.state, "redis_client", None)
        cache_key = f"reasoning:{user_id}:{hash(reasoning_request.query)}"

        if redis_client:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    logger.info("✅ Cache hit for reasoning request")
                    cached_data = json.loads(cached)
                    return ReasoningResponse(**cached_data)
            except Exception as cache_err:
                logger.warning(f"⚠️ Redis cache read failed: {cache_err}")

        # Step 1: Aggregate user data from all services
        user_data = await request.app.state.data_aggregator.aggregate_user_data(
            user_id=user_id,
            time_window=reasoning_request.time_window,
            data_types=reasoning_request.data_types,
        )

        # Step 2: Integrate medical knowledge
        knowledge_context = (
            await request.app.state.knowledge_integrator.get_relevant_knowledge(
                query=reasoning_request.query, user_context=user_data
            )
        )

        # Step 3: Generate reasoning and insights
        reasoning_result = await request.app.state.reasoning_engine.reason(
            query=reasoning_request.query,
            user_data=user_data,
            knowledge_context=knowledge_context,
            reasoning_type=reasoning_request.reasoning_type,
        )

        processing_time = time.time() - start_time

        response = ReasoningResponse(
            query=reasoning_request.query,
            reasoning=reasoning_result.get("reasoning", "No reasoning available"),
            insights=reasoning_result.get("insights", []),
            recommendations=reasoning_result.get("recommendations", []),
            evidence=reasoning_result.get("evidence", {}),
            confidence=reasoning_result.get("confidence", "low"),
            processing_time=processing_time,
            data_sources=reasoning_result.get("data_sources", []),
        )

        # Step 4: Cache result for future reference
        if redis_client:
            try:
                await redis_client.setex(
                    cache_key, 3600, response.json()  # 1 hour cache
                )
            except Exception as cache_err:
                logger.warning(f"⚠️ Redis cache write failed: {cache_err}")

        logger.info(f"✅ Reasoning completed in {processing_time:.2f}s")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Reasoning failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reasoning failed: {str(e)}")


# Core reasoning endpoint - the main PPA interface
@router.post("/api/v1/reason", response_model=ReasoningResponse)
async def reason_about_health(
    request: Request,
    reasoning_request: ReasoningRequest,
    current_user: Dict[str, Any] = Depends(require_auth),
):
    """
    Main reasoning endpoint - answers health questions using all available data.

    This is the core PPA interface that:
    1. Aggregates data from all microservices
    2. Integrates medical knowledge
    3. Provides explainable reasoning
    4. Returns actionable insights
    """
    return await perform_reasoning(request, reasoning_request, current_user)


# Natural language query endpoint
@router.post("/api/v1/query")
async def natural_language_query(
    request: Request,
    query: HealthQuery,
    current_user: Dict[str, Any] = Depends(require_auth),
):
    """
    Natural language health query endpoint.

    Accepts questions like:
    - "Why do I feel tired today?"
    - "What's causing my headache?"
    - "How does my blood pressure relate to my diet?"
    """
    try:
        # Convert natural language to reasoning request
        reasoning_request = ReasoningRequest(
            query=query.question,
            reasoning_type="symptom_analysis",
            time_window=query.time_window or "24h",
            data_types=["vitals", "symptoms", "medications", "nutrition", "sleep"],
        )

        # Use the core reasoning function
        return await perform_reasoning(request, reasoning_request, current_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Natural language query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


# Daily insights summary endpoint
@router.get("/api/v1/insights/daily-summary")
async def get_daily_insights_summary(
    request: Request, current_user: Dict[str, Any] = Depends(require_auth)
):
    """
    Generate daily health insights summary.

    Provides a comprehensive overview of the user's health status,
    trends, and recommendations for the day.
    """
    try:
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
        return await perform_reasoning(request, reasoning_request, current_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Daily insights summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Daily summary failed: {str(e)}")


# Doctor mode report endpoint
@router.post("/api/v1/doctor-mode/report")
async def generate_doctor_report(
    request: Request,
    report_request: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(require_auth),
):
    """
    Generate comprehensive doctor mode report.

    Creates a detailed health report suitable for sharing with healthcare providers,
    including trends, patterns, and clinical insights.
    """
    try:
        user_id = current_user["id"]

        # Create reasoning request for doctor report
        reasoning_request = ReasoningRequest(
            query="Generate comprehensive doctor mode report",
            reasoning_type="doctor_report",
            time_window=report_request.get("time_window", "30d"),
            data_types=[
                "vitals",
                "symptoms",
                "medications",
                "nutrition",
                "sleep",
                "activity",
                "lab_results",
            ],
        )

        # Use the core reasoning function
        reasoning_result = await perform_reasoning(
            request, reasoning_request, current_user
        )

        # Format for doctor mode
        doctor_report = {
            "patient_id": user_id,
            "report_date": datetime.utcnow().isoformat(),
            "time_period": report_request.get("time_window", "30d"),
            "summary": reasoning_result.reasoning,
            "key_insights": reasoning_result.insights,
            "recommendations": reasoning_result.recommendations,
            "trends": reasoning_result.evidence.get("trends", []),
            "anomalies": reasoning_result.evidence.get("anomalies", []),
            "data_quality": reasoning_result.evidence.get("data_quality", {}),
            "confidence_score": reasoning_result.confidence,
        }

        return create_success_response(
            data=doctor_report, message="Doctor mode report generated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Doctor mode report failed: {e}")
        raise HTTPException(status_code=500, detail=f"Doctor report failed: {str(e)}")
