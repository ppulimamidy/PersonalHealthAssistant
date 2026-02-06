"""
Vital Signs Service
Comprehensive service for managing vital signs data with business logic and validation.
"""

import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, func, desc, case, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from common.models.base import (
    BaseServiceException, ResourceNotFoundException, ValidationException,
    ErrorCode, ErrorSeverity
)
from common.utils.logging import get_logger
from common.utils.resilience import with_resilience
from ..models.vital_signs import (
    VitalSigns, VitalSignType, MeasurementMethod, VitalSignsFilter,
    BloodPressureCreate, HeartRateCreate, TemperatureCreate, OxygenSaturationCreate,
    RespiratoryRateCreate, BloodGlucoseCreate, BodyCompositionCreate
)

logger = get_logger(__name__)

class VitalSignsService:
    """
    Service for managing vital signs data with comprehensive business logic.
    """
    
    def __init__(self):
        self.logger = logger
    
    @with_resilience("vital_signs_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def create_blood_pressure(
        self, 
        user_id: str, 
        blood_pressure_data: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new blood pressure measurement"""
        try:
            # Validate blood pressure data
            self._validate_blood_pressure(blood_pressure_data)
            
            # Calculate mean arterial pressure if not provided
            if not blood_pressure_data.get("mean_arterial_pressure"):
                systolic = blood_pressure_data["systolic"]
                diastolic = blood_pressure_data["diastolic"]
                blood_pressure_data["mean_arterial_pressure"] = self._calculate_map(systolic, diastolic)
            
            # Create vital sign record
            vital_sign = VitalSigns(
                user_id=user_id,
                vital_sign_type=VitalSignType.BLOOD_PRESSURE.value,
                measurement_method=blood_pressure_data.get("measurement_method", MeasurementMethod.MANUAL.value),
                measurement_location=blood_pressure_data.get("measurement_location"),
                systolic=blood_pressure_data["systolic"],
                diastolic=blood_pressure_data["diastolic"],
                mean_arterial_pressure=blood_pressure_data["mean_arterial_pressure"],
                device_id=blood_pressure_data.get("device_id"),
                device_model=blood_pressure_data.get("device_model"),
                measurement_notes=blood_pressure_data.get("measurement_notes"),
                measurement_quality=blood_pressure_data.get("measurement_quality", "good"),
                measurement_duration=blood_pressure_data.get("measurement_duration"),
                metadata=blood_pressure_data.get("metadata", {})
            )
            
            db.add(vital_sign)
            await db.commit()
            await db.refresh(vital_sign)
            
            # Log the measurement
            self.logger.info(f"Blood pressure recorded for user {user_id}: {blood_pressure_data['systolic']}/{blood_pressure_data['diastolic']} mmHg")
            
            return vital_sign.to_dict()
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error creating blood pressure measurement: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def create_heart_rate(
        self, 
        user_id: str, 
        heart_rate_data: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new heart rate measurement"""
        try:
            # Validate heart rate data
            self._validate_heart_rate(heart_rate_data)
            
            # Create vital sign record
            vital_sign = VitalSigns(
                user_id=user_id,
                vital_sign_type=VitalSignType.HEART_RATE.value,
                measurement_method=heart_rate_data.get("measurement_method", MeasurementMethod.MANUAL.value),
                measurement_location=heart_rate_data.get("measurement_location"),
                heart_rate=heart_rate_data["heart_rate"],
                heart_rate_variability=heart_rate_data.get("heart_rate_variability"),
                irregular_heartbeat_detected=heart_rate_data.get("irregular_heartbeat_detected"),
                device_id=heart_rate_data.get("device_id"),
                device_model=heart_rate_data.get("device_model"),
                measurement_notes=heart_rate_data.get("measurement_notes"),
                measurement_quality=heart_rate_data.get("measurement_quality", "good"),
                measurement_duration=heart_rate_data.get("measurement_duration"),
                metadata=heart_rate_data.get("metadata", {})
            )
            
            db.add(vital_sign)
            await db.commit()
            await db.refresh(vital_sign)
            
            # Log the measurement
            self.logger.info(f"Heart rate recorded for user {user_id}: {heart_rate_data['heart_rate']} bpm")
            
            return vital_sign.to_dict()
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error creating heart rate measurement: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def create_temperature(
        self, 
        user_id: str, 
        temperature_data: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new body temperature measurement"""
        try:
            # Validate temperature data
            self._validate_temperature(temperature_data)
            
            # Create vital sign record
            vital_sign = VitalSigns(
                user_id=user_id,
                vital_sign_type=VitalSignType.BODY_TEMPERATURE.value,
                measurement_method=temperature_data.get("measurement_method", MeasurementMethod.MANUAL.value),
                measurement_location=temperature_data.get("measurement_location"),
                temperature=temperature_data["temperature"],
                temperature_method=temperature_data.get("temperature_method"),
                device_id=temperature_data.get("device_id"),
                device_model=temperature_data.get("device_model"),
                measurement_notes=temperature_data.get("measurement_notes"),
                measurement_quality=temperature_data.get("measurement_quality", "good"),
                measurement_duration=temperature_data.get("measurement_duration"),
                metadata=temperature_data.get("metadata", {})
            )
            
            db.add(vital_sign)
            await db.commit()
            await db.refresh(vital_sign)
            
            # Log the measurement
            self.logger.info(f"Temperature recorded for user {user_id}: {temperature_data['temperature']}°C")
            
            return vital_sign.to_dict()
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error creating temperature measurement: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def create_oxygen_saturation(
        self, 
        user_id: str, 
        oxygen_data: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new oxygen saturation measurement"""
        try:
            # Validate oxygen saturation data
            self._validate_oxygen_saturation(oxygen_data)
            
            # Create vital sign record
            vital_sign = VitalSigns(
                user_id=user_id,
                vital_sign_type=VitalSignType.OXYGEN_SATURATION.value,
                measurement_method=oxygen_data.get("measurement_method", MeasurementMethod.MANUAL.value),
                measurement_location=oxygen_data.get("measurement_location"),
                oxygen_saturation=oxygen_data["oxygen_saturation"],
                perfusion_index=oxygen_data.get("perfusion_index"),
                device_id=oxygen_data.get("device_id"),
                device_model=oxygen_data.get("device_model"),
                measurement_notes=oxygen_data.get("measurement_notes"),
                measurement_quality=oxygen_data.get("measurement_quality", "good"),
                measurement_duration=oxygen_data.get("measurement_duration"),
                metadata=oxygen_data.get("metadata", {})
            )
            
            db.add(vital_sign)
            await db.commit()
            await db.refresh(vital_sign)
            
            # Log the measurement
            self.logger.info(f"Oxygen saturation recorded for user {user_id}: {oxygen_data['oxygen_saturation']}%")
            
            return vital_sign.to_dict()
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error creating oxygen saturation measurement: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def create_respiratory_rate(
        self, 
        user_id: str, 
        respiratory_data: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new respiratory rate measurement"""
        try:
            # Validate respiratory rate data
            self._validate_respiratory_rate(respiratory_data)
            
            # Create vital sign record
            vital_sign = VitalSigns(
                user_id=user_id,
                vital_sign_type=VitalSignType.RESPIRATORY_RATE.value,
                measurement_method=respiratory_data.get("measurement_method", MeasurementMethod.MANUAL.value),
                measurement_location=respiratory_data.get("measurement_location"),
                respiratory_rate=respiratory_data["respiratory_rate"],
                respiratory_pattern=respiratory_data.get("respiratory_pattern"),
                device_id=respiratory_data.get("device_id"),
                device_model=respiratory_data.get("device_model"),
                measurement_notes=respiratory_data.get("measurement_notes"),
                measurement_quality=respiratory_data.get("measurement_quality", "good"),
                measurement_duration=respiratory_data.get("measurement_duration"),
                metadata=respiratory_data.get("metadata", {})
            )
            
            db.add(vital_sign)
            await db.commit()
            await db.refresh(vital_sign)
            
            # Log the measurement
            self.logger.info(f"Respiratory rate recorded for user {user_id}: {respiratory_data['respiratory_rate']} breaths/min")
            
            return vital_sign.to_dict()
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error creating respiratory rate measurement: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def create_blood_glucose(
        self, 
        user_id: str, 
        glucose_data: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new blood glucose measurement"""
        try:
            # Validate blood glucose data
            self._validate_blood_glucose(glucose_data)
            
            # Create vital sign record
            vital_sign = VitalSigns(
                user_id=user_id,
                vital_sign_type=VitalSignType.BLOOD_GLUCOSE.value,
                measurement_method=glucose_data.get("measurement_method", MeasurementMethod.MANUAL.value),
                measurement_location=glucose_data.get("measurement_location"),
                blood_glucose=glucose_data["blood_glucose"],
                glucose_unit=glucose_data["glucose_unit"],
                glucose_context=glucose_data.get("glucose_context"),
                device_id=glucose_data.get("device_id"),
                device_model=glucose_data.get("device_model"),
                measurement_notes=glucose_data.get("measurement_notes"),
                measurement_quality=glucose_data.get("measurement_quality", "good"),
                measurement_duration=glucose_data.get("measurement_duration"),
                metadata=glucose_data.get("metadata", {})
            )
            
            db.add(vital_sign)
            await db.commit()
            await db.refresh(vital_sign)
            
            # Log the measurement
            self.logger.info(f"Blood glucose recorded for user {user_id}: {glucose_data['blood_glucose']} {glucose_data['glucose_unit']}")
            
            return vital_sign.to_dict()
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error creating blood glucose measurement: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def create_body_composition(
        self, 
        user_id: str, 
        composition_data: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Create a new body composition measurement"""
        try:
            # Validate body composition data
            self._validate_body_composition(composition_data)
            
            # Calculate BMI if weight and height are provided
            if composition_data.get("weight") and composition_data.get("height") and not composition_data.get("bmi"):
                weight_kg = composition_data["weight"]
                height_m = composition_data["height"] / 100  # Convert cm to meters
                composition_data["bmi"] = weight_kg / (height_m ** 2)
            
            # Create vital sign record
            vital_sign = VitalSigns(
                user_id=user_id,
                vital_sign_type=VitalSignType.WEIGHT.value,
                measurement_method=composition_data.get("measurement_method", MeasurementMethod.MANUAL.value),
                measurement_location=composition_data.get("measurement_location"),
                weight=composition_data.get("weight"),
                height=composition_data.get("height"),
                bmi=composition_data.get("bmi"),
                waist_circumference=composition_data.get("waist_circumference"),
                body_fat_percentage=composition_data.get("body_fat_percentage"),
                muscle_mass=composition_data.get("muscle_mass"),
                bone_density=composition_data.get("bone_density"),
                device_id=composition_data.get("device_id"),
                device_model=composition_data.get("device_model"),
                measurement_notes=composition_data.get("measurement_notes"),
                measurement_quality=composition_data.get("measurement_quality", "good"),
                measurement_duration=composition_data.get("measurement_duration"),
                metadata=composition_data.get("metadata", {})
            )
            
            db.add(vital_sign)
            await db.commit()
            await db.refresh(vital_sign)
            
            # Log the measurement
            self.logger.info(f"Body composition recorded for user {user_id}: weight={composition_data.get('weight')}kg, height={composition_data.get('height')}cm")
            
            return vital_sign.to_dict()
            
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error creating body composition measurement: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=100, timeout=30.0, max_retries=3)
    async def get_vital_signs(
        self, 
        user_id: str, 
        filter_params: VitalSignsFilter, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get vital signs with filtering and pagination"""
        try:
            # Build query
            query = select(VitalSigns).where(VitalSigns.user_id == user_id)
            
            # Apply filters
            if filter_params.vital_sign_type:
                query = query.where(VitalSigns.vital_sign_type == filter_params.vital_sign_type.value)
            
            if filter_params.measurement_method:
                query = query.where(VitalSigns.measurement_method == filter_params.measurement_method.value)
            
            if filter_params.start_date:
                query = query.where(VitalSigns.created_at >= filter_params.start_date)
            
            if filter_params.end_date:
                query = query.where(VitalSigns.created_at <= filter_params.end_date)
            
            if filter_params.device_id:
                query = query.where(VitalSigns.device_id == filter_params.device_id)
            
            if filter_params.measurement_quality:
                query = query.where(VitalSigns.measurement_quality == filter_params.measurement_quality)
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await db.execute(count_query)
            total = total_result.scalar()
            
            # Apply pagination and ordering
            query = query.order_by(desc(VitalSigns.created_at))
            query = query.offset(filter_params.offset).limit(filter_params.limit)
            
            # Execute query
            result = await db.execute(query)
            vital_signs = result.scalars().all()
            
            # Convert to dictionaries
            data = [vital_sign.to_dict() for vital_sign in vital_signs]
            
            return {
                "data": data,
                "total": total,
                "limit": filter_params.limit,
                "offset": filter_params.offset
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving vital signs: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=100, timeout=30.0, max_retries=3)
    async def get_vital_sign(
        self, 
        vital_sign_id: uuid.UUID, 
        user_id: str, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get a specific vital sign by ID"""
        try:
            query = select(VitalSigns).where(
                and_(
                    VitalSigns.id == vital_sign_id,
                    VitalSigns.user_id == user_id
                )
            )
            
            result = await db.execute(query)
            vital_sign = result.scalar_one_or_none()
            
            if not vital_sign:
                raise ResourceNotFoundException(f"Vital sign with ID {vital_sign_id} not found")
            
            return vital_sign.to_dict()
            
        except ResourceNotFoundException:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving vital sign: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def update_vital_sign(
        self, 
        vital_sign_id: uuid.UUID, 
        user_id: str, 
        update_data: Dict[str, Any], 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Update a vital sign measurement"""
        try:
            # Get existing vital sign
            query = select(VitalSigns).where(
                and_(
                    VitalSigns.id == vital_sign_id,
                    VitalSigns.user_id == user_id
                )
            )
            
            result = await db.execute(query)
            vital_sign = result.scalar_one_or_none()
            
            if not vital_sign:
                raise ResourceNotFoundException(f"Vital sign with ID {vital_sign_id} not found")
            
            # Define allowed fields for update
            allowed_fields = {
                "measurement_notes", "measurement_quality", "measurement_duration",
                "device_id", "device_model", "metadata"
            }
            
            # Validate update data
            invalid_fields = set(update_data.keys()) - allowed_fields
            if invalid_fields:
                raise ValidationException(f"Cannot update fields: {', '.join(invalid_fields)}")
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(vital_sign, field):
                    setattr(vital_sign, field, value)
            
            vital_sign.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(vital_sign)
            
            self.logger.info(f"Vital sign {vital_sign_id} updated for user {user_id}")
            
            return vital_sign.to_dict()
            
        except (ResourceNotFoundException, ValidationException):
            raise
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error updating vital sign: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def delete_vital_sign(
        self, 
        vital_sign_id: uuid.UUID, 
        user_id: str, 
        db: AsyncSession
    ) -> None:
        """Delete a vital sign measurement"""
        try:
            # Get existing vital sign
            query = select(VitalSigns).where(
                and_(
                    VitalSigns.id == vital_sign_id,
                    VitalSigns.user_id == user_id
                )
            )
            
            result = await db.execute(query)
            vital_sign = result.scalar_one_or_none()
            
            if not vital_sign:
                raise ResourceNotFoundException(f"Vital sign with ID {vital_sign_id} not found")
            
            await db.delete(vital_sign)
            await db.commit()
            
            self.logger.info(f"Vital sign {vital_sign_id} deleted for user {user_id}")
            
        except ResourceNotFoundException:
            raise
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Error deleting vital sign: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=50, timeout=60.0, max_retries=3)
    async def get_recent_summary(
        self, 
        user_id: str, 
        days: int, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get summary of recent vital signs"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get recent vital signs
            query = select(VitalSigns).where(
                and_(
                    VitalSigns.user_id == user_id,
                    VitalSigns.created_at >= start_date
                )
            ).order_by(desc(VitalSigns.created_at))
            
            result = await db.execute(query)
            vital_signs = result.scalars().all()
            
            # Group by type and calculate statistics
            summary = {}
            for vital_sign in vital_signs:
                vital_type = vital_sign.vital_sign_type
                if vital_type not in summary:
                    summary[vital_type] = {
                        "count": 0,
                        "latest": None,
                        "average": None,
                        "min": None,
                        "max": None,
                        "measurements": []
                    }
                
                summary[vital_type]["count"] += 1
                
                # Get the relevant value based on vital sign type
                value = self._get_vital_sign_value(vital_sign, vital_type)
                if value is not None:
                    summary[vital_type]["measurements"].append({
                        "value": value,
                        "timestamp": vital_sign.created_at.isoformat(),
                        "quality": vital_sign.measurement_quality
                    })
            
            # Calculate statistics for each type
            for vital_type, data in summary.items():
                if data["measurements"]:
                    values = [m["value"] for m in data["measurements"]]
                    data["latest"] = data["measurements"][0]["value"]
                    data["average"] = sum(values) / len(values)
                    data["min"] = min(values)
                    data["max"] = max(values)
                    data["measurements"] = data["measurements"][:10]  # Keep only latest 10
            
            return {
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "summary": summary
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving vital signs summary: {str(e)}")
            raise
    
    @with_resilience("vital_signs_service", max_concurrent=50, timeout=60.0, max_retries=3)
    async def get_trends(
        self, 
        user_id: str, 
        vital_sign_type: VitalSignType, 
        period: str, 
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get trend analysis for a specific vital sign type"""
        try:
            # Parse period
            period_days = int(period.replace("d", ""))
            start_date = datetime.utcnow() - timedelta(days=period_days)
            
            # Get vital signs for the period
            query = select(VitalSigns).where(
                and_(
                    VitalSigns.user_id == user_id,
                    VitalSigns.vital_sign_type == vital_sign_type.value,
                    VitalSigns.created_at >= start_date
                )
            ).order_by(VitalSigns.created_at)
            
            result = await db.execute(query)
            vital_signs = result.scalars().all()
            
            if not vital_signs:
                return {
                    "vital_sign_type": vital_sign_type.value,
                    "period": period,
                    "data_points": 0,
                    "trend": "insufficient_data",
                    "statistics": {},
                    "recommendations": ["Insufficient data for trend analysis"]
                }
            
            # Extract values and timestamps
            values = []
            timestamps = []
            for vital_sign in vital_signs:
                value = self._get_vital_sign_value(vital_sign, vital_sign_type.value)
                if value is not None:
                    values.append(value)
                    timestamps.append(vital_sign.created_at)
            
            if len(values) < 2:
                return {
                    "vital_sign_type": vital_sign_type.value,
                    "period": period,
                    "data_points": len(values),
                    "trend": "insufficient_data",
                    "statistics": {},
                    "recommendations": ["Need more data points for trend analysis"]
                }
            
            # Calculate basic statistics
            avg_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)
            
            # Calculate trend (simple linear regression)
            trend = self._calculate_trend(values, timestamps)
            
            # Generate recommendations
            recommendations = self._generate_trend_recommendations(
                vital_sign_type, values, trend, avg_value
            )
            
            return {
                "vital_sign_type": vital_sign_type.value,
                "period": period,
                "data_points": len(values),
                "trend": trend,
                "statistics": {
                    "average": avg_value,
                    "min": min_value,
                    "max": max_value,
                    "range": max_value - min_value,
                    "latest": values[-1] if values else None
                },
                "recommendations": recommendations
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating trends: {str(e)}")
            raise
    
    def _validate_blood_pressure(self, data: Dict[str, Any]) -> None:
        """Validate blood pressure data"""
        if data["systolic"] <= 0 or data["diastolic"] <= 0:
            raise ValidationException("Blood pressure values must be positive")
        
        if data["diastolic"] >= data["systolic"]:
            raise ValidationException("Diastolic pressure must be less than systolic pressure")
        
        if data["systolic"] > 300 or data["diastolic"] > 200:
            raise ValidationException("Blood pressure values are outside reasonable range")
    
    def _validate_heart_rate(self, data: Dict[str, Any]) -> None:
        """Validate heart rate data"""
        if data["heart_rate"] <= 0 or data["heart_rate"] > 300:
            raise ValidationException("Heart rate must be between 1 and 300 bpm")
    
    def _validate_temperature(self, data: Dict[str, Any]) -> None:
        """Validate temperature data"""
        if data["temperature"] < 20 or data["temperature"] > 50:
            raise ValidationException("Temperature must be between 20°C and 50°C")
    
    def _validate_oxygen_saturation(self, data: Dict[str, Any]) -> None:
        """Validate oxygen saturation data"""
        if data["oxygen_saturation"] < 0 or data["oxygen_saturation"] > 100:
            raise ValidationException("Oxygen saturation must be between 0% and 100%")
    
    def _validate_respiratory_rate(self, data: Dict[str, Any]) -> None:
        """Validate respiratory rate data"""
        if data["respiratory_rate"] <= 0 or data["respiratory_rate"] > 100:
            raise ValidationException("Respiratory rate must be between 1 and 100 breaths/min")
    
    def _validate_blood_glucose(self, data: Dict[str, Any]) -> None:
        """Validate blood glucose data"""
        if data["blood_glucose"] <= 0 or data["blood_glucose"] > 1000:
            raise ValidationException("Blood glucose must be between 1 and 1000")
    
    def _validate_body_composition(self, data: Dict[str, Any]) -> None:
        """Validate body composition data"""
        if data.get("weight") and (data["weight"] <= 0 or data["weight"] > 500):
            raise ValidationException("Weight must be between 1 and 500 kg")
        
        if data.get("height") and (data["height"] <= 0 or data["height"] > 300):
            raise ValidationException("Height must be between 1 and 300 cm")
    
    def _calculate_map(self, systolic: float, diastolic: float) -> float:
        """Calculate mean arterial pressure"""
        return diastolic + (systolic - diastolic) / 3
    
    def _get_vital_sign_value(self, vital_sign: VitalSigns, vital_type: str) -> Optional[float]:
        """Get the relevant value for a vital sign type"""
        value_mapping = {
            VitalSignType.BLOOD_PRESSURE.value: vital_sign.systolic,  # Use systolic as primary
            VitalSignType.HEART_RATE.value: vital_sign.heart_rate,
            VitalSignType.BODY_TEMPERATURE.value: vital_sign.temperature,
            VitalSignType.OXYGEN_SATURATION.value: vital_sign.oxygen_saturation,
            VitalSignType.RESPIRATORY_RATE.value: vital_sign.respiratory_rate,
            VitalSignType.BLOOD_GLUCOSE.value: vital_sign.blood_glucose,
            VitalSignType.WEIGHT.value: vital_sign.weight,
            VitalSignType.BODY_MASS_INDEX.value: vital_sign.bmi,
        }
        
        return value_mapping.get(vital_type)
    
    def _calculate_trend(self, values: List[float], timestamps: List[datetime]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "insufficient_data"
        
        # Simple trend calculation
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        if not first_half or not second_half:
            return "insufficient_data"
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
        
        if change_percent > 5:
            return "increasing"
        elif change_percent < -5:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_trend_recommendations(
        self, 
        vital_sign_type: VitalSignType, 
        values: List[float], 
        trend: str, 
        average: float
    ) -> List[str]:
        """Generate recommendations based on trends"""
        recommendations = []
        
        if vital_sign_type == VitalSignType.BLOOD_PRESSURE:
            if average > 140:
                recommendations.append("Consider lifestyle modifications to manage blood pressure")
            if trend == "increasing":
                recommendations.append("Monitor blood pressure more frequently")
        
        elif vital_sign_type == VitalSignType.HEART_RATE:
            if average > 100:
                recommendations.append("Consider stress management and cardiovascular health")
            if trend == "increasing":
                recommendations.append("Focus on heart health and stress reduction")
        
        elif vital_sign_type == VitalSignType.BLOOD_GLUCOSE:
            if average > 140:
                recommendations.append("Review diet and medication management")
            if trend == "increasing":
                recommendations.append("Consult with healthcare provider about glucose management")
        
        elif vital_sign_type == VitalSignType.WEIGHT:
            if trend == "increasing":
                recommendations.append("Consider dietary and exercise modifications")
            elif trend == "decreasing":
                recommendations.append("Continue current healthy practices")
        
        # General recommendations
        if len(values) < 5:
            recommendations.append("Continue monitoring to establish baseline patterns")
        
        return recommendations 