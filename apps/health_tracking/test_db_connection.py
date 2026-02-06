#!/usr/bin/env python3
"""
Database Connection Test for Health Tracking Service
"""

import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Add the parent directory to the path to import common modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.database.connection import get_async_db
from common.config.settings import settings

async def test_database_connection():
    """Test database connection and basic operations"""
    print("🔍 Testing Database Connection...")
    
    try:
        # Test database connection
        async for db in get_async_db():
            print("✅ Database connection successful")
            
            # Test basic query
            result = await db.execute(text("SELECT 1"))
            row = result.fetchone()
            print(f"✅ Basic query successful: {row[0]}")
            
            # Test if health_tracking tables exist
            result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE '%health%'
                ORDER BY table_name
            """))
            tables = result.fetchall()
            print(f"✅ Found {len(tables)} health-related tables:")
            for table in tables:
                print(f"   - {table[0]}")
            
            # Test if specific tables exist
            required_tables = [
                'health_metrics',
                'health_goals', 
                'health_insights',
                'vital_signs',
                'symptoms',
                'devices',
                'alerts'
            ]
            
            for table in required_tables:
                result = await db.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = '{table}'
                    )
                """))
                exists = result.scalar()
                status = "✅" if exists else "❌"
                print(f"{status} Table '{table}': {'EXISTS' if exists else 'MISSING'}")
            
            break
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    return True

async def test_models_import():
    """Test if all models can be imported"""
    print("\n🔍 Testing Model Imports...")
    
    try:
        from apps.health_tracking.models.health_metrics import HealthMetric, MetricType
        print("✅ Health metrics models imported successfully")
    except Exception as e:
        print(f"❌ Health metrics models import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.models.health_goals import HealthGoal, GoalStatus
        print("✅ Health goals models imported successfully")
    except Exception as e:
        print(f"❌ Health goals models import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.models.health_insights import HealthInsight, InsightType
        print("✅ Health insights models imported successfully")
    except Exception as e:
        print(f"❌ Health insights models import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.models.vital_signs import VitalSigns, VitalSignType
        print("✅ Vital signs models imported successfully")
    except Exception as e:
        print(f"❌ Vital signs models import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.models.symptoms import Symptoms, SymptomCategory
        print("✅ Symptoms models imported successfully")
    except Exception as e:
        print(f"❌ Symptoms models import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.models.alerts import Alert, AlertType
        print("✅ Alerts models imported successfully")
    except Exception as e:
        print(f"❌ Alerts models import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.models.devices import Device, DeviceType
        print("✅ Devices models imported successfully")
    except Exception as e:
        print(f"❌ Devices models import failed: {e}")
        return False
    
    return True

async def test_service_import():
    """Test if services can be imported"""
    print("\n🔍 Testing Service Imports...")
    
    try:
        from apps.health_tracking.services.health_analytics import HealthAnalyticsService
        print("✅ Health analytics service imported successfully")
    except Exception as e:
        print(f"❌ Health analytics service import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.services.health_insights import HealthInsightsService
        print("✅ Health insights service imported successfully")
    except Exception as e:
        print(f"❌ Health insights service import failed: {e}")
        return False
    
    return True

async def test_api_import():
    """Test if API routers can be imported"""
    print("\n🔍 Testing API Router Imports...")
    
    try:
        from apps.health_tracking.api.metrics import router as metrics_router
        print("✅ Metrics API router imported successfully")
    except Exception as e:
        print(f"❌ Metrics API router import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.api.goals import router as goals_router
        print("✅ Goals API router imported successfully")
    except Exception as e:
        print(f"❌ Goals API router import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.api.symptoms import router as symptoms_router
        print("✅ Symptoms API router imported successfully")
    except Exception as e:
        print(f"❌ Symptoms API router import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.api.vitals import router as vitals_router
        print("✅ Vitals API router imported successfully")
    except Exception as e:
        print(f"❌ Vitals API router import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.api.insights import router as insights_router
        print("✅ Insights API router imported successfully")
    except Exception as e:
        print(f"❌ Insights API router import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.api.analytics import router as analytics_router
        print("✅ Analytics API router imported successfully")
    except Exception as e:
        print(f"❌ Analytics API router import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.api.devices import router as devices_router
        print("✅ Devices API router imported successfully")
    except Exception as e:
        print(f"❌ Devices API router import failed: {e}")
        return False
    
    try:
        from apps.health_tracking.api.alerts import router as alerts_router
        print("✅ Alerts API router imported successfully")
    except Exception as e:
        print(f"❌ Alerts API router import failed: {e}")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("🚀 Health Tracking Service - Database and Import Tests")
    print("=" * 60)
    
    # Test database connection
    db_success = await test_database_connection()
    
    # Test model imports
    models_success = await test_models_import()
    
    # Test service imports
    services_success = await test_service_import()
    
    # Test API imports
    api_success = await test_api_import()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"Database Connection: {'✅ PASS' if db_success else '❌ FAIL'}")
    print(f"Model Imports: {'✅ PASS' if models_success else '❌ FAIL'}")
    print(f"Service Imports: {'✅ PASS' if services_success else '❌ FAIL'}")
    print(f"API Router Imports: {'✅ PASS' if api_success else '❌ FAIL'}")
    
    all_success = db_success and models_success and services_success and api_success
    
    if all_success:
        print("\n🎉 All tests passed! Service should be working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 