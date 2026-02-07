"""
GDPR API endpoints for the Personal Health Assistant Consent Audit Service.

This module provides comprehensive GDPR endpoints including:
- GDPR compliance monitoring
- Data subject rights management
- Data processing impact assessments
- GDPR audit trails
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.utils.logging import get_logger

from models.audit import (
    AuditEventType,
    AuditSeverity,
    ConsentAuditLogCreate,
)
from services.audit_service import (
    get_compliance_status,
    get_audit_logs,
    get_audit_summary,
    get_consent_status,
    create_audit_log,
)


class GDPRRightExerciseRequest(BaseModel):
    user_id: UUID
    right_type: str
    description: str
    data_categories: Optional[List[str]] = None
    details: Optional[Dict[str, Any]] = None


logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """Extract user ID from JWT token."""
    try:
        return UUID("00000000-0000-0000-0000-000000000000")  # Placeholder
    except Exception as e:
        logger.error(f"Failed to get current user ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


# ---------------------------------------------------------------------------
# GDPR Compliance Status
# ---------------------------------------------------------------------------


@router.get("/compliance/status")
async def get_gdpr_compliance_status(
    user_id: Optional[UUID] = Query(None, description="User ID to check"),
    db: AsyncSession = Depends(get_async_db),
):
    """Get comprehensive GDPR compliance status."""
    try:
        gdpr_status = await get_compliance_status(db, framework="gdpr", user_id=user_id)

        gdpr_compliant = gdpr_status.get("gdpr_compliant", True)

        # Augment with GDPR-specific principles
        gdpr_status["principles"] = {
            "lawfulness_fairness_transparency": gdpr_compliant,
            "purpose_limitation": gdpr_compliant,
            "data_minimization": gdpr_compliant,
            "accuracy": gdpr_compliant,
            "storage_limitation": gdpr_compliant,
            "integrity_confidentiality": gdpr_compliant,
            "accountability": gdpr_compliant,
        }
        gdpr_status["data_subject_rights"] = {
            "right_to_access": True,
            "right_to_rectification": True,
            "right_to_erasure": True,
            "right_to_portability": True,
            "right_to_restriction": True,
            "right_to_object": True,
            "right_to_withdraw_consent": True,
        }

        return gdpr_status
    except Exception as e:
        logger.error(f"Failed to get GDPR compliance status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get GDPR compliance status: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Data Subject Rights
# ---------------------------------------------------------------------------


@router.get("/data-subject-rights/{user_id}")
async def get_gdpr_data_subject_rights(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get GDPR data subject rights for a user."""
    try:
        consents = await get_consent_status(db, user_id)
        has_active = any(c.granted and c.revoked_at is None for c in consents)

        return {
            "user_id": str(user_id),
            "has_active_consent": has_active,
            "total_consent_records": len(consents),
            "rights": {
                "right_to_access": {
                    "available": True,
                    "description": "Right to access personal data",
                    "processing_time": "30 days",
                },
                "right_to_rectification": {
                    "available": True,
                    "description": "Right to correct inaccurate data",
                    "processing_time": "30 days",
                },
                "right_to_erasure": {
                    "available": True,
                    "description": "Right to be forgotten",
                    "processing_time": "30 days",
                },
                "right_to_portability": {
                    "available": True,
                    "description": "Right to data portability",
                    "processing_time": "30 days",
                },
                "right_to_restriction": {
                    "available": True,
                    "description": "Right to restrict processing",
                    "processing_time": "30 days",
                },
                "right_to_object": {
                    "available": True,
                    "description": "Right to object to processing",
                    "processing_time": "30 days",
                },
                "right_to_withdraw_consent": {
                    "available": True,
                    "description": "Right to withdraw consent",
                    "processing_time": "Immediate",
                },
            },
            "data_categories": [
                "personal_information",
                "health_data",
                "device_data",
                "usage_data",
                "preferences",
                "biometric_data",
                "location_data",
            ],
            "processing_purposes": [
                "health_monitoring",
                "personalization",
                "analytics",
                "research",
                "improvement",
                "marketing",
            ],
            "legal_basis": [
                "consent",
                "contract",
                "legal_obligation",
                "vital_interests",
                "public_task",
                "legitimate_interests",
            ],
        }
    except Exception as e:
        logger.error(f"Failed to get GDPR data subject rights for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get GDPR data subject rights: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Exercise GDPR Right
# ---------------------------------------------------------------------------


@router.post("/exercise-right")
async def exercise_gdpr_right(
    request: Request,
    exercise_request: GDPRRightExerciseRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """Exercise a GDPR data subject right."""
    try:
        logger.info(
            f"User {exercise_request.user_id} exercising GDPR right: {exercise_request.right_type}"
        )

        # Map right type to audit event type
        event_type_map = {
            "right_to_access": AuditEventType.RIGHT_TO_ACCESS,
            "right_to_rectification": AuditEventType.RIGHT_TO_RECTIFICATION,
            "right_to_erasure": AuditEventType.RIGHT_TO_ERASURE,
            "right_to_portability": AuditEventType.RIGHT_TO_PORTABILITY,
            "right_to_restriction": AuditEventType.RIGHT_TO_RESTRICTION,
            "right_to_object": AuditEventType.RIGHT_TO_OBJECT,
        }
        event_type = event_type_map.get(
            exercise_request.right_type, AuditEventType.DATA_ACCESS
        )

        request_id = uuid4()

        audit_data = ConsentAuditLogCreate(
            user_id=exercise_request.user_id,
            event_type=event_type,
            event_description=exercise_request.description,
            actor_id=exercise_request.user_id,
            actor_type="user",
            severity=AuditSeverity.MEDIUM,
            event_data={
                "right_type": exercise_request.right_type,
                "data_categories": exercise_request.data_categories or [],
                "details": exercise_request.details or {},
                "request_id": str(request_id),
                "regulation": "GDPR",
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        await create_audit_log(db, audit_data)
        await db.commit()

        return {
            "gdpr_right_exercised": exercise_request.right_type,
            "status": "processing",
            "request_id": str(request_id),
            "estimated_completion": (
                datetime.utcnow() + timedelta(days=30)
            ).isoformat(),
            "user_id": str(exercise_request.user_id),
            "description": exercise_request.description,
            "data_categories": exercise_request.data_categories or [],
            "details": exercise_request.details or {},
            "timestamp": datetime.utcnow().isoformat(),
            "regulation": "GDPR",
        }
    except Exception as e:
        await db.rollback()
        logger.error(
            f"Failed to exercise GDPR right {exercise_request.right_type} "
            f"for user {exercise_request.user_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to exercise GDPR right: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Data Processing Impact Assessment (DPIA)
# ---------------------------------------------------------------------------


@router.get("/data-processing-impact")
async def get_data_processing_impact_assessment(
    user_id: Optional[UUID] = Query(None, description="User ID to check"),
    processing_purpose: Optional[str] = Query(
        None, description="Processing purpose to assess"
    ),
    db: AsyncSession = Depends(get_async_db),
):
    """Get data processing impact assessment for GDPR compliance."""
    try:
        summary = await get_audit_summary(db, user_id=user_id)

        score = summary.compliance_score
        risk_level = "low" if score >= 90 else ("medium" if score >= 70 else "high")

        return {
            "assessment_id": str(uuid4()),
            "user_id": str(user_id) if user_id else "system-wide",
            "processing_purpose": processing_purpose or "health_monitoring",
            "assessment_date": datetime.utcnow().isoformat(),
            "risk_level": risk_level,
            "gdpr_compliant": score >= 90,
            "compliance_score": score,
            "total_events_assessed": summary.total_events,
            "assessment_results": {
                "necessity": {
                    "score": min(10, round(score / 10)),
                    "description": "Processing is necessary for health monitoring",
                    "compliant": True,
                },
                "proportionality": {
                    "score": min(10, round(score / 10)),
                    "description": "Processing is proportional to the purpose",
                    "compliant": True,
                },
                "data_minimization": {
                    "score": min(10, round(score / 10)),
                    "description": "Only necessary data is processed",
                    "compliant": True,
                },
                "security": {
                    "score": 10
                    if summary.security_incidents == 0
                    else max(1, 10 - summary.security_incidents),
                    "description": "Appropriate security measures in place",
                    "compliant": summary.security_incidents == 0,
                },
                "transparency": {
                    "score": min(10, round(score / 10)),
                    "description": "Processing is transparent to data subjects",
                    "compliant": True,
                },
            },
            "recommendations": [
                "Continue monitoring data processing activities",
                "Regular review of consent mechanisms",
                "Periodic security assessments",
            ],
        }
    except Exception as e:
        logger.error(f"Failed to get data processing impact assessment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data processing impact assessment: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Breach Notification
# ---------------------------------------------------------------------------


@router.get("/breach-notification")
async def get_breach_notification_status(
    user_id: Optional[UUID] = Query(None, description="User ID to check"),
    db: AsyncSession = Depends(get_async_db),
):
    """Get GDPR breach notification status and requirements."""
    try:
        summary = await get_audit_summary(db, user_id=user_id)

        return {
            "user_id": str(user_id) if user_id else "system-wide",
            "breaches_detected": summary.data_breaches,
            "notifications_required": summary.data_breaches,
            "notifications_sent": 0,
            "gdpr_compliant": summary.data_breaches == 0,
            "notification_timeline": {
                "detection_to_assessment": "72 hours",
                "assessment_to_notification": "72 hours",
                "total_timeline": "72 hours",
            },
            "notification_requirements": {
                "supervisory_authority": True,
                "data_subjects": True,
                "documentation": True,
            },
            "last_assessment": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get breach notification status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get breach notification status: {str(e)}",
        )


# ---------------------------------------------------------------------------
# GDPR Requests
# ---------------------------------------------------------------------------


@router.get("/requests/{user_id}")
async def get_gdpr_requests(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get GDPR-related requests for a user (right-exercise audit logs)."""
    try:
        # Fetch audit logs that represent right-exercise events
        right_types = [
            AuditEventType.RIGHT_TO_ACCESS,
            AuditEventType.RIGHT_TO_RECTIFICATION,
            AuditEventType.RIGHT_TO_ERASURE,
            AuditEventType.RIGHT_TO_PORTABILITY,
            AuditEventType.RIGHT_TO_RESTRICTION,
            AuditEventType.RIGHT_TO_OBJECT,
        ]

        all_requests: list = []
        for evt in right_types:
            logs = await get_audit_logs(
                db, user_id=user_id, event_type=evt, skip=0, limit=1000
            )
            for log in logs:
                all_requests.append(
                    {
                        "request_id": str(log.id),
                        "request_type": log.event_type,
                        "status": "processing",
                        "submitted_date": log.event_timestamp.isoformat(),
                        "description": log.event_description,
                        "data_categories": log.event_data.get("data_categories", [])
                        if log.event_data
                        else [],
                        "gdpr_article": _right_to_article(log.event_type),
                    }
                )

        all_requests.sort(key=lambda x: x["submitted_date"], reverse=True)

        return {
            "user_id": str(user_id),
            "total_requests": len(all_requests),
            "requests": all_requests,
            "last_updated": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get GDPR requests for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get GDPR requests: {str(e)}",
        )


def _right_to_article(event_type: str) -> str:
    """Map event type to GDPR article."""
    mapping = {
        "right_to_access": "Article 15",
        "right_to_rectification": "Article 16",
        "right_to_erasure": "Article 17",
        "right_to_portability": "Article 20",
        "right_to_restriction": "Article 18",
        "right_to_object": "Article 21",
    }
    return mapping.get(event_type, "Article 7")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health")
async def gdpr_health_check():
    """Health check for GDPR service."""
    return {
        "status": "healthy",
        "service": "gdpr",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "gdpr_compliance_monitoring",
            "data_subject_rights_management",
            "data_processing_impact_assessment",
            "breach_notification_tracking",
            "gdpr_audit_trails",
            "gdpr_requests_tracking",
        ],
    }
