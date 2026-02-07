"""Unit tests for Consent Audit service models."""
import pytest
from datetime import datetime
import uuid


class TestConsentAuditLogModels:
    def test_audit_log_create(self):
        """Test ConsentAuditLogCreate model with valid data."""
        from apps.consent_audit.models.audit import ConsentAuditLogCreate

        log = ConsentAuditLogCreate(
            user_id=uuid.uuid4(),
            event_type="consent_granted",
            severity="medium",
            event_description="User granted consent for data processing.",
            event_data={"purpose": "treatment", "scope": "full_medical"},
            actor_id=uuid.uuid4(),
            actor_type="user",
            actor_role="patient",
            ip_address="192.168.1.100",
            gdpr_compliant=True,
            hipaa_compliant=True,
        )
        assert log.event_type == "consent_granted"
        assert log.gdpr_compliant is True
        assert log.actor_type == "user"

    def test_audit_log_create_minimal(self):
        """Test ConsentAuditLogCreate with minimal required fields."""
        from apps.consent_audit.models.audit import ConsentAuditLogCreate

        log = ConsentAuditLogCreate(
            user_id=uuid.uuid4(),
            event_type="data_access",
            event_description="Data was accessed.",
            actor_id=uuid.uuid4(),
            actor_type="system",
        )
        assert log.severity == "medium"
        assert log.compliance_issues == []
        assert log.risk_factors == []

    def test_audit_log_update_partial(self):
        """Test ConsentAuditLogUpdate allows partial updates."""
        from apps.consent_audit.models.audit import ConsentAuditLogUpdate

        update = ConsentAuditLogUpdate(
            severity="high",
            compliance_notes="Requires follow-up review.",
        )
        assert update.severity == "high"
        assert update.risk_level is None

    def test_audit_log_missing_required(self):
        """Test ConsentAuditLogCreate fails without required fields."""
        from apps.consent_audit.models.audit import ConsentAuditLogCreate

        with pytest.raises(Exception):
            ConsentAuditLogCreate(
                event_type="consent_granted",
                # Missing user_id, event_description, actor_id, actor_type
            )


class TestConsentRecordModels:
    def test_consent_record_create(self):
        """Test ConsentRecordCreate model with valid data."""
        from apps.consent_audit.models.audit import ConsentRecordCreate

        record = ConsentRecordCreate(
            user_id=uuid.uuid4(),
            consent_type="data_processing",
            purpose="Treatment and care coordination",
            granted=True,
            expires_at=datetime(2027, 1, 1),
            version="2.0",
        )
        assert record.consent_type == "data_processing"
        assert record.granted is True
        assert record.version == "2.0"

    def test_consent_record_create_minimal(self):
        """Test ConsentRecordCreate with minimal fields."""
        from apps.consent_audit.models.audit import ConsentRecordCreate

        record = ConsentRecordCreate(
            user_id=uuid.uuid4(),
            consent_type="analytics",
            purpose="Health analytics",
        )
        assert record.granted is True
        assert record.expires_at is None

    def test_consent_record_missing_required(self):
        """Test ConsentRecordCreate fails without required fields."""
        from apps.consent_audit.models.audit import ConsentRecordCreate

        with pytest.raises(Exception):
            ConsentRecordCreate(consent_type="test")


class TestDataProcessingAuditModels:
    def test_data_processing_audit_create(self):
        """Test DataProcessingAuditCreate model."""
        from apps.consent_audit.models.audit import DataProcessingAuditCreate

        audit = DataProcessingAuditCreate(
            user_id=uuid.uuid4(),
            processing_purpose="treatment",
            data_categories=["medical_records", "lab_results"],
            processing_method="automated_analysis",
            legal_basis="consent",
            data_encrypted=True,
            consent_verified=True,
        )
        assert audit.processing_purpose == "treatment"
        assert len(audit.data_categories) == 2
        assert audit.data_encrypted is True

    def test_data_processing_audit_missing_required(self):
        """Test DataProcessingAuditCreate fails without required fields."""
        from apps.consent_audit.models.audit import DataProcessingAuditCreate

        with pytest.raises(Exception):
            DataProcessingAuditCreate(processing_purpose="treatment")


class TestComplianceReportModels:
    def test_compliance_report_create(self):
        """Test ComplianceReportCreate model."""
        from apps.consent_audit.models.audit import ComplianceReportCreate

        report = ComplianceReportCreate(
            report_type="quarterly",
            report_period_start=datetime(2026, 1, 1),
            report_period_end=datetime(2026, 3, 31),
            scope_description="Q1 2026 compliance review for all services.",
            framework="gdpr",
            executive_summary="All systems compliant.",
            recommendations=["Increase audit frequency"],
        )
        assert report.report_type == "quarterly"
        assert report.framework == "gdpr"
        assert len(report.recommendations) == 1


class TestAuditEnums:
    def test_audit_event_type_enum(self):
        """Test AuditEventType enum values."""
        from apps.consent_audit.models.audit import AuditEventType

        assert AuditEventType.CONSENT_GRANTED == "consent_granted"
        assert AuditEventType.DATA_DELETION == "data_deletion"
        assert AuditEventType.SECURITY_BREACH == "security_breach"

    def test_compliance_status_enum(self):
        """Test ComplianceStatus enum values."""
        from apps.consent_audit.models.audit import ComplianceStatus

        assert ComplianceStatus.COMPLIANT == "compliant"
        assert ComplianceStatus.NON_COMPLIANT == "non_compliant"

    def test_data_processing_purpose_enum(self):
        """Test DataProcessingPurpose enum values."""
        from apps.consent_audit.models.audit import DataProcessingPurpose

        assert DataProcessingPurpose.TREATMENT == "treatment"
        assert DataProcessingPurpose.RESEARCH == "research"
