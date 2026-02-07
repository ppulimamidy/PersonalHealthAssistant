"""
Audit service for the Personal Health Assistant Consent Audit Service.

This service provides comprehensive audit functionality including:
- Consent audit logging
- Compliance checking
- Risk assessment
- Audit trail generation
- GDPR and HIPAA validation
- Consent record management
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, update

from common.utils.logging import get_logger
from common.database.connection import get_db_manager

from models.audit import (
    # ORM models
    ConsentAuditLog,
    DataProcessingAudit,
    ComplianceReport,
    ConsentRecord,
    # Enums
    AuditEventType,
    AuditSeverity,
    ComplianceStatus,
    DataProcessingPurpose,
    # Pydantic schemas
    ConsentAuditLogCreate,
    ConsentAuditLogUpdate,
    ConsentAuditLogResponse,
    DataProcessingAuditCreate,
    DataProcessingAuditUpdate,
    DataProcessingAuditResponse,
    ComplianceReportCreate,
    ComplianceReportUpdate,
    ComplianceReportResponse,
    ConsentRecordCreate,
    ConsentRecordResponse,
    AuditSummary,
)

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Audit log helpers
# ---------------------------------------------------------------------------


def _audit_log_to_response(row: ConsentAuditLog) -> ConsentAuditLogResponse:
    """Convert a ConsentAuditLog ORM instance to a response schema."""
    return ConsentAuditLogResponse(
        id=row.id,
        user_id=row.user_id,
        event_type=row.event_type,
        severity=row.severity,
        event_description=row.event_description,
        event_data=row.event_data or {},
        event_timestamp=row.event_timestamp,
        ip_address=row.ip_address,
        user_agent=row.user_agent,
        session_id=row.session_id,
        actor_id=row.actor_id,
        actor_type=row.actor_type,
        actor_role=row.actor_role,
        consent_record_id=row.consent_record_id,
        data_subject_id=row.data_subject_id,
        gdpr_compliant=row.gdpr_compliant,
        hipaa_compliant=row.hipaa_compliant,
        compliance_notes=row.compliance_notes,
        compliance_issues=row.compliance_issues or [],
        risk_level=row.risk_level or "low",
        risk_factors=row.risk_factors or [],
        mitigation_actions=row.mitigation_actions or [],
        created_at=row.created_at,
    )


def _processing_audit_to_response(
    row: DataProcessingAudit,
) -> DataProcessingAuditResponse:
    """Convert a DataProcessingAudit ORM instance to a response schema."""
    return DataProcessingAuditResponse(
        id=row.id,
        user_id=row.user_id,
        processing_purpose=row.processing_purpose,
        processing_timestamp=row.processing_timestamp,
        processing_duration=row.processing_duration,
        data_categories=row.data_categories or [],
        data_volume=row.data_volume,
        data_sensitivity=row.data_sensitivity or "medium",
        consent_record_id=row.consent_record_id,
        data_subject_id=row.data_subject_id,
        processing_method=row.processing_method,
        processing_location=row.processing_location,
        processing_tools=row.processing_tools or [],
        third_parties_involved=row.third_parties_involved or [],
        data_shared_with=row.data_shared_with or [],
        legal_basis=row.legal_basis,
        consent_verified=row.consent_verified,
        consent_verification_method=row.consent_verification_method,
        compliance_status=row.compliance_status or "pending_review",
        data_encrypted=row.data_encrypted,
        access_controls=row.access_controls or [],
        retention_period=row.retention_period,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _compliance_report_to_response(row: ComplianceReport) -> ComplianceReportResponse:
    """Convert a ComplianceReport ORM instance to a response schema."""
    return ComplianceReportResponse(
        id=row.id,
        report_type=row.report_type,
        framework=row.framework,
        report_period_start=row.report_period_start,
        report_period_end=row.report_period_end,
        report_status=row.report_status,
        user_id=row.user_id,
        organization_id=row.organization_id,
        scope_description=row.scope_description,
        total_consents=row.total_consents,
        active_consents=row.active_consents,
        expired_consents=row.expired_consents,
        withdrawn_consents=row.withdrawn_consents,
        compliance_violations=row.compliance_violations,
        security_incidents=row.security_incidents,
        data_breaches=row.data_breaches,
        data_processing_events=row.data_processing_events,
        data_sharing_events=row.data_sharing_events,
        data_access_events=row.data_access_events,
        executive_summary=row.executive_summary,
        detailed_findings=row.detailed_findings or {},
        recommendations=row.recommendations or [],
        action_items=row.action_items or [],
        gdpr_compliance_score=row.gdpr_compliance_score,
        hipaa_compliance_score=row.hipaa_compliance_score,
        overall_compliance_score=row.overall_compliance_score,
        created_at=row.created_at,
        updated_at=row.updated_at,
        submitted_at=row.submitted_at,
    )


def _consent_record_to_response(row: ConsentRecord) -> ConsentRecordResponse:
    """Convert a ConsentRecord ORM instance to a response schema."""
    return ConsentRecordResponse(
        id=row.id,
        user_id=row.user_id,
        consent_type=row.consent_type,
        purpose=row.purpose,
        granted=row.granted,
        granted_at=row.granted_at,
        expires_at=row.expires_at,
        revoked_at=row.revoked_at,
        version=row.version,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ---------------------------------------------------------------------------
# Audit Log CRUD
# ---------------------------------------------------------------------------


async def create_audit_log(
    db: AsyncSession, data: ConsentAuditLogCreate
) -> ConsentAuditLogResponse:
    """Create a new consent audit log entry."""
    now = datetime.utcnow()
    row = ConsentAuditLog(
        id=uuid4(),
        user_id=data.user_id,
        event_type=data.event_type.value
        if isinstance(data.event_type, AuditEventType)
        else data.event_type,
        severity=data.severity.value
        if isinstance(data.severity, AuditSeverity)
        else data.severity,
        event_description=data.event_description,
        event_data=data.event_data or {},
        event_timestamp=now,
        ip_address=data.ip_address,
        user_agent=data.user_agent,
        session_id=data.session_id,
        actor_id=data.actor_id,
        actor_type=data.actor_type,
        actor_role=data.actor_role,
        consent_record_id=data.consent_record_id,
        data_subject_id=data.data_subject_id or data.user_id,
        gdpr_compliant=data.gdpr_compliant,
        hipaa_compliant=data.hipaa_compliant,
        compliance_notes=data.compliance_notes,
        compliance_issues=data.compliance_issues or [],
        risk_level=data.risk_level.value
        if isinstance(data.risk_level, AuditSeverity)
        else data.risk_level,
        risk_factors=data.risk_factors or [],
        mitigation_actions=data.mitigation_actions or [],
        created_at=now,
    )
    db.add(row)
    await db.flush()
    logger.info(f"Created audit log {row.id} for user {row.user_id}")
    return _audit_log_to_response(row)


async def get_audit_log(
    db: AsyncSession, log_id: UUID
) -> Optional[ConsentAuditLogResponse]:
    """Get a single audit log by ID."""
    result = await db.execute(
        select(ConsentAuditLog).where(ConsentAuditLog.id == log_id)
    )
    row = result.scalars().first()
    if row is None:
        return None
    return _audit_log_to_response(row)


async def get_audit_logs(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    event_type: Optional[AuditEventType] = None,
    severity: Optional[AuditSeverity] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[ConsentAuditLogResponse]:
    """Return paginated audit logs with optional filtering."""
    stmt = select(ConsentAuditLog)

    conditions = []
    if user_id is not None:
        conditions.append(ConsentAuditLog.user_id == user_id)
    if event_type is not None:
        evt = event_type.value if isinstance(event_type, AuditEventType) else event_type
        conditions.append(ConsentAuditLog.event_type == evt)
    if severity is not None:
        sev = severity.value if isinstance(severity, AuditSeverity) else severity
        conditions.append(ConsentAuditLog.severity == sev)
    if start_date is not None:
        conditions.append(ConsentAuditLog.event_timestamp >= start_date)
    if end_date is not None:
        conditions.append(ConsentAuditLog.event_timestamp <= end_date)

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = (
        stmt.order_by(desc(ConsentAuditLog.event_timestamp)).offset(skip).limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [_audit_log_to_response(r) for r in rows]


async def get_compliance_violations(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[ConsentAuditLogResponse]:
    """Get audit logs flagged as non-compliant."""
    stmt = select(ConsentAuditLog).where(
        or_(
            ConsentAuditLog.gdpr_compliant == False,  # noqa: E712
            ConsentAuditLog.hipaa_compliant == False,  # noqa: E712
        )
    )
    conditions = []
    if user_id is not None:
        conditions.append(ConsentAuditLog.user_id == user_id)
    if start_date is not None:
        conditions.append(ConsentAuditLog.event_timestamp >= start_date)
    if end_date is not None:
        conditions.append(ConsentAuditLog.event_timestamp <= end_date)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(desc(ConsentAuditLog.event_timestamp))
    result = await db.execute(stmt)
    return [_audit_log_to_response(r) for r in result.scalars().all()]


async def get_high_risk_events(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[ConsentAuditLogResponse]:
    """Get high / critical severity audit events."""
    stmt = select(ConsentAuditLog).where(
        ConsentAuditLog.severity.in_(["high", "critical"])
    )
    conditions = []
    if user_id is not None:
        conditions.append(ConsentAuditLog.user_id == user_id)
    if start_date is not None:
        conditions.append(ConsentAuditLog.event_timestamp >= start_date)
    if end_date is not None:
        conditions.append(ConsentAuditLog.event_timestamp <= end_date)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(desc(ConsentAuditLog.event_timestamp))
    result = await db.execute(stmt)
    return [_audit_log_to_response(r) for r in result.scalars().all()]


# ---------------------------------------------------------------------------
# Audit Summary
# ---------------------------------------------------------------------------


async def get_audit_summary(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> AuditSummary:
    """Compute aggregate audit statistics."""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    base_cond = and_(
        ConsentAuditLog.event_timestamp >= start_date,
        ConsentAuditLog.event_timestamp <= end_date,
    )
    if user_id is not None:
        base_cond = and_(base_cond, ConsentAuditLog.user_id == user_id)

    # Total events
    total_q = await db.execute(
        select(func.count()).select_from(ConsentAuditLog).where(base_cond)
    )
    total_events = total_q.scalar() or 0

    # Non-compliant (GDPR or HIPAA)
    nc_q = await db.execute(
        select(func.count())
        .select_from(ConsentAuditLog)
        .where(
            and_(
                base_cond,
                or_(
                    ConsentAuditLog.gdpr_compliant == False,  # noqa: E712
                    ConsentAuditLog.hipaa_compliant == False,  # noqa: E712
                ),
            )
        )
    )
    non_compliant = nc_q.scalar() or 0

    # GDPR violations
    gdpr_q = await db.execute(
        select(func.count())
        .select_from(ConsentAuditLog)
        .where(and_(base_cond, ConsentAuditLog.gdpr_compliant == False))  # noqa: E712
    )
    gdpr_violations = gdpr_q.scalar() or 0

    # HIPAA violations
    hipaa_q = await db.execute(
        select(func.count())
        .select_from(ConsentAuditLog)
        .where(and_(base_cond, ConsentAuditLog.hipaa_compliant == False))  # noqa: E712
    )
    hipaa_violations = hipaa_q.scalar() or 0

    # High-risk events
    hr_q = await db.execute(
        select(func.count())
        .select_from(ConsentAuditLog)
        .where(and_(base_cond, ConsentAuditLog.severity == "high"))
    )
    high_risk = hr_q.scalar() or 0

    # Critical events
    cr_q = await db.execute(
        select(func.count())
        .select_from(ConsentAuditLog)
        .where(and_(base_cond, ConsentAuditLog.severity == "critical"))
    )
    critical = cr_q.scalar() or 0

    # Security incidents
    si_q = await db.execute(
        select(func.count())
        .select_from(ConsentAuditLog)
        .where(and_(base_cond, ConsentAuditLog.event_type == "security_breach"))
    )
    security_incidents = si_q.scalar() or 0

    # Data breaches (same as security_breach for now)
    data_breaches = security_incidents

    compliant_events = total_events - non_compliant
    score = (
        100.0
        if total_events == 0
        else round((compliant_events / total_events) * 100, 2)
    )

    return AuditSummary(
        total_events=total_events,
        compliant_events=compliant_events,
        non_compliant_events=non_compliant,
        high_risk_events=high_risk,
        critical_events=critical,
        gdpr_violations=gdpr_violations,
        hipaa_violations=hipaa_violations,
        security_incidents=security_incidents,
        data_breaches=data_breaches,
        period_start=start_date,
        period_end=end_date,
        compliance_score=score,
    )


# ---------------------------------------------------------------------------
# Data Processing Audit CRUD
# ---------------------------------------------------------------------------


async def create_data_processing_audit(
    db: AsyncSession, data: DataProcessingAuditCreate
) -> DataProcessingAuditResponse:
    """Create a new data processing audit record."""
    now = datetime.utcnow()
    row = DataProcessingAudit(
        id=uuid4(),
        user_id=data.user_id,
        processing_purpose=data.processing_purpose.value
        if isinstance(data.processing_purpose, DataProcessingPurpose)
        else data.processing_purpose,
        processing_timestamp=now,
        processing_duration=data.processing_duration,
        data_categories=data.data_categories or [],
        data_volume=data.data_volume,
        data_sensitivity=data.data_sensitivity.value
        if isinstance(data.data_sensitivity, AuditSeverity)
        else data.data_sensitivity,
        consent_record_id=data.consent_record_id,
        data_subject_id=data.data_subject_id or data.user_id,
        processing_method=data.processing_method,
        processing_location=data.processing_location,
        processing_tools=data.processing_tools or [],
        third_parties_involved=data.third_parties_involved or [],
        data_shared_with=data.data_shared_with or [],
        legal_basis=data.legal_basis,
        consent_verified=data.consent_verified,
        consent_verification_method=data.consent_verification_method,
        compliance_status="pending_review",
        data_encrypted=data.data_encrypted,
        access_controls=data.access_controls or [],
        retention_period=data.retention_period,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    await db.flush()
    logger.info(f"Created data processing audit {row.id} for user {row.user_id}")
    return _processing_audit_to_response(row)


async def get_data_processing_audits(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    purpose: Optional[DataProcessingPurpose] = None,
    compliance_status: Optional[ComplianceStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[DataProcessingAuditResponse]:
    """Return paginated data processing audits with optional filtering."""
    stmt = select(DataProcessingAudit)
    conditions = []
    if user_id is not None:
        conditions.append(DataProcessingAudit.user_id == user_id)
    if purpose is not None:
        p = purpose.value if isinstance(purpose, DataProcessingPurpose) else purpose
        conditions.append(DataProcessingAudit.processing_purpose == p)
    if compliance_status is not None:
        cs = (
            compliance_status.value
            if isinstance(compliance_status, ComplianceStatus)
            else compliance_status
        )
        conditions.append(DataProcessingAudit.compliance_status == cs)
    if start_date is not None:
        conditions.append(DataProcessingAudit.processing_timestamp >= start_date)
    if end_date is not None:
        conditions.append(DataProcessingAudit.processing_timestamp <= end_date)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = (
        stmt.order_by(desc(DataProcessingAudit.processing_timestamp))
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [_processing_audit_to_response(r) for r in result.scalars().all()]


# ---------------------------------------------------------------------------
# Compliance Report CRUD
# ---------------------------------------------------------------------------


async def create_compliance_report(
    db: AsyncSession, data: ComplianceReportCreate
) -> ComplianceReportResponse:
    """Create a new compliance report."""
    now = datetime.utcnow()
    row = ComplianceReport(
        id=uuid4(),
        report_type=data.report_type,
        framework=data.framework,
        report_period_start=data.report_period_start,
        report_period_end=data.report_period_end,
        report_status="draft",
        user_id=data.user_id,
        organization_id=data.organization_id,
        scope_description=data.scope_description,
        executive_summary=data.executive_summary,
        detailed_findings=data.detailed_findings or {},
        recommendations=data.recommendations or [],
        action_items=data.action_items or [],
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    await db.flush()
    logger.info(f"Created compliance report {row.id}")
    return _compliance_report_to_response(row)


async def get_compliance_reports(
    db: AsyncSession,
    report_type: Optional[str] = None,
    framework: Optional[str] = None,
    user_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[ComplianceReportResponse]:
    """Return paginated compliance reports with optional filtering."""
    stmt = select(ComplianceReport)
    conditions = []
    if report_type is not None:
        conditions.append(ComplianceReport.report_type == report_type)
    if framework is not None:
        conditions.append(ComplianceReport.framework == framework)
    if user_id is not None:
        conditions.append(ComplianceReport.user_id == user_id)
    if start_date is not None:
        conditions.append(ComplianceReport.created_at >= start_date)
    if end_date is not None:
        conditions.append(ComplianceReport.created_at <= end_date)
    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(desc(ComplianceReport.created_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return [_compliance_report_to_response(r) for r in result.scalars().all()]


async def get_compliance_report(
    db: AsyncSession, report_id: UUID
) -> Optional[ComplianceReportResponse]:
    """Get a single compliance report by ID."""
    result = await db.execute(
        select(ComplianceReport).where(ComplianceReport.id == report_id)
    )
    row = result.scalars().first()
    return _compliance_report_to_response(row) if row else None


# ---------------------------------------------------------------------------
# Consent Record CRUD
# ---------------------------------------------------------------------------


async def create_consent(
    db: AsyncSession, data: ConsentRecordCreate
) -> ConsentRecordResponse:
    """Create a new consent record."""
    now = datetime.utcnow()
    row = ConsentRecord(
        id=uuid4(),
        user_id=data.user_id,
        consent_type=data.consent_type,
        purpose=data.purpose,
        granted=data.granted,
        granted_at=now if data.granted else None,
        expires_at=data.expires_at,
        version=data.version,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    await db.flush()
    logger.info(f"Created consent record {row.id} for user {row.user_id}")
    return _consent_record_to_response(row)


async def get_consent_status(
    db: AsyncSession, user_id: UUID
) -> List[ConsentRecordResponse]:
    """Get all consent records for a user."""
    result = await db.execute(
        select(ConsentRecord)
        .where(ConsentRecord.user_id == user_id)
        .order_by(desc(ConsentRecord.created_at))
    )
    return [_consent_record_to_response(r) for r in result.scalars().all()]


async def get_consent_record(
    db: AsyncSession, consent_id: UUID
) -> Optional[ConsentRecordResponse]:
    """Get a single consent record by ID."""
    result = await db.execute(
        select(ConsentRecord).where(ConsentRecord.id == consent_id)
    )
    row = result.scalars().first()
    return _consent_record_to_response(row) if row else None


async def revoke_consent(
    db: AsyncSession, consent_id: UUID
) -> Optional[ConsentRecordResponse]:
    """Revoke a consent record by setting granted=False and revoked_at."""
    result = await db.execute(
        select(ConsentRecord).where(ConsentRecord.id == consent_id)
    )
    row = result.scalars().first()
    if row is None:
        return None

    now = datetime.utcnow()
    row.granted = False
    row.revoked_at = now
    row.updated_at = now
    await db.flush()
    logger.info(f"Revoked consent record {consent_id}")
    return _consent_record_to_response(row)


# ---------------------------------------------------------------------------
# Compliance Status helpers
# ---------------------------------------------------------------------------


async def get_compliance_status(
    db: AsyncSession,
    framework: Optional[str] = None,
    user_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """Compute compliance status by examining audit logs for the last 30 days."""
    summary = await get_audit_summary(db, user_id=user_id)

    gdpr_score = 100.0
    hipaa_score = 100.0
    if summary.total_events > 0:
        gdpr_score = round(
            ((summary.total_events - summary.gdpr_violations) / summary.total_events)
            * 100,
            2,
        )
        hipaa_score = round(
            ((summary.total_events - summary.hipaa_violations) / summary.total_events)
            * 100,
            2,
        )

    overall_score = round((gdpr_score + hipaa_score) / 2, 2)

    status: Dict[str, Any] = {
        "overall_compliant": overall_score >= 95.0,
        "overall_score": overall_score,
        "total_violations": summary.non_compliant_events,
        "total_events": summary.total_events,
        "period": {
            "start": summary.period_start.isoformat(),
            "end": summary.period_end.isoformat(),
        },
        "regulations": {
            "gdpr": {
                "compliant": gdpr_score >= 95.0,
                "violations": summary.gdpr_violations,
                "score": gdpr_score,
            },
            "hipaa": {
                "compliant": hipaa_score >= 95.0,
                "violations": summary.hipaa_violations,
                "score": hipaa_score,
            },
        },
        "security": {
            "incidents": summary.security_incidents,
            "breaches": summary.data_breaches,
            "high_risk_events": summary.high_risk_events,
            "critical_events": summary.critical_events,
        },
        "recommendations": [],
    }

    if summary.non_compliant_events > 0:
        status["recommendations"].append(
            "Review and address compliance violations in audit logs"
        )
    if overall_score < 95.0:
        status["recommendations"].append(
            "Improve compliance practices to achieve 95%+ score"
        )
    if summary.data_breaches > 0:
        status["recommendations"].append(
            "Implement additional security measures to prevent data breaches"
        )
    if not status["recommendations"]:
        status["recommendations"].append("Continue monitoring compliance")

    # Filter by framework if requested
    if framework == "gdpr":
        return {
            "gdpr_compliant": gdpr_score >= 95.0,
            "gdpr_score": gdpr_score,
            "total_violations": summary.gdpr_violations,
            "total_events": summary.total_events,
            "period": status["period"],
            "recommendations": status["recommendations"],
        }
    elif framework == "hipaa":
        return {
            "hipaa_compliant": hipaa_score >= 95.0,
            "hipaa_score": hipaa_score,
            "total_violations": summary.hipaa_violations,
            "total_events": summary.total_events,
            "period": status["period"],
            "recommendations": status["recommendations"],
        }

    return status
