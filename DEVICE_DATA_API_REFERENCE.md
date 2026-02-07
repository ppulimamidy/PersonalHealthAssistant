# Device Data Service API Reference

## Overview
The Device Data Service provides comprehensive APIs for managing health devices, data collection, and device analytics. This service handles device registration, data ingestion, device health monitoring, and analytics.

**Base URL**: `http://localhost:8004`
**API Version**: `v1`

## Authentication
All endpoints require authentication using JWT Bearer tokens.

```http
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### 1. Health Check
**GET** `/health`

Check if the service is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-26T01:09:32.000Z"
}
```

---

### 2. Device Management

#### 2.1 Get Supported Device Types
**GET** `/api/v1/device-data/devices/types/supported`

Get all supported device types with descriptions.

**Response:**
```json
[
  {
    "name": "smart_ring",
    "description": "Smart ring for health monitoring (Oura, etc.)"
  },
  {
    "name": "smartwatch",
    "description": "Smart watch with health tracking capabilities"
  },
  {
    "name": "fitness_tracker",
    "description": "Dedicated fitness and activity tracker"
  }
  // ... 47 total device types
]
```

#### 2.2 Get Supported Connection Types
**GET** `/api/v1/device-data/devices/connection-types/supported`

Get all supported connection types.

**Response:**
```json
[
  {
    "name": "bluetooth",
    "description": "Bluetooth wireless connection"
  },
  {
    "name": "wifi",
    "description": "WiFi wireless connection"
  },
  {
    "name": "api",
    "description": "Application Programming Interface"
  }
  // ... 7 total connection types
]
```

#### 2.3 List Devices
**GET** `/api/v1/device-data/devices/`

Get all devices for the authenticated user.

**Query Parameters:**
- `limit` (optional): Number of devices to return (default: 50)
- `offset` (optional): Number of devices to skip (default: 0)
- `device_type` (optional): Filter by device type
- `status` (optional): Filter by device status

**Response:**
```json
{
  "devices": [
    {
      "id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
      "name": "Test Oura Ring",
      "device_type": "smart_ring",
      "manufacturer": "Oura",
      "model": "Gen 3",
      "serial_number": "TEST123456",
      "connection_type": "api",
      "status": "inactive",
      "is_active": true,
      "is_primary": false,
      "battery_level": null,
      "last_sync_at": null,
      "last_used_at": null
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

#### 2.4 Create Device
**POST** `/api/v1/device-data/devices/`

Register a new device.

**Request Body:**
```json
{
  "name": "My Oura Ring",
  "device_type": "smart_ring",
  "manufacturer": "Oura",
  "model": "Gen 3",
  "serial_number": "OURA123456",
  "connection_type": "api",
  "connection_id": "optional_connection_id",
  "api_key": "optional_api_key",
  "api_secret": "optional_api_secret",
  "supported_metrics": ["heart_rate", "sleep", "activity"],
  "device_metadata": {
    "firmware_version": "2.1.0",
    "color": "black"
  },
  "settings": {
    "sync_frequency": "hourly"
  }
}
```

**Response (201 Created):**
```json
{
  "id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "name": "My Oura Ring",
  "device_type": "smart_ring",
  "manufacturer": "Oura",
  "model": "Gen 3",
  "serial_number": "OURA123456",
  "mac_address": null,
  "connection_type": "api",
  "connection_id": "optional_connection_id",
  "supported_metrics": ["heart_rate", "sleep", "activity"],
  "device_metadata": {
    "firmware_version": "2.1.0",
    "color": "black"
  },
  "settings": {
    "sync_frequency": "hourly"
  },
  "user_id": "a517e8b8-ec02-45d8-9d37-1d31468d7522",
  "status": "inactive",
  "is_active": true,
  "is_primary": false,
  "firmware_version": null,
  "battery_level": null,
  "created_at": "2025-07-26T01:09:33.333372",
  "updated_at": "2025-07-26T01:09:33.333374",
  "last_sync_at": null,
  "last_used_at": null
}
```

#### 2.5 Get Device by ID
**GET** `/api/v1/device-data/devices/{device_id}`

Get detailed information about a specific device.

**Response:**
```json
{
  "id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "name": "My Oura Ring",
  "device_type": "smart_ring",
  "manufacturer": "Oura",
  "model": "Gen 3",
  "serial_number": "OURA123456",
  "mac_address": null,
  "connection_type": "api",
  "connection_id": "optional_connection_id",
  "api_key": "optional_api_key",
  "api_secret": "optional_api_secret",
  "supported_metrics": ["heart_rate", "sleep", "activity"],
  "device_metadata": {
    "firmware_version": "2.1.0",
    "color": "black"
  },
  "settings": {
    "sync_frequency": "hourly"
  },
  "user_id": "a517e8b8-ec02-45d8-9d37-1d31468d7522",
  "status": "inactive",
  "is_active": true,
  "is_primary": false,
  "firmware_version": null,
  "battery_level": null,
  "created_at": "2025-07-26T01:09:33.333372",
  "updated_at": "2025-07-26T01:09:33.333374",
  "last_sync_at": null,
  "last_used_at": null
}
```

#### 2.6 Update Device
**PUT** `/api/v1/device-data/devices/{device_id}`

Update device information.

**Request Body:**
```json
{
  "name": "Updated Device Name",
  "status": "active",
  "is_primary": true,
  "settings": {
    "sync_frequency": "daily"
  }
}
```

**Response:**
```json
{
  "id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "name": "Updated Device Name",
  "device_type": "smart_ring",
  "manufacturer": "Oura",
  "model": "Gen 3",
  "serial_number": "OURA123456",
  "status": "active",
  "is_active": true,
  "is_primary": true,
  "settings": {
    "sync_frequency": "daily"
  },
  "updated_at": "2025-07-26T01:10:00.000000"
}
```

#### 2.7 Delete Device
**DELETE** `/api/v1/device-data/devices/{device_id}`

Delete a device and all associated data.

**Response (204 No Content):**
```json
{
  "success": true,
  "message": "Device deleted successfully"
}
```

#### 2.8 Connect Device
**POST** `/api/v1/device-data/devices/{device_id}/connect`

Connect to a device and establish communication.

**Request Body:**
```json
{
  "connection_type": "api",
  "connection_id": "device_connection_id",
  "api_key": "your_api_key",
  "api_secret": "your_api_secret",
  "device_info": {
    "firmware_version": "2.1.0",
    "battery_level": 85
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Device connected successfully",
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "status": "connected",
  "connection_quality": "excellent"
}
```

#### 2.9 Disconnect Device
**POST** `/api/v1/device-data/devices/{device_id}/disconnect`

Disconnect from a device.

**Response:**
```json
{
  "success": true,
  "message": "Device disconnected successfully",
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "status": "disconnected"
}
```

#### 2.10 Get Device Health
**GET** `/api/v1/device-data/devices/{device_id}/health`

Get device health status and diagnostics.

**Response:**
```json
{
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "status": "active",
  "battery_level": 85,
  "connection_quality": "excellent",
  "last_sync_status": "successful",
  "error_message": null,
  "firmware_version": "2.1.0",
  "sync_latency": 0.5
}
```

#### 2.11 Set Primary Device
**POST** `/api/v1/device-data/devices/{device_id}/set-primary`

Set a device as the primary device for the user.

**Response:**
```json
{
  "success": true,
  "message": "Device set as primary",
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "is_primary": true
}
```

#### 2.12 Sync Device
**POST** `/api/v1/device-data/devices/{device_id}/sync`

Trigger a manual sync for a device.

**Request Body:**
```json
{
  "force_sync": true,
  "sync_metrics": ["heart_rate", "sleep"],
  "sync_from_date": "2025-07-20T00:00:00Z",
  "sync_to_date": "2025-07-26T23:59:59Z"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Device sync initiated",
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "sync_id": "sync_123456",
  "estimated_duration": "5 minutes"
}
```

#### 2.13 Get Device Statistics
**GET** `/api/v1/device-data/devices/statistics/summary`

Get overall device statistics for the user.

**Response:**
```json
{
  "total_devices": 3,
  "active_devices": 2,
  "connected_devices": 1,
  "devices_by_type": {
    "smart_ring": 1,
    "smartwatch": 1,
    "fitness_tracker": 1
  },
  "devices_by_status": {
    "active": 2,
    "inactive": 1
  },
  "last_sync": "2025-07-26T01:00:00Z"
}
```

---

### 3. Data Management

#### 3.1 Get Data Summary
**GET** `/api/v1/device-data/data/summary`

Get overall data summary for the user.

**Response:**
```json
{
  "total_records": 15420,
  "data_by_type": {
    "heart_rate": 5200,
    "sleep": 3100,
    "activity": 7120
  },
  "last_record_at": "2025-07-26T01:00:00Z"
}
```

#### 3.2 Get Data Points
**GET** `/api/v1/device-data/data/points`

Get data points with filtering and pagination.

**Query Parameters:**
- `device_id` (optional): Filter by device ID
- `data_type` (optional): Filter by data type
- `start_date` (optional): Start date for data range
- `end_date` (optional): End date for data range
- `limit` (optional): Number of records to return (default: 100)
- `offset` (optional): Number of records to skip (default: 0)

**Response:**
```json
{
  "data_points": [
    {
      "id": "dp_123456",
      "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
      "data_type": "heart_rate",
      "source": "smart_ring",
      "value": 72,
      "unit": "bpm",
      "raw_value": 72.5,
      "quality": "high",
      "timestamp": "2025-07-26T01:00:00Z",
      "is_validated": true,
      "validation_score": 0.95,
      "tags": ["resting", "normal"],
      "is_processed": true,
      "is_anomaly": false,
      "anomaly_score": 0.1
    }
  ],
  "total": 15420,
  "limit": 100,
  "offset": 0
}
```

#### 3.3 Create Data Point
**POST** `/api/v1/device-data/data/points`

Create a new data point.

**Request Body:**
```json
{
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "data_type": "heart_rate",
  "source": "smart_ring",
  "value": 72,
  "unit": "bpm",
  "raw_value": 72.5,
  "quality": "high",
  "timestamp": "2025-07-26T01:00:00Z",
  "tags": ["resting", "normal"],
  "data_metadata": {
    "measurement_method": "optical",
    "confidence": 0.95
  }
}
```

**Response (201 Created):**
```json
{
  "id": "dp_123456",
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "data_type": "heart_rate",
  "source": "smart_ring",
  "value": 72,
  "unit": "bpm",
  "raw_value": 72.5,
  "quality": "high",
  "timestamp": "2025-07-26T01:00:00Z",
  "created_at": "2025-07-26T01:00:00Z"
}
```

#### 3.4 Batch Create Data Points
**POST** `/api/v1/device-data/data/points/batch`

Create multiple data points in a single request.

**Request Body:**
```json
{
  "data_points": [
    {
      "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
      "data_type": "heart_rate",
      "value": 72,
      "timestamp": "2025-07-26T01:00:00Z"
    },
    {
      "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
      "data_type": "heart_rate",
      "value": 75,
      "timestamp": "2025-07-26T01:01:00Z"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "created_count": 2,
  "failed_count": 0,
  "data_point_ids": ["dp_123456", "dp_123457"]
}
```

#### 3.5 Get Data Point by ID
**GET** `/api/v1/device-data/data/points/{data_point_id}`

Get a specific data point by ID.

**Response:**
```json
{
  "id": "dp_123456",
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "data_type": "heart_rate",
  "source": "smart_ring",
  "value": 72,
  "unit": "bpm",
  "raw_value": 72.5,
  "quality": "high",
  "timestamp": "2025-07-26T01:00:00Z",
  "is_validated": true,
  "validation_score": 0.95,
  "tags": ["resting", "normal"],
  "is_processed": true,
  "is_anomaly": false,
  "anomaly_score": 0.1,
  "data_metadata": {
    "measurement_method": "optical",
    "confidence": 0.95
  },
  "created_at": "2025-07-26T01:00:00Z",
  "updated_at": "2025-07-26T01:00:00Z"
}
```

#### 3.6 Get Recent Data by Type
**GET** `/api/v1/device-data/data/recent/{data_type}`

Get recent data points for a specific data type.

**Query Parameters:**
- `device_id` (optional): Filter by device ID
- `hours` (optional): Number of hours to look back (default: 24)
- `limit` (optional): Number of records to return (default: 100)

**Response:**
```json
{
  "data_type": "heart_rate",
  "data_points": [
    {
      "id": "dp_123456",
      "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
      "value": 72,
      "unit": "bpm",
      "timestamp": "2025-07-26T01:00:00Z",
      "quality": "high"
    }
  ],
  "total": 24,
  "time_range": {
    "start": "2025-07-25T01:00:00Z",
    "end": "2025-07-26T01:00:00Z"
  }
}
```

#### 3.7 Get Data Statistics
**GET** `/api/v1/device-data/data/statistics`

Get statistical information about data.

**Query Parameters:**
- `device_id` (optional): Filter by device ID
- `data_type` (optional): Filter by data type
- `start_date` (optional): Start date for statistics
- `end_date` (optional): End date for statistics

**Response:**
```json
{
  "total_records": 15420,
  "data_types": {
    "heart_rate": {
      "count": 5200,
      "min_value": 45,
      "max_value": 180,
      "avg_value": 72.5,
      "last_record": "2025-07-26T01:00:00Z"
    },
    "sleep": {
      "count": 3100,
      "min_value": 4.5,
      "max_value": 9.2,
      "avg_value": 7.3,
      "last_record": "2025-07-26T00:00:00Z"
    }
  },
  "time_range": {
    "start": "2025-07-01T00:00:00Z",
    "end": "2025-07-26T23:59:59Z"
  }
}
```

#### 3.8 Get Data Aggregation
**GET** `/api/v1/device-data/data/aggregation`

Get aggregated data for charts and analytics.

**Query Parameters:**
- `device_id` (optional): Filter by device ID
- `data_type`: Data type to aggregate
- `aggregation_type`: Type of aggregation (hourly, daily, weekly, monthly)
- `start_date`: Start date for aggregation
- `end_date`: End date for aggregation

**Response:**
```json
{
  "data_type": "heart_rate",
  "aggregation_type": "hourly",
  "data": [
    {
      "timestamp": "2025-07-26T00:00:00Z",
      "avg_value": 72.5,
      "min_value": 68,
      "max_value": 78,
      "count": 60
    },
    {
      "timestamp": "2025-07-26T01:00:00Z",
      "avg_value": 71.2,
      "min_value": 65,
      "max_value": 76,
      "count": 60
    }
  ],
  "time_range": {
    "start": "2025-07-26T00:00:00Z",
    "end": "2025-07-26T23:59:59Z"
  }
}
```

#### 3.9 Get Data Anomalies
**GET** `/api/v1/device-data/data/anomalies/detect`

Detect anomalies in data.

**Query Parameters:**
- `device_id` (optional): Filter by device ID
- `data_type` (optional): Filter by data type
- `start_date` (optional): Start date for anomaly detection
- `end_date` (optional): End date for anomaly detection
- `threshold` (optional): Anomaly detection threshold (default: 0.8)

**Response:**
```json
{
  "anomalies": [
    {
      "data_point_id": "dp_123456",
      "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
      "data_type": "heart_rate",
      "value": 180,
      "timestamp": "2025-07-26T01:00:00Z",
      "anomaly_score": 0.95,
      "severity": "high",
      "description": "Unusually high heart rate detected"
    }
  ],
  "total_anomalies": 1,
  "time_range": {
    "start": "2025-07-26T00:00:00Z",
    "end": "2025-07-26T23:59:59Z"
  }
}
```

#### 3.10 Get Device Anomalies
**GET** `/api/v1/device-data/data/anomalies/{device_id}`

Get anomalies for a specific device.

**Response:**
```json
{
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "anomalies": [
    {
      "data_point_id": "dp_123456",
      "data_type": "heart_rate",
      "value": 180,
      "timestamp": "2025-07-26T01:00:00Z",
      "anomaly_score": 0.95,
      "severity": "high"
    }
  ],
  "total_anomalies": 1
}
```

#### 3.11 Get Data Quality Levels
**GET** `/api/v1/device-data/data/quality-levels`

Get data quality information.

**Response:**
```json
{
  "quality_levels": {
    "high": 12000,
    "medium": 3000,
    "low": 420
  },
  "total_records": 15420,
  "quality_distribution": {
    "high": 77.8,
    "medium": 19.5,
    "low": 2.7
  }
}
```

#### 3.12 Get Device Data Quality
**GET** `/api/v1/device-data/data/quality/{device_id}`

Get data quality information for a specific device.

**Response:**
```json
{
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "quality_levels": {
    "high": 8000,
    "medium": 1500,
    "low": 200
  },
  "total_records": 9700,
  "quality_score": 0.85,
  "recommendations": [
    "Consider recalibrating device for better accuracy"
  ]
}
```

#### 3.13 Get Real-time Data
**GET** `/api/v1/device-data/data/realtime/{device_id}/latest`

Get the latest real-time data from a device.

**Response:**
```json
{
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "latest_data": {
    "heart_rate": {
      "value": 72,
      "unit": "bpm",
      "timestamp": "2025-07-26T01:00:00Z",
      "quality": "high"
    },
    "battery_level": {
      "value": 85,
      "unit": "percent",
      "timestamp": "2025-07-26T01:00:00Z"
    }
  },
  "last_updated": "2025-07-26T01:00:00Z"
}
```

#### 3.14 Get Data Stream
**GET** `/api/v1/device-data/data/stream/{device_id}`

Get a real-time data stream for a device (WebSocket).

**WebSocket URL**: `ws://localhost:8004/api/v1/device-data/data/stream/{device_id}`

**Message Format:**
```json
{
  "type": "data_point",
  "data": {
    "data_type": "heart_rate",
    "value": 72,
    "unit": "bpm",
    "timestamp": "2025-07-26T01:00:00Z"
  }
}
```

---

### 4. Analytics and Agents

#### 4.1 List Analytics Agents
**GET** `/api/v1/device-data/agents`

Get available analytics agents.

**Response:**
```json
{
  "agents": [
    {
      "name": "data_quality_monitor",
      "description": "Monitors data quality and provides recommendations",
      "status": "active",
      "version": "1.0.0"
    },
    {
      "name": "anomaly_detector",
      "description": "Detects anomalies in health data",
      "status": "active",
      "version": "1.0.0"
    }
  ],
  "total_agents": 2
}
```

#### 4.2 Get Agent Health
**GET** `/api/v1/device-data/agents/health`

Get health status of all agents.

**Response:**
```json
{
  "overall_status": "healthy",
  "agents": [
    {
      "name": "data_quality_monitor",
      "status": "healthy",
      "last_check": "2025-07-26T01:00:00Z",
      "uptime": "24h 30m"
    },
    {
      "name": "anomaly_detector",
      "status": "healthy",
      "last_check": "2025-07-26T01:00:00Z",
      "uptime": "24h 30m"
    }
  ]
}
```

#### 4.3 Get Agent Status
**GET** `/api/v1/device-data/agents/status`

Get detailed status of all agents.

**Response:**
```json
{
  "agents": [
    {
      "name": "data_quality_monitor",
      "status": "active",
      "version": "1.0.0",
      "last_run": "2025-07-26T01:00:00Z",
      "next_run": "2025-07-26T02:00:00Z",
      "processed_records": 15420,
      "errors": 0
    }
  ]
}
```

#### 4.4 Run Agent Analysis
**POST** `/api/v1/device-data/agents/analyze`

Run analysis on all devices.

**Request Body:**
```json
{
  "agent_name": "data_quality_monitor",
  "parameters": {
    "quality_threshold": 0.8
  }
}
```

**Response:**
```json
{
  "success": true,
  "analysis_id": "analysis_123456",
  "message": "Analysis started successfully",
  "estimated_duration": "10 minutes"
}
```

#### 4.5 Run Device Analysis
**POST** `/api/v1/device-data/agents/analyze/{device_id}`

Run analysis on a specific device.

**Request Body:**
```json
{
  "agent_name": "anomaly_detector",
  "parameters": {
    "sensitivity": "high"
  }
}
```

**Response:**
```json
{
  "success": true,
  "analysis_id": "analysis_123457",
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "message": "Device analysis started successfully"
}
```

#### 4.6 Get Agent Metrics
**GET** `/api/v1/device-data/agents/{agent_name}/metrics`

Get metrics for a specific agent.

**Response:**
```json
{
  "agent_name": "data_quality_monitor",
  "metrics": {
    "total_analyses": 150,
    "successful_analyses": 148,
    "failed_analyses": 2,
    "average_processing_time": "2.5s",
    "last_24h_analyses": 24
  },
  "performance": {
    "cpu_usage": "15%",
    "memory_usage": "256MB",
    "uptime": "24h 30m"
  }
}
```

#### 4.7 Reset Agent
**POST** `/api/v1/device-data/agents/{agent_name}/reset`

Reset a specific agent.

**Response:**
```json
{
  "success": true,
  "message": "Agent reset successfully",
  "agent_name": "data_quality_monitor"
}
```

#### 4.8 Calibrate Device
**POST** `/api/v1/device-data/agents/calibrate/{device_id}`

Calibrate a device using analytics agents.

**Request Body:**
```json
{
  "calibration_type": "accuracy",
  "parameters": {
    "reference_data": "manual_measurements",
    "tolerance": 0.05
  }
}
```

**Response:**
```json
{
  "success": true,
  "calibration_id": "calibration_123456",
  "device_id": "a0390c94-e27e-4117-9e94-3fab43c0ab3f",
  "message": "Device calibration started successfully"
}
```

---

### 5. Error Responses

All endpoints may return the following error responses:

#### 400 Bad Request
```json
{
  "success": false,
  "error": "Invalid request data",
  "error_code": "HTTP_400",
  "details": {
    "request_id": "req_123456",
    "validation_errors": [
      {
        "field": "device_type",
        "message": "Invalid device type"
      }
    ]
  }
}
```

#### 401 Unauthorized
```json
{
  "success": false,
  "error": "Token has expired",
  "error_code": "HTTP_401",
  "details": {
    "request_id": "req_123456"
  }
}
```

#### 404 Not Found
```json
{
  "success": false,
  "error": "Device not found",
  "error_code": "HTTP_404",
  "details": {
    "request_id": "req_123456"
  }
}
```

#### 409 Conflict
```json
{
  "success": false,
  "error": "Device with this serial number already exists",
  "error_code": "HTTP_409",
  "details": {
    "request_id": "req_123456"
  }
}
```

#### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Failed to create device",
  "error_code": "HTTP_500",
  "details": {
    "request_id": "req_123456"
  }
}
```

---

## Data Types

### Device Types
- `wearable` - General wearable health device
- `smartwatch` - Smart watch with health tracking capabilities
- `fitness_tracker` - Dedicated fitness and activity tracker
- `smart_ring` - Smart ring for health monitoring (Oura, etc.)
- `smart_band` - Smart wristband or bracelet
- `smart_clothing` - Smart clothing with embedded sensors
- `smart_shoes` - Smart shoes with activity tracking
- `smart_glasses` - Smart glasses with health features
- `smart_earbuds` - Smart earbuds with health monitoring
- `blood_pressure_monitor` - Blood pressure monitoring device
- `glucose_monitor` - Blood glucose monitoring device
- `thermometer` - Digital thermometer
- `scale` - Smart scale with body composition
- `sleep_tracker` - Dedicated sleep tracking device
- `heart_rate_monitor` - Heart rate monitoring device
- `oxygen_monitor` - Blood oxygen saturation monitor
- `ecg_monitor` - Electrocardiogram monitoring device
- `blood_glucose_meter` - Traditional blood glucose meter
- `insulin_pump` - Insulin pump device
- `continuous_glucose_monitor` - Continuous glucose monitoring system
- `pulse_oximeter` - Pulse oximeter for oxygen levels
- `blood_pressure_cuff` - Blood pressure cuff monitor
- `therapy_device` - Medical therapy device
- `medication_dispenser` - Smart medication dispenser
- `cpap_machine` - CPAP machine for sleep apnea
- `inhaler` - Smart inhaler device
- `hearing_aid` - Smart hearing aid
- `prosthetic` - Smart prosthetic device
- `mobile_app` - Mobile health application
- `health_platform` - Health platform or service
- `fitness_app` - Fitness tracking application
- `nutrition_app` - Nutrition tracking application
- `meditation_app` - Meditation and wellness app
- `smart_mirror` - Smart mirror with health features
- `smart_toilet` - Smart toilet with health monitoring
- `smart_shower` - Smart shower with health tracking
- `air_quality_monitor` - Air quality monitoring device
- `water_quality_monitor` - Water quality monitoring device
- `fertility_tracker` - Fertility tracking device
- `pregnancy_monitor` - Pregnancy monitoring device
- `baby_monitor` - Smart baby monitor
- `pet_health_tracker` - Pet health tracking device
- `athletic_performance` - Athletic performance tracker
- `clinical_device` - Clinical medical device
- `research_device` - Research and development device
- `lab_equipment` - Laboratory equipment
- `other` - Other health device

### Connection Types
- `bluetooth` - Bluetooth wireless connection
- `wifi` - WiFi wireless connection
- `usb` - USB wired connection
- `nfc` - Near Field Communication
- `cellular` - Cellular network connection
- `manual` - Manual data entry
- `api` - Application Programming Interface

### Device Status
- `active` - Device is active and connected
- `inactive` - Device is inactive
- `connecting` - Device is attempting to connect
- `disconnected` - Device is disconnected
- `error` - Device has an error
- `maintenance` - Device is in maintenance mode
- `offline` - Device is offline
- `syncing` - Device is syncing data

### Data Quality Levels
- `high` - High quality data
- `medium` - Medium quality data
- `low` - Low quality data

---

## Rate Limits

- **General endpoints**: 1000 requests per minute
- **Data ingestion**: 10000 requests per minute
- **Analytics**: 100 requests per minute

## Webhooks

The service supports webhooks for real-time notifications:

- **Device connected**: `POST /webhooks/device-connected`
- **Device disconnected**: `POST /webhooks/device-disconnected`
- **Data anomaly detected**: `POST /webhooks/anomaly-detected`
- **Device sync completed**: `POST /webhooks/sync-completed`

---

## SDK Examples

### JavaScript/TypeScript Example

```typescript
class DeviceDataAPI {
  private baseURL = 'http://localhost:8004';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Get all devices
  async getDevices() {
    return this.request('/api/v1/device-data/devices/');
  }

  // Create a new device
  async createDevice(deviceData: any) {
    return this.request('/api/v1/device-data/devices/', {
      method: 'POST',
      body: JSON.stringify(deviceData),
    });
  }

  // Get device by ID
  async getDevice(deviceId: string) {
    return this.request(`/api/v1/device-data/devices/${deviceId}`);
  }

  // Update device
  async updateDevice(deviceId: string, updates: any) {
    return this.request(`/api/v1/device-data/devices/${deviceId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  // Delete device
  async deleteDevice(deviceId: string) {
    return this.request(`/api/v1/device-data/devices/${deviceId}`, {
      method: 'DELETE',
    });
  }

  // Get data points
  async getDataPoints(params: any = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/api/v1/device-data/data/points?${queryString}`);
  }

  // Create data point
  async createDataPoint(dataPoint: any) {
    return this.request('/api/v1/device-data/data/points', {
      method: 'POST',
      body: JSON.stringify(dataPoint),
    });
  }
}

// Usage example
const api = new DeviceDataAPI('your-jwt-token');

// Get all devices
const devices = await api.getDevices();
console.log('Devices:', devices);

// Create a new device
const newDevice = await api.createDevice({
  name: 'My Oura Ring',
  device_type: 'smart_ring',
  manufacturer: 'Oura',
  model: 'Gen 3',
  connection_type: 'api',
  serial_number: 'OURA123456'
});
console.log('Created device:', newDevice);
```

---

## Support

For API support and questions:
- **Documentation**: [API Documentation](http://localhost:8004/docs)
- **OpenAPI Spec**: [OpenAPI JSON](http://localhost:8004/openapi.json)
- **Health Check**: [Service Health](http://localhost:8004/health)

---

*Last updated: July 26, 2025*
*API Version: 1.0* 