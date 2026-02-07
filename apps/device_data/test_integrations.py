"""
Device Integration Test Script
Test script to demonstrate device integrations with sample data.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from common.config.settings import get_settings
from common.utils.logging import setup_logging

from .models.device import Device, DeviceType, DeviceStatus, ConnectionType
from .models.data_point import DataType, DataQuality, DataSource
from .services.device_service import DeviceService
from .services.data_service import DataService
from .services.device_integrations import (
    AppleHealthIntegration, FitbitIntegration, WhoopIntegration, CGMIntegration
)

logger = setup_logging()
settings = get_settings()


async def test_apple_health_integration():
    """Test Apple Health integration with sample data"""
    logger.info("🧪 Testing Apple Health Integration...")
    
    # Create a test device
    device = Device(
        id=uuid4(),
        user_id=uuid4(),  # Test user ID
        name="iPhone 15 Pro - Apple Health",
        device_type=DeviceType.SMARTWATCH,
        manufacturer="Apple",
        model="iPhone 15 Pro",
        connection_type=ConnectionType.API,
        api_key="test_apple_health_token",
        status=DeviceStatus.ACTIVE,
        supported_metrics=["heart_rate", "steps", "sleep", "weight"]
    )
    
    # Create integration
    integration = AppleHealthIntegration(device)
    
    # Test authentication
    auth_success = await integration.authenticate()
    logger.info(f"✅ Apple Health Authentication: {'SUCCESS' if auth_success else 'FAILED'}")
    
    # Test device info
    device_info = await integration.get_device_info()
    logger.info(f"📱 Apple Health Device Info: {device_info}")
    
    # Test data sync
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    data_points = await integration.sync_data(start_date, end_date)
    logger.info(f"📊 Apple Health Data Points: {len(data_points)}")
    
    # Log sample data points
    for i, point in enumerate(data_points[:5]):  # Show first 5 points
        logger.info(f"  Point {i+1}: {point.data_type} = {point.value} {point.unit} at {point.timestamp}")
    
    return data_points


async def test_fitbit_integration():
    """Test Fitbit integration with sample data"""
    logger.info("🧪 Testing Fitbit Integration...")
    
    # Create a test device
    device = Device(
        id=uuid4(),
        user_id=uuid4(),  # Test user ID
        name="Fitbit Charge 5",
        device_type=DeviceType.FITNESS_TRACKER,
        manufacturer="Fitbit",
        model="Charge 5",
        connection_type=ConnectionType.API,
        api_key="test_fitbit_token",
        connection_id="test_user_id",
        status=DeviceStatus.ACTIVE,
        supported_metrics=["heart_rate", "steps", "sleep", "weight"]
    )
    
    # Create integration
    integration = FitbitIntegration(device)
    
    # Test authentication (will fail with test token, but shows the flow)
    try:
        auth_success = await integration.authenticate()
        logger.info(f"✅ Fitbit Authentication: {'SUCCESS' if auth_success else 'FAILED'}")
    except Exception as e:
        logger.info(f"❌ Fitbit Authentication: FAILED (expected with test token) - {e}")
    
    # Test device info
    try:
        device_info = await integration.get_device_info()
        logger.info(f"📱 Fitbit Device Info: {device_info}")
    except Exception as e:
        logger.info(f"❌ Fitbit Device Info: FAILED (expected with test token) - {e}")
    
    # Test data sync (will fail with test token, but shows the flow)
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        data_points = await integration.sync_data(start_date, end_date)
        logger.info(f"📊 Fitbit Data Points: {len(data_points)}")
    except Exception as e:
        logger.info(f"❌ Fitbit Data Sync: FAILED (expected with test token) - {e}")
    
    return []


async def test_whoop_integration():
    """Test Whoop integration with sample data"""
    logger.info("🧪 Testing Whoop Integration...")
    
    # Create a test device
    device = Device(
        id=uuid4(),
        user_id=uuid4(),  # Test user ID
        name="Whoop 4.0",
        device_type=DeviceType.WEARABLE,
        manufacturer="Whoop",
        model="4.0",
        connection_type=ConnectionType.API,
        api_key="test_whoop_token",
        status=DeviceStatus.ACTIVE,
        supported_metrics=["heart_rate", "sleep", "recovery", "strain"]
    )
    
    # Create integration
    integration = WhoopIntegration(device)
    
    # Test authentication (will fail with test token, but shows the flow)
    try:
        auth_success = await integration.authenticate()
        logger.info(f"✅ Whoop Authentication: {'SUCCESS' if auth_success else 'FAILED'}")
    except Exception as e:
        logger.info(f"❌ Whoop Authentication: FAILED (expected with test token) - {e}")
    
    # Test device info
    try:
        device_info = await integration.get_device_info()
        logger.info(f"📱 Whoop Device Info: {device_info}")
    except Exception as e:
        logger.info(f"❌ Whoop Device Info: FAILED (expected with test token) - {e}")
    
    # Test data sync (will fail with test token, but shows the flow)
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        data_points = await integration.sync_data(start_date, end_date)
        logger.info(f"📊 Whoop Data Points: {len(data_points)}")
    except Exception as e:
        logger.info(f"❌ Whoop Data Sync: FAILED (expected with test token) - {e}")
    
    return []


async def test_cgm_integration():
    """Test CGM integration with sample data"""
    logger.info("🧪 Testing CGM Integration...")
    
    # Create a test device
    device = Device(
        id=uuid4(),
        user_id=uuid4(),  # Test user ID
        name="Dexcom G6",
        device_type=DeviceType.GLUCOSE_MONITOR,
        manufacturer="Dexcom",
        model="G6",
        connection_type=ConnectionType.API,
        api_key="test_cgm_token",
        status=DeviceStatus.ACTIVE,
        supported_metrics=["blood_glucose", "calibration", "events"]
    )
    
    # Create integration
    integration = CGMIntegration(device)
    
    # Test authentication (will fail with test token, but shows the flow)
    try:
        auth_success = await integration.authenticate()
        logger.info(f"✅ CGM Authentication: {'SUCCESS' if auth_success else 'FAILED'}")
    except Exception as e:
        logger.info(f"❌ CGM Authentication: FAILED (expected with test token) - {e}")
    
    # Test device info
    try:
        device_info = await integration.get_device_info()
        logger.info(f"📱 CGM Device Info: {device_info}")
    except Exception as e:
        logger.info(f"❌ CGM Device Info: FAILED (expected with test token) - {e}")
    
    # Test data sync (will fail with test token, but shows the flow)
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        data_points = await integration.sync_data(start_date, end_date)
        logger.info(f"📊 CGM Data Points: {len(data_points)}")
    except Exception as e:
        logger.info(f"❌ CGM Data Sync: FAILED (expected with test token) - {e}")
    
    return []


async def test_integration_factory():
    """Test the device integration factory"""
    logger.info("🏭 Testing Device Integration Factory...")
    
    # Test devices
    test_devices = [
        Device(
            id=uuid4(),
            user_id=uuid4(),
            name="Apple Health Test",
            device_type=DeviceType.SMARTWATCH,
            manufacturer="Apple",
            model="iPhone",
            connection_type=ConnectionType.API,
            api_key="test_token"
        ),
        Device(
            id=uuid4(),
            user_id=uuid4(),
            name="Fitbit Test",
            device_type=DeviceType.FITNESS_TRACKER,
            manufacturer="Fitbit",
            model="Charge",
            connection_type=ConnectionType.API,
            api_key="test_token"
        ),
        Device(
            id=uuid4(),
            user_id=uuid4(),
            name="Whoop Test",
            device_type=DeviceType.WEARABLE,
            manufacturer="Whoop",
            model="4.0",
            connection_type=ConnectionType.API,
            api_key="test_token"
        ),
        Device(
            id=uuid4(),
            user_id=uuid4(),
            name="CGM Test",
            device_type=DeviceType.GLUCOSE_MONITOR,
            manufacturer="Dexcom",
            model="G6",
            connection_type=ConnectionType.API,
            api_key="test_token"
        )
    ]
    
    from .services.device_integrations import DeviceIntegrationFactory
    
    for device in test_devices:
        try:
            integration = DeviceIntegrationFactory.create_integration(device)
            logger.info(f"✅ Created integration for {device.name}: {type(integration).__name__}")
        except Exception as e:
            logger.error(f"❌ Failed to create integration for {device.name}: {e}")


async def main():
    """Main test function"""
    logger.info("🚀 Starting Device Integration Tests...")
    
    try:
        # Test integration factory
        await test_integration_factory()
        
        # Test individual integrations
        await test_apple_health_integration()
        await test_fitbit_integration()
        await test_whoop_integration()
        await test_cgm_integration()
        
        logger.info("✅ All device integration tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 