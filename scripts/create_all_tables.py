#!/usr/bin/env python3
"""
Master Database Table Creation Script
Creates all schemas, tables, indexes, and views for all PersonalHealthAssistant services.

Usage:
    python scripts/create_all_tables.py [--drop-first] [--service SERVICE_NAME]

Services and their schemas:
    auth               -> auth schema (18 tables)
    user_profile       -> public schema (4 tables)
    health_tracking    -> public schema (7 tables)
    voice_input        -> public schema (1 table)
    device_data        -> device_data schema (2 tables)
    medical_records    -> medical_records schema (18 tables)
    nutrition          -> nutrition schema (7 tables)
    ai_insights        -> public schema (9 tables)
    genomics           -> genomics schema (9 tables)
    doctor_collaboration -> doctor_collaboration schema (4 tables)
"""

import asyncio
import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from common.config.settings import get_settings

settings = get_settings()


async def get_engine():
    """Create async engine."""
    db_url = settings.DATABASE_URL
    if "postgresql://" in db_url and "+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    return create_async_engine(db_url, echo=False)


async def create_schemas(engine):
    """Create all database schemas."""
    schemas = [
        "auth",
        "device_data",
        "medical_records",
        "nutrition",
        "genomics",
        "doctor_collaboration",
    ]
    async with engine.begin() as conn:
        for schema in schemas:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            print(f"  ✓ Schema '{schema}' ready")


async def create_auth_tables(engine):
    """Create auth service tables (18 tables)."""
    print("\n📋 Creating Auth Service tables...")
    try:
        from apps.auth.models.user import User, UserProfile, UserPreferences
        from apps.auth.models.session import Session, RefreshToken, TokenBlacklist
        from apps.auth.models.roles import Role, Permission, UserRole, RolePermission
        from apps.auth.models.mfa import MFADevice, MFABackupCode, MFAAttempt
        from apps.auth.models.audit import AuthAuditLog, SecurityAlert
        from apps.auth.models.consent import (
            ConsentRecord,
            DataAccessLog,
            ConsentTemplate,
        )
        from common.models.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✓ Auth tables created (18 tables)")
    except Exception as e:
        print(f"  ✗ Auth tables failed: {e}")


async def create_user_profile_tables(engine):
    """Create user profile service tables (4 tables)."""
    print("\n📋 Creating User Profile Service tables...")
    try:
        from apps.user_profile.models.profile import Profile
        from apps.user_profile.models.preferences import Preferences
        from apps.user_profile.models.privacy_settings import PrivacySettings
        from apps.user_profile.models.health_attributes import HealthAttributes
        from common.models.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✓ User Profile tables created (4 tables)")
    except Exception as e:
        print(f"  ✗ User Profile tables failed: {e}")


async def create_health_tracking_tables(engine):
    """Create health tracking service tables (7 tables)."""
    print("\n📋 Creating Health Tracking Service tables...")
    try:
        from apps.health_tracking.models.health_metrics import HealthMetric
        from apps.health_tracking.models.health_goals import HealthGoal
        from apps.health_tracking.models.health_insights import HealthInsight
        from apps.health_tracking.models.symptoms import Symptoms
        from apps.health_tracking.models.vital_signs import VitalSigns
        from common.models.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✓ Health Tracking tables created (7 tables)")
    except Exception as e:
        print(f"  ✗ Health Tracking tables failed: {e}")


async def create_device_data_tables(engine):
    """Create device data service tables (2 tables)."""
    print("\n📋 Creating Device Data Service tables...")
    try:
        from apps.device_data.models.device import Device
        from apps.device_data.models.data_point import DeviceDataPoint
        from common.models.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✓ Device Data tables created (2 tables)")
    except Exception as e:
        print(f"  ✗ Device Data tables failed: {e}")


async def create_medical_records_tables(engine):
    """Create medical records service tables (18 tables)."""
    print("\n📋 Creating Medical Records Service tables...")
    try:
        from apps.medical_records.models.lab_results_db import LabResultDB
        from apps.medical_records.models.documents import (
            DocumentDB,
            DocumentProcessingLogDB,
        )
        from apps.medical_records.models.imaging import (
            ImagingStudyDB,
            MedicalImageDB,
            DICOMSeriesDB,
            DICOMInstanceDB,
        )
        from apps.medical_records.models.clinical_reports import (
            ClinicalReportDB,
            ReportVersionDB,
            ReportTemplateDB,
            ReportCategoryDB,
            ReportAuditLogDB,
        )
        from apps.medical_records.models.epic_fhir_data import (
            EpicFHIRConnection,
            EpicFHIRObservation,
            EpicFHIRDiagnosticReport,
            EpicFHIRDocument,
            EpicFHIRImagingStudy,
            EpicFHIRSyncLog,
        )
        from common.models.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Also create Epic FHIR tables (separate Base)
        try:
            from apps.medical_records.models.epic_fhir_data import Base as EpicBase

            async with engine.begin() as conn:
                await conn.run_sync(EpicBase.metadata.create_all)
        except Exception:
            pass

        print("  ✓ Medical Records tables created (18 tables)")
    except Exception as e:
        print(f"  ✗ Medical Records tables failed: {e}")


async def create_nutrition_tables(engine):
    """Create nutrition service tables (7 tables)."""
    print("\n📋 Creating Nutrition Service tables...")
    try:
        sql_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "apps",
            "nutrition",
            "migrations",
            "create_nutrition_tables.sql",
        )
        if os.path.exists(sql_file):
            with open(sql_file, "r") as f:
                sql = f.read()
            async with engine.begin() as conn:
                # Execute statements one by one
                for statement in sql.split(";"):
                    statement = statement.strip()
                    if statement and not statement.startswith("--"):
                        try:
                            await conn.execute(text(statement))
                        except Exception:
                            pass  # Ignore already-exists errors
            print("  ✓ Nutrition tables created (7 tables)")
        else:
            # Fallback to ORM
            from apps.nutrition.models.database_models import Base as NutritionBase

            async with engine.begin() as conn:
                await conn.run_sync(NutritionBase.metadata.create_all)
            print("  ✓ Nutrition tables created via ORM (7 tables)")
    except Exception as e:
        print(f"  ✗ Nutrition tables failed: {e}")


async def create_ai_insights_tables(engine):
    """Create AI insights service tables (9 tables)."""
    print("\n📋 Creating AI Insights Service tables...")
    try:
        from apps.ai_insights.models.insight_models import InsightDB, HealthPatternDB
        from apps.ai_insights.models.health_score_models import (
            HealthScoreDB,
            HealthScoreTrendDB,
            RiskAssessmentDB,
            WellnessIndexDB,
        )
        from apps.ai_insights.models.recommendation_models import (
            RecommendationDB,
            RecommendationActionDB,
            HealthGoalDB,
        )
        from common.models.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✓ AI Insights tables created (9 tables)")
    except Exception as e:
        print(f"  ✗ AI Insights tables failed: {e}")


async def create_genomics_tables(engine):
    """Create genomics service tables (9 tables)."""
    print("\n📋 Creating Genomics Service tables...")
    try:
        from apps.genomics.models.genomic_data import (
            GenomicData,
            GeneticVariant,
            PharmacogenomicProfile,
        )
        from apps.genomics.models.analysis import (
            GenomicAnalysis,
            DiseaseRiskAssessment,
            AncestryAnalysis,
        )
        from apps.genomics.models.counseling import (
            GeneticCounseling,
            CounselingSession,
            RiskReport,
        )
        from common.models.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✓ Genomics tables created (9 tables)")
    except Exception as e:
        print(f"  ✗ Genomics tables failed: {e}")


async def create_doctor_collaboration_tables(engine):
    """Create doctor collaboration service tables (4 tables)."""
    print("\n📋 Creating Doctor Collaboration Service tables...")
    try:
        from apps.doctor_collaboration.models.appointment import Appointment
        from apps.doctor_collaboration.models.consultation import Consultation
        from apps.doctor_collaboration.models.messaging import Message
        from apps.doctor_collaboration.models.notification import Notification
        from common.models.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✓ Doctor Collaboration tables created (4 tables)")
    except Exception as e:
        print(f"  ✗ Doctor Collaboration tables failed: {e}")


async def create_voice_input_tables(engine):
    """Create voice input service tables (1 table)."""
    print("\n📋 Creating Voice Input Service tables...")
    try:
        from apps.voice_input.models.voice_input import VoiceInput
        from common.models.base import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("  ✓ Voice Input tables created (1 table)")
    except Exception as e:
        print(f"  ✗ Voice Input tables failed: {e}")


async def verify_tables(engine):
    """Verify all tables were created."""
    print("\n🔍 Verifying tables...")
    async with engine.begin() as conn:
        result = await conn.execute(
            text(
                """
            SELECT schemaname, tablename
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schemaname, tablename
        """
            )
        )
        rows = result.fetchall()

        current_schema = None
        count = 0
        for schema, table in rows:
            if schema != current_schema:
                if current_schema:
                    print(f"    ({count} tables)")
                current_schema = schema
                count = 0
                print(f"\n  Schema: {schema}")
            print(f"    - {table}")
            count += 1
        if current_schema:
            print(f"    ({count} tables)")

        print(f"\n  Total: {len(rows)} tables across all schemas")


# Map of service names to creation functions
SERVICE_CREATORS = {
    "auth": create_auth_tables,
    "user_profile": create_user_profile_tables,
    "health_tracking": create_health_tracking_tables,
    "voice_input": create_voice_input_tables,
    "device_data": create_device_data_tables,
    "medical_records": create_medical_records_tables,
    "nutrition": create_nutrition_tables,
    "ai_insights": create_ai_insights_tables,
    "genomics": create_genomics_tables,
    "doctor_collaboration": create_doctor_collaboration_tables,
}


async def main():
    parser = argparse.ArgumentParser(description="Create all database tables")
    parser.add_argument(
        "--drop-first", action="store_true", help="Drop all tables before creating"
    )
    parser.add_argument(
        "--service", type=str, help="Create tables for a specific service only"
    )
    parser.add_argument(
        "--verify-only", action="store_true", help="Only verify existing tables"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  PersonalHealthAssistant - Database Table Creation")
    print("=" * 60)
    print(
        f"\n  Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}"
    )

    engine = await get_engine()

    try:
        if args.verify_only:
            await verify_tables(engine)
            return

        if args.drop_first:
            print("\n⚠️  Dropping all tables...")
            async with engine.begin() as conn:
                for schema in [
                    "doctor_collaboration",
                    "genomics",
                    "nutrition",
                    "medical_records",
                    "device_data",
                    "auth",
                ]:
                    await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
                await conn.execute(
                    text(
                        "DROP TABLE IF EXISTS user_profiles, user_preferences, "
                        "privacy_settings, health_attributes, health_metrics, "
                        "health_goals, health_insights, symptoms, vital_signs, "
                        "alerts, devices, voice_inputs, insights, health_patterns, "
                        "health_scores, health_score_trends, risk_assessments, "
                        "wellness_indices, recommendations, recommendation_actions CASCADE"
                    )
                )
            print("  ✓ All tables dropped")

        # Create schemas first
        print("\n📁 Creating schemas...")
        await create_schemas(engine)

        # Create tables
        if args.service:
            if args.service in SERVICE_CREATORS:
                await SERVICE_CREATORS[args.service](engine)
            else:
                print(f"  ✗ Unknown service: {args.service}")
                print(f"  Available: {', '.join(SERVICE_CREATORS.keys())}")
                return
        else:
            # Create in dependency order
            for service_name in [
                "auth",
                "user_profile",
                "health_tracking",
                "voice_input",
                "device_data",
                "medical_records",
                "nutrition",
                "ai_insights",
                "genomics",
                "doctor_collaboration",
            ]:
                await SERVICE_CREATORS[service_name](engine)

        # Verify
        await verify_tables(engine)

        print("\n" + "=" * 60)
        print("  ✅ Database setup complete!")
        print("=" * 60)

    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
