"""
User Preferences Service

This module provides the PreferencesService class for managing user preferences
including notification settings, UI preferences, privacy settings, and health tracking preferences.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from ..models.preferences import (
    Preferences, PreferencesCreate, PreferencesUpdate, PreferencesResponse,
    NotificationSettings, PrivacySettings as PreferencesPrivacySettings
)
from ..models.profile import Profile
from common.database import get_db
from common.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class PreferencesService:
    """Service for managing user preferences"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_preferences(self, user_id: int, profile_id: int, preferences_data: PreferencesCreate) -> PreferencesResponse:
        """Create new user preferences"""
        try:
            # Check if preferences already exist for this user
            existing = self.db.query(Preferences).filter(Preferences.user_id == user_id).first()
            if existing:
                raise ValidationError("Preferences already exist for this user")
            
            # Create new preferences
            preferences = Preferences(
                user_id=user_id,
                profile_id=profile_id,
                **preferences_data.dict(exclude={'user_id', 'profile_id'})
            )
            
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
            
            logger.info(f"Created preferences for user {user_id}")
            return PreferencesResponse.model_validate(preferences)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating preferences: {e}")
            raise DatabaseError("Failed to create preferences")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating preferences: {e}")
            raise
    
    def get_preferences(self, user_id: int) -> Optional[PreferencesResponse]:
        """Get user preferences by user ID"""
        try:
            preferences = self.db.query(Preferences).filter(Preferences.user_id == user_id).first()
            if not preferences:
                return None
            
            return PreferencesResponse.model_validate(preferences)
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting preferences: {e}")
            raise DatabaseError("Failed to get preferences")
    
    def update_preferences(self, user_id: int, preferences_data: PreferencesUpdate) -> PreferencesResponse:
        """Update user preferences"""
        try:
            preferences = self.db.query(Preferences).filter(Preferences.user_id == user_id).first()
            if not preferences:
                raise ValidationError("Preferences not found for this user")
            
            # Update only provided fields
            update_data = preferences_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(preferences, field, value)
            
            preferences.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(preferences)
            
            logger.info(f"Updated preferences for user {user_id}")
            return PreferencesResponse.model_validate(preferences)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating preferences: {e}")
            raise DatabaseError("Failed to update preferences")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error updating preferences: {e}")
            raise
    
    def delete_preferences(self, user_id: int) -> bool:
        """Delete user preferences"""
        try:
            preferences = self.db.query(Preferences).filter(Preferences.user_id == user_id).first()
            if not preferences:
                return False
            
            self.db.delete(preferences)
            self.db.commit()
            
            logger.info(f"Deleted preferences for user {user_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting preferences: {e}")
            raise DatabaseError("Failed to delete preferences")
    
    def update_notification_settings(self, user_id: int, settings: NotificationSettings) -> PreferencesResponse:
        """Update notification settings specifically"""
        try:
            preferences = self.db.query(Preferences).filter(Preferences.user_id == user_id).first()
            if not preferences:
                raise ValidationError("Preferences not found for this user")
            
            # Update notification-related fields
            for field, value in settings.dict().items():
                if hasattr(preferences, field):
                    setattr(preferences, field, value)
            
            preferences.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(preferences)
            
            logger.info(f"Updated notification settings for user {user_id}")
            return PreferencesResponse.model_validate(preferences)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating notification settings: {e}")
            raise DatabaseError("Failed to update notification settings")
    
    def update_privacy_settings(self, user_id: int, settings: PreferencesPrivacySettings) -> PreferencesResponse:
        """Update privacy settings specifically"""
        try:
            preferences = self.db.query(Preferences).filter(Preferences.user_id == user_id).first()
            if not preferences:
                raise ValidationError("Preferences not found for this user")
            
            # Update privacy-related fields
            for field, value in settings.dict().items():
                if hasattr(preferences, field):
                    setattr(preferences, field, value)
            
            preferences.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(preferences)
            
            logger.info(f"Updated privacy settings for user {user_id}")
            return PreferencesResponse.model_validate(preferences)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating privacy settings: {e}")
            raise DatabaseError("Failed to update privacy settings")
    
    def get_preferences_summary(self, user_id: int) -> Dict[str, Any]:
        """Get a summary of user preferences"""
        try:
            preferences = self.db.query(Preferences).filter(Preferences.user_id == user_id).first()
            if not preferences:
                return {}
            
            return {
                "notification_settings": {
                    "email_notifications": preferences.email_notifications,
                    "sms_notifications": preferences.sms_notifications,
                    "push_notifications": preferences.push_notifications,
                    "in_app_notifications": preferences.in_app_notifications,
                    "health_alerts": preferences.health_alerts,
                    "medication_reminders": preferences.medication_reminders,
                    "appointment_reminders": preferences.appointment_reminders,
                    "lab_result_notifications": preferences.lab_result_notifications,
                    "wellness_tips": preferences.wellness_tips,
                    "research_updates": preferences.research_updates,
                    "marketing_emails": preferences.marketing_emails
                },
                "ui_preferences": {
                    "theme": preferences.theme,
                    "language": preferences.language,
                    "units": preferences.units,
                    "timezone": preferences.timezone,
                    "date_format": preferences.date_format,
                    "time_format": preferences.time_format
                },
                "privacy_settings": {
                    "share_data_with_providers": preferences.share_data_with_providers,
                    "share_data_for_research": preferences.share_data_for_research,
                    "share_anonymous_data": preferences.share_anonymous_data,
                    "allow_location_tracking": preferences.allow_location_tracking,
                    "allow_analytics_tracking": preferences.allow_analytics_tracking
                },
                "health_tracking": {
                    "auto_track_activity": preferences.auto_track_activity,
                    "auto_track_sleep": preferences.auto_track_sleep,
                    "auto_track_heart_rate": preferences.auto_track_heart_rate,
                    "auto_track_steps": preferences.auto_track_steps,
                    "auto_track_weight": preferences.auto_track_weight,
                    "auto_track_blood_pressure": preferences.auto_track_blood_pressure,
                    "auto_track_blood_glucose": preferences.auto_track_blood_glucose
                },
                "last_updated": preferences.last_updated
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting preferences summary: {e}")
            raise DatabaseError("Failed to get preferences summary")
    
    def reset_preferences_to_defaults(self, user_id: int) -> PreferencesResponse:
        """Reset user preferences to default values"""
        try:
            preferences = self.db.query(Preferences).filter(Preferences.user_id == user_id).first()
            if not preferences:
                raise ValidationError("Preferences not found for this user")
            
            # Create default preferences
            default_preferences = PreferencesCreate(
                user_id=user_id,
                profile_id=preferences.profile_id
            )
            
            # Update with default values
            for field, value in default_preferences.dict(exclude={'user_id', 'profile_id'}).items():
                setattr(preferences, field, value)
            
            preferences.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(preferences)
            
            logger.info(f"Reset preferences to defaults for user {user_id}")
            return PreferencesResponse.model_validate(preferences)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error resetting preferences: {e}")
            raise DatabaseError("Failed to reset preferences")
    
    def export_preferences(self, user_id: int) -> Dict[str, Any]:
        """Export user preferences for data portability"""
        try:
            preferences = self.db.query(Preferences).filter(Preferences.user_id == user_id).first()
            if not preferences:
                return {}
            
            return {
                "export_date": datetime.utcnow().isoformat(),
                "user_id": preferences.user_id,
                "profile_id": preferences.profile_id,
                "preferences": preferences.__dict__,
                "metadata": {
                    "version": "1.0",
                    "export_type": "user_preferences"
                }
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error exporting preferences: {e}")
            raise DatabaseError("Failed to export preferences")
    
    def import_preferences(self, user_id: int, profile_id: int, preferences_data: Dict[str, Any]) -> PreferencesResponse:
        """Import user preferences from exported data"""
        try:
            # Validate import data
            if "preferences" not in preferences_data:
                raise ValidationError("Invalid preferences import data")
            
            # Delete existing preferences if they exist
            existing = self.db.query(Preferences).filter(Preferences.user_id == user_id).first()
            if existing:
                self.db.delete(existing)
            
            # Create new preferences from import data
            import_prefs = preferences_data["preferences"]
            preferences = Preferences(
                user_id=user_id,
                profile_id=profile_id,
                email_notifications=import_prefs.get("email_notifications", True),
                sms_notifications=import_prefs.get("sms_notifications", False),
                push_notifications=import_prefs.get("push_notifications", True),
                in_app_notifications=import_prefs.get("in_app_notifications", True),
                health_alerts=import_prefs.get("health_alerts", True),
                medication_reminders=import_prefs.get("medication_reminders", True),
                appointment_reminders=import_prefs.get("appointment_reminders", True),
                lab_result_notifications=import_prefs.get("lab_result_notifications", True),
                wellness_tips=import_prefs.get("wellness_tips", True),
                research_updates=import_prefs.get("research_updates", False),
                marketing_emails=import_prefs.get("marketing_emails", False),
                theme=import_prefs.get("theme", "auto"),
                language=import_prefs.get("language", "en"),
                units=import_prefs.get("units", "metric"),
                timezone=import_prefs.get("timezone", "UTC"),
                date_format=import_prefs.get("date_format", "MM/DD/YYYY"),
                time_format=import_prefs.get("time_format", "12-hour"),
                share_data_with_providers=import_prefs.get("share_data_with_providers", True),
                share_data_for_research=import_prefs.get("share_data_for_research", False),
                share_anonymous_data=import_prefs.get("share_anonymous_data", True),
                allow_location_tracking=import_prefs.get("allow_location_tracking", False),
                allow_analytics_tracking=import_prefs.get("allow_analytics_tracking", True),
                auto_track_activity=import_prefs.get("auto_track_activity", True),
                auto_track_sleep=import_prefs.get("auto_track_sleep", True),
                auto_track_heart_rate=import_prefs.get("auto_track_heart_rate", True),
                auto_track_steps=import_prefs.get("auto_track_steps", True),
                auto_track_weight=import_prefs.get("auto_track_weight", False),
                auto_track_blood_pressure=import_prefs.get("auto_track_blood_pressure", False),
                auto_track_blood_glucose=import_prefs.get("auto_track_blood_glucose", False),
                custom_preferences=import_prefs.get("custom_preferences", {})
            )
            
            self.db.add(preferences)
            self.db.commit()
            self.db.refresh(preferences)
            
            logger.info(f"Imported preferences for user {user_id}")
            return PreferencesResponse.model_validate(preferences)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error importing preferences: {e}")
            raise DatabaseError("Failed to import preferences")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error importing preferences: {e}")
            raise


def get_preferences_service() -> PreferencesService:
    """Get a PreferencesService instance with database session"""
    db = next(get_db())
    return PreferencesService(db) 