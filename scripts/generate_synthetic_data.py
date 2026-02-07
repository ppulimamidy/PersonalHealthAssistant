#!/usr/bin/env python3
"""
Comprehensive Synthetic Data Generation Script
Generates realistic test data for all PersonalHealthAssistant services.

Usage:
    python scripts/generate_synthetic_data.py [--service SERVICE_NAME] [--users N]

This script creates:
  - Test users with profiles
  - Health metrics, vitals, symptoms, goals
  - Device data and data points
  - Medical records (lab results, documents, imaging, clinical reports)
  - Nutrition data (meal logs, goals, food recognition)
  - AI insights, health scores, patterns
  - Genomics data (variants, analyses, ancestry)
  - Doctor collaboration data (appointments, messages, consultations)
"""

import asyncio
import argparse
import sys
import os
import uuid
import random
from datetime import datetime, timedelta, date
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from common.config.settings import get_settings

settings = get_settings()

# ============================================================
# Configuration
# ============================================================

NUM_USERS = 5
DAYS_OF_DATA = 30

# Sample user data
SAMPLE_USERS = [
    {
        "email": "alice@example.com",
        "first_name": "Alice",
        "last_name": "Johnson",
        "gender": "female",
        "dob": "1990-03-15",
        "blood_type": "A+",
    },
    {
        "email": "bob@example.com",
        "first_name": "Bob",
        "last_name": "Smith",
        "gender": "male",
        "dob": "1985-07-22",
        "blood_type": "O+",
    },
    {
        "email": "carol@example.com",
        "first_name": "Carol",
        "last_name": "Williams",
        "gender": "female",
        "dob": "1992-11-08",
        "blood_type": "B+",
    },
    {
        "email": "david@example.com",
        "first_name": "David",
        "last_name": "Brown",
        "gender": "male",
        "dob": "1988-01-30",
        "blood_type": "AB+",
    },
    {
        "email": "eve@example.com",
        "first_name": "Eve",
        "last_name": "Davis",
        "gender": "female",
        "dob": "1995-06-12",
        "blood_type": "O-",
    },
]

# Medical data constants
SYMPTOM_TYPES = [
    "headache",
    "fatigue",
    "nausea",
    "back_pain",
    "joint_pain",
    "chest_pain",
    "dizziness",
    "shortness_of_breath",
    "fever",
    "cough",
    "insomnia",
    "anxiety",
    "muscle_ache",
    "stomach_pain",
    "sore_throat",
]

MEDICATION_NAMES = [
    "Ibuprofen",
    "Acetaminophen",
    "Lisinopril",
    "Metformin",
    "Atorvastatin",
    "Omeprazole",
    "Levothyroxine",
    "Amoxicillin",
    "Vitamin D3",
    "Fish Oil",
]

LAB_TEST_NAMES = [
    ("Complete Blood Count", "CBC", "count/mL"),
    ("Hemoglobin A1c", "HbA1c", "%"),
    ("Total Cholesterol", "CHOL", "mg/dL"),
    ("LDL Cholesterol", "LDL", "mg/dL"),
    ("HDL Cholesterol", "HDL", "mg/dL"),
    ("Triglycerides", "TG", "mg/dL"),
    ("Fasting Glucose", "GLU", "mg/dL"),
    ("Creatinine", "CRE", "mg/dL"),
    ("TSH", "TSH", "mIU/L"),
    ("Vitamin D", "VITD", "ng/mL"),
]

FOOD_ITEMS = [
    {
        "name": "Grilled Chicken Breast",
        "calories": 165,
        "protein": 31,
        "carbs": 0,
        "fat": 3.6,
    },
    {"name": "Brown Rice", "calories": 216, "protein": 5, "carbs": 45, "fat": 1.8},
    {"name": "Salmon Fillet", "calories": 208, "protein": 20, "carbs": 0, "fat": 13},
    {"name": "Mixed Salad", "calories": 65, "protein": 3, "carbs": 12, "fat": 1},
    {"name": "Greek Yogurt", "calories": 100, "protein": 17, "carbs": 6, "fat": 0.7},
    {"name": "Banana", "calories": 105, "protein": 1.3, "carbs": 27, "fat": 0.4},
    {"name": "Oatmeal", "calories": 150, "protein": 5, "carbs": 27, "fat": 2.5},
    {"name": "Avocado Toast", "calories": 250, "protein": 6, "carbs": 28, "fat": 14},
    {"name": "Quinoa Bowl", "calories": 222, "protein": 8, "carbs": 39, "fat": 4},
    {
        "name": "Whole Wheat Pasta",
        "calories": 174,
        "protein": 7,
        "carbs": 37,
        "fat": 0.8,
    },
]

GENE_NAMES = [
    "BRCA1",
    "BRCA2",
    "TP53",
    "MTHFR",
    "APOE",
    "CYP2D6",
    "CYP2C19",
    "CYP3A4",
    "VKORC1",
    "SLCO1B1",
    "HLA-B",
    "DPYD",
    "UGT1A1",
]

CHROMOSOMES = [str(i) for i in range(1, 23)] + ["X", "Y"]


async def get_engine():
    """Create async engine."""
    db_url = settings.DATABASE_URL
    if "postgresql://" in db_url and "+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    return create_async_engine(db_url, echo=False)


def random_date(start_days_ago=30, end_days_ago=0):
    """Generate a random date within range."""
    start = datetime.utcnow() - timedelta(days=start_days_ago)
    end = datetime.utcnow() - timedelta(days=end_days_ago)
    delta = (end - start).total_seconds()
    random_seconds = random.uniform(0, delta)
    return start + timedelta(seconds=random_seconds)


def random_uuid():
    return str(uuid.uuid4())


# ============================================================
# Data Generators
# ============================================================


async def generate_auth_users(session, num_users):
    """Generate users in the auth schema."""
    print("\n👤 Generating Auth Users...")
    user_ids = []

    for i, user_data in enumerate(SAMPLE_USERS[:num_users]):
        user_id = random_uuid()
        user_ids.append(user_id)

        # Create user
        await session.execute(
            text(
                """
            INSERT INTO auth.users (id, email, password_hash, first_name, last_name,
                                    is_active, is_verified, email_verified, created_at, updated_at)
            VALUES (:id, :email, :password_hash, :first_name, :last_name,
                    true, true, true, :created_at, :updated_at)
            ON CONFLICT (email) DO UPDATE SET id = auth.users.id
            RETURNING id
        """
            ),
            {
                "id": user_id,
                "email": user_data["email"],
                "password_hash": "$2b$12$LQv3c1yqBo9SkvXS7QTJPe1VMRwGA/0v23JFH/eS.MHN.p.w6bnJm",  # "password123"
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "created_at": datetime.utcnow() - timedelta(days=90),
                "updated_at": datetime.utcnow(),
            },
        )

    await session.commit()
    print(f"  ✓ Created {len(user_ids)} users")
    return user_ids


async def generate_user_profiles(session, user_ids):
    """Generate user profiles."""
    print("\n📝 Generating User Profiles...")

    for i, user_id in enumerate(user_ids):
        user_data = SAMPLE_USERS[i]
        try:
            await session.execute(
                text(
                    """
                INSERT INTO user_profiles (id, user_id, first_name, last_name, date_of_birth,
                                          gender, phone_number, created_at, updated_at)
                VALUES (:id, :user_id, :first_name, :last_name, :dob,
                        :gender, :phone, :created_at, :updated_at)
                ON CONFLICT DO NOTHING
            """
                ),
                {
                    "id": random_uuid(),
                    "user_id": user_id,
                    "first_name": user_data["first_name"],
                    "last_name": user_data["last_name"],
                    "dob": user_data["dob"],
                    "gender": user_data["gender"],
                    "phone": f"+1{random.randint(2000000000, 9999999999)}",
                    "created_at": datetime.utcnow() - timedelta(days=89),
                    "updated_at": datetime.utcnow(),
                },
            )
        except Exception:
            pass

    await session.commit()
    print(f"  ✓ Created {len(user_ids)} profiles")


async def generate_health_metrics(session, user_ids):
    """Generate health metrics, vitals, symptoms, and goals."""
    print("\n💓 Generating Health Tracking Data...")

    metrics_count = 0
    vitals_count = 0
    symptoms_count = 0
    goals_count = 0

    for user_id in user_ids:
        # Health Metrics (weight, BMI, etc.) - daily for 30 days
        base_weight = random.uniform(55, 95)
        for day in range(DAYS_OF_DATA):
            dt = datetime.utcnow() - timedelta(days=day)
            weight = base_weight + random.uniform(-1, 1)
            try:
                await session.execute(
                    text(
                        """
                    INSERT INTO health_metrics (id, user_id, metric_type, value, unit,
                                               recorded_at, created_at)
                    VALUES (:id, :user_id, :metric_type, :value, :unit, :recorded_at, :created_at)
                    ON CONFLICT DO NOTHING
                """
                    ),
                    {
                        "id": random_uuid(),
                        "user_id": user_id,
                        "metric_type": "weight",
                        "value": round(weight, 1),
                        "unit": "kg",
                        "recorded_at": dt,
                        "created_at": dt,
                    },
                )
                metrics_count += 1
            except Exception:
                pass

        # Vital Signs - 2-3 per day
        for day in range(DAYS_OF_DATA):
            for _ in range(random.randint(1, 3)):
                dt = random_date(day + 1, day)
                try:
                    await session.execute(
                        text(
                            """
                        INSERT INTO vital_signs (id, user_id, vital_type, value, unit,
                                                measurement_method, recorded_at, created_at)
                        VALUES (:id, :user_id, :vital_type, :value, :unit,
                                :method, :recorded_at, :created_at)
                        ON CONFLICT DO NOTHING
                    """
                        ),
                        {
                            "id": random_uuid(),
                            "user_id": user_id,
                            "vital_type": random.choice(
                                [
                                    "heart_rate",
                                    "blood_pressure_systolic",
                                    "blood_pressure_diastolic",
                                    "temperature",
                                    "spo2",
                                    "respiratory_rate",
                                ]
                            ),
                            "value": round(random.uniform(60, 100), 1),
                            "unit": "bpm",
                            "method": "automatic",
                            "recorded_at": dt,
                            "created_at": dt,
                        },
                    )
                    vitals_count += 1
                except Exception:
                    pass

        # Symptoms - random occurrences
        for _ in range(random.randint(5, 15)):
            dt = random_date(DAYS_OF_DATA, 0)
            try:
                await session.execute(
                    text(
                        """
                    INSERT INTO symptoms (id, user_id, symptom_type, severity, description,
                                         started_at, created_at)
                    VALUES (:id, :user_id, :symptom_type, :severity, :description,
                            :started_at, :created_at)
                    ON CONFLICT DO NOTHING
                """
                    ),
                    {
                        "id": random_uuid(),
                        "user_id": user_id,
                        "symptom_type": random.choice(SYMPTOM_TYPES),
                        "severity": random.choice(["mild", "moderate", "severe"]),
                        "description": f"Experienced {random.choice(SYMPTOM_TYPES)} symptoms",
                        "started_at": dt,
                        "created_at": dt,
                    },
                )
                symptoms_count += 1
            except Exception:
                pass

        # Health Goals
        goal_types = ["weight_loss", "exercise", "sleep", "nutrition", "hydration"]
        for goal_type in random.sample(goal_types, 3):
            try:
                await session.execute(
                    text(
                        """
                    INSERT INTO health_goals (id, user_id, goal_type, title, description,
                                             target_value, current_value, unit, status,
                                             start_date, target_date, created_at)
                    VALUES (:id, :user_id, :goal_type, :title, :description,
                            :target, :current, :unit, :status,
                            :start_date, :target_date, :created_at)
                    ON CONFLICT DO NOTHING
                """
                    ),
                    {
                        "id": random_uuid(),
                        "user_id": user_id,
                        "goal_type": goal_type,
                        "title": f"Improve {goal_type.replace('_', ' ')}",
                        "description": f"Goal to improve {goal_type.replace('_', ' ')} over next 3 months",
                        "target": round(random.uniform(50, 100), 1),
                        "current": round(random.uniform(20, 60), 1),
                        "unit": "points",
                        "status": random.choice(["active", "in_progress", "completed"]),
                        "start_date": (datetime.utcnow() - timedelta(days=60)).date(),
                        "target_date": (datetime.utcnow() + timedelta(days=30)).date(),
                        "created_at": datetime.utcnow() - timedelta(days=60),
                    },
                )
                goals_count += 1
            except Exception:
                pass

    await session.commit()
    print(f"  ✓ Created {metrics_count} health metrics")
    print(f"  ✓ Created {vitals_count} vital signs")
    print(f"  ✓ Created {symptoms_count} symptoms")
    print(f"  ✓ Created {goals_count} health goals")


async def generate_device_data(session, user_ids):
    """Generate device data and data points."""
    print("\n📱 Generating Device Data...")

    devices_count = 0
    points_count = 0
    device_types = [
        ("Apple Watch Series 9", "apple_watch", "Apple"),
        ("Dexcom G7", "cgm", "Dexcom"),
        ("Oura Ring Gen 3", "smart_ring", "Oura"),
        ("Withings Body+", "smart_scale", "Withings"),
        ("Omron BP Monitor", "blood_pressure_monitor", "Omron"),
    ]

    for user_id in user_ids:
        # Create devices
        user_devices = random.sample(device_types, random.randint(2, 4))
        device_ids = []

        for name, device_type, manufacturer in user_devices:
            device_id = random_uuid()
            device_ids.append((device_id, device_type))
            try:
                await session.execute(
                    text(
                        """
                    INSERT INTO device_data.devices (id, user_id, device_name, device_type,
                                                    manufacturer, connection_status, last_sync_at,
                                                    created_at, updated_at)
                    VALUES (:id, :user_id, :name, :type, :manufacturer,
                            :status, :last_sync, :created_at, :updated_at)
                    ON CONFLICT DO NOTHING
                """
                    ),
                    {
                        "id": device_id,
                        "user_id": user_id,
                        "name": name,
                        "type": device_type,
                        "manufacturer": manufacturer,
                        "status": "connected",
                        "last_sync": datetime.utcnow()
                        - timedelta(hours=random.randint(1, 12)),
                        "created_at": datetime.utcnow() - timedelta(days=60),
                        "updated_at": datetime.utcnow(),
                    },
                )
                devices_count += 1
            except Exception:
                pass

        # Create data points
        for device_id, device_type in device_ids:
            data_type_map = {
                "apple_watch": ["heart_rate", "steps", "calories"],
                "cgm": ["glucose"],
                "smart_ring": ["heart_rate", "sleep_score", "readiness_score"],
                "smart_scale": ["weight", "body_fat_percentage"],
                "blood_pressure_monitor": ["systolic", "diastolic"],
            }
            data_types = data_type_map.get(device_type, ["generic"])

            for day in range(min(DAYS_OF_DATA, 14)):
                for data_type in data_types:
                    dt = random_date(day + 1, day)
                    value = {
                        "heart_rate": random.uniform(58, 95),
                        "steps": random.randint(3000, 15000),
                        "calories": random.randint(1500, 3000),
                        "glucose": random.uniform(70, 180),
                        "sleep_score": random.randint(60, 95),
                        "readiness_score": random.randint(50, 95),
                        "weight": random.uniform(55, 95),
                        "body_fat_percentage": random.uniform(12, 30),
                        "systolic": random.randint(110, 140),
                        "diastolic": random.randint(65, 90),
                    }.get(data_type, random.uniform(0, 100))
                    try:
                        await session.execute(
                            text(
                                """
                            INSERT INTO device_data.device_data_points
                                (id, device_id, user_id, data_type, value, unit, quality,
                                 recorded_at, created_at)
                            VALUES (:id, :device_id, :user_id, :data_type, :value, :unit,
                                    :quality, :recorded_at, :created_at)
                            ON CONFLICT DO NOTHING
                        """
                            ),
                            {
                                "id": random_uuid(),
                                "device_id": device_id,
                                "user_id": user_id,
                                "data_type": data_type,
                                "value": round(float(value), 2),
                                "unit": "units",
                                "quality": random.choice(["high", "medium", "good"]),
                                "recorded_at": dt,
                                "created_at": dt,
                            },
                        )
                        points_count += 1
                    except Exception:
                        pass

    await session.commit()
    print(f"  ✓ Created {devices_count} devices")
    print(f"  ✓ Created {points_count} data points")


async def generate_medical_records(session, user_ids):
    """Generate medical records data."""
    print("\n🏥 Generating Medical Records...")

    lab_count = 0
    doc_count = 0

    for user_id in user_ids:
        # Lab Results
        for _ in range(random.randint(3, 8)):
            test_name, test_code, unit = random.choice(LAB_TEST_NAMES)
            dt = random_date(90, 0)
            value_ranges = {
                "HbA1c": (4.5, 8.0),
                "CHOL": (150, 280),
                "LDL": (60, 190),
                "HDL": (35, 85),
                "TG": (80, 300),
                "GLU": (65, 150),
                "CRE": (0.6, 1.4),
                "TSH": (0.3, 5.0),
                "VITD": (15, 60),
            }
            low, high = value_ranges.get(test_code, (50, 200))
            value = round(random.uniform(low, high), 2)
            ref_low, ref_high = low * 0.8, high * 0.7

            try:
                await session.execute(
                    text(
                        """
                    INSERT INTO medical_records.lab_results
                        (id, user_id, test_name, test_code, value, unit,
                         reference_range_low, reference_range_high, status,
                         performed_at, created_at, updated_at)
                    VALUES (:id, :user_id, :test_name, :test_code, :value, :unit,
                            :ref_low, :ref_high, :status,
                            :performed_at, :created_at, :updated_at)
                    ON CONFLICT DO NOTHING
                """
                    ),
                    {
                        "id": random_uuid(),
                        "user_id": user_id,
                        "test_name": test_name,
                        "test_code": test_code,
                        "value": value,
                        "unit": unit,
                        "ref_low": round(ref_low, 2),
                        "ref_high": round(ref_high, 2),
                        "status": "completed",
                        "performed_at": dt,
                        "created_at": dt,
                        "updated_at": dt,
                    },
                )
                lab_count += 1
            except Exception:
                pass

        # Documents
        doc_types = [
            "lab_report",
            "prescription",
            "discharge_summary",
            "radiology_report",
            "referral",
        ]
        for _ in range(random.randint(2, 5)):
            dt = random_date(90, 0)
            try:
                await session.execute(
                    text(
                        """
                    INSERT INTO medical_records.documents
                        (id, user_id, document_type, title, description,
                         file_name, file_type, status, created_at, updated_at)
                    VALUES (:id, :user_id, :doc_type, :title, :description,
                            :file_name, :file_type, :status, :created_at, :updated_at)
                    ON CONFLICT DO NOTHING
                """
                    ),
                    {
                        "id": random_uuid(),
                        "user_id": user_id,
                        "doc_type": random.choice(doc_types),
                        "title": f"{random.choice(doc_types).replace('_', ' ').title()} - {dt.strftime('%Y-%m-%d')}",
                        "description": "Automatically generated test document",
                        "file_name": f"doc_{random_uuid()[:8]}.pdf",
                        "file_type": "application/pdf",
                        "status": "processed",
                        "created_at": dt,
                        "updated_at": dt,
                    },
                )
                doc_count += 1
            except Exception:
                pass

    await session.commit()
    print(f"  ✓ Created {lab_count} lab results")
    print(f"  ✓ Created {doc_count} documents")


async def generate_nutrition_data(session, user_ids):
    """Generate nutrition service data."""
    print("\n🍎 Generating Nutrition Data...")

    meal_count = 0
    goal_count = 0

    for user_id in user_ids:
        # Meal Logs - 3 meals per day for 14 days
        for day in range(min(DAYS_OF_DATA, 14)):
            meal_times = ["breakfast", "lunch", "dinner"]
            for meal_type in meal_times:
                dt = random_date(day + 1, day)
                food = random.choice(FOOD_ITEMS)
                try:
                    await session.execute(
                        text(
                            """
                        INSERT INTO nutrition.meal_logs
                            (id, user_id, meal_type, food_name, calories, protein,
                             carbohydrates, fat, serving_size, logged_at, created_at)
                        VALUES (:id, :user_id, :meal_type, :food_name, :calories,
                                :protein, :carbs, :fat, :serving, :logged_at, :created_at)
                        ON CONFLICT DO NOTHING
                    """
                        ),
                        {
                            "id": random_uuid(),
                            "user_id": user_id,
                            "meal_type": meal_type,
                            "food_name": food["name"],
                            "calories": food["calories"],
                            "protein": food["protein"],
                            "carbs": food["carbs"],
                            "fat": food["fat"],
                            "serving": 1.0,
                            "logged_at": dt,
                            "created_at": dt,
                        },
                    )
                    meal_count += 1
                except Exception:
                    pass

        # Nutrition Goals
        try:
            await session.execute(
                text(
                    """
                INSERT INTO nutrition.nutrition_goals
                    (id, user_id, goal_type, target_calories, target_protein,
                     target_carbs, target_fat, status, start_date, end_date, created_at)
                VALUES (:id, :user_id, :goal_type, :calories, :protein,
                        :carbs, :fat, :status, :start_date, :end_date, :created_at)
                ON CONFLICT DO NOTHING
            """
                ),
                {
                    "id": random_uuid(),
                    "user_id": user_id,
                    "goal_type": random.choice(
                        ["weight_loss", "muscle_gain", "maintenance"]
                    ),
                    "calories": random.choice([1800, 2000, 2200, 2500]),
                    "protein": random.randint(80, 150),
                    "carbs": random.randint(200, 350),
                    "fat": random.randint(50, 100),
                    "status": "active",
                    "start_date": (datetime.utcnow() - timedelta(days=30)).date(),
                    "end_date": (datetime.utcnow() + timedelta(days=60)).date(),
                    "created_at": datetime.utcnow() - timedelta(days=30),
                },
            )
            goal_count += 1
        except Exception:
            pass

    await session.commit()
    print(f"  ✓ Created {meal_count} meal logs")
    print(f"  ✓ Created {goal_count} nutrition goals")


async def generate_ai_insights(session, user_ids):
    """Generate AI insights data."""
    print("\n🧠 Generating AI Insights Data...")

    insight_count = 0
    score_count = 0

    insight_types = [
        "health_trend",
        "anomaly",
        "recommendation",
        "risk_alert",
        "achievement",
    ]
    for user_id in user_ids:
        # Insights
        for _ in range(random.randint(5, 15)):
            dt = random_date(30, 0)
            insight_type = random.choice(insight_types)
            try:
                await session.execute(
                    text(
                        """
                    INSERT INTO insights (id, user_id, insight_type, title, description,
                                         confidence_score, severity, is_read, created_at, updated_at)
                    VALUES (:id, :user_id, :type, :title, :description,
                            :confidence, :severity, :is_read, :created_at, :updated_at)
                    ON CONFLICT DO NOTHING
                """
                    ),
                    {
                        "id": random_uuid(),
                        "user_id": user_id,
                        "type": insight_type,
                        "title": f"{insight_type.replace('_', ' ').title()} detected",
                        "description": f"AI analysis found a {insight_type.replace('_', ' ')} pattern in your recent health data.",
                        "confidence": round(random.uniform(0.6, 0.99), 2),
                        "severity": random.choice(["low", "medium", "high"]),
                        "is_read": random.choice([True, False]),
                        "created_at": dt,
                        "updated_at": dt,
                    },
                )
                insight_count += 1
            except Exception:
                pass

        # Health Scores - daily for 30 days
        for day in range(DAYS_OF_DATA):
            dt = datetime.utcnow() - timedelta(days=day)
            try:
                await session.execute(
                    text(
                        """
                    INSERT INTO health_scores (id, user_id, score_type, score_value,
                                              max_score, components, calculated_at, created_at)
                    VALUES (:id, :user_id, :score_type, :score_value,
                            :max_score, :components, :calculated_at, :created_at)
                    ON CONFLICT DO NOTHING
                """
                    ),
                    {
                        "id": random_uuid(),
                        "user_id": user_id,
                        "score_type": "overall_health",
                        "score_value": round(random.uniform(60, 95), 1),
                        "max_score": 100,
                        "components": '{"fitness": '
                        + str(round(random.uniform(50, 95), 1))
                        + ', "nutrition": '
                        + str(round(random.uniform(50, 95), 1))
                        + ', "sleep": '
                        + str(round(random.uniform(50, 95), 1))
                        + ', "stress": '
                        + str(round(random.uniform(50, 95), 1))
                        + "}",
                        "calculated_at": dt,
                        "created_at": dt,
                    },
                )
                score_count += 1
            except Exception:
                pass

    await session.commit()
    print(f"  ✓ Created {insight_count} insights")
    print(f"  ✓ Created {score_count} health scores")


async def generate_genomics_data(session, user_ids):
    """Generate genomics data."""
    print("\n🧬 Generating Genomics Data...")

    variant_count = 0
    analysis_count = 0

    for user_id in user_ids:
        # Genomic Data (upload records)
        genomic_data_id = random_uuid()
        try:
            await session.execute(
                text(
                    """
                INSERT INTO genomics.genomic_data
                    (id, user_id, data_source, data_format, file_name,
                     quality_status, total_variants, created_at, updated_at)
                VALUES (:id, :user_id, :source, :format, :file_name,
                        :quality, :total_variants, :created_at, :updated_at)
                ON CONFLICT DO NOTHING
            """
                ),
                {
                    "id": genomic_data_id,
                    "user_id": user_id,
                    "source": random.choice(["23andMe", "AncestryDNA", "WGS", "WES"]),
                    "format": "VCF",
                    "file_name": f"sample_{user_id[:8]}.vcf.gz",
                    "quality": "passed",
                    "total_variants": random.randint(20000, 50000),
                    "created_at": datetime.utcnow() - timedelta(days=60),
                    "updated_at": datetime.utcnow(),
                },
            )
        except Exception:
            pass

        # Genetic Variants
        for _ in range(random.randint(10, 25)):
            gene = random.choice(GENE_NAMES)
            chrom = random.choice(CHROMOSOMES[:22])
            try:
                await session.execute(
                    text(
                        """
                    INSERT INTO genomics.genetic_variants
                        (id, user_id, gene_name, chromosome, position, ref_allele,
                         alt_allele, variant_type, classification, clinical_significance,
                         created_at)
                    VALUES (:id, :user_id, :gene, :chrom, :pos, :ref, :alt,
                            :type, :classification, :significance, :created_at)
                    ON CONFLICT DO NOTHING
                """
                    ),
                    {
                        "id": random_uuid(),
                        "user_id": user_id,
                        "gene": gene,
                        "chrom": chrom,
                        "pos": random.randint(1000000, 100000000),
                        "ref": random.choice(["A", "T", "G", "C"]),
                        "alt": random.choice(["A", "T", "G", "C"]),
                        "type": random.choice(["SNP", "insertion", "deletion"]),
                        "classification": random.choice(
                            [
                                "benign",
                                "likely_benign",
                                "VUS",
                                "likely_pathogenic",
                                "pathogenic",
                            ]
                        ),
                        "significance": random.choice(
                            ["benign", "uncertain", "risk_factor"]
                        ),
                        "created_at": datetime.utcnow() - timedelta(days=30),
                    },
                )
                variant_count += 1
            except Exception:
                pass

        # Genomic Analysis
        try:
            await session.execute(
                text(
                    """
                INSERT INTO genomics.genomic_analyses
                    (id, user_id, analysis_type, status, results,
                     started_at, completed_at, created_at)
                VALUES (:id, :user_id, :type, :status, :results,
                        :started_at, :completed_at, :created_at)
                ON CONFLICT DO NOTHING
            """
                ),
                {
                    "id": random_uuid(),
                    "user_id": user_id,
                    "type": random.choice(
                        [
                            "variant_calling",
                            "ancestry",
                            "pharmacogenomics",
                            "disease_risk",
                            "carrier_screening",
                        ]
                    ),
                    "status": "completed",
                    "results": '{"summary": "Analysis complete", "findings": 12, "risk_factors": 3}',
                    "started_at": datetime.utcnow() - timedelta(days=30),
                    "completed_at": datetime.utcnow() - timedelta(days=29),
                    "created_at": datetime.utcnow() - timedelta(days=30),
                },
            )
            analysis_count += 1
        except Exception:
            pass

    await session.commit()
    print(f"  ✓ Created {variant_count} genetic variants")
    print(f"  ✓ Created {analysis_count} genomic analyses")


async def generate_doctor_collaboration_data(session, user_ids):
    """Generate doctor collaboration data."""
    print("\n👨‍⚕️ Generating Doctor Collaboration Data...")

    appt_count = 0
    msg_count = 0
    doctor_id = random_uuid()  # Shared doctor

    for user_id in user_ids:
        # Appointments
        for _ in range(random.randint(2, 5)):
            dt = random_date(60, -30)  # Past and future appointments
            try:
                await session.execute(
                    text(
                        """
                    INSERT INTO doctor_collaboration.appointments
                        (id, patient_id, doctor_id, appointment_type, status,
                         scheduled_start, scheduled_end, notes, created_at, updated_at)
                    VALUES (:id, :patient_id, :doctor_id, :type, :status,
                            :start, :end, :notes, :created_at, :updated_at)
                    ON CONFLICT DO NOTHING
                """
                    ),
                    {
                        "id": random_uuid(),
                        "patient_id": user_id,
                        "doctor_id": doctor_id,
                        "type": random.choice(
                            [
                                "checkup",
                                "follow_up",
                                "consultation",
                                "emergency",
                                "telehealth",
                            ]
                        ),
                        "status": random.choice(
                            ["scheduled", "completed", "cancelled"]
                        ),
                        "start": dt,
                        "end": dt + timedelta(minutes=30),
                        "notes": "Standard appointment notes",
                        "created_at": dt - timedelta(days=7),
                        "updated_at": dt,
                    },
                )
                appt_count += 1
            except Exception:
                pass

        # Messages
        for _ in range(random.randint(3, 8)):
            dt = random_date(30, 0)
            try:
                await session.execute(
                    text(
                        """
                    INSERT INTO doctor_collaboration.messages
                        (id, sender_id, recipient_id, subject, content,
                         is_read, created_at, updated_at)
                    VALUES (:id, :sender, :recipient, :subject, :content,
                            :is_read, :created_at, :updated_at)
                    ON CONFLICT DO NOTHING
                """
                    ),
                    {
                        "id": random_uuid(),
                        "sender": random.choice([user_id, doctor_id]),
                        "recipient": random.choice([user_id, doctor_id]),
                        "subject": random.choice(
                            [
                                "Lab Results Follow-up",
                                "Medication Question",
                                "Appointment Confirmation",
                                "Symptom Update",
                                "Treatment Plan Discussion",
                            ]
                        ),
                        "content": "This is a sample message for testing purposes.",
                        "is_read": random.choice([True, False]),
                        "created_at": dt,
                        "updated_at": dt,
                    },
                )
                msg_count += 1
            except Exception:
                pass

    await session.commit()
    print(f"  ✓ Created {appt_count} appointments")
    print(f"  ✓ Created {msg_count} messages")


# ============================================================
# Main
# ============================================================

SERVICE_GENERATORS = {
    "auth": generate_auth_users,
    "user_profile": generate_user_profiles,
    "health_tracking": generate_health_metrics,
    "device_data": generate_device_data,
    "medical_records": generate_medical_records,
    "nutrition": generate_nutrition_data,
    "ai_insights": generate_ai_insights,
    "genomics": generate_genomics_data,
    "doctor_collaboration": generate_doctor_collaboration_data,
}


async def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic data for all services"
    )
    parser.add_argument(
        "--service", type=str, help="Generate data for specific service only"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=NUM_USERS,
        help=f"Number of test users (default: {NUM_USERS})",
    )
    args = parser.parse_args()

    global NUM_USERS, DAYS_OF_DATA
    NUM_USERS = min(args.users, len(SAMPLE_USERS))

    print("=" * 60)
    print("  PersonalHealthAssistant - Synthetic Data Generation")
    print("=" * 60)
    print(f"\n  Users: {NUM_USERS}")
    print(f"  Days of data: {DAYS_OF_DATA}")
    print(
        f"  Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}"
    )

    engine = await get_engine()
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Always create users first
            user_ids = await generate_auth_users(session, NUM_USERS)

            if args.service:
                if args.service == "auth":
                    pass  # Already done
                elif args.service in SERVICE_GENERATORS:
                    await SERVICE_GENERATORS[args.service](session, user_ids)
                else:
                    print(f"  ✗ Unknown service: {args.service}")
                    print(f"  Available: {', '.join(SERVICE_GENERATORS.keys())}")
                    return
            else:
                # Generate data for all services (in dependency order)
                await generate_user_profiles(session, user_ids)
                await generate_health_metrics(session, user_ids)
                await generate_device_data(session, user_ids)
                await generate_medical_records(session, user_ids)
                await generate_nutrition_data(session, user_ids)
                await generate_ai_insights(session, user_ids)
                await generate_genomics_data(session, user_ids)
                await generate_doctor_collaboration_data(session, user_ids)

        print("\n" + "=" * 60)
        print("  ✅ Synthetic data generation complete!")
        print("=" * 60)
        print("\n  Test users created:")
        for i, user in enumerate(SAMPLE_USERS[:NUM_USERS]):
            print(
                f"    {i+1}. {user['email']} ({user['first_name']} {user['last_name']})"
            )
        print(f"\n  Password for all users: password123")

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
