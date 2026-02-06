"""
User Preferences Models

This module contains user preference models including:
- Preferences: Main user preferences
- PreferencesCreate: Schema for creating preferences
- PreferencesUpdate: Schema for updating preferences
- PreferencesResponse: Schema for API responses
"""

from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from common.models.base import Base


class NotificationType(str, Enum):
    """Types of notifications"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationFrequency(str, Enum):
    """Notification frequency options"""
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    NEVER = "never"


class Theme(str, Enum):
    """UI theme options"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class Language(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"


class Units(str, Enum):
    """Measurement units"""
    METRIC = "metric"
    IMPERIAL = "imperial"


class Preferences(Base):
    """User preferences model"""
    __tablename__ = "user_preferences"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("user_profiles.id"), unique=True, nullable=False, index=True)
    
    # Notification Preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    push_notifications = Column(Boolean, default=True)
    in_app_notifications = Column(Boolean, default=True)
    
    # Notification Types
    health_alerts = Column(Boolean, default=True)
    medication_reminders = Column(Boolean, default=True)
    appointment_reminders = Column(Boolean, default=True)
    lab_result_notifications = Column(Boolean, default=True)
    wellness_tips = Column(Boolean, default=True)
    research_updates = Column(Boolean, default=False)
    marketing_emails = Column(Boolean, default=False)
    
    # Notification Frequency
    health_alert_frequency = Column(String(20), default=NotificationFrequency.IMMEDIATE)
    medication_reminder_frequency = Column(String(20), default=NotificationFrequency.DAILY)
    appointment_reminder_frequency = Column(String(20), default=NotificationFrequency.DAILY)
    lab_result_frequency = Column(String(20), default=NotificationFrequency.IMMEDIATE)
    wellness_tip_frequency = Column(String(20), default=NotificationFrequency.WEEKLY)
    research_update_frequency = Column(String(20), default=NotificationFrequency.MONTHLY)
    
    # UI Preferences
    theme = Column(String(20), default=Theme.AUTO)
    language = Column(String(10), default=Language.ENGLISH)
    units = Column(String(20), default=Units.METRIC)
    timezone = Column(String(50), default="UTC")
    date_format = Column(String(20), default="MM/DD/YYYY")
    time_format = Column(String(20), default="12-hour")
    
    # Privacy Preferences
    share_data_with_providers = Column(Boolean, default=True)
    share_data_for_research = Column(Boolean, default=False)
    share_anonymous_data = Column(Boolean, default=True)
    allow_location_tracking = Column(Boolean, default=False)
    allow_analytics_tracking = Column(Boolean, default=True)
    
    # Health Tracking Preferences
    auto_track_activity = Column(Boolean, default=True)
    auto_track_sleep = Column(Boolean, default=True)
    auto_track_heart_rate = Column(Boolean, default=True)
    auto_track_steps = Column(Boolean, default=True)
    auto_track_weight = Column(Boolean, default=False)
    auto_track_blood_pressure = Column(Boolean, default=False)
    auto_track_blood_glucose = Column(Boolean, default=False)
    
    # Custom Preferences (JSON)
    custom_preferences = Column(JSON, default=dict)
    
    # Timestamps
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships - temporarily disabled to fix SQLAlchemy conflict
    # user = relationship("apps.user_profile.models.user_stub.User", back_populates="preferences")
    # profile = relationship("Profile", back_populates="preferences")


# Pydantic Models for API
class PreferencesBase(BaseModel):
    """Base preferences schema"""
    # Notification Preferences
    email_notifications: bool = Field(default=True, description="Enable email notifications")
    sms_notifications: bool = Field(default=False, description="Enable SMS notifications")
    push_notifications: bool = Field(default=True, description="Enable push notifications")
    in_app_notifications: bool = Field(default=True, description="Enable in-app notifications")
    
    # Notification Types
    health_alerts: bool = Field(default=True, description="Receive health alerts")
    medication_reminders: bool = Field(default=True, description="Receive medication reminders")
    appointment_reminders: bool = Field(default=True, description="Receive appointment reminders")
    lab_result_notifications: bool = Field(default=True, description="Receive lab result notifications")
    wellness_tips: bool = Field(default=True, description="Receive wellness tips")
    research_updates: bool = Field(default=False, description="Receive research updates")
    marketing_emails: bool = Field(default=False, description="Receive marketing emails")
    
    # Notification Frequency
    health_alert_frequency: NotificationFrequency = Field(default=NotificationFrequency.IMMEDIATE)
    medication_reminder_frequency: NotificationFrequency = Field(default=NotificationFrequency.DAILY)
    appointment_reminder_frequency: NotificationFrequency = Field(default=NotificationFrequency.DAILY)
    lab_result_frequency: NotificationFrequency = Field(default=NotificationFrequency.IMMEDIATE)
    wellness_tip_frequency: NotificationFrequency = Field(default=NotificationFrequency.WEEKLY)
    research_update_frequency: NotificationFrequency = Field(default=NotificationFrequency.MONTHLY)
    
    # UI Preferences
    theme: Theme = Field(default=Theme.AUTO, description="UI theme preference")
    language: Language = Field(default=Language.ENGLISH, description="Preferred language")
    units: Units = Field(default=Units.METRIC, description="Measurement units preference")
    timezone: str = Field(default="UTC", description="User's timezone")
    date_format: str = Field(default="MM/DD/YYYY", description="Preferred date format")
    time_format: str = Field(default="12-hour", description="Preferred time format")
    
    # Privacy Preferences
    share_data_with_providers: bool = Field(default=True, description="Share data with healthcare providers")
    share_data_for_research: bool = Field(default=False, description="Share data for research purposes")
    share_anonymous_data: bool = Field(default=True, description="Share anonymous data for analytics")
    allow_location_tracking: bool = Field(default=False, description="Allow location tracking")
    allow_analytics_tracking: bool = Field(default=True, description="Allow analytics tracking")
    
    # Health Tracking Preferences
    auto_track_activity: bool = Field(default=True, description="Automatically track activity")
    auto_track_sleep: bool = Field(default=True, description="Automatically track sleep")
    auto_track_heart_rate: bool = Field(default=True, description="Automatically track heart rate")
    auto_track_steps: bool = Field(default=True, description="Automatically track steps")
    auto_track_weight: bool = Field(default=False, description="Automatically track weight")
    auto_track_blood_pressure: bool = Field(default=False, description="Automatically track blood pressure")
    auto_track_blood_glucose: bool = Field(default=False, description="Automatically track blood glucose")
    
    # Custom Preferences
    custom_preferences: dict = Field(default_factory=dict, description="Custom user preferences")

    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate timezone format"""
        # Basic validation - could be enhanced with pytz
        if v and len(v) > 50:
            raise ValueError('Timezone string too long')
        return v

    @validator('date_format')
    def validate_date_format(cls, v):
        """Validate date format"""
        valid_formats = ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD", "MM-DD-YYYY", "DD-MM-YYYY"]
        if v not in valid_formats:
            raise ValueError(f'Date format must be one of: {", ".join(valid_formats)}')
        return v

    @validator('time_format')
    def validate_time_format(cls, v):
        """Validate time format"""
        valid_formats = ["12-hour", "24-hour"]
        if v not in valid_formats:
            raise ValueError('Time format must be either "12-hour" or "24-hour"')
        return v


class PreferencesCreate(PreferencesBase):
    """Schema for creating new preferences"""
    user_id: uuid.UUID = Field(..., description="Associated user ID")
    profile_id: int = Field(..., description="Associated profile ID")


class PreferencesUpdate(BaseModel):
    """Schema for updating preferences (all fields optional)"""
    # Notification Preferences
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    in_app_notifications: Optional[bool] = None
    
    # Notification Types
    health_alerts: Optional[bool] = None
    medication_reminders: Optional[bool] = None
    appointment_reminders: Optional[bool] = None
    lab_result_notifications: Optional[bool] = None
    wellness_tips: Optional[bool] = None
    research_updates: Optional[bool] = None
    marketing_emails: Optional[bool] = None
    
    # Notification Frequency
    health_alert_frequency: Optional[NotificationFrequency] = None
    medication_reminder_frequency: Optional[NotificationFrequency] = None
    appointment_reminder_frequency: Optional[NotificationFrequency] = None
    lab_result_frequency: Optional[NotificationFrequency] = None
    wellness_tip_frequency: Optional[NotificationFrequency] = None
    research_update_frequency: Optional[NotificationFrequency] = None
    
    # UI Preferences
    theme: Optional[Theme] = None
    language: Optional[Language] = None
    units: Optional[Units] = None
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    time_format: Optional[str] = None
    
    # Privacy Preferences
    share_data_with_providers: Optional[bool] = None
    share_data_for_research: Optional[bool] = None
    share_anonymous_data: Optional[bool] = None
    allow_location_tracking: Optional[bool] = None
    allow_analytics_tracking: Optional[bool] = None
    
    # Health Tracking Preferences
    auto_track_activity: Optional[bool] = None
    auto_track_sleep: Optional[bool] = None
    auto_track_heart_rate: Optional[bool] = None
    auto_track_steps: Optional[bool] = None
    auto_track_weight: Optional[bool] = None
    auto_track_blood_pressure: Optional[bool] = None
    auto_track_blood_glucose: Optional[bool] = None
    
    # Custom Preferences
    custom_preferences: Optional[dict] = None

    @validator('timezone')
    def validate_timezone(cls, v):
        """Validate timezone format"""
        if v and len(v) > 50:
            raise ValueError('Timezone string too long')
        return v

    @validator('date_format')
    def validate_date_format(cls, v):
        """Validate date format"""
        if v:
            valid_formats = ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD", "MM-DD-YYYY", "DD-MM-YYYY"]
            if v not in valid_formats:
                raise ValueError(f'Date format must be one of: {", ".join(valid_formats)}')
        return v

    @validator('time_format')
    def validate_time_format(cls, v):
        """Validate time format"""
        if v:
            valid_formats = ["12-hour", "24-hour"]
            if v not in valid_formats:
                raise ValueError('Time format must be either "12-hour" or "24-hour"')
        return v


class PreferencesResponse(PreferencesBase):
    """Schema for preferences API responses"""
    id: int
    user_id: uuid.UUID
    profile_id: int
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationSettings(BaseModel):
    """Simplified notification settings for quick updates"""
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True
    in_app_notifications: bool = True
    health_alerts: bool = True
    medication_reminders: bool = True
    appointment_reminders: bool = True
    lab_result_notifications: bool = True
    wellness_tips: bool = True
    research_updates: bool = False
    marketing_emails: bool = False


class PrivacySettings(BaseModel):
    """Simplified privacy settings for quick updates"""
    share_data_with_providers: bool = True
    share_data_for_research: bool = False
    share_anonymous_data: bool = True
    allow_location_tracking: bool = False
    allow_analytics_tracking: bool = True 