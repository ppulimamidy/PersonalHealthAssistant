"""
Health Attributes Service

This module provides the HealthAttributesService class for managing user health attributes
including biometric data, health goals, and risk assessments.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status, Depends

from ..models.health_attributes import (
    HealthAttributes, HealthAttributesCreate, HealthAttributesUpdate, HealthAttributesResponse
)
from ..models.profile import Profile
from common.database import get_db
from common.exceptions import DatabaseError, ValidationError

logger = logging.getLogger(__name__)


class HealthAttributesService:
    """Service for managing user health attributes."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_health_attributes(
        self, 
        user_id: int, 
        health_data: HealthAttributesCreate
    ) -> HealthAttributesResponse:
        """Create health attributes for a user."""
        try:
            # Check if health attributes already exist
            existing = self.db.query(HealthAttributes).filter(
                HealthAttributes.user_id == user_id
            ).first()
            
            if existing:
                raise ValidationError("Health attributes already exist for this user")
            
            # Calculate BMI if height and weight are provided
            if health_data.height_cm and health_data.weight_kg:
                health_data.bmi = self._calculate_bmi(health_data.height_cm, health_data.weight_kg)
            
            # Calculate risk scores
            health_data.cardiovascular_risk_score = self._calculate_cardiovascular_risk(health_data)
            health_data.diabetes_risk_score = self._calculate_diabetes_risk(health_data)
            health_data.obesity_risk_score = self._calculate_obesity_risk(health_data)
            health_data.overall_health_score = self._calculate_overall_health_score(health_data)
            
            # Create new health attributes
            health_attributes = HealthAttributes(
                user_id=user_id,
                **health_data.dict()
            )
            
            self.db.add(health_attributes)
            self.db.commit()
            self.db.refresh(health_attributes)
            
            logger.info(f"Created health attributes for user {user_id}")
            return HealthAttributesResponse.from_orm(health_attributes)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating health attributes: {e}")
            raise DatabaseError("Failed to create health attributes")
        except Exception as e:
            logger.error(f"Error creating health attributes: {e}")
            raise
    
    async def get_health_attributes(self, user_id: int) -> Optional[HealthAttributesResponse]:
        """Get health attributes for a user."""
        try:
            health_attributes = self.db.query(HealthAttributes).filter(
                HealthAttributes.user_id == user_id
            ).first()
            
            if not health_attributes:
                return None
            
            return HealthAttributesResponse.from_orm(health_attributes)
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting health attributes: {e}")
            raise DatabaseError("Failed to get health attributes")
    
    async def update_health_attributes(
        self, 
        user_id: int, 
        health_data: HealthAttributesUpdate
    ) -> HealthAttributesResponse:
        """Update health attributes for a user."""
        try:
            health_attributes = self.db.query(HealthAttributes).filter(
                HealthAttributes.user_id == user_id
            ).first()
            
            if not health_attributes:
                raise ValidationError("Health attributes not found")
            
            # Update fields
            update_data = health_data.dict(exclude_unset=True)
            
            # Recalculate BMI if height or weight changed
            if 'height_cm' in update_data or 'weight_kg' in update_data:
                new_height = update_data.get('height_cm', health_attributes.height_cm)
                new_weight = update_data.get('weight_kg', health_attributes.weight_kg)
                if new_height and new_weight:
                    update_data['bmi'] = self._calculate_bmi(new_height, new_weight)
            
            for field, value in update_data.items():
                setattr(health_attributes, field, value)
            
            # Recalculate risk scores
            health_attributes.cardiovascular_risk_score = self._calculate_cardiovascular_risk(health_attributes)
            health_attributes.diabetes_risk_score = self._calculate_diabetes_risk(health_attributes)
            health_attributes.obesity_risk_score = self._calculate_obesity_risk(health_attributes)
            health_attributes.overall_health_score = self._calculate_overall_health_score(health_attributes)
            
            health_attributes.last_updated = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(health_attributes)
            
            logger.info(f"Updated health attributes for user {user_id}")
            return HealthAttributesResponse.from_orm(health_attributes)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating health attributes: {e}")
            raise DatabaseError("Failed to update health attributes")
        except Exception as e:
            logger.error(f"Error updating health attributes: {e}")
            raise
    
    async def delete_health_attributes(self, user_id: int) -> bool:
        """Delete health attributes for a user."""
        try:
            health_attributes = self.db.query(HealthAttributes).filter(
                HealthAttributes.user_id == user_id
            ).first()
            
            if not health_attributes:
                return False
            
            self.db.delete(health_attributes)
            self.db.commit()
            
            logger.info(f"Deleted health attributes for user {user_id}")
            return True
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting health attributes: {e}")
            raise DatabaseError("Failed to delete health attributes")
    
    async def validate_health_data(self, health_data: HealthAttributesCreate) -> Dict[str, Any]:
        """Validate health attributes data."""
        try:
            validation_errors = []
            warnings = []
            
            # Validate height
            if health_data.height_cm:
                if health_data.height_cm < 50 or health_data.height_cm > 300:
                    validation_errors.append("Height must be between 50 and 300 cm")
            
            # Validate weight
            if health_data.weight_kg:
                if health_data.weight_kg < 20 or health_data.weight_kg > 500:
                    validation_errors.append("Weight must be between 20 and 500 kg")
            
            # Validate BMI
            if health_data.bmi:
                if health_data.bmi < 10 or health_data.bmi > 100:
                    validation_errors.append("BMI must be between 10 and 100")
            
            # Validate blood pressure
            if health_data.blood_pressure_systolic:
                if health_data.blood_pressure_systolic < 70 or health_data.blood_pressure_systolic > 250:
                    validation_errors.append("Systolic blood pressure must be between 70 and 250 mmHg")
            
            if health_data.blood_pressure_diastolic:
                if health_data.blood_pressure_diastolic < 40 or health_data.blood_pressure_diastolic > 150:
                    validation_errors.append("Diastolic blood pressure must be between 40 and 150 mmHg")
            
            # Validate heart rate
            if health_data.resting_heart_rate:
                if health_data.resting_heart_rate < 30 or health_data.resting_heart_rate > 200:
                    validation_errors.append("Resting heart rate must be between 30 and 200 bpm")
            
            # Validate oxygen saturation
            if health_data.oxygen_saturation:
                if health_data.oxygen_saturation < 70 or health_data.oxygen_saturation > 100:
                    validation_errors.append("Oxygen saturation must be between 70 and 100%")
            
            # Validate body temperature
            if health_data.body_temperature:
                if health_data.body_temperature < 30 or health_data.body_temperature > 45:
                    validation_errors.append("Body temperature must be between 30 and 45°C")
            
            # Warnings for potentially concerning values
            if health_data.bmi and health_data.bmi > 30:
                warnings.append("BMI indicates obesity - consider consulting a healthcare provider")
            
            if health_data.blood_pressure_systolic and health_data.blood_pressure_systolic > 140:
                warnings.append("Systolic blood pressure is elevated")
            
            if health_data.resting_heart_rate and health_data.resting_heart_rate > 100:
                warnings.append("Resting heart rate is elevated")
            
            return {
                "is_valid": len(validation_errors) == 0,
                "errors": validation_errors,
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Error validating health data: {e}")
            raise ValidationError("Failed to validate health data")
    
    async def export_health_attributes(self, user_id: int) -> Dict[str, Any]:
        """Export health attributes for a user."""
        try:
            health_attributes = self.db.query(HealthAttributes).filter(
                HealthAttributes.user_id == user_id
            ).first()
            
            if not health_attributes:
                raise ValidationError("Health attributes not found")
            
            export_data = {
                "user_id": health_attributes.user_id,
                "height_cm": health_attributes.height_cm,
                "weight_kg": health_attributes.weight_kg,
                "bmi": health_attributes.bmi,
                "body_fat_percentage": health_attributes.body_fat_percentage,
                "muscle_mass_kg": health_attributes.muscle_mass_kg,
                "waist_circumference_cm": health_attributes.waist_circumference_cm,
                "hip_circumference_cm": health_attributes.hip_circumference_cm,
                "body_water_percentage": health_attributes.body_water_percentage,
                "resting_heart_rate": health_attributes.resting_heart_rate,
                "blood_pressure_systolic": health_attributes.blood_pressure_systolic,
                "blood_pressure_diastolic": health_attributes.blood_pressure_diastolic,
                "oxygen_saturation": health_attributes.oxygen_saturation,
                "body_temperature": health_attributes.body_temperature,
                "primary_health_goal": health_attributes.primary_health_goal,
                "secondary_health_goals": health_attributes.secondary_health_goals,
                "target_weight_kg": health_attributes.target_weight_kg,
                "target_bmi": health_attributes.target_bmi,
                "target_resting_heart_rate": health_attributes.target_resting_heart_rate,
                "target_blood_pressure_systolic": health_attributes.target_blood_pressure_systolic,
                "target_blood_pressure_diastolic": health_attributes.target_blood_pressure_diastolic,
                "daily_step_goal": health_attributes.daily_step_goal,
                "weekly_workout_goal": health_attributes.weekly_workout_goal,
                "daily_active_minutes_goal": health_attributes.daily_active_minutes_goal,
                "weekly_cardio_minutes_goal": health_attributes.weekly_cardio_minutes_goal,
                "smoking_status": health_attributes.smoking_status,
                "alcohol_consumption": health_attributes.alcohol_consumption,
                "family_history_diabetes": health_attributes.family_history_diabetes,
                "family_history_heart_disease": health_attributes.family_history_heart_disease,
                "family_history_cancer": health_attributes.family_history_cancer,
                "family_history_hypertension": health_attributes.family_history_hypertension,
                "has_diabetes": health_attributes.has_diabetes,
                "has_hypertension": health_attributes.has_hypertension,
                "has_heart_disease": health_attributes.has_heart_disease,
                "has_asthma": health_attributes.has_asthma,
                "has_arthritis": health_attributes.has_arthritis,
                "has_depression": health_attributes.has_depression,
                "has_anxiety": health_attributes.has_anxiety,
                "has_sleep_apnea": health_attributes.has_sleep_apnea,
                "sleep_hours_per_night": health_attributes.sleep_hours_per_night,
                "stress_level": health_attributes.stress_level,
                "diet_type": health_attributes.diet_type,
                "exercise_frequency": health_attributes.exercise_frequency,
                "sedentary_hours_per_day": health_attributes.sedentary_hours_per_day,
                "overall_health_score": health_attributes.overall_health_score,
                "cardiovascular_risk_score": health_attributes.cardiovascular_risk_score,
                "diabetes_risk_score": health_attributes.diabetes_risk_score,
                "obesity_risk_score": health_attributes.obesity_risk_score,
                "custom_health_data": health_attributes.custom_health_data,
                "exported_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Exported health attributes for user {user_id}")
            return export_data
            
        except Exception as e:
            logger.error(f"Error exporting health attributes: {e}")
            raise
    
    async def import_health_attributes(
        self, 
        user_id: int, 
        import_data: Dict[str, Any]
    ) -> HealthAttributesResponse:
        """Import health attributes for a user."""
        try:
            # Validate import data
            required_fields = ["height_cm", "weight_kg"]
            
            for field in required_fields:
                if field not in import_data:
                    raise ValidationError(f"Missing required field: {field}")
            
            # Check if health attributes exist
            existing = self.db.query(HealthAttributes).filter(
                HealthAttributes.user_id == user_id
            ).first()
            
            if existing:
                # Update existing attributes
                for field, value in import_data.items():
                    if hasattr(existing, field):
                        setattr(existing, field, value)
                
                # Recalculate derived values
                if 'height_cm' in import_data or 'weight_kg' in import_data:
                    new_height = import_data.get('height_cm', existing.height_cm)
                    new_weight = import_data.get('weight_kg', existing.weight_kg)
                    if new_height and new_weight:
                        existing.bmi = self._calculate_bmi(new_height, new_weight)
                
                existing.cardiovascular_risk_score = self._calculate_cardiovascular_risk(existing)
                existing.diabetes_risk_score = self._calculate_diabetes_risk(existing)
                existing.obesity_risk_score = self._calculate_obesity_risk(existing)
                existing.overall_health_score = self._calculate_overall_health_score(existing)
                
                health_attributes = existing
            else:
                # Create new attributes
                health_attributes = HealthAttributes(
                    user_id=user_id,
                    **import_data
                )
                self.db.add(health_attributes)
            
            self.db.commit()
            self.db.refresh(health_attributes)
            
            logger.info(f"Imported health attributes for user {user_id}")
            return HealthAttributesResponse.from_orm(health_attributes)
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error importing health attributes: {e}")
            raise DatabaseError("Failed to import health attributes")
        except Exception as e:
            logger.error(f"Error importing health attributes: {e}")
            raise
    
    async def get_health_summary(self, user_id: int) -> Dict[str, Any]:
        """Get health attributes summary for a user."""
        try:
            health_attributes = self.db.query(HealthAttributes).filter(
                HealthAttributes.user_id == user_id
            ).first()
            
            if not health_attributes:
                return {"message": "No health attributes found"}
            
            # Calculate health metrics
            bmi_category = self._get_bmi_category(health_attributes.bmi) if health_attributes.bmi else None
            blood_pressure_category = self._get_blood_pressure_category(
                health_attributes.blood_pressure_systolic, 
                health_attributes.blood_pressure_diastolic
            ) if health_attributes.blood_pressure_systolic else None
            
            summary = {
                "user_id": user_id,
                "overall_health_score": health_attributes.overall_health_score,
                "bmi": {
                    "value": health_attributes.bmi,
                    "category": bmi_category
                },
                "blood_pressure": {
                    "systolic": health_attributes.blood_pressure_systolic,
                    "diastolic": health_attributes.blood_pressure_diastolic,
                    "category": blood_pressure_category
                },
                "resting_heart_rate": health_attributes.resting_heart_rate,
                "risk_scores": {
                    "cardiovascular": health_attributes.cardiovascular_risk_score,
                    "diabetes": health_attributes.diabetes_risk_score,
                    "obesity": health_attributes.obesity_risk_score
                },
                "health_goals": {
                    "primary": health_attributes.primary_health_goal,
                    "secondary": health_attributes.secondary_health_goals
                },
                "activity_goals": {
                    "daily_steps": health_attributes.daily_step_goal,
                    "weekly_workouts": health_attributes.weekly_workout_goal,
                    "daily_active_minutes": health_attributes.daily_active_minutes_goal,
                    "weekly_cardio_minutes": health_attributes.weekly_cardio_minutes_goal
                },
                "lifestyle_factors": {
                    "smoking_status": health_attributes.smoking_status,
                    "alcohol_consumption": health_attributes.alcohol_consumption,
                    "sleep_hours": health_attributes.sleep_hours_per_night,
                    "stress_level": health_attributes.stress_level,
                    "diet_type": health_attributes.diet_type,
                    "exercise_frequency": health_attributes.exercise_frequency,
                    "sedentary_hours": health_attributes.sedentary_hours_per_day
                },
                "medical_conditions": {
                    "diabetes": health_attributes.has_diabetes,
                    "hypertension": health_attributes.has_hypertension,
                    "heart_disease": health_attributes.has_heart_disease,
                    "asthma": health_attributes.has_asthma,
                    "arthritis": health_attributes.has_arthritis,
                    "depression": health_attributes.has_depression,
                    "anxiety": health_attributes.has_anxiety,
                    "sleep_apnea": health_attributes.has_sleep_apnea
                },
                "family_history": {
                    "diabetes": health_attributes.family_history_diabetes,
                    "heart_disease": health_attributes.family_history_heart_disease,
                    "cancer": health_attributes.family_history_cancer,
                    "hypertension": health_attributes.family_history_hypertension
                },
                "last_updated": health_attributes.last_updated.isoformat() if health_attributes.last_updated else None
            }
            
            logger.info(f"Generated health summary for user {user_id}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating health summary: {e}")
            raise
    
    def _calculate_bmi(self, height_cm: float, weight_kg: float) -> float:
        """Calculate BMI from height and weight."""
        height_m = height_cm / 100
        return round(weight_kg / (height_m ** 2), 1)
    
    def _get_bmi_category(self, bmi: float) -> str:
        """Get BMI category."""
        if bmi < 18.5:
            return "underweight"
        elif bmi < 25:
            return "normal"
        elif bmi < 30:
            return "overweight"
        else:
            return "obese"
    
    def _get_blood_pressure_category(self, systolic: int, diastolic: int) -> str:
        """Get blood pressure category."""
        if systolic < 120 and diastolic < 80:
            return "normal"
        elif systolic < 130 and diastolic < 80:
            return "elevated"
        elif systolic < 140 or diastolic < 90:
            return "stage1_hypertension"
        else:
            return "stage2_hypertension"
    
    def _calculate_cardiovascular_risk(self, health_data) -> float:
        """Calculate cardiovascular risk score."""
        risk_score = 0
        
        # Age factor (simplified)
        risk_score += 20
        
        # BMI factor
        if health_data.bmi:
            if health_data.bmi > 30:
                risk_score += 15
            elif health_data.bmi > 25:
                risk_score += 10
        
        # Blood pressure factor
        if health_data.blood_pressure_systolic:
            if health_data.blood_pressure_systolic > 140:
                risk_score += 20
            elif health_data.blood_pressure_systolic > 130:
                risk_score += 10
        
        # Smoking factor
        if health_data.smoking_status == "current":
            risk_score += 25
        
        # Family history factor
        if health_data.family_history_heart_disease:
            risk_score += 15
        
        return min(100, risk_score)
    
    def _calculate_diabetes_risk(self, health_data) -> float:
        """Calculate diabetes risk score."""
        risk_score = 0
        
        # BMI factor
        if health_data.bmi:
            if health_data.bmi > 30:
                risk_score += 25
            elif health_data.bmi > 25:
                risk_score += 15
        
        # Family history factor
        if health_data.family_history_diabetes:
            risk_score += 20
        
        # Age factor (simplified)
        risk_score += 10
        
        # Physical activity factor
        if health_data.exercise_frequency == "rarely":
            risk_score += 15
        elif health_data.exercise_frequency == "sometimes":
            risk_score += 10
        
        return min(100, risk_score)
    
    def _calculate_obesity_risk(self, health_data) -> float:
        """Calculate obesity risk score."""
        risk_score = 0
        
        # Current BMI factor
        if health_data.bmi:
            if health_data.bmi > 30:
                risk_score += 40
            elif health_data.bmi > 25:
                risk_score += 20
        
        # Physical activity factor
        if health_data.exercise_frequency == "rarely":
            risk_score += 25
        elif health_data.exercise_frequency == "sometimes":
            risk_score += 15
        
        # Sedentary behavior factor
        if health_data.sedentary_hours_per_day and health_data.sedentary_hours_per_day > 8:
            risk_score += 20
        
        # Diet factor (simplified)
        risk_score += 10
        
        return min(100, risk_score)
    
    def _calculate_overall_health_score(self, health_data) -> float:
        """Calculate overall health score."""
        score = 100
        
        # Deduct points for risk factors
        if health_data.cardiovascular_risk_score:
            score -= health_data.cardiovascular_risk_score * 0.3
        
        if health_data.diabetes_risk_score:
            score -= health_data.diabetes_risk_score * 0.2
        
        if health_data.obesity_risk_score:
            score -= health_data.obesity_risk_score * 0.2
        
        # Add points for positive factors
        if health_data.exercise_frequency == "regular":
            score += 10
        elif health_data.exercise_frequency == "frequent":
            score += 15
        
        if health_data.sleep_hours_per_night and 7 <= health_data.sleep_hours_per_night <= 9:
            score += 10
        
        if health_data.stress_level == "low":
            score += 10
        
        return max(0, min(100, score))


def get_health_attributes_service(db: Session = Depends(get_db)) -> HealthAttributesService:
    """Dependency to get health attributes service instance."""
    return HealthAttributesService(db) 