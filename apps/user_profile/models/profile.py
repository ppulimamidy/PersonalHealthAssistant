"""
User Profile Models

This module contains the core user profile models including:
- Profile: Main user profile with personal information
- ProfileCreate: Schema for creating new profiles
- ProfileUpdate: Schema for updating profiles
- ProfileResponse: Schema for API responses
"""

from datetime import datetime, date
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import Column, String, DateTime, Date, Text, Boolean, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, ENUM
import uuid

from common.models.base import Base
from .user_stub import User  # Import the User stub model


class Gender(str, Enum):
    """Gender options for user profiles"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class MaritalStatus(str, Enum):
    """Marital status options"""
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"
    PARTNERED = "partnered"


class BloodType(str, Enum):
    """Blood type options"""
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"


class ActivityLevel(str, Enum):
    """Physical activity level"""
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"


class Profile(Base):
    """User profile model"""
    __tablename__ = "user_profiles"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    preferred_name = Column(String(100))
    date_of_birth = Column(Date, nullable=False)
    gender = Column(ENUM('male', 'female', 'other', 'prefer_not_to_say', name='gender'), nullable=False)
    marital_status = Column(ENUM('single', 'married', 'divorced', 'widowed', 'separated', 'partnered', name='maritalstatus'))
    
    # Contact Information
    email = Column(String(255), nullable=False, index=True)
    phone_number = Column(String(20))
    emergency_contact_name = Column(String(200))
    emergency_contact_phone = Column(String(20))
    emergency_contact_relationship = Column(String(100))
    
    # Address Information
    address_line_1 = Column(String(255))
    address_line_2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    
    # Health Information
    blood_type = Column(ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', name='bloodtype'))
    height_cm = Column(Integer)  # Height in centimeters
    weight_kg = Column(Integer)  # Weight in kilograms
    activity_level = Column(ENUM('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active', name='activitylevel'))
    allergies = Column(Text)  # JSON string of allergies
    medications = Column(Text)  # JSON string of current medications
    medical_conditions = Column(Text)  # JSON string of medical conditions
    family_history = Column(Text)  # JSON string of family medical history
    
    # Additional Information
    occupation = Column(String(200))
    employer = Column(String(200))
    education_level = Column(String(100))
    insurance_provider = Column(String(200))
    insurance_policy_number = Column(String(100))
    
    # Profile Status
    is_complete = Column(Boolean, default=False)
    completion_percentage = Column(Integer, default=0)  # 0-100
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships - temporarily disabled to fix SQLAlchemy conflict
    # user = relationship("apps.user_profile.models.user_stub.User", back_populates="profile")
    # preferences = relationship("Preferences", back_populates="profile", uselist=False)
    # privacy_settings = relationship("PrivacySettings", back_populates="profile", uselist=False)
    # health_attributes = relationship("HealthAttributes", back_populates="profile", uselist=False)


# Pydantic Models for API
class ProfileBase(BaseModel):
    """Base profile schema"""
    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    middle_name: Optional[str] = Field(None, max_length=100, description="User's middle name")
    preferred_name: Optional[str] = Field(None, max_length=100, description="User's preferred name")
    date_of_birth: date = Field(..., description="User's date of birth")
    gender: Gender = Field(..., description="User's gender")
    marital_status: Optional[MaritalStatus] = Field(None, description="User's marital status")
    
    # Contact Information
    email: EmailStr = Field(..., description="User's email address")
    phone_number: Optional[str] = Field(None, max_length=20, description="User's phone number")
    emergency_contact_name: Optional[str] = Field(None, max_length=200, description="Emergency contact name")
    emergency_contact_phone: Optional[str] = Field(None, max_length=20, description="Emergency contact phone")
    emergency_contact_relationship: Optional[str] = Field(None, max_length=100, description="Relationship to emergency contact")
    
    # Address Information
    address_line_1: Optional[str] = Field(None, max_length=255, description="Primary address line")
    address_line_2: Optional[str] = Field(None, max_length=255, description="Secondary address line")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=100, description="State/Province")
    postal_code: Optional[str] = Field(None, max_length=20, description="Postal/ZIP code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    
    # Health Information
    blood_type: Optional[BloodType] = Field(None, description="User's blood type")
    height_cm: Optional[int] = Field(None, ge=50, le=300, description="Height in centimeters")
    weight_kg: Optional[int] = Field(None, ge=20, le=500, description="Weight in kilograms")
    activity_level: Optional[ActivityLevel] = Field(None, description="Physical activity level")
    allergies: Optional[str] = Field(None, description="JSON string of allergies")
    medications: Optional[str] = Field(None, description="JSON string of current medications")
    medical_conditions: Optional[str] = Field(None, description="JSON string of medical conditions")
    family_history: Optional[str] = Field(None, description="JSON string of family medical history")
    
    # Additional Information
    occupation: Optional[str] = Field(None, max_length=200, description="User's occupation")
    employer: Optional[str] = Field(None, max_length=200, description="User's employer")
    education_level: Optional[str] = Field(None, max_length=100, description="User's education level")
    insurance_provider: Optional[str] = Field(None, max_length=200, description="Insurance provider")
    insurance_policy_number: Optional[str] = Field(None, max_length=100, description="Insurance policy number")

    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth is not in the future and reasonable"""
        if v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        if v < date(1900, 1, 1):
            raise ValueError('Date of birth seems too far in the past')
        return v

    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Phone number must contain only digits, spaces, dashes, parentheses, and plus sign')
        return v

    @validator('emergency_contact_phone')
    def validate_emergency_phone(cls, v):
        """Validate emergency contact phone number format"""
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Emergency contact phone number must contain only digits, spaces, dashes, parentheses, and plus sign')
        return v


class ProfileCreate(ProfileBase):
    """Schema for creating a new profile"""
    user_id: uuid.UUID = Field(..., description="Associated user ID")


class ProfileUpdate(BaseModel):
    """Schema for updating a profile (all fields optional)"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    marital_status: Optional[MaritalStatus] = None
    
    # Contact Information
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=100)
    
    # Address Information
    address_line_1: Optional[str] = Field(None, max_length=255)
    address_line_2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    
    # Health Information
    blood_type: Optional[BloodType] = None
    height_cm: Optional[int] = Field(None, ge=50, le=300)
    weight_kg: Optional[int] = Field(None, ge=20, le=500)
    activity_level: Optional[ActivityLevel] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    medical_conditions: Optional[str] = None
    family_history: Optional[str] = None
    
    # Additional Information
    occupation: Optional[str] = Field(None, max_length=200)
    employer: Optional[str] = Field(None, max_length=200)
    education_level: Optional[str] = Field(None, max_length=100)
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)

    @validator('date_of_birth')
    def validate_date_of_birth(cls, v):
        """Validate date of birth is not in the future and reasonable"""
        if v and v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        if v and v < date(1900, 1, 1):
            raise ValueError('Date of birth seems too far in the past')
        return v

    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Phone number must contain only digits, spaces, dashes, parentheses, and plus sign')
        return v

    @validator('emergency_contact_phone')
    def validate_emergency_phone(cls, v):
        """Validate emergency contact phone number format"""
        if v and not v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Emergency contact phone number must contain only digits, spaces, dashes, parentheses, and plus sign')
        return v


class ProfileResponse(ProfileBase):
    """Schema for profile API responses"""
    id: int
    user_id: uuid.UUID
    is_complete: bool
    completion_percentage: int
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ProfileSummary(BaseModel):
    """Simplified profile for summary views"""
    id: int
    user_id: uuid.UUID
    first_name: str
    last_name: str
    preferred_name: Optional[str]
    email: str
    date_of_birth: date
    gender: Gender
    is_complete: bool
    completion_percentage: int
    last_updated: datetime

    class Config:
        from_attributes = True 