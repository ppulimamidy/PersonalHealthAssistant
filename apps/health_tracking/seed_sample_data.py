#!/usr/bin/env python3
"""
Seed Sample Data for Health Tracking Service
Creates sample data for testing all endpoints.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from common.database.connection import get_async_db
from common.utils.logging import get_logger, setup_logging

# Import models
from apps.health_tracking.models.health_metrics import HealthMetric, MetricType, MetricUnit
from apps.health_tracking.models.health_goals import HealthGoal, GoalStatus, GoalType
from apps.health_tracking.models.health_insights import HealthInsight, InsightType, InsightSeverity, InsightStatus
from apps.health_tracking.models.vital_signs import VitalSigns, VitalSignType, MeasurementMethod
from apps.health_tracking.models.symptoms import Symptoms, SymptomCategory, SymptomSeverity
from apps.health_tracking.models.devices import Device
from apps.health_tracking.models.alerts import Alert

# Setup logging
setup_logging(enable_console=True, enable_file=True, enable_json=True)
logger = get_logger(__name__)

# Sample user ID
SAMPLE_USER_ID = "123e4567-e89b-12d3-a456-426614174000"

async def create_sample_health_metrics(db: AsyncSession) -> None:
    """Create sample health metrics"""
    logger.info("Creating sample health metrics...")
    
    metrics_data = [
        {
            "user_id": SAMPLE_USER_ID,
            "metric_type": MetricType.BLOOD_PRESSURE_SYSTOLIC.value,
            "value": 120.0,
            "unit": MetricUnit.MMHG.value,
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "source": "manual",
            "device_id": "bp-monitor-001",
            "notes": "Morning reading"
        },
        {
            "user_id": SAMPLE_USER_ID,
            "metric_type": MetricType.BLOOD_PRESSURE_DIASTOLIC.value,
            "value": 80.0,
            "unit": MetricUnit.MMHG.value,
            "timestamp": datetime.utcnow() - timedelta(hours=2),
            "source": "manual",
            "device_id": "bp-monitor-001",
            "notes": "Morning reading"
        },
        {
            "user_id": SAMPLE_USER_ID,
            "metric_type": MetricType.HEART_RATE.value,
            "value": 72.0,
            "unit": MetricUnit.BEATS_PER_MINUTE.value,
            "timestamp": datetime.utcnow() - timedelta(hours=1),
            "source": "smartwatch",
            "device_id": "apple-watch-001",
            "notes": "Resting heart rate"
        },
        {
            "user_id": SAMPLE_USER_ID,
            "metric_type": MetricType.BLOOD_GLUCOSE.value,
            "value": 95.0,
            "unit": MetricUnit.MG_DL.value,
            "timestamp": datetime.utcnow() - timedelta(hours=3),
            "source": "glucometer",
            "device_id": "glucometer-001",
            "notes": "Fasting glucose"
        },
        {
            "user_id": SAMPLE_USER_ID,
            "metric_type": MetricType.WEIGHT.value,
            "value": 70.5,
            "unit": MetricUnit.KG.value,
            "timestamp": datetime.utcnow() - timedelta(days=1),
            "source": "smart-scale",
            "device_id": "smart-scale-001",
            "notes": "Daily weight"
        }
    ]
    
    for metric_data in metrics_data:
        metric = HealthMetric(
            id=uuid.uuid4(),
            **metric_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(metric)
    
    await db.commit()
    logger.info(f"Created {len(metrics_data)} health metrics")

async def create_sample_health_goals(db: AsyncSession) -> None:
    """Create sample health goals"""
    logger.info("Creating sample health goals...")
    
    goals_data = [
        {
            "user_id": SAMPLE_USER_ID,
            "title": "Lower Blood Pressure",
            "description": "Reduce systolic blood pressure to below 120 mmHg",
            "metric_type": MetricType.BLOOD_PRESSURE_SYSTOLIC.value,
            "goal_type": GoalType.REDUCTION.value,
            "target_value": 120.0,
            "current_value": 125.0,
            "unit": MetricUnit.MMHG.value,
            "frequency": "daily",
            "start_date": datetime.utcnow().date(),
            "target_date": (datetime.utcnow() + timedelta(days=30)).date(),
            "status": GoalStatus.ACTIVE.value,
            "progress": 75.0
        },
        {
            "user_id": SAMPLE_USER_ID,
            "title": "Increase Daily Steps",
            "description": "Walk 10,000 steps per day",
            "metric_type": MetricType.STEPS.value,
            "goal_type": GoalType.IMPROVEMENT.value,
            "target_value": 10000.0,
            "current_value": 8500.0,
            "unit": MetricUnit.STEPS.value,
            "frequency": "daily",
            "start_date": datetime.utcnow().date(),
            "target_date": (datetime.utcnow() + timedelta(days=7)).date(),
            "status": GoalStatus.ACTIVE.value,
            "progress": 85.0
        }
    ]
    
    for goal_data in goals_data:
        goal = HealthGoal(
            id=uuid.uuid4(),
            **goal_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(goal)
    
    await db.commit()
    logger.info(f"Created {len(goals_data)} health goals")

async def create_sample_vital_signs(db: AsyncSession) -> None:
    """Create sample vital signs"""
    logger.info("Creating sample vital signs...")
    
    vitals_data = [
        {
            "user_id": SAMPLE_USER_ID,
            "vital_sign_type": VitalSignType.BLOOD_PRESSURE.value,
            "measurement_method": MeasurementMethod.MANUAL.value,
            "systolic": 120.0,
            "diastolic": 80.0,
            "mean_arterial_pressure": 93.3,
            "device_id": "bp-monitor-001",
            "measurement_notes": "Morning reading"
        },
        {
            "user_id": SAMPLE_USER_ID,
            "vital_sign_type": VitalSignType.HEART_RATE.value,
            "measurement_method": MeasurementMethod.DIGITAL_DEVICE.value,
            "heart_rate": 72.0,
            "heart_rate_variability": 45.0,
            "device_id": "apple-watch-001",
            "measurement_notes": "Resting heart rate"
        },
        {
            "user_id": SAMPLE_USER_ID,
            "vital_sign_type": VitalSignType.BODY_TEMPERATURE.value,
            "measurement_method": MeasurementMethod.MANUAL.value,
            "temperature": 36.8,
            "temperature_method": "oral",
            "measurement_notes": "Normal body temperature"
        }
    ]
    
    for vital_data in vitals_data:
        vital = VitalSigns(
            id=uuid.uuid4(),
            **vital_data,
            created_at=datetime.utcnow()
        )
        db.add(vital)
    
    await db.commit()
    logger.info(f"Created {len(vitals_data)} vital signs")

async def create_sample_symptoms(db: AsyncSession) -> None:
    """Create sample symptoms"""
    logger.info("Creating sample symptoms...")
    
    symptoms_data = [
        {
            "user_id": SAMPLE_USER_ID,
            "symptom_name": "Headache",
            "symptom_category": SymptomCategory.NEUROLOGICAL.value,
            "description": "Mild headache in the morning",
            "severity": SymptomSeverity.MILD.value,
            "severity_level": 3.0,
            "frequency": "occasional",
            "duration": "hours",
            "duration_hours": 2.0,
            "body_location": "forehead",
            "triggers": ["stress", "lack of sleep"],
            "relief_factors": ["rest", "hydration"]
        },
        {
            "user_id": SAMPLE_USER_ID,
            "symptom_name": "Fatigue",
            "symptom_category": SymptomCategory.GENERAL.value,
            "description": "Feeling tired throughout the day",
            "severity": SymptomSeverity.MODERATE.value,
            "severity_level": 5.0,
            "frequency": "daily",
            "duration": "hours",
            "duration_hours": 8.0,
            "body_location": "whole body",
            "triggers": ["poor sleep", "stress"],
            "relief_factors": ["sleep", "exercise"]
        }
    ]
    
    for symptom_data in symptoms_data:
        symptom = Symptoms(
            id=uuid.uuid4(),
            **symptom_data,
            created_at=datetime.utcnow()
        )
        db.add(symptom)
    
    await db.commit()
    logger.info(f"Created {len(symptoms_data)} symptoms")

async def create_sample_devices(db: AsyncSession) -> None:
    """Create sample devices"""
    logger.info("Creating sample devices...")
    
    devices_data = [
        {
            "user_id": SAMPLE_USER_ID,
            "device_name": "Apple Watch Series 7",
            "device_type": "smartwatch",
            "manufacturer": "Apple",
            "model": "Series 7",
            "serial_number": "AW123456789",
            "firmware_version": "8.5.1",
            "device_status": "active",
            "last_sync": datetime.utcnow(),
            "battery_level": 85,
            "is_connected": True,
            "connection_method": "bluetooth"
        },
        {
            "user_id": SAMPLE_USER_ID,
            "device_name": "Blood Pressure Monitor",
            "device_type": "blood_pressure",
            "manufacturer": "Omron",
            "model": "BP7100",
            "serial_number": "OM789012345",
            "firmware_version": "2.1.0",
            "device_status": "active",
            "last_sync": datetime.utcnow() - timedelta(hours=2),
            "battery_level": 90,
            "is_connected": False,
            "connection_method": "usb"
        }
    ]
    
    for device_data in devices_data:
        device = Device(
            id=uuid.uuid4(),
            **device_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(device)
    
    await db.commit()
    logger.info(f"Created {len(devices_data)} devices")

async def create_sample_alerts(db: AsyncSession) -> None:
    """Create sample alerts"""
    logger.info("Creating sample alerts...")
    
    alerts_data = [
        {
            "user_id": SAMPLE_USER_ID,
            "alert_type": "health_reminder",
            "title": "Blood Pressure Check Due",
            "message": "It's time to check your blood pressure",
            "severity": "info",
            "status": "active",
            "is_read": False,
            "is_actionable": True,
            "scheduled_for": datetime.utcnow() + timedelta(hours=1)
        },
        {
            "user_id": SAMPLE_USER_ID,
            "alert_type": "goal_progress",
            "title": "Goal Progress Update",
            "message": "You're 85% towards your daily step goal",
            "severity": "info",
            "status": "active",
            "is_read": False,
            "is_actionable": False
        }
    ]
    
    for alert_data in alerts_data:
        alert = Alert(
            id=uuid.uuid4(),
            **alert_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(alert)
    
    await db.commit()
    logger.info(f"Created {len(alerts_data)} alerts")

async def create_sample_insights(db: AsyncSession) -> None:
    """Create sample health insights"""
    logger.info("Creating sample health insights...")
    
    insights_data = [
        {
            "user_id": SAMPLE_USER_ID,
            "insight_type": InsightType.TREND_UP.value,
            "title": "Blood Pressure Improving",
            "description": "Your blood pressure has been trending downward over the past week",
            "summary": "Positive trend in blood pressure readings",
            "severity": InsightSeverity.LOW.value,
            "status": InsightStatus.ACTIVE.value,
            "confidence": 0.85,
            "actionable": True,
            "action_taken": False
        },
        {
            "user_id": SAMPLE_USER_ID,
            "insight_type": InsightType.PATTERN.value,
            "title": "Sleep Pattern Detected",
            "description": "Your heart rate is consistently lower on days when you get 8+ hours of sleep",
            "summary": "Correlation between sleep duration and heart rate",
            "severity": InsightSeverity.MEDIUM.value,
            "status": InsightStatus.ACTIVE.value,
            "confidence": 0.92,
            "actionable": True,
            "action_taken": False
        }
    ]
    
    for insight_data in insights_data:
        insight = HealthInsight(
            id=uuid.uuid4(),
            **insight_data,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(insight)
    
    await db.commit()
    logger.info(f"Created {len(insights_data)} health insights")

async def main():
    """Main function to seed all sample data"""
    logger.info("🚀 Starting Health Tracking Service Data Seeding")
    
    async for db in get_async_db():
        try:
            # Create sample data for all tables
            await create_sample_health_metrics(db)
            await create_sample_health_goals(db)
            await create_sample_vital_signs(db)
            await create_sample_symptoms(db)
            await create_sample_devices(db)
            await create_sample_alerts(db)
            await create_sample_insights(db)
            
            logger.info("✅ All sample data created successfully!")
            break
            
        except Exception as e:
            logger.error(f"Error creating sample data: {e}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(main()) 