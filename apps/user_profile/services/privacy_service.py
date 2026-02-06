"""
Privacy Settings Service

This module provides the PrivacyService class for managing user privacy settings
including data sharing preferences, visibility controls, and compliance settings.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status, Depends

from ..models.privacy_settings import (
    PrivacySettings, PrivacySettingsCreate, PrivacySettingsUpdate, PrivacySettingsResponse
)
from ..models.profile import Profile
from common.database import get_db
from common.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class PrivacyService:
    """Service for managing user privacy settings."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_privacy_settings(
        self, 
        user_id: int, 
        privacy_data: PrivacySettingsCreate
    ) -> PrivacySettingsResponse:
        """Create privacy settings for a user."""
        try:
            # Check if privacy settings already exist
            existing = self.db.query(PrivacySettings).filter(
                PrivacySettings.user_id == user_id
            ).first()
            
            if existing:
                raise ValidationError("Privacy settings already exist for this user")
            
            # Create new privacy settings
            privacy_settings = PrivacySettings(
                user_id=user_id,
                **privacy_data.dict()
            )
            
            self.db.add(privacy_settings)
            self.db.commit()
            self.db.refresh(privacy_settings)
            
            logger.info(f"Created privacy settings for user {user_id}")
            return PrivacySettingsResponse.from_orm(privacy_settings)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating privacy settings: {e}")
            raise DatabaseError("Failed to create privacy settings")
        except Exception as e:
            logger.error(f"Error creating privacy settings: {e}")
            raise
    
    async def get_privacy_settings(self, user_id: int) -> Optional[PrivacySettingsResponse]:
        """Get privacy settings for a user."""
        try:
            privacy_settings = self.db.query(PrivacySettings).filter(
                PrivacySettings.user_id == user_id
            ).first()
            
            if not privacy_settings:
                return None
            
            return PrivacySettingsResponse.from_orm(privacy_settings)
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting privacy settings: {e}")
            raise DatabaseError("Failed to get privacy settings")
    
    async def update_privacy_settings(
        self, 
        user_id: int, 
        privacy_data: PrivacySettingsUpdate
    ) -> PrivacySettingsResponse:
        """Update privacy settings for a user."""
        try:
            privacy_settings = self.db.query(PrivacySettings).filter(
                PrivacySettings.user_id == user_id
            ).first()
            
            if not privacy_settings:
                raise ValidationError("Privacy settings not found")
            
            # Update fields
            update_data = privacy_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(privacy_settings, field, value)
            
            privacy_settings.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(privacy_settings)
            
            logger.info(f"Updated privacy settings for user {user_id}")
            return PrivacySettingsResponse.from_orm(privacy_settings)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating privacy settings: {e}")
            raise DatabaseError("Failed to update privacy settings")
        except Exception as e:
            logger.error(f"Error updating privacy settings: {e}")
            raise
    
    async def delete_privacy_settings(self, user_id: int) -> bool:
        """Delete privacy settings for a user."""
        try:
            privacy_settings = self.db.query(PrivacySettings).filter(
                PrivacySettings.user_id == user_id
            ).first()
            
            if not privacy_settings:
                return False
            
            self.db.delete(privacy_settings)
            self.db.commit()
            
            logger.info(f"Deleted privacy settings for user {user_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting privacy settings: {e}")
            raise DatabaseError("Failed to delete privacy settings")
    
    async def validate_privacy_data(self, privacy_data: PrivacySettingsCreate) -> Dict[str, Any]:
        """Validate privacy settings data."""
        try:
            validation_errors = []
            
            # Validate profile visibility
            if privacy_data.profile_visibility not in ["public", "private", "friends_only"]:
                validation_errors.append("Invalid profile visibility setting")
            
            # Validate data retention period
            if privacy_data.data_retention_period and privacy_data.data_retention_period < 0:
                validation_errors.append("Data retention period must be positive")
            
            # Validate consent expiry dates
            if privacy_data.consent_expiry_dates:
                for consent_type, expiry_date in privacy_data.consent_expiry_dates.items():
                    if isinstance(expiry_date, str):
                        try:
                            datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                        except ValueError:
                            validation_errors.append(f"Invalid expiry date format for {consent_type}")
            
            return {
                "is_valid": len(validation_errors) == 0,
                "errors": validation_errors,
                "warnings": []
            }
            
        except Exception as e:
            logger.error(f"Error validating privacy data: {e}")
            raise ValidationError("Failed to validate privacy data")
    
    async def export_privacy_settings(self, user_id: int) -> Dict[str, Any]:
        """Export privacy settings for a user."""
        try:
            privacy_settings = self.db.query(PrivacySettings).filter(
                PrivacySettings.user_id == user_id
            ).first()
            
            if not privacy_settings:
                raise ValidationError("Privacy settings not found")
            
            export_data = {
                "user_id": privacy_settings.user_id,
                "profile_visibility": privacy_settings.profile_visibility,
                "allow_profile_search": privacy_settings.allow_profile_search,
                "show_online_status": privacy_settings.show_online_status,
                "share_personal_info": privacy_settings.share_personal_info,
                "share_health_data": privacy_settings.share_health_data,
                "share_medical_records": privacy_settings.share_medical_records,
                "share_activity_data": privacy_settings.share_activity_data,
                "share_nutrition_data": privacy_settings.share_nutrition_data,
                "share_sleep_data": privacy_settings.share_sleep_data,
                "share_location_data": privacy_settings.share_location_data,
                "share_device_data": privacy_settings.share_device_data,
                "share_with_primary_care": privacy_settings.share_with_primary_care,
                "share_with_specialists": privacy_settings.share_with_specialists,
                "share_with_emergency_services": privacy_settings.share_with_emergency_services,
                "share_with_pharmacies": privacy_settings.share_with_pharmacies,
                "share_with_insurance": privacy_settings.share_with_insurance,
                "share_for_research": privacy_settings.share_for_research,
                "share_for_analytics": privacy_settings.share_for_analytics,
                "share_for_ai_training": privacy_settings.share_for_ai_training,
                "share_for_public_health": privacy_settings.share_for_public_health,
                "share_with_family_members": privacy_settings.share_with_family_members,
                "share_with_caregivers": privacy_settings.share_with_caregivers,
                "share_with_fitness_apps": privacy_settings.share_with_fitness_apps,
                "share_with_health_apps": privacy_settings.share_with_health_apps,
                "data_retention_period": privacy_settings.data_retention_period,
                "auto_delete_inactive": privacy_settings.auto_delete_inactive,
                "delete_on_account_closure": privacy_settings.delete_on_account_closure,
                "notify_data_access": privacy_settings.notify_data_access,
                "notify_data_sharing": privacy_settings.notify_data_sharing,
                "notify_privacy_changes": privacy_settings.notify_privacy_changes,
                "notify_breach_alerts": privacy_settings.notify_breach_alerts,
                "consent_history": privacy_settings.consent_history,
                "consent_expiry_dates": privacy_settings.consent_expiry_dates,
                "consent_renewal_reminders": privacy_settings.consent_renewal_reminders,
                "enable_data_encryption": privacy_settings.enable_data_encryption,
                "enable_two_factor_auth": privacy_settings.enable_two_factor_auth,
                "enable_audit_logging": privacy_settings.enable_audit_logging,
                "enable_data_export": privacy_settings.enable_data_export,
                "custom_privacy_rules": privacy_settings.custom_privacy_rules,
                "exported_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Exported privacy settings for user {user_id}")
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting privacy settings: {e}")
            raise
    
    async def import_privacy_settings(
        self, 
        user_id: int, 
        import_data: Dict[str, Any]
    ) -> PrivacySettingsResponse:
        """Import privacy settings for a user."""
        try:
            # Validate import data
            required_fields = [
                "profile_visibility", "allow_profile_search", "show_online_status"
            ]
            
            for field in required_fields:
                if field not in import_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Check if privacy settings exist
            existing = self.db.query(PrivacySettings).filter(
                PrivacySettings.user_id == user_id
            ).first()
            
            if existing:
                # Update existing settings
                for field, value in import_data.items():
                    if hasattr(existing, field):
                        setattr(existing, field, value)
                existing.last_updated = datetime.utcnow()
                privacy_settings = existing
            else:
                # Create new settings
                privacy_settings = PrivacySettings(
                    user_id=user_id,
                    **import_data
                )
                self.db.add(privacy_settings)
            
            self.db.commit()
            self.db.refresh(privacy_settings)
            
            logger.info(f"Imported privacy settings for user {user_id}")
            return PrivacySettingsResponse.from_orm(privacy_settings)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error importing privacy settings: {e}")
            raise DatabaseError("Failed to import privacy settings")
        except Exception as e:
            logger.error(f"Error importing privacy settings: {e}")
            raise
    
    async def get_privacy_summary(self, user_id: int) -> Dict[str, Any]:
        """Get privacy settings summary for a user."""
        try:
            privacy_settings = self.db.query(PrivacySettings).filter(
                PrivacySettings.user_id == user_id
            ).first()
            
            if not privacy_settings:
                return {"message": "No privacy settings found"}
            
            # Calculate privacy score
            privacy_score = 0
            total_checks = 0
            
            # Profile visibility checks
            if privacy_settings.profile_visibility == "private":
                privacy_score += 20
            elif privacy_settings.profile_visibility == "friends_only":
                privacy_score += 15
            total_checks += 1
            
            # Data sharing checks
            sharing_settings = [
                privacy_settings.share_personal_info,
                privacy_settings.share_health_data,
                privacy_settings.share_medical_records,
                privacy_settings.share_activity_data,
                privacy_settings.share_location_data
            ]
            
            for setting in sharing_settings:
                if not setting:
                    privacy_score += 10
                total_checks += 1
            
            # Security checks
            if privacy_settings.enable_data_encryption:
                privacy_score += 15
            if privacy_settings.enable_two_factor_auth:
                privacy_score += 15
            if privacy_settings.enable_audit_logging:
                privacy_score += 10
            total_checks += 3
            
            final_score = min(100, privacy_score)
            
            summary = {
                "user_id": user_id,
                "privacy_score": final_score,
                "profile_visibility": privacy_settings.profile_visibility,
                "data_sharing_enabled": any([
                    privacy_settings.share_personal_info,
                    privacy_settings.share_health_data,
                    privacy_settings.share_medical_records
                ]),
                "security_features_enabled": {
                    "data_encryption": privacy_settings.enable_data_encryption,
                    "two_factor_auth": privacy_settings.enable_two_factor_auth,
                    "audit_logging": privacy_settings.enable_audit_logging
                },
                "notifications_enabled": {
                    "data_access": privacy_settings.notify_data_access,
                    "data_sharing": privacy_settings.notify_data_sharing,
                    "privacy_changes": privacy_settings.notify_privacy_changes,
                    "breach_alerts": privacy_settings.notify_breach_alerts
                },
                "last_updated": privacy_settings.last_updated.isoformat() if privacy_settings.last_updated else None
            }
            
            logger.info(f"Generated privacy summary for user {user_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating privacy summary: {e}")
            raise


def get_privacy_service(db: Session = Depends(get_db)) -> PrivacyService:
    """Dependency to get privacy service instance."""
    return PrivacyService(db) 