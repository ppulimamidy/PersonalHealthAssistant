"""
Genetic counseling API endpoints for Personal Health Assistant.

This module provides endpoints for genetic counseling including:
- Counseling session management
- Risk report generation
- Educational materials
- Follow-up scheduling
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from common.database.connection import get_db
from common.middleware.auth import get_current_user
from apps.auth.models.user import User
from ..models.counseling import (
    GeneticCounseling, GeneticCounselingCreate, GeneticCounselingUpdate, GeneticCounselingResponse,
    CounselingSession, CounselingSessionCreate, CounselingSessionResponse,
    RiskReport, RiskReportCreate, RiskReportResponse,
    CounselingType, SessionStatus, ReportType, RiskCategory
)
from ..services.counseling_service import CounselingService

router = APIRouter()


# Genetic Counseling endpoints
@router.post("/", response_model=GeneticCounselingResponse, status_code=status.HTTP_201_CREATED)
async def create_counseling(
    counseling: GeneticCounselingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new genetic counseling session."""
    try:
        service = CounselingService(db)
        return await service.create_counseling(counseling, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[GeneticCounselingResponse])
async def list_counseling(
    skip: int = 0,
    limit: int = 100,
    counseling_type: Optional[CounselingType] = None,
    status: Optional[SessionStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List genetic counseling sessions for the current user."""
    try:
        service = CounselingService(db)
        return await service.list_counseling(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            counseling_type=counseling_type,
            status=status
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{counseling_id}", response_model=GeneticCounselingResponse)
async def get_counseling(
    counseling_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific genetic counseling by ID."""
    try:
        service = CounselingService(db)
        return await service.get_counseling(counseling_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{counseling_id}", response_model=GeneticCounselingResponse)
async def update_counseling(
    counseling_id: str,
    counseling: GeneticCounselingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update genetic counseling."""
    try:
        service = CounselingService(db)
        return await service.update_counseling(counseling_id, counseling, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{counseling_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_counseling(
    counseling_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete genetic counseling."""
    try:
        service = CounselingService(db)
        await service.delete_counseling(counseling_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Counseling Session endpoints
@router.post("/{counseling_id}/sessions", response_model=CounselingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_counseling_session(
    counseling_id: str,
    session: CounselingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new counseling session."""
    try:
        service = CounselingService(db)
        return await service.create_counseling_session(counseling_id, session, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{counseling_id}/sessions", response_model=List[CounselingSessionResponse])
async def list_counseling_sessions(
    counseling_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List counseling sessions for a specific counseling."""
    try:
        service = CounselingService(db)
        return await service.list_counseling_sessions(
            counseling_id=counseling_id,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}", response_model=CounselingSessionResponse)
async def get_counseling_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific counseling session by ID."""
    try:
        service = CounselingService(db)
        return await service.get_counseling_session(session_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/sessions/{session_id}", response_model=CounselingSessionResponse)
async def update_counseling_session(
    session_id: str,
    session: CounselingSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update counseling session."""
    try:
        service = CounselingService(db)
        return await service.update_counseling_session(session_id, session, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_counseling_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete counseling session."""
    try:
        service = CounselingService(db)
        await service.delete_counseling_session(session_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Risk Report endpoints
@router.post("/risk-reports", response_model=RiskReportResponse, status_code=status.HTTP_201_CREATED)
async def create_risk_report(
    report: RiskReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new risk report."""
    try:
        service = CounselingService(db)
        return await service.create_risk_report(report, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/risk-reports", response_model=List[RiskReportResponse])
async def list_risk_reports(
    skip: int = 0,
    limit: int = 100,
    report_type: Optional[ReportType] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List risk reports for the current user."""
    try:
        service = CounselingService(db)
        return await service.list_risk_reports(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            report_type=report_type
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/risk-reports/{report_id}", response_model=RiskReportResponse)
async def get_risk_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific risk report by ID."""
    try:
        service = CounselingService(db)
        return await service.get_risk_report(report_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/risk-reports/{report_id}", response_model=RiskReportResponse)
async def update_risk_report(
    report_id: str,
    report: RiskReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update risk report."""
    try:
        service = CounselingService(db)
        return await service.update_risk_report(report_id, report, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/risk-reports/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_risk_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete risk report."""
    try:
        service = CounselingService(db)
        await service.delete_risk_report(report_id, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Additional counseling endpoints
@router.get("/educational-materials", response_model=List[dict])
async def get_educational_materials(
    topic: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get educational materials for genetic counseling."""
    try:
        service = CounselingService(db)
        return await service.get_educational_materials(
            user_id=current_user.id,
            topic=topic
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recommendations", response_model=List[dict])
async def get_counseling_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized counseling recommendations."""
    try:
        service = CounselingService(db)
        return await service.get_counseling_recommendations(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/schedule-followup", response_model=GeneticCounselingResponse)
async def schedule_followup(
    counseling_id: str,
    followup_date: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule follow-up counseling session."""
    try:
        service = CounselingService(db)
        return await service.schedule_followup(
            counseling_id=counseling_id,
            user_id=current_user.id,
            followup_date=followup_date
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/counselors", response_model=List[dict])
async def get_available_counselors(
    specialization: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available genetic counselors."""
    try:
        service = CounselingService(db)
        return await service.get_available_counselors(
            user_id=current_user.id,
            specialization=specialization
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export-report", response_model=dict)
async def export_counseling_report(
    counseling_id: str,
    format: str = "pdf",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export counseling report."""
    try:
        service = CounselingService(db)
        return await service.export_counseling_report(
            counseling_id=counseling_id,
            user_id=current_user.id,
            format=format
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/statistics", response_model=dict)
async def get_counseling_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get counseling statistics for the user."""
    try:
        service = CounselingService(db)
        return await service.get_counseling_statistics(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 