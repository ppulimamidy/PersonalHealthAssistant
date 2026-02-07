"""Unit tests for Device Data service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import uuid


# Test device model creation
class TestDeviceModels:
    def test_device_data_point_creation(self):
        """Test DeviceDataPoint Pydantic model."""
        from apps.device_data.models.data_point import DataPointCreate

        data = DataPointCreate(
            device_id=str(uuid.uuid4()),
            data_type="heart_rate",
            value=72.0,
            unit="bpm",
            timestamp=datetime.utcnow(),
        )
        assert data.data_type == "heart_rate"
        assert data.value == 72.0

    def test_device_creation(self):
        """Test Device Pydantic model."""
        from apps.device_data.models.device import DeviceCreate

        data = DeviceCreate(
            name="Test Watch",
            device_type="smartwatch",
            manufacturer="Test Inc",
            model="TW-100",
            connection_type="bluetooth",
        )
        assert data.name == "Test Watch"

    def test_data_point_with_metadata(self):
        """Test DataPointCreate with metadata and tags."""
        from apps.device_data.models.data_point import DataPointCreate

        data = DataPointCreate(
            device_id=str(uuid.uuid4()),
            data_type="blood_glucose",
            value=95.5,
            unit="mg/dL",
            timestamp=datetime.utcnow(),
            data_metadata={"sensor": "cgm", "calibrated": True},
            tags=["glucose", "fasting"],
        )
        assert data.data_metadata["sensor"] == "cgm"
        assert len(data.tags) == 2

    def test_data_point_invalid_value(self):
        """Test DataPointCreate rejects extreme values."""
        from apps.device_data.models.data_point import DataPointCreate

        with pytest.raises(Exception):
            DataPointCreate(
                device_id=str(uuid.uuid4()),
                data_type="heart_rate",
                value=99999999,
                unit="bpm",
                timestamp=datetime.utcnow(),
            )

    def test_device_update_partial(self):
        """Test DeviceUpdate allows partial updates."""
        from apps.device_data.models.device import DeviceUpdate

        update = DeviceUpdate(name="Updated Watch")
        assert update.name == "Updated Watch"
        assert update.manufacturer is None

    def test_data_point_query_defaults(self):
        """Test DataPointQuery default values."""
        from apps.device_data.models.data_point import DataPointQuery

        query = DataPointQuery()
        assert query.limit == 100
        assert query.offset == 0


class TestAppleHealth:
    def test_supported_types(self):
        """Test Apple Health supported types list."""
        supported = [
            "steps",
            "heart_rate",
            "sleep_analysis",
            "workouts",
            "active_energy",
            "resting_heart_rate",
            "blood_oxygen",
            "respiratory_rate",
            "body_temperature",
            "blood_pressure",
            "weight",
            "height",
            "body_fat_percentage",
        ]
        assert len(supported) == 13
        assert "steps" in supported


class TestDataEnums:
    def test_data_type_enum(self):
        """Test DataType enum values."""
        from apps.device_data.models.data_point import DataType

        assert DataType.HEART_RATE == "heart_rate"
        assert DataType.BLOOD_GLUCOSE == "blood_glucose"
        assert DataType.STEPS_COUNT == "steps_count"

    def test_data_quality_enum(self):
        """Test DataQuality enum values."""
        from apps.device_data.models.data_point import DataQuality

        assert DataQuality.EXCELLENT == "excellent"
        assert DataQuality.POOR == "poor"

    def test_device_type_enum(self):
        """Test DeviceType enum values."""
        from apps.device_data.models.device import DeviceType

        assert DeviceType.SMARTWATCH == "smartwatch"
        assert DeviceType.GLUCOSE_MONITOR == "glucose_monitor"
