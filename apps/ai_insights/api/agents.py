"""
Agents API
RESTful API endpoints for AI agents.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.ai_insights.agents import (
    InsightGeneratorAgent,
    PatternDetectionAgent,
    RiskAssessmentAgent,
    TrendAnalysisAgent,
)
from common.database.connection import get_async_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

# Instantiate agents
_insight_generator = InsightGeneratorAgent()
_pattern_detector = PatternDetectionAgent()
_risk_assessor = RiskAssessmentAgent()
_trend_analyzer = TrendAnalysisAgent()


@router.get("/health")
async def health_check():
    """Health check endpoint for agents."""
    return {
        "service": "agents",
        "status": "healthy",
        "message": "Agents API is running",
    }


@router.post("/generate-insight")
async def generate_insight(
    data: dict,
    db: AsyncSession = Depends(get_async_db),
):
    """Generate AI insight using the InsightGeneratorAgent."""
    try:
        result = await _insight_generator.execute(data, db)
        return {
            "success": result.success,
            "agent": result.agent_name,
            "status": result.status,
            "insights": result.insights,
            "recommendations": result.recommendations,
            "data": result.data,
            "confidence_score": result.confidence_score,
            "execution_time_ms": result.execution_time_ms,
            "error": result.error,
        }
    except Exception as e:
        logger.error(f"Insight generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Insight generation failed: {str(e)}"
        )


@router.post("/detect-patterns")
async def detect_patterns(
    data: dict,
    db: AsyncSession = Depends(get_async_db),
):
    """Detect health patterns using the PatternDetectionAgent."""
    try:
        result = await _pattern_detector.execute(data, db)
        return {
            "success": result.success,
            "agent": result.agent_name,
            "status": result.status,
            "patterns": result.patterns,
            "data": result.data,
            "confidence_score": result.confidence_score,
            "execution_time_ms": result.execution_time_ms,
            "error": result.error,
        }
    except Exception as e:
        logger.error(f"Pattern detection failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Pattern detection failed: {str(e)}"
        )


@router.post("/assess-risk")
async def assess_risk(
    data: dict,
    db: AsyncSession = Depends(get_async_db),
):
    """Assess health risks using the RiskAssessmentAgent."""
    try:
        result = await _risk_assessor.execute(data, db)
        return {
            "success": result.success,
            "agent": result.agent_name,
            "status": result.status,
            "risks": result.risks,
            "insights": result.insights,
            "data": result.data,
            "confidence_score": result.confidence_score,
            "execution_time_ms": result.execution_time_ms,
            "error": result.error,
        }
    except Exception as e:
        logger.error(f"Risk assessment failed: {e}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")


@router.post("/analyze-trends")
async def analyze_trends(
    data: dict,
    db: AsyncSession = Depends(get_async_db),
):
    """Analyze health trends using the TrendAnalysisAgent."""
    try:
        result = await _trend_analyzer.execute(data, db)
        return {
            "success": result.success,
            "agent": result.agent_name,
            "status": result.status,
            "trends": result.trends,
            "insights": result.insights,
            "data": result.data,
            "confidence_score": result.confidence_score,
            "execution_time_ms": result.execution_time_ms,
            "error": result.error,
        }
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/status")
async def get_agents_status():
    """Get status of all AI agents."""
    statuses = {}
    for name, agent in [
        ("insight_generator", _insight_generator),
        ("pattern_detector", _pattern_detector),
        ("risk_assessor", _risk_assessor),
        ("trend_analyzer", _trend_analyzer),
    ]:
        statuses[name] = await agent.get_status()

    return {
        "service": "ai_agents",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": statuses,
    }
