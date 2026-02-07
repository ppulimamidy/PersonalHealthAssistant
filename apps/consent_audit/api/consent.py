"""
Consent API endpoints for the Personal Health Assistant Consent Audit Service.

This module provides comprehensive consent endpoints including:
- Consent record creation and management
- Consent verification
- Consent status tracking
- Data subject rights management
- Consent history
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.utils.logging import get_logger

from models.audit import (
    ConsentRecordCreate,
    ConsentRecordResponse,
    ConsentAuditLogCreate,
    ConsentAuditLogResponse,
    AuditEventType,
    AuditSeverity,
)
from services.audit_service import (
    create_consent,
    get_consent_status,
    get_consent_record,
    revoke_consent,
    create_audit_log,
    get_audit_logs,
)

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
# Consent Verification
# ---------------------------------------------------------------------------


@router.post("/verify")
async def verify_consent(
    request: Request,
    user_id: UUID,
    consent_record_id: Optional[UUID] = None,
    data_categories: Optional[List[str]] = None,
    processing_purpose: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """Verify consent for data processing."""
    try:
        logger.info(f"Verifying consent for user {user_id}")

        consents = await get_consent_status(db, user_id)
        active = [c for c in consents if c.granted and c.revoked_at is None]

        issues: List[str] = []
        recommendations: List[str] = []

        if not active:
            issues.append("No active consent records found")
            recommendations.append("Obtain valid consent before processing")

        if consent_record_id:
            matching = [c for c in active if c.id == consent_record_id]
            if not matching:
                issues.append(
                    f"Consent record {consent_record_id} not found or revoked"
                )

        is_compliant = len(issues) == 0

        return {
            "consent_verified": is_compliant,
            "verification_result": {
                "is_compliant": is_compliant,
                "gdpr_compliant": is_compliant,
                "hipaa_compliant": is_compliant,
                "missing_consents": [],
                "compliance_issues": issues,
                "recommendations": recommendations,
            },
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user_id),
            "consent_record_id": str(consent_record_id) if consent_record_id else None,
        }
    except Exception as e:
        logger.error(f"Failed to verify consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify consent: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Consent Status
# ---------------------------------------------------------------------------


@router.get("/status/{user_id}")
async def get_consent_status_endpoint(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get consent status for a user."""
    try:
        consents = await get_consent_status(db, user_id)

        active = sum(
            1
            for c in consents
            if c.granted
            and c.revoked_at is None
            and (c.expires_at is None or c.expires_at > datetime.utcnow())
        )
        expired = sum(
            1 for c in consents if c.expires_at and c.expires_at <= datetime.utcnow()
        )
        withdrawn = sum(1 for c in consents if c.revoked_at is not None)
        pending = sum(1 for c in consents if not c.granted and c.revoked_at is None)

        return {
            "user_id": str(user_id),
            "consent_status": {
                "active_consents": active,
                "expired_consents": expired,
                "withdrawn_consents": withdrawn,
                "pending_consents": pending,
            },
            "compliance_status": {
                "gdpr_compliant": active > 0,
                "hipaa_compliant": active > 0,
                "overall_compliant": active > 0,
            },
            "consents": [c.model_dump() for c in consents],
            "recommendations": []
            if active > 0
            else ["No active consent – obtain consent before processing"],
        }
    except Exception as e:
        logger.error(f"Failed to get consent status for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consent status: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Consent Record CRUD
# ---------------------------------------------------------------------------


@router.post("/records", response_model=ConsentRecordResponse)
async def create_consent_record(
    request: Request,
    consent_data: ConsentRecordCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new consent record."""
    try:
        logger.info(f"Creating consent record for user {consent_data.user_id}")
        result = await create_consent(db, consent_data)

        # Also create an audit log for the consent grant
        audit_data = ConsentAuditLogCreate(
            user_id=consent_data.user_id,
            event_type=AuditEventType.CONSENT_GRANTED,
            event_description=f"Consent granted: {consent_data.consent_type} for {consent_data.purpose}",
            actor_id=consent_data.user_id,
            actor_type="user",
            consent_record_id=result.id,
            severity=AuditSeverity.LOW,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        await create_audit_log(db, audit_data)
        await db.commit()

        logger.info(f"Successfully created consent record {result.id}")
        return result
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create consent record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create consent record: {str(e)}",
        )


@router.post("/records/{consent_id}/revoke", response_model=ConsentRecordResponse)
async def revoke_consent_endpoint(
    consent_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """Revoke a consent record."""
    try:
        logger.info(f"Revoking consent record {consent_id}")
        result = await revoke_consent(db, consent_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Consent record {consent_id} not found",
            )

        # Also create an audit log for the revocation
        audit_data = ConsentAuditLogCreate(
            user_id=result.user_id,
            event_type=AuditEventType.CONSENT_WITHDRAWN,
            event_description=f"Consent revoked: {result.consent_type} for {result.purpose}",
            actor_id=result.user_id,
            actor_type="user",
            consent_record_id=consent_id,
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        await create_audit_log(db, audit_data)
        await db.commit()

        logger.info(f"Successfully revoked consent record {consent_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to revoke consent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke consent: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Data Subject Rights
# ---------------------------------------------------------------------------


@router.get("/rights/{user_id}")
async def get_data_subject_rights(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get data subject rights information for a user."""
    try:
        consents = await get_consent_status(db, user_id)
        has_active = any(c.granted and c.revoked_at is None for c in consents)

        return {
            "user_id": str(user_id),
            "rights": {
                "right_to_access": {
                    "available": True,
                    "description": "Right to access personal data",
                },
                "right_to_rectification": {
                    "available": True,
                    "description": "Right to correct inaccurate data",
                },
                "right_to_erasure": {
                    "available": True,
                    "description": "Right to be forgotten",
                },
                "right_to_portability": {
                    "available": True,
                    "description": "Right to data portability",
                },
                "right_to_restriction": {
                    "available": True,
                    "description": "Right to restrict processing",
                },
                "right_to_object": {
                    "available": True,
                    "description": "Right to object to processing",
                },
            },
            "has_active_consent": has_active,
            "total_consent_records": len(consents),
        }
    except Exception as e:
        logger.error(f"Failed to get data subject rights for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data subject rights: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Exercise Data Subject Right
# ---------------------------------------------------------------------------


@router.post("/exercise-right")
async def exercise_data_subject_right(
    request: Request,
    user_id: UUID,
    right_type: str,
    description: str,
    data_categories: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """Exercise a data subject right."""
    try:
        logger.info(f"User {user_id} exercising right: {right_type}")

        # Map right type to audit event type
        event_type_map = {
            "right_to_access": AuditEventType.RIGHT_TO_ACCESS,
            "right_to_rectification": AuditEventType.RIGHT_TO_RECTIFICATION,
            "right_to_erasure": AuditEventType.RIGHT_TO_ERASURE,
            "right_to_portability": AuditEventType.RIGHT_TO_PORTABILITY,
            "right_to_restriction": AuditEventType.RIGHT_TO_RESTRICTION,
            "right_to_object": AuditEventType.RIGHT_TO_OBJECT,
        }
        event_type = event_type_map.get(right_type, AuditEventType.DATA_ACCESS)

        request_id = uuid4()

        audit_data = ConsentAuditLogCreate(
            user_id=user_id,
            event_type=event_type,
            event_description=description,
            actor_id=user_id,
            actor_type="user",
            severity=AuditSeverity.MEDIUM,
            event_data={
                "right_type": right_type,
                "data_categories": data_categories or [],
                "request_id": str(request_id),
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        await create_audit_log(db, audit_data)
        await db.commit()

        return {
            "right_exercised": right_type,
            "status": "processing",
            "request_id": str(request_id),
            "estimated_completion": (
                datetime.utcnow() + timedelta(days=30)
            ).isoformat(),
            "user_id": str(user_id),
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to exercise right {right_type} for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to exercise right: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Consent History
# ---------------------------------------------------------------------------


@router.get("/history/{user_id}")
async def get_consent_history(
    user_id: UUID,
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_async_db),
):
    """Get consent history for a user (audit logs filtered to consent events)."""
    try:
        consent_event_types = [
            AuditEventType.CONSENT_GRANTED,
            AuditEventType.CONSENT_WITHDRAWN,
            AuditEventType.CONSENT_EXPIRED,
            AuditEventType.CONSENT_MODIFIED,
        ]

        # Fetch all consent-related audit logs for the user
        all_logs: List[ConsentAuditLogResponse] = []
        for evt in consent_event_types:
            logs = await get_audit_logs(
                db,
                user_id=user_id,
                event_type=evt,
                start_date=start_date,
                end_date=end_date,
                skip=0,
                limit=1000,
            )
            all_logs.extend(logs)

        # Sort by timestamp descending, paginate
        all_logs.sort(key=lambda x: x.event_timestamp, reverse=True)
        paginated = all_logs[offset : offset + limit]

        return {
            "user_id": str(user_id),
            "consent_history": [l.model_dump() for l in paginated],
            "total_events": len(all_logs),
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }
    except Exception as e:
        logger.error(f"Failed to get consent history for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get consent history: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health")
async def consent_health_check():
    """Health check for consent service."""
    return {
        "status": "healthy",
        "service": "consent",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "consent_verification",
            "consent_status_tracking",
            "data_subject_rights",
            "consent_history",
            "right_exercise_processing",
        ],
    }
