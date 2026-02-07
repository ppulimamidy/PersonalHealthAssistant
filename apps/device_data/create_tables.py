"""
Device Data Service Database Migration
Creates tables for device management and data collection.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from common.config.settings import get_settings
from common.utils.logging import setup_logging

from .models.device import Device
from .models.data_point import DeviceDataPoint

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()


async def create_device_data_tables():
    """Create device data tables"""
    try:
        # Create async engine
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=True,
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        async with engine.begin() as conn:
            # Create device_data schema
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS device_data"))
            
            # Create devices table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS device_data.devices (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    device_type VARCHAR(50) NOT NULL,
                    manufacturer VARCHAR(255) NOT NULL,
                    model VARCHAR(255) NOT NULL,
                    serial_number VARCHAR(255) UNIQUE,
                    mac_address VARCHAR(17) UNIQUE,
                    connection_type VARCHAR(50) NOT NULL,
                    connection_id VARCHAR(255),
                    api_key VARCHAR(500),
                    api_secret VARCHAR(500),
                    status VARCHAR(50) DEFAULT 'inactive',
                    is_active BOOLEAN DEFAULT TRUE,
                    is_primary BOOLEAN DEFAULT FALSE,
                    supported_metrics JSONB DEFAULT '[]',
                    firmware_version VARCHAR(100),
                    battery_level INTEGER,
                    metadata JSONB DEFAULT '{}',
                    settings JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_sync_at TIMESTAMP,
                    last_used_at TIMESTAMP
                )
            """))
            
            # Create device_data_points table
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS device_data.device_data_points (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL,
                    device_id UUID NOT NULL REFERENCES device_data.devices(id) ON DELETE CASCADE,
                    data_type VARCHAR(50) NOT NULL,
                    source VARCHAR(50) DEFAULT 'device_sync',
                    value NUMERIC(10, 4) NOT NULL,
                    unit VARCHAR(50) NOT NULL,
                    raw_value TEXT,
                    quality VARCHAR(20) DEFAULT 'unknown',
                    is_validated BOOLEAN DEFAULT FALSE,
                    validation_score NUMERIC(3, 2),
                    timestamp TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{}',
                    tags JSONB DEFAULT '[]',
                    is_processed BOOLEAN DEFAULT FALSE,
                    is_anomaly BOOLEAN,
                    anomaly_score NUMERIC(3, 2)
                )
            """))
            
            # Create indexes for performance
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_devices_user_id ON device_data.devices(user_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_devices_status ON device_data.devices(status)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_devices_type ON device_data.devices(device_type)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_devices_serial ON device_data.devices(serial_number)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_devices_mac ON device_data.devices(mac_address)"))
            
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_data_points_user_id ON device_data.device_data_points(user_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_data_points_device_id ON device_data.device_data_points(device_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_data_points_timestamp ON device_data.device_data_points(timestamp)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_data_points_data_type ON device_data.device_data_points(data_type)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_data_points_quality ON device_data.device_data_points(quality)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_data_points_anomaly ON device_data.device_data_points(is_anomaly)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_data_points_user_timestamp ON device_data.device_data_points(user_id, timestamp)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_data_points_device_timestamp ON device_data.device_data_points(device_id, timestamp)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_data_points_type_timestamp ON device_data.device_data_points(data_type, timestamp)"))
            
            # Create device_sync_logs table for tracking sync operations
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS device_data.device_sync_logs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    device_id UUID NOT NULL REFERENCES device_data.devices(id) ON DELETE CASCADE,
                    sync_id VARCHAR(255) NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    data_points_synced INTEGER DEFAULT 0,
                    sync_duration NUMERIC(5, 2),
                    errors JSONB DEFAULT '[]',
                    warnings JSONB DEFAULT '[]',
                    metadata JSONB DEFAULT '{}',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """))
            
            # Create indexes for sync logs
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sync_logs_device_id ON device_data.device_sync_logs(device_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sync_logs_status ON device_data.device_sync_logs(status)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sync_logs_started_at ON device_data.device_sync_logs(started_at)"))
            
            # Create device_health_checks table for monitoring
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS device_data.device_health_checks (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    device_id UUID NOT NULL REFERENCES device_data.devices(id) ON DELETE CASCADE,
                    status VARCHAR(50) NOT NULL,
                    battery_level INTEGER,
                    connection_quality VARCHAR(20),
                    last_sync_status VARCHAR(50),
                    error_message TEXT,
                    firmware_version VARCHAR(100),
                    sync_latency NUMERIC(5, 2),
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes for health checks
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_health_checks_device_id ON device_data.device_health_checks(device_id)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_health_checks_status ON device_data.device_health_checks(status)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_health_checks_checked_at ON device_data.device_health_checks(checked_at)"))
            
            # Create device_data_types table (reference table for supported data types)
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS device_data.device_data_types (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) NOT NULL UNIQUE,
                    category VARCHAR(50) NOT NULL,
                    unit VARCHAR(50) NOT NULL,
                    description TEXT,
                    data_type VARCHAR(50) NOT NULL,
                    min_value NUMERIC(10, 4),
                    max_value NUMERIC(10, 4),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes for device_data_types
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_device_data_types_name ON device_data.device_data_types(name)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_device_data_types_category ON device_data.device_data_types(category)"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_device_data_types_active ON device_data.device_data_types(is_active)"))
            
            # Insert default device data types
            await conn.execute(text("""
                INSERT INTO device_data.device_data_types (name, category, unit, description, data_type, min_value, max_value) VALUES
                ('heart_rate', 'cardiovascular', 'bpm', 'Heart rate in beats per minute', 'numeric', 40, 200),
                ('blood_pressure_systolic', 'cardiovascular', 'mmHg', 'Systolic blood pressure', 'numeric', 70, 200),
                ('blood_pressure_diastolic', 'cardiovascular', 'mmHg', 'Diastolic blood pressure', 'numeric', 40, 130),
                ('blood_oxygen', 'respiratory', '%', 'Blood oxygen saturation', 'numeric', 70, 100),
                ('respiratory_rate', 'respiratory', 'breaths/min', 'Breathing rate per minute', 'numeric', 8, 40),
                ('temperature', 'vital_signs', '°C', 'Body temperature', 'numeric', 35, 42),
                ('weight', 'body_composition', 'kg', 'Body weight', 'numeric', 20, 300),
                ('body_fat_percentage', 'body_composition', '%', 'Body fat percentage', 'numeric', 5, 50),
                ('muscle_mass', 'body_composition', 'kg', 'Muscle mass', 'numeric', 10, 100),
                ('steps', 'activity', 'count', 'Daily step count', 'numeric', 0, 50000),
                ('calories_burned', 'activity', 'kcal', 'Calories burned', 'numeric', 0, 5000),
                ('distance', 'activity', 'km', 'Distance traveled', 'numeric', 0, 100),
                ('sleep_duration', 'sleep', 'hours', 'Sleep duration', 'numeric', 0, 24),
                ('sleep_quality', 'sleep', 'score', 'Sleep quality score', 'numeric', 0, 100),
                ('glucose', 'metabolic', 'mg/dL', 'Blood glucose level', 'numeric', 40, 400),
                ('hydration', 'hydration', 'ml', 'Water intake', 'numeric', 0, 5000),
                ('stress_level', 'wellness', 'score', 'Stress level score', 'numeric', 0, 100),
                ('mood', 'wellness', 'score', 'Mood score', 'numeric', 0, 100)
                ON CONFLICT (name) DO NOTHING
            """))
            
            # Note: RLS policies are disabled for now as auth.uid() function is not available
            # Row-level security will be implemented later when auth system is properly integrated
            
            logger.info("✅ Device data tables created successfully")
            
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Error creating device data tables: {e}")
        raise


async def main():
    """Main function to run the migration"""
    logger.info("🚀 Starting device data service database migration...")
    
    try:
        await create_device_data_tables()
        logger.info("✅ Device data service database migration completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 