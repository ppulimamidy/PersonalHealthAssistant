"""Unit tests for Medical Records service models."""
import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4


class TestLabResultModels:
    def test_lab_result_create(self):
        """Test LabResultCreate model with valid data."""
        from apps.medical_records.models.lab_results import LabResultCreate

        result = LabResultCreate(
            patient_id=uuid4(),
            test_name="Complete Blood Count",
            test_code="CBC-001",
            value=Decimal("7.5"),
            unit="g/dL",
            reference_range_low=Decimal("6.0"),
            reference_range_high=Decimal("10.0"),
            test_date=datetime.utcnow(),
            lab_name="Quest Diagnostics",
            specimen_type="blood",
        )
        assert result.test_name == "Complete Blood Count"
        assert result.value == Decimal("7.5")
        assert result.abnormal is False

    def test_lab_result_abnormal(self):
        """Test LabResultCreate with abnormal flag."""
        from apps.medical_records.models.lab_results import LabResultCreate

        result = LabResultCreate(
            patient_id=uuid4(),
            test_name="Glucose",
            value=Decimal("250"),
            unit="mg/dL",
            abnormal=True,
            critical=True,
            test_date=datetime.utcnow(),
        )
        assert result.abnormal is True
        assert result.critical is True

    def test_lab_result_update_partial(self):
        """Test LabResultUpdate allows partial updates."""
        from apps.medical_records.models.lab_results import LabResultUpdate

        update = LabResultUpdate(value=Decimal("8.0"), unit="g/dL")
        assert update.value == Decimal("8.0")
        assert update.test_name is None

    def test_lab_result_missing_required_fields(self):
        """Test LabResultCreate fails without required fields."""
        from apps.medical_records.models.lab_results import LabResultCreate

        with pytest.raises(Exception):
            LabResultCreate(
                test_name="Incomplete",
                # Missing patient_id and test_date
            )

    def test_lab_result_decimal_from_string(self):
        """Test LabResultCreate converts string to Decimal."""
        from apps.medical_records.models.lab_results import LabResultCreate

        result = LabResultCreate(
            patient_id=uuid4(),
            test_name="HbA1c",
            value="6.5",
            unit="%",
            test_date=datetime.utcnow(),
        )
        assert result.value == Decimal("6.5")


class TestDocumentModels:
    def test_document_upload_request(self):
        """Test DocumentUploadRequest creation."""
        from apps.medical_records.models.documents import DocumentUploadRequest

        doc = DocumentUploadRequest(
            patient_id=uuid4(),
            document_type="lab_report",
            title="Blood Work Results",
            description="Annual blood work",
            tags=["annual", "blood_work"],
        )
        assert doc.document_type == "lab_report"
        assert len(doc.tags) == 2

    def test_document_create(self):
        """Test DocumentCreate model."""
        from apps.medical_records.models.documents import DocumentCreate

        doc = DocumentCreate(
            patient_id=uuid4(),
            document_type="clinical_note",
            title="Visit Note - Dr. Smith",
            content="Patient presents with...",
            source="manual",
        )
        assert doc.title == "Visit Note - Dr. Smith"
        assert doc.processing_status == "pending"
        assert doc.document_status == "uploaded"

    def test_document_update_partial(self):
        """Test DocumentUpdate allows partial updates."""
        from apps.medical_records.models.documents import DocumentUpdate

        update = DocumentUpdate(title="Updated Title")
        assert update.title == "Updated Title"
        assert update.content is None

    def test_document_type_enum(self):
        """Test DocumentType enum values."""
        from apps.medical_records.models.documents import DocumentType

        assert DocumentType.LAB_REPORT == "lab_report"
        assert DocumentType.CLINICAL_NOTE == "clinical_note"
        assert DocumentType.PRESCRIPTION == "prescription"

    def test_document_missing_required_fields(self):
        """Test DocumentUploadRequest fails without required fields."""
        from apps.medical_records.models.documents import DocumentUploadRequest

        with pytest.raises(Exception):
            DocumentUploadRequest(
                # Missing patient_id and document_type
                title="Incomplete",
            )
