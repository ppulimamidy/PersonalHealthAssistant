"""
Profile Service

This module provides comprehensive profile management functionality including:
- Profile CRUD operations
- Profile validation and sanitization
- Profile completion tracking
- Profile privacy controls
- Profile data export/import
"""

import json
import sys
import os
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status, Depends

# Add parent directories to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common.utils.logging import get_logger
from common.services.base import BaseService
from common.database.connection import get_async_db

from ..models.profile import (
    Profile, ProfileCreate, ProfileUpdate, ProfileResponse, ProfileSummary,
    Gender, MaritalStatus, BloodType, ActivityLevel
)
from ..models.preferences import Preferences, PreferencesCreate
from ..models.privacy_settings import PrivacySettings, PrivacySettingsCreate
from ..models.health_attributes import HealthAttributes, HealthAttributesCreate

logger = get_logger(__name__)


class ProfileService(BaseService):
    """Service for managing user profiles"""
    
    @property
    def model_class(self):
        return Profile

    @property
    def schema_class(self):
        return ProfileResponse

    @property
    def create_schema_class(self):
        return ProfileCreate

    @property
    def update_schema_class(self):
        return ProfileUpdate

    def __init__(self, db: AsyncSession):
        super().__init__(db)
        self.logger = logger

    async def create_profile(self, profile_data: ProfileCreate) -> ProfileResponse:
        """
        Create a new user profile with default preferences and privacy settings.
        
        Args:
            profile_data: Profile creation data
            
        Returns:
            ProfileResponse: Created profile data
            
        Raises:
            HTTPException: If profile creation fails
        """
        try:
            # Check if profile already exists for user
            existing_profile = await self._get_profile_by_user_id(profile_data.user_id)
            if existing_profile:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Profile already exists for this user"
                )
            
            # Create profile
            profile = Profile(**profile_data.dict())
            self.db.add(profile)
            await self.db.flush()  # Get the profile ID
            
            # Create default preferences
            preferences_data = PreferencesCreate(
                user_id=profile_data.user_id,
                profile_id=profile.id
            )
            preferences = Preferences(**preferences_data.dict())
            self.db.add(preferences)
            
            # Create default privacy settings
            privacy_data = PrivacySettingsCreate(
                user_id=profile_data.user_id,
                profile_id=profile.id
            )
            privacy_settings = PrivacySettings(**privacy_data.dict())
            self.db.add(privacy_settings)
            
            # Create default health attributes
            health_data = HealthAttributesCreate(
                user_id=profile_data.user_id,
                profile_id=profile.id
            )
            health_attributes = HealthAttributes(**health_data.dict())
            self.db.add(health_attributes)
            
            await self.db.commit()
            
            # Calculate completion percentage
            await self._update_completion_percentage(profile.id)
            
            # Reload profile with relationships
            await self.db.refresh(profile)
            
            self.logger.info(f"Created profile for user {profile_data.user_id}")
            return ProfileResponse.from_orm(profile)
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to create profile for user {profile_data.user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create profile"
            )

    async def get_profile(self, user_id: str) -> Optional[ProfileResponse]:
        """
        Get user profile by user ID.
        
        Args:
            user_id: User ID (UUID string)
            
        Returns:
            ProfileResponse: Profile data or None if not found
        """
        try:
            profile = await self._get_profile_by_user_id(user_id)
            if not profile:
                # Return None instead of raising an exception when profile doesn't exist
                return None
            
            return ProfileResponse.from_orm(profile)
            
        except Exception as e:
            self.logger.error(f"Failed to get profile for user {user_id}: {e}")
            # Return None instead of raising an exception for database errors
            return None

    async def update_profile(self, user_id: str, profile_data: ProfileUpdate) -> ProfileResponse:
        """
        Update user profile.
        
        Args:
            user_id: User ID (UUID string)
            profile_data: Profile update data
            
        Returns:
            ProfileResponse: Updated profile data
            
        Raises:
            HTTPException: If profile update fails
        """
        try:
            profile = await self._get_profile_by_user_id(user_id)
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found"
                )
            
            # Update profile fields
            update_data = profile_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(profile, field, value)
            
            profile.last_updated = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(profile)
            
            # Update completion percentage
            await self._update_completion_percentage(profile.id)
            
            self.logger.info(f"Updated profile for user {user_id}")
            return ProfileResponse.from_orm(profile)
            
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to update profile for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )

    async def delete_profile(self, user_id: str) -> bool:
        """
        Delete user profile (hard delete: remove profile and all related data).
        Args:
            user_id: User ID (UUID string)
        Returns:
            bool: True if deleted successfully
        Raises:
            HTTPException: If profile deletion fails
        """
        try:
            profile = await self._get_profile_by_user_id(user_id)
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found"
                )
            
            # Delete related data first
            await self.db.execute(
                "DELETE FROM user_preferences WHERE user_id = :user_id", {"user_id": user_id}
            )
            await self.db.execute(
                "DELETE FROM privacy_settings WHERE user_id = :user_id", {"user_id": user_id}
            )
            # Delete health_attributes by profile_id since it has a foreign key constraint
            await self.db.execute(
                "DELETE FROM health_attributes WHERE profile_id = :profile_id", {"profile_id": profile.id}
            )
            
            # Delete the profile itself using raw SQL
            result = await self.db.execute(
                "DELETE FROM user_profiles WHERE user_id = :user_id", {"user_id": user_id}
            )
            
            await self.db.commit()
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found"
                )
            
            self.logger.info(f"Hard deleted profile and related data for user {user_id}")
            return True
        except HTTPException:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to hard delete profile for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete profile"
            )

    async def get_profile_summary(self, user_id: str) -> Optional[ProfileSummary]:
        """
        Get profile summary for quick views.
        
        Args:
            user_id: User ID (UUID string)
            
        Returns:
            ProfileSummary: Profile summary or None if not found
        """
        try:
            profile = await self._get_profile_by_user_id(user_id)
            if not profile:
                return None
            
            return ProfileSummary.from_orm(profile)
            
        except Exception as e:
            self.logger.error(f"Failed to get profile summary for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve profile summary"
            )

    async def validate_profile_data(self, profile_data: ProfileUpdate) -> Dict[str, Any]:
        """
        Validate profile data and return validation results.
        
        Args:
            profile_data: Profile data to validate
            
        Returns:
            Dict[str, Any]: Validation results
        """
        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "completion_percentage": 0
        }
        
        # Required fields validation
        required_fields = ["first_name", "last_name", "date_of_birth", "gender", "email"]
        for field in required_fields:
            if not getattr(profile_data, field, None):
                validation_results["errors"].append(f"Missing required field: {field}")
                validation_results["is_valid"] = False
        
        # Email validation
        if profile_data.email:
            # Basic email validation (more comprehensive validation in Pydantic)
            if "@" not in profile_data.email or "." not in profile_data.email:
                validation_results["errors"].append("Invalid email format")
                validation_results["is_valid"] = False
        
        # Date of birth validation
        if profile_data.date_of_birth:
            if profile_data.date_of_birth > date.today():
                validation_results["errors"].append("Date of birth cannot be in the future")
                validation_results["is_valid"] = False
            elif profile_data.date_of_birth < date(1900, 1, 1):
                validation_results["warnings"].append("Date of birth seems too far in the past")
        
        # Phone number validation
        if profile_data.phone_number:
            phone_clean = profile_data.phone_number.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            if not phone_clean.isdigit():
                validation_results["errors"].append("Invalid phone number format")
                validation_results["is_valid"] = False
        
        # Calculate completion percentage
        completion_percentage = await self._calculate_completion_percentage(profile_data)
        validation_results["completion_percentage"] = completion_percentage
        
        return validation_results

    async def export_profile_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all profile data for user.
        
        Args:
            user_id: User ID (UUID string)
            
        Returns:
            Dict[str, Any]: Complete profile data export
            
        Raises:
            HTTPException: If export fails
        """
        try:
            profile = await self._get_profile_by_user_id(user_id)
            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Profile not found"
                )
            
            # Get related data
            preferences = await self._get_preferences_by_user_id(user_id)
            privacy_settings = await self._get_privacy_settings_by_user_id(user_id)
            health_attributes = await self._get_health_attributes_by_user_id(user_id)
            
            export_data = {
                "export_date": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "profile": ProfileResponse.from_orm(profile).dict(),
                "preferences": preferences.dict() if preferences else {},
                "privacy_settings": privacy_settings.dict() if privacy_settings else {},
                "health_attributes": health_attributes.dict() if health_attributes else {}
            }
            
            self.logger.info(f"Exported profile data for user {user_id}")
            return export_data
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to export profile data for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to export profile data"
            )

    async def import_profile_data(self, user_id: str, import_data: Dict[str, Any]) -> ProfileResponse:
        """
        Import profile data for user.
        
        Args:
            user_id: User ID (UUID string)
            import_data: Profile data to import
            
        Returns:
            ProfileResponse: Imported profile data
            
        Raises:
            HTTPException: If import fails
        """
        try:
            # Validate import data
            if "profile" not in import_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid import data: missing profile"
                )
            
            profile_data = import_data["profile"]
            profile_data["user_id"] = user_id
            
            # Check if profile exists
            existing_profile = await self._get_profile_by_user_id(user_id)
            if existing_profile:
                # Update existing profile
                update_data = ProfileUpdate(**profile_data)
                return await self.update_profile(user_id, update_data)
            else:
                # Create new profile
                create_data = ProfileCreate(**profile_data)
                return await self.create_profile(create_data)
                
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to import profile data for user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to import profile data"
            )

    # Private helper methods
    async def _get_profile_by_user_id(self, user_id: str) -> Optional[Profile]:
        """Get profile by user ID with relationships loaded."""
        query = select(Profile).where(Profile.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_preferences_by_user_id(self, user_id: str) -> Optional[Preferences]:
        """Get preferences by user ID."""
        query = select(Preferences).where(Preferences.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_privacy_settings_by_user_id(self, user_id: str) -> Optional[PrivacySettings]:
        """Get privacy settings by user ID."""
        query = select(PrivacySettings).where(PrivacySettings.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_health_attributes_by_user_id(self, user_id: str) -> Optional[HealthAttributes]:
        """Get health attributes by user ID."""
        query = select(HealthAttributes).where(HealthAttributes.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _update_completion_percentage(self, profile_id: int) -> None:
        """Update profile completion percentage."""
        try:
            profile = await self.db.get(Profile, profile_id)
            if profile:
                completion_percentage = await self._calculate_completion_percentage_from_profile(profile)
                profile.completion_percentage = completion_percentage
                profile.is_complete = completion_percentage >= 80
                await self.db.commit()
        except Exception as e:
            self.logger.error(f"Failed to update completion percentage for profile {profile_id}: {e}")

    async def _calculate_completion_percentage(self, profile_data: ProfileUpdate) -> int:
        """Calculate profile completion percentage from profile data."""
        total_fields = 25  # Total number of profile fields
        filled_fields = 0
        
        # Count filled required fields
        required_fields = ["first_name", "last_name", "date_of_birth", "gender", "email"]
        for field in required_fields:
            if getattr(profile_data, field, None):
                filled_fields += 1
        
        # Count filled optional fields
        optional_fields = [
            "middle_name", "preferred_name", "marital_status", "phone_number",
            "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relationship",
            "address_line_1", "city", "state", "postal_code", "country",
            "blood_type", "height_cm", "weight_kg", "activity_level",
            "allergies", "medications", "medical_conditions", "family_history"
        ]
        
        for field in optional_fields:
            if getattr(profile_data, field, None):
                filled_fields += 1
        
        return min(100, int((filled_fields / total_fields) * 100))

    async def _calculate_completion_percentage_from_profile(self, profile: Profile) -> int:
        """Calculate completion percentage from profile object."""
        total_fields = 25
        filled_fields = 0
        
        # Required fields
        required_fields = ["first_name", "last_name", "date_of_birth", "gender", "email"]
        for field in required_fields:
            if getattr(profile, field, None):
                filled_fields += 1
        
        # Optional fields
        optional_fields = [
            "middle_name", "preferred_name", "marital_status", "phone_number",
            "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relationship",
            "address_line_1", "city", "state", "postal_code", "country",
            "blood_type", "height_cm", "weight_kg", "activity_level",
            "allergies", "medications", "medical_conditions", "family_history"
        ]
        
        for field in optional_fields:
            if getattr(profile, field, None):
                filled_fields += 1
        
        return min(100, int((filled_fields / total_fields) * 100))

    async def _archive_profile_data(self, profile_id: int) -> None:
        """Archive profile data for deletion."""
        try:
            # This would typically move data to an archive table
            # For now, we'll just log the archiving
            self.logger.info(f"Archiving profile data for profile {profile_id}")
        except Exception as e:
            self.logger.error(f"Failed to archive profile data for profile {profile_id}: {e}")


# Dependency injection
async def get_profile_service(db: AsyncSession = Depends(get_async_db)) -> ProfileService:
    """Get profile service instance."""
    return ProfileService(db) 