"""
Audit API endpoints for the Personal Health Assistant Consent Audit Service.

This module provides comprehensive audit endpoints including:
- Consent audit logging
- Data processing audits
- Compliance monitoring
- Risk assessment
- Audit trail generation
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.middleware.rate_limiter import rate_limit
from common.middleware.security import security_headers
from common.utils.logging import get_logger

from models.audit import (
    AuditEventType,
    AuditSeverity,
    ComplianceStatus,
    DataProcessingPurpose,
    ConsentAuditLogCreate,
    ConsentAuditLogUpdate,
    ConsentAuditLogResponse,
    DataProcessingAuditCreate,
    DataProcessingAuditUpdate,
    DataProcessingAuditResponse,
    ComplianceReportCreate,
    ComplianceReportUpdate,
    ComplianceReportResponse,
    AuditSummary,
)
from services.audit_service import (
    create_audit_log,
    get_audit_log,
    get_audit_logs,
    get_compliance_violations,
    get_high_risk_events,
    get_audit_summary,
    create_data_processing_audit,
    get_data_processing_audits,
)

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """Extract user ID from JWT token."""
    try:
        # Placeholder – in production this validates the JWT and extracts the sub claim
        return UUID("00000000-0000-0000-0000-000000000000")
    except Exception as e:
        logger.error(f"Failed to get current user ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


# ---------------------------------------------------------------------------
# Audit Log endpoints
# ---------------------------------------------------------------------------


@router.post("/logs", response_model=ConsentAuditLogResponse)
@rate_limit(requests_per_minute=60)
@security_headers
async def create_audit_log_endpoint(
    request: Request,
    audit_data: ConsentAuditLogCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new consent audit log entry."""
    try:
        logger.info(f"Creating audit log for user {audit_data.user_id}")
        # Enrich with request metadata if not provided
        if not audit_data.ip_address and request.client:
            audit_data.ip_address = request.client.host
        if not audit_data.user_agent:
            audit_data.user_agent = request.headers.get("user-agent")

        result = await create_audit_log(db, audit_data)
        await db.commit()
        logger.info(f"Successfully created audit log {result.id}")
        return result
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create audit log: {str(e)}",
        )


@router.get("/logs/{audit_id}", response_model=ConsentAuditLogResponse)
@security_headers
async def get_audit_log_endpoint(
    audit_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    """Get a specific audit log by ID."""
    try:
        result = await get_audit_log(db, audit_id)
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Audit log {audit_id} not found",
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit log {audit_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit log: {str(e)}",
        )


@router.get("/logs/user/{user_id}", response_model=List[ConsentAuditLogResponse])
@security_headers
async def get_user_audit_logs_endpoint(
    user_id: UUID,
    event_type: Optional[AuditEventType] = Query(
        None, description="Filter by event type"
    ),
    severity: Optional[AuditSeverity] = Query(
        None, description="Filter by severity level"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_async_db),
):
    """Get audit logs for a specific user with filtering."""
    try:
        return await get_audit_logs(
            db,
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            start_date=start_date,
            end_date=end_date,
            skip=offset,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Failed to get audit logs for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit logs: {str(e)}",
        )


@router.get("/logs/my", response_model=List[ConsentAuditLogResponse])
@security_headers
async def get_my_audit_logs_endpoint(
    event_type: Optional[AuditEventType] = Query(
        None, description="Filter by event type"
    ),
    severity: Optional[AuditSeverity] = Query(
        None, description="Filter by severity level"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_db),
):
    """Get audit logs for the current user."""
    try:
        return await get_audit_logs(
            db,
            user_id=current_user_id,
            event_type=event_type,
            severity=severity,
            start_date=start_date,
            end_date=end_date,
            skip=offset,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Failed to get audit logs for current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit logs: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Violations & High-Risk
# ---------------------------------------------------------------------------


@router.get("/violations", response_model=List[ConsentAuditLogResponse])
@security_headers
async def get_compliance_violations_endpoint(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: AsyncSession = Depends(get_async_db),
):
    """Get all compliance violations."""
    try:
        return await get_compliance_violations(
            db, user_id=user_id, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        logger.error(f"Failed to get compliance violations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance violations: {str(e)}",
        )


@router.get("/high-risk", response_model=List[ConsentAuditLogResponse])
@security_headers
async def get_high_risk_events_endpoint(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    db: AsyncSession = Depends(get_async_db),
):
    """Get all high-risk audit events."""
    try:
        return await get_high_risk_events(
            db, user_id=user_id, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        logger.error(f"Failed to get high-risk events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get high-risk events: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Data Processing Audit
# ---------------------------------------------------------------------------


@router.post("/processing", response_model=DataProcessingAuditResponse)
@rate_limit(requests_per_minute=30)
@security_headers
async def create_data_processing_audit_endpoint(
    request: Request,
    audit_data: DataProcessingAuditCreate,
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new data processing audit entry."""
    try:
        logger.info(f"Creating data processing audit for user {audit_data.user_id}")
        result = await create_data_processing_audit(db, audit_data)
        await db.commit()
        logger.info(f"Successfully created data processing audit {result.id}")
        return result
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to create data processing audit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create data processing audit: {str(e)}",
        )


@router.get("/processing", response_model=List[DataProcessingAuditResponse])
@security_headers
async def get_data_processing_audits_endpoint(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    purpose: Optional[DataProcessingPurpose] = Query(
        None, description="Filter by processing purpose"
    ),
    compliance_status: Optional[ComplianceStatus] = Query(
        None, description="Filter by compliance status"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Start date for filtering"
    ),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_async_db),
):
    """Get data processing audits with filtering."""
    try:
        return await get_data_processing_audits(
            db,
            user_id=user_id,
            purpose=purpose,
            compliance_status=compliance_status,
            start_date=start_date,
            end_date=end_date,
            skip=offset,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Failed to get data processing audits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get data processing audits: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=AuditSummary)
@security_headers
async def get_audit_summary_endpoint(
    user_id: Optional[UUID] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Start date for summary"),
    end_date: Optional[datetime] = Query(None, description="End date for summary"),
    db: AsyncSession = Depends(get_async_db),
):
    """Get audit summary statistics."""
    try:
        return await get_audit_summary(
            db, user_id=user_id, start_date=start_date, end_date=end_date
        )
    except Exception as e:
        logger.error(f"Failed to get audit summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit summary: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Consent Event logging (convenience endpoint)
# ---------------------------------------------------------------------------


@router.post("/events/consent", response_model=ConsentAuditLogResponse)
@rate_limit(requests_per_minute=60)
@security_headers
async def log_consent_event(
    request: Request,
    event_type: AuditEventType,
    event_description: str,
    actor_id: UUID,
    actor_type: str = "user",
    consent_record_id: Optional[UUID] = None,
    data_subject_id: Optional[UUID] = None,
    severity: AuditSeverity = AuditSeverity.MEDIUM,
    event_data: Optional[Dict[str, Any]] = None,
    session_id: Optional[UUID] = None,
    current_user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_db),
):
    """Log a consent-related event with automatic compliance checking."""
    try:
        logger.info(f"Logging consent event: {event_type} for user {current_user_id}")

        # Determine compliance
        gdpr_compliant = True
        hipaa_compliant = True
        compliance_issues: List[str] = []

        if event_type == AuditEventType.DATA_ACCESS and not consent_record_id:
            gdpr_compliant = False
            compliance_issues.append("No consent record for data access")
        elif event_type == AuditEventType.DATA_SHARING and not consent_record_id:
            gdpr_compliant = False
            hipaa_compliant = False
            compliance_issues.append("No consent record for data sharing")
        elif event_type == AuditEventType.SECURITY_BREACH:
            severity = AuditSeverity.CRITICAL
            gdpr_compliant = False
            hipaa_compliant = False
            compliance_issues.append("Security breach detected")

        audit_data = ConsentAuditLogCreate(
            user_id=current_user_id,
            event_type=event_type,
            event_description=event_description,
            actor_id=actor_id,
            actor_type=actor_type,
            consent_record_id=consent_record_id,
            data_subject_id=data_subject_id,
            severity=severity,
            event_data=event_data or {},
            gdpr_compliant=gdpr_compliant,
            hipaa_compliant=hipaa_compliant,
            compliance_issues=compliance_issues,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            session_id=session_id,
        )

        result = await create_audit_log(db, audit_data)
        await db.commit()
        logger.info(f"Successfully logged consent event {result.id}")
        return result
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to log consent event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to log consent event: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Consent Verification
# ---------------------------------------------------------------------------


@router.post("/verify", response_model=Dict[str, Any])
@security_headers
async def verify_consent_compliance(
    user_id: UUID,
    consent_record_id: Optional[UUID] = None,
    data_categories: Optional[List[str]] = None,
    processing_purpose: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
):
    """Verify consent compliance for data processing."""
    try:
        logger.info(f"Verifying consent compliance for user {user_id}")

        from services.audit_service import get_consent_status as _get_consents

        consents = await _get_consents(db, user_id)
        active_consents = [c for c in consents if c.granted and c.revoked_at is None]

        issues: List[str] = []
        recommendations: List[str] = []
        gdpr_ok = True
        hipaa_ok = True

        if not active_consents:
            gdpr_ok = False
            issues.append("No active consent records found for user")
            recommendations.append("Obtain valid consent before processing")

        if consent_record_id:
            matching = [c for c in active_consents if c.id == consent_record_id]
            if not matching:
                gdpr_ok = False
                issues.append(
                    f"Consent record {consent_record_id} not found or revoked"
                )

        is_compliant = gdpr_ok and hipaa_ok and len(issues) == 0

        return {
            "user_id": str(user_id),
            "consent_record_id": str(consent_record_id) if consent_record_id else None,
            "data_categories": data_categories or [],
            "processing_purpose": processing_purpose or "health_monitoring",
            "compliance_status": "compliant" if is_compliant else "non_compliant",
            "gdpr_compliant": gdpr_ok,
            "hipaa_compliant": hipaa_ok,
            "consent_valid": len(active_consents) > 0,
            "active_consents": len(active_consents),
            "issues": issues,
            "recommendations": recommendations
            or ["Continue monitoring consent status"],
            "verification_timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to verify consent compliance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify consent compliance: {str(e)}",
        )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@router.get("/health")
async def audit_health_check():
    """Health check for audit service."""
    return {
        "status": "healthy",
        "service": "audit",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "consent_audit_logging",
            "data_processing_audits",
            "compliance_monitoring",
            "risk_assessment",
            "audit_trail_generation",
        ],
    }
