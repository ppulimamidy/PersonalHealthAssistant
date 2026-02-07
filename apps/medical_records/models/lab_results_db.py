"""
Lab Results SQLAlchemy Model
Database model for laboratory test results.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB

from common.models.base import Base


class LabResultDB(Base):
    """SQLAlchemy model for lab results."""
    
    __tablename__ = "lab_results"
    __table_args__ = {"schema": "medical_records"}
    
    # Primary key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Patient relationship (no foreign key for now)
    patient_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    
    # Test information
    test_name = Column(String(200), nullable=False, index=True)
    test_code = Column(String(50), nullable=True)  # LOINC code
    value = Column(Numeric(10, 4), nullable=True)
    unit = Column(String(50), nullable=True)
    
    # Reference ranges
    reference_range_low = Column(Numeric(10, 4), nullable=True)
    reference_range_high = Column(Numeric(10, 4), nullable=True)
    reference_range_text = Column(String(200), nullable=True)
    
    # Result flags
    abnormal = Column(Boolean, default=False, nullable=False, index=True)
    critical = Column(Boolean, default=False, nullable=False, index=True)
    
    # Dates
    test_date = Column(DateTime, nullable=False, index=True)
    result_date = Column(DateTime, nullable=True)
    
    # Provider information
    lab_name = Column(String(200), nullable=True)
    ordering_provider = Column(String(200), nullable=True)
    specimen_type = Column(String(100), nullable=True)
    
    # Status and source
    status = Column(String(50), default="final", nullable=False)
    source = Column(String(50), default="manual", nullable=False, index=True)
    
    # External references
    external_id = Column(String(200), nullable=True, index=True)
    fhir_resource_id = Column(String(200), nullable=True)
    
    # Metadata
    record_metadata = Column(JSONB, default={}, nullable=False)
    
    def __repr__(self) -> str:
        return f"<LabResultDB(id={self.id}, test_name='{self.test_name}', patient_id={self.patient_id})>"
    
    @property
    def is_abnormal(self) -> bool:
        """Check if the result is abnormal."""
        return self.abnormal or self.critical
    
    @property
    def formatted_value(self) -> str:
        """Get formatted value with unit."""
        if self.value is None:
            return "N/A"
        value_str = str(self.value)
        if self.unit:
            return f"{value_str} {self.unit}"
        return value_str
    
    @property
    def reference_range_display(self) -> str:
        """Get formatted reference range."""
        if self.reference_range_text:
            return self.reference_range_text
        
        if self.reference_range_low is not None and self.reference_range_high is not None:
            low = str(self.reference_range_low)
            high = str(self.reference_range_high)
            unit = f" {self.unit}" if self.unit else ""
            return f"{low} - {high}{unit}"
        
        return "N/A"
    
    def to_dict(self) -> dict:
        """Convert to dictionary with proper type handling."""
        data = super().to_dict()
        
        # Convert Decimal to string for JSON serialization
        for field in ['value', 'reference_range_low', 'reference_range_high']:
            if data.get(field) is not None:
                data[field] = str(data[field])
        
        # Convert datetime to ISO format
        for field in ['test_date', 'result_date', 'created_at', 'updated_at']:
            if data.get(field) is not None:
                data[field] = data[field].isoformat()
        
        # Convert UUID to string
        for field in ['id', 'patient_id']:
            if data.get(field) is not None:
                data[field] = str(data[field])
        
        return data 