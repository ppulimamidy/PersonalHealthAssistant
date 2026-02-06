"""
User Profile Models Module

This module contains all the data models for the user profile service including:
- User profiles
- User preferences
- Privacy settings
- Health attributes
- Profile validation schemas
"""

from .user_stub import User, UserStatus, UserType
from .profile import Profile, ProfileCreate, ProfileUpdate, ProfileResponse, Base
from .preferences import Preferences, PreferencesCreate, PreferencesUpdate, PreferencesResponse
from .health_attributes import HealthAttributes, HealthAttributesCreate, HealthAttributesUpdate
from .privacy_settings import PrivacySettings, PrivacySettingsCreate, PrivacySettingsUpdate

__all__ = [
    "User",
    "UserStatus", 
    "UserType",
    "Profile",
    "ProfileCreate", 
    "ProfileUpdate",
    "ProfileResponse",
    "Preferences",
    "PreferencesCreate",
    "PreferencesUpdate", 
    "PreferencesResponse",
    "HealthAttributes",
    "HealthAttributesCreate",
    "HealthAttributesUpdate",
    "PrivacySettings",
    "PrivacySettingsCreate",
    "PrivacySettingsUpdate",
    "Base"
] 