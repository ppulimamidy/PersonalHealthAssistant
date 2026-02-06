"""
Privacy Settings Models

This module contains privacy settings models including:
- PrivacySettings: User privacy preferences
- PrivacySettingsCreate: Schema for creating privacy settings
- PrivacySettingsUpdate: Schema for updating privacy settings
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from common.models.base import Base


class DataCategory(str, Enum):
    """Data categories for privacy controls"""
    PERSONAL_INFO = "personal_info"
    HEALTH_DATA = "health_data"
    MEDICAL_RECORDS = "medical_records"
    ACTIVITY_DATA = "activity_data"
    NUTRITION_DATA = "nutrition_data"
    SLEEP_DATA = "sleep_data"
    LOCATION_DATA = "location_data"
    DEVICE_DATA = "device_data"
    ANALYTICS_DATA = "analytics_data"
    RESEARCH_DATA = "research_data"


class SharingLevel(str, Enum):
    """Data sharing levels"""
    PRIVATE = "private"
    PROVIDERS_ONLY = "providers_only"
    RESEARCH_ONLY = "research_only"
    PUBLIC = "public"
    ANONYMOUS = "anonymous"


class ConsentStatus(str, Enum):
    """Consent status options"""
    GRANTED = "granted"
    DENIED = "denied"
    PENDING = "pending"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class PrivacySettings(Base):
    """Privacy settings model"""
    __tablename__ = "privacy_settings"
    __table_args__ = {'extend_existing': True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), unique=True, nullable=False, index=True)
    
    # General Privacy Settings
    profile_visibility = Column(String(20), default=SharingLevel.PRIVATE)  # Profile visibility level
    allow_profile_search = Column(Boolean, default=False)  # Allow others to search for profile
    show_online_status = Column(Boolean, default=False)  # Show online status to others
    
    # Data Sharing Settings
    share_personal_info = Column(Boolean, default=False)  # Share personal information
    share_health_data = Column(Boolean, default=True)  # Share health data with providers
    share_medical_records = Column(Boolean, default=True)  # Share medical records
    share_activity_data = Column(Boolean, default=False)  # Share activity data
    share_nutrition_data = Column(Boolean, default=False)  # Share nutrition data
    share_sleep_data = Column(Boolean, default=False)  # Share sleep data
    share_location_data = Column(Boolean, default=False)  # Share location data
    share_device_data = Column(Boolean, default=True)  # Share device data for health monitoring
    
    # Provider Sharing Settings
    share_with_primary_care = Column(Boolean, default=True)  # Share with primary care provider
    share_with_specialists = Column(Boolean, default=True)  # Share with specialists
    share_with_emergency_services = Column(Boolean, default=True)  # Share with emergency services
    share_with_pharmacies = Column(Boolean, default=False)  # Share with pharmacies
    share_with_insurance = Column(Boolean, default=False)  # Share with insurance companies
    
    # Research and Analytics Settings
    share_for_research = Column(Boolean, default=False)  # Share data for research
    share_for_analytics = Column(Boolean, default=True)  # Share for analytics (anonymous)
    share_for_ai_training = Column(Boolean, default=False)  # Share for AI model training
    share_for_public_health = Column(Boolean, default=False)  # Share for public health initiatives
    
    # Third-Party Sharing Settings
    share_with_family_members = Column(Boolean, default=False)  # Share with family members
    share_with_caregivers = Column(Boolean, default=False)  # Share with caregivers
    share_with_fitness_apps = Column(Boolean, default=False)  # Share with fitness apps
    share_with_health_apps = Column(Boolean, default=False)  # Share with health apps
    
    # Data Retention Settings
    data_retention_period = Column(Integer, default=7)  # Years to retain data
    auto_delete_inactive = Column(Boolean, default=False)  # Auto-delete inactive accounts
    delete_on_account_closure = Column(Boolean, default=True)  # Delete data on account closure
    
    # Notification Settings
    notify_data_access = Column(Boolean, default=True)  # Notify when data is accessed
    notify_data_sharing = Column(Boolean, default=True)  # Notify when data is shared
    notify_privacy_changes = Column(Boolean, default=True)  # Notify of privacy setting changes
    notify_breach_alerts = Column(Boolean, default=True)  # Notify of data breaches
    
    # Consent Management
    consent_history = Column(JSON, default=list)  # History of consent decisions
    consent_expiry_dates = Column(JSON, default=dict)  # Expiry dates for consents
    consent_renewal_reminders = Column(Boolean, default=True)  # Remind to renew consents
    
    # Advanced Privacy Settings
    enable_data_encryption = Column(Boolean, default=True)  # Enable data encryption
    enable_two_factor_auth = Column(Boolean, default=True)  # Enable 2FA for privacy
    enable_audit_logging = Column(Boolean, default=True)  # Enable audit logging
    enable_data_export = Column(Boolean, default=True)  # Enable data export
    
    # Custom Privacy Rules
    custom_privacy_rules = Column(JSON, default=dict)  # Custom privacy rules
    
    # Timestamps
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships - temporarily disabled to fix SQLAlchemy conflict
    # user = relationship("apps.user_profile.models.user_stub.User", back_populates="privacy_settings")
    # profile = relationship("Profile", back_populates="privacy_settings")


# Pydantic Models for API
class PrivacySettingsBase(BaseModel):
    """Base privacy settings schema"""
    # General Privacy Settings
    profile_visibility: SharingLevel = Field(default=SharingLevel.PRIVATE, description="Profile visibility level")
    allow_profile_search: bool = Field(default=False, description="Allow others to search for profile")
    show_online_status: bool = Field(default=False, description="Show online status to others")
    
    # Data Sharing Settings
    share_personal_info: bool = Field(default=False, description="Share personal information")
    share_health_data: bool = Field(default=True, description="Share health data with providers")
    share_medical_records: bool = Field(default=True, description="Share medical records")
    share_activity_data: bool = Field(default=False, description="Share activity data")
    share_nutrition_data: bool = Field(default=False, description="Share nutrition data")
    share_sleep_data: bool = Field(default=False, description="Share sleep data")
    share_location_data: bool = Field(default=False, description="Share location data")
    share_device_data: bool = Field(default=True, description="Share device data for health monitoring")
    
    # Provider Sharing Settings
    share_with_primary_care: bool = Field(default=True, description="Share with primary care provider")
    share_with_specialists: bool = Field(default=True, description="Share with specialists")
    share_with_emergency_services: bool = Field(default=True, description="Share with emergency services")
    share_with_pharmacies: bool = Field(default=False, description="Share with pharmacies")
    share_with_insurance: bool = Field(default=False, description="Share with insurance companies")
    
    # Research and Analytics Settings
    share_for_research: bool = Field(default=False, description="Share data for research")
    share_for_analytics: bool = Field(default=True, description="Share for analytics (anonymous)")
    share_for_ai_training: bool = Field(default=False, description="Share for AI model training")
    share_for_public_health: bool = Field(default=False, description="Share for public health initiatives")
    
    # Third-Party Sharing Settings
    share_with_family_members: bool = Field(default=False, description="Share with family members")
    share_with_caregivers: bool = Field(default=False, description="Share with caregivers")
    share_with_fitness_apps: bool = Field(default=False, description="Share with fitness apps")
    share_with_health_apps: bool = Field(default=False, description="Share with health apps")
    
    # Data Retention Settings
    data_retention_period: int = Field(default=7, ge=1, le=50, description="Years to retain data")
    auto_delete_inactive: bool = Field(default=False, description="Auto-delete inactive accounts")
    delete_on_account_closure: bool = Field(default=True, description="Delete data on account closure")
    
    # Notification Settings
    notify_data_access: bool = Field(default=True, description="Notify when data is accessed")
    notify_data_sharing: bool = Field(default=True, description="Notify when data is shared")
    notify_privacy_changes: bool = Field(default=True, description="Notify of privacy setting changes")
    notify_breach_alerts: bool = Field(default=True, description="Notify of data breaches")
    
    # Consent Management
    consent_history: List[dict] = Field(default_factory=list, description="History of consent decisions")
    consent_expiry_dates: dict = Field(default_factory=dict, description="Expiry dates for consents")
    consent_renewal_reminders: bool = Field(default=True, description="Remind to renew consents")
    
    # Advanced Privacy Settings
    enable_data_encryption: bool = Field(default=True, description="Enable data encryption")
    enable_two_factor_auth: bool = Field(default=True, description="Enable 2FA for privacy")
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging")
    enable_data_export: bool = Field(default=True, description="Enable data export")
    
    # Custom Privacy Rules
    custom_privacy_rules: dict = Field(default_factory=dict, description="Custom privacy rules")

    @validator('data_retention_period')
    def validate_retention_period(cls, v):
        """Validate data retention period"""
        if v < 1 or v > 50:
            raise ValueError('Data retention period must be between 1 and 50 years')
        return v


class PrivacySettingsCreate(PrivacySettingsBase):
    """Schema for creating privacy settings"""
    user_id: uuid.UUID = Field(..., description="Associated user ID")
    profile_id: int = Field(..., description="Associated profile ID")


class PrivacySettingsUpdate(BaseModel):
    """Schema for updating privacy settings (all fields optional)"""
    # General Privacy Settings
    profile_visibility: Optional[SharingLevel] = None
    allow_profile_search: Optional[bool] = None
    show_online_status: Optional[bool] = None
    
    # Data Sharing Settings
    share_personal_info: Optional[bool] = None
    share_health_data: Optional[bool] = None
    share_medical_records: Optional[bool] = None
    share_activity_data: Optional[bool] = None
    share_nutrition_data: Optional[bool] = None
    share_sleep_data: Optional[bool] = None
    share_location_data: Optional[bool] = None
    share_device_data: Optional[bool] = None
    
    # Provider Sharing Settings
    share_with_primary_care: Optional[bool] = None
    share_with_specialists: Optional[bool] = None
    share_with_emergency_services: Optional[bool] = None
    share_with_pharmacies: Optional[bool] = None
    share_with_insurance: Optional[bool] = None
    
    # Research and Analytics Settings
    share_for_research: Optional[bool] = None
    share_for_analytics: Optional[bool] = None
    share_for_ai_training: Optional[bool] = None
    share_for_public_health: Optional[bool] = None
    
    # Third-Party Sharing Settings
    share_with_family_members: Optional[bool] = None
    share_with_caregivers: Optional[bool] = None
    share_with_fitness_apps: Optional[bool] = None
    share_with_health_apps: Optional[bool] = None
    
    # Data Retention Settings
    data_retention_period: Optional[int] = Field(None, ge=1, le=50)
    auto_delete_inactive: Optional[bool] = None
    delete_on_account_closure: Optional[bool] = None
    
    # Notification Settings
    notify_data_access: Optional[bool] = None
    notify_data_sharing: Optional[bool] = None
    notify_privacy_changes: Optional[bool] = None
    notify_breach_alerts: Optional[bool] = None
    
    # Consent Management
    consent_history: Optional[List[dict]] = None
    consent_expiry_dates: Optional[dict] = None
    consent_renewal_reminders: Optional[bool] = None
    
    # Advanced Privacy Settings
    enable_data_encryption: Optional[bool] = None
    enable_two_factor_auth: Optional[bool] = None
    enable_audit_logging: Optional[bool] = None
    enable_data_export: Optional[bool] = None
    
    # Custom Privacy Rules
    custom_privacy_rules: Optional[dict] = None

    @validator('data_retention_period')
    def validate_retention_period(cls, v):
        """Validate data retention period"""
        if v and (v < 1 or v > 50):
            raise ValueError('Data retention period must be between 1 and 50 years')
        return v


class PrivacySettingsResponse(PrivacySettingsBase):
    """Schema for privacy settings API responses"""
    id: int
    user_id: uuid.UUID
    profile_id: int
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class DataSharingSummary(BaseModel):
    """Simplified data sharing summary"""
    share_health_data: bool
    share_medical_records: bool
    share_for_research: bool
    share_for_analytics: bool
    profile_visibility: SharingLevel
    last_updated: datetime

    class Config:
        from_attributes = True


class ConsentRecord(BaseModel):
    """Individual consent record"""
    data_category: DataCategory
    sharing_level: SharingLevel
    status: ConsentStatus
    granted_at: datetime
    expires_at: Optional[datetime]
    description: str
    version: str

    class Config:
        from_attributes = True 