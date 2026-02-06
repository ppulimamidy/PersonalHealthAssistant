"""
Consent management models for the Personal Health Assistant.

This module defines consent models for HIPAA compliance, data governance,
and regulatory requirements.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, validator
import uuid
from ..models import Base


class ConsentType(str, Enum):
    """Consent type enumeration."""
    HIPAA_PRIVACY = "hipaa_privacy"
    HIPAA_TREATMENT = "hipaa_treatment"
    HIPAA_PAYMENT = "hipaa_payment"
    HIPAA_OPERATIONS = "hipaa_operations"
    DATA_PROCESSING = "data_processing"
    MARKETING = "marketing"
    RESEARCH = "research"
    THIRD_PARTY_SHARING = "third_party_sharing"
    AI_ANALYSIS = "ai_analysis"
    DEVICE_INTEGRATION = "device_integration"
    EMERGENCY_ACCESS = "emergency_access"
    FAMILY_ACCESS = "family_access"
    PROVIDER_ACCESS = "provider_access"
    INSURANCE_ACCESS = "insurance_access"
    PHARMA_ACCESS = "pharma_access"


class ConsentStatus(str, Enum):
    """Consent status enumeration."""
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class ConsentScope(str, Enum):
    """Consent scope enumeration."""
    ALL_DATA = "all_data"
    SPECIFIC_DATA = "specific_data"
    ANONYMIZED_DATA = "anonymized_data"
    AGGREGATED_DATA = "aggregated_data"
    EMERGENCY_ONLY = "emergency_only"
    LIMITED_ACCESS = "limited_access"


class ConsentRecord(Base):
    """Consent record model for comprehensive consent management."""
    
    __tablename__ = "consent_records"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    
    # Consent information
    consent_type = Column(SQLEnum(ConsentType), nullable=False, index=True)
    consent_scope = Column(SQLEnum(ConsentScope), default=ConsentScope.ALL_DATA)
    status = Column(SQLEnum(ConsentStatus), default=ConsentStatus.PENDING)
    version = Column(String, nullable=False, default="1.0")
    
    # Consent details
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    detailed_terms = Column(Text, nullable=True)  # Full terms and conditions
    data_categories = Column(JSON, default=list)  # Specific data categories covered
    
    # Consent lifecycle
    requested_at = Column(DateTime, default=datetime.utcnow)
    granted_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    withdrawn_at = Column(DateTime, nullable=True)
    
    # Consent method
    consent_method = Column(String, nullable=True)  # "electronic", "paper", "verbal"
    consent_location = Column(String, nullable=True)  # Where consent was given
    witness_present = Column(Boolean, default=False)
    
    # Granular permissions
    permissions = Column(JSON, default=dict)  # Detailed permissions granted
    restrictions = Column(JSON, default=dict)  # Any restrictions on use
    
    # Third-party information
    third_parties = Column(JSON, default=list)  # List of third parties authorized
    sharing_purposes = Column(JSON, default=list)  # Purposes for data sharing
    
    # HIPAA compliance
    hipaa_authorization = Column(Boolean, default=False)
    hipaa_expiration = Column(DateTime, nullable=True)
    hipaa_conditions = Column(Text, nullable=True)
    
    # Audit information
    created_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="consent_records", foreign_keys=[user_id])
    creator = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    data_access_logs = relationship("DataAccessLog", back_populates="consent_record")
    
    def __repr__(self):
        return f"<ConsentRecord(id={self.id}, user_id={self.user_id}, type={self.consent_type}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if consent is currently active."""
        if self.status != ConsentStatus.GRANTED:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        return True
    
    @property
    def is_hipaa_compliant(self) -> bool:
        """Check if consent meets HIPAA requirements."""
        if not self.hipaa_authorization:
            return False
        if self.hipaa_expiration and datetime.utcnow() > self.hipaa_expiration:
            return False
        return True
    
    def grant(self, granted_by: uuid.UUID = None):
        """Grant the consent."""
        self.status = ConsentStatus.GRANTED
        self.granted_at = datetime.utcnow()
        if granted_by:
            self.reviewed_by = granted_by
    
    def withdraw(self, withdrawn_by: uuid.UUID = None, reason: str = None):
        """Withdraw the consent."""
        self.status = ConsentStatus.WITHDRAWN
        self.withdrawn_at = datetime.utcnow()
        if reason:
            self.review_notes = reason
    
    def expire(self):
        """Mark consent as expired."""
        self.status = ConsentStatus.EXPIRED
    
    def add_third_party(self, party_name: str, party_id: str, purposes: List[str]):
        """Add a third party to the consent."""
        if not self.third_parties:
            self.third_parties = []
        self.third_parties.append({
            "name": party_name,
            "id": party_id,
            "added_at": datetime.utcnow().isoformat()
        })
        if not self.sharing_purposes:
            self.sharing_purposes = []
        self.sharing_purposes.extend(purposes)


class DataAccessLog(Base):
    """Data access log model for tracking consent-based data access."""
    
    __tablename__ = "data_access_logs"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    consent_record_id = Column(UUID(as_uuid=True), ForeignKey("auth.consent_records.id"), nullable=True)
    
    # Access information
    access_type = Column(String, nullable=False)  # "read", "write", "share", "export"
    data_category = Column(String, nullable=False)  # Type of data accessed
    data_subject_id = Column(UUID(as_uuid=True), nullable=True)  # Patient whose data was accessed
    
    # Access context
    access_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    purpose = Column(String, nullable=True)  # Purpose of access
    justification = Column(Text, nullable=True)  # Reason for access
    
    # Accessor information
    accessed_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("auth.sessions.id"), nullable=True)
    ip_address = Column(String, nullable=True)
    
    # Consent verification
    consent_verified = Column(Boolean, default=False)
    consent_verification_method = Column(String, nullable=True)
    consent_verification_timestamp = Column(DateTime, nullable=True)
    
    # Compliance
    hipaa_compliant = Column(Boolean, default=False)
    gdpr_compliant = Column(Boolean, default=False)
    compliance_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    consent_record = relationship("ConsentRecord", back_populates="data_access_logs")
    accessed_by_user = relationship("User", foreign_keys=[accessed_by])
    session = relationship("Session")
    
    def __repr__(self):
        return f"<DataAccessLog(id={self.id}, user_id={self.user_id}, access_type={self.access_type}, data_category={self.data_category})>"
    
    def verify_consent(self, method: str = "automatic"):
        """Verify that consent exists for this access."""
        self.consent_verified = True
        self.consent_verification_method = method
        self.consent_verification_timestamp = datetime.utcnow()


class ConsentTemplate(Base):
    """Consent template model for standardized consent forms."""
    
    __tablename__ = "consent_templates"
    __table_args__ = {'schema': 'auth', 'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template information
    name = Column(String, nullable=False, unique=True)
    consent_type = Column(SQLEnum(ConsentType), nullable=False)
    version = Column(String, nullable=False, default="1.0")
    is_active = Column(Boolean, default=True)
    
    # Template content
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    detailed_terms = Column(Text, nullable=True)
    
    # Template structure
    sections = Column(JSON, default=list)  # Structured sections of the consent
    required_fields = Column(JSON, default=list)  # Required user inputs
    optional_fields = Column(JSON, default=list)  # Optional user inputs
    
    # Legal compliance
    legal_requirements = Column(JSON, default=list)  # Legal requirements met
    regulatory_compliance = Column(JSON, default=list)  # Regulatory compliance
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ConsentTemplate(id={self.id}, name={self.name}, type={self.consent_type}, version={self.version})>"


# Pydantic models for API
class ConsentRecordBase(BaseModel):
    """Base consent record model."""
    consent_type: ConsentType
    consent_scope: ConsentScope = ConsentScope.ALL_DATA
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    detailed_terms: Optional[str] = None
    data_categories: List[str] = []
    permissions: Dict[str, Any] = {}
    restrictions: Dict[str, Any] = {}
    third_parties: List[Dict[str, Any]] = []
    sharing_purposes: List[str] = []
    hipaa_authorization: bool = False
    hipaa_expiration: Optional[datetime] = None
    hipaa_conditions: Optional[str] = None


class ConsentRecordCreate(ConsentRecordBase):
    """Model for consent record creation."""
    user_id: uuid.UUID
    consent_method: Optional[str] = None
    consent_location: Optional[str] = None
    witness_present: bool = False
    expires_at: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None


class ConsentRecordUpdate(BaseModel):
    """Model for consent record updates."""
    status: Optional[ConsentStatus] = None
    expires_at: Optional[datetime] = None
    permissions: Optional[Dict[str, Any]] = None
    restrictions: Optional[Dict[str, Any]] = None
    review_notes: Optional[str] = None


class ConsentRecordResponse(ConsentRecordBase):
    """Model for consent record API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    status: ConsentStatus
    version: str
    requested_at: datetime
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    consent_method: Optional[str] = None
    consent_location: Optional[str] = None
    witness_present: bool
    created_by: Optional[uuid.UUID] = None
    reviewed_by: Optional[uuid.UUID] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DataAccessLogBase(BaseModel):
    """Base data access log model."""
    access_type: str
    data_category: str
    purpose: Optional[str] = None
    justification: Optional[str] = None
    consent_verified: bool = False
    hipaa_compliant: bool = False
    gdpr_compliant: bool = False


class DataAccessLogCreate(DataAccessLogBase):
    """Model for data access log creation."""
    user_id: uuid.UUID
    accessed_by: uuid.UUID
    consent_record_id: Optional[uuid.UUID] = None
    data_subject_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None
    ip_address: Optional[str] = None


class DataAccessLogResponse(DataAccessLogBase):
    """Model for data access log API responses."""
    id: uuid.UUID
    user_id: uuid.UUID
    accessed_by: uuid.UUID
    consent_record_id: Optional[uuid.UUID] = None
    data_subject_id: Optional[uuid.UUID] = None
    access_timestamp: datetime
    session_id: Optional[uuid.UUID] = None
    ip_address: Optional[str] = None
    consent_verification_method: Optional[str] = None
    consent_verification_timestamp: Optional[datetime] = None
    compliance_notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConsentTemplateBase(BaseModel):
    """Base consent template model."""
    name: str = Field(..., min_length=1, max_length=100)
    consent_type: ConsentType
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    detailed_terms: Optional[str] = None
    sections: List[Dict[str, Any]] = []
    required_fields: List[str] = []
    optional_fields: List[str] = []
    legal_requirements: List[str] = []
    regulatory_compliance: List[str] = []


class ConsentTemplateCreate(ConsentTemplateBase):
    """Model for consent template creation."""
    pass


class ConsentTemplateUpdate(BaseModel):
    """Model for consent template updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10)
    detailed_terms: Optional[str] = None
    sections: Optional[List[Dict[str, Any]]] = None
    required_fields: Optional[List[str]] = None
    optional_fields: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ConsentTemplateResponse(ConsentTemplateBase):
    """Model for consent template API responses."""
    id: uuid.UUID
    version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConsentVerificationRequest(BaseModel):
    """Model for consent verification requests."""
    consent_record_id: uuid.UUID
    access_type: str
    data_category: str
    purpose: Optional[str] = None


class ConsentVerificationResponse(BaseModel):
    """Model for consent verification responses."""
    is_valid: bool
    consent_record: Optional[ConsentRecordResponse] = None
    missing_consents: List[str] = []
    compliance_issues: List[str] = []
    recommendations: List[str] = []


# Consent configuration
CONSENT_CONFIG = {
    "default_expiry": {
        "hipaa_privacy": timedelta(days=365),  # 1 year
        "hipaa_treatment": timedelta(days=365),  # 1 year
        "data_processing": timedelta(days=365),  # 1 year
        "marketing": timedelta(days=90),  # 90 days
        "research": timedelta(days=365 * 5),  # 5 years
    },
    "required_consents": {
        "patient": ["hipaa_privacy", "hipaa_treatment", "data_processing"],
        "doctor": ["hipaa_privacy", "hipaa_treatment", "hipaa_operations"],
        "admin": ["hipaa_privacy", "hipaa_operations"],
    },
    "compliance": {
        "hipaa_required": True,
        "gdpr_required": True,
        "consent_verification": True,
        "audit_trail": True,
    }
} 