# Dexcom CGM API Endpoints Documentation

## Overview
This document provides the complete API specification for Dexcom CGM (Continuous Glucose Monitor) integration endpoints. All endpoints require JWT authentication via the `Authorization: Bearer <token>` header.

**Base URL:** `http://localhost:8004/api/v1/device-data`

---

## 🔐 Authentication
All endpoints require authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

To get a JWT token, use the auth service:
```
POST http://localhost:8000/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

---

## 📱 Device Management Endpoints

### 1. Create Dexcom Device
**POST** `/devices/`

Creates a new Dexcom CGM device for the authenticated user.

**Request Body:**
```json
{
  "name": "Dexcom G7",
  "device_type": "continuous_glucose_monitor",
  "manufacturer": "DEXCOM",
  "model": "G7",
  "serial_number": "DEXCOM123456",
  "connection_type": "api",
  "device_metadata": {
    "sandbox": true
  }
}
```

**Response (201 Created):**
```json
{
  "id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
  "name": "Dexcom G7",
  "device_type": "continuous_glucose_monitor",
  "manufacturer": "DEXCOM",
  "model": "G7",
  "serial_number": "DEXCOM123456",
  "status": "inactive",
  "created_at": "2025-07-27T00:15:17.646260Z"
}
```

### 2. List User Devices
**GET** `/devices/`

Returns all devices for the authenticated user.

**Response (200 OK):**
```json
[
  {
    "id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
    "name": "Dexcom G7",
    "device_type": "continuous_glucose_monitor",
    "manufacturer": "DEXCOM",
    "model": "G7",
    "serial_number": "DEXCOM123456",
    "status": "active",
    "created_at": "2025-07-27T00:15:17.646260Z"
  }
]
```

### 3. Get Device Details
**GET** `/devices/{device_id}`

Returns detailed information about a specific device.

**Response (200 OK):**
```json
{
  "id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
  "name": "Dexcom G7",
  "device_type": "continuous_glucose_monitor",
  "manufacturer": "DEXCOM",
  "model": "G7",
  "serial_number": "DEXCOM123456",
  "status": "active",
  "device_metadata": {
    "sandbox": true,
    "sandbox_user": "User7",
    "oauth_completed": true
  },
  "created_at": "2025-07-27T00:15:17.646260Z"
}
```

### 4. Update Device (Full Update)
**PUT** `/devices/{device_id}`

Updates all device information (full update).

**Request Body:**
```json
{
  "name": "Updated Device Name",
  "model": "G7",
  "serial_number": "DEXCOM123456"
}
```

**Response (200 OK):**
```json
{
  "id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
  "name": "Updated Device Name",
  "device_type": "continuous_glucose_monitor",
  "manufacturer": "DEXCOM",
  "model": "G7",
  "serial_number": "DEXCOM123456",
  "status": "active",
  "updated_at": "2025-07-27T01:44:25.026435Z"
}
```

### 5. Update Device (Partial Update)
**PATCH** `/devices/{device_id}`

Partially updates device information.

**Request Body:**
```json
{
  "name": "Updated Device Name"
}
```

**Response (200 OK):**
```json
{
  "id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
  "name": "Updated Device Name",
  "device_type": "continuous_glucose_monitor",
  "manufacturer": "DEXCOM",
  "model": "G7",
  "serial_number": "DEXCOM123456",
  "status": "active",
  "updated_at": "2025-07-27T01:44:25.026435Z"
}
```

---

## 🔐 OAuth Authentication Endpoints

### 1. Start OAuth Flow
**GET** `/oauth/{device_id}/authorize`

Initiates the OAuth flow for a Dexcom device. Returns available sandbox users for testing.

**Response (200 OK):**
```json
{
  "success": true,
  "oauth_type": "sandbox",
  "sandbox_users": ["User7", "User8", "User6", "User4"],
  "message": "Select a sandbox user for testing",
  "device_id": "1a5fc123-2d4d-4513-acba-b2723ff144db"
}
```

### 2. Complete OAuth Callback
**POST** `/oauth/{device_id}/callback`

Completes the OAuth flow by selecting a sandbox user.

**Query Parameters:**
- `sandbox_user` (required): One of "User7", "User8", "User6", "User4"

**Response (200 OK):**
```json
{
  "success": true,
  "message": "OAuth completed successfully with sandbox user User7",
  "device_id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
  "sandbox_user": "User7",
  "device_status": "active",
  "oauth_completed": true
}
```

### 3. Check OAuth Status
**GET** `/oauth/{device_id}/status`

Returns the current OAuth status for a device.

**Response (200 OK):**
```json
{
  "success": true,
  "device_id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
  "oauth_completed": true,
  "sandbox_user": "User7",
  "oauth_completed_at": "2025-07-27T00:18:30.123456Z",
  "device_status": "active",
  "has_access_token": true
}
```

---

## 🔄 Integration Management Endpoints

### 1. Test Device Connection
**POST** `/integrations/{device_id}/test`

Tests the connection to the Dexcom device.

**Response (200 OK):**
```json
{
  "success": true,
  "device_id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
  "status": "connected",
  "message": "Device connection test successful"
}
```

### 2. Get Device Integration Info
**GET** `/integrations/{device_id}/info`

Returns detailed integration information including supported data types.

**Response (200 OK):**
```json
{
  "success": true,
  "device_type": "dexcom_cgm",
  "user": {
    "id": "User7",
    "email": "user-User7@dexcom-sandbox.com",
    "first_name": "Sandbox",
    "last_name": "User-User7",
    "timezone": "UTC"
  },
  "devices": [
    {
      "id": "G7-123456",
      "name": "Dexcom G7",
      "model": "G7"
    }
  ],
  "statistics": {
    "total_egvs": 288,
    "total_calibrations": 12,
    "total_events": 24
  },
  "last_sync": "2025-07-27T00:20:00.000000Z",
  "status": "connected",
  "supported_data_types": [
    "continuous_glucose",
    "glucose_calibration", 
    "insulin_event",
    "carb_event",
    "glucose_alert",
    "glucose_trend",
    "sensor_status",
    "transmitter_status"
  ]
}
```

### 3. Sync Device Data
**POST** `/integrations/{device_id}/sync`

Syncs data from the Dexcom device for a specified date range.

**Query Parameters:**
- `start_date` (optional): Start date in ISO format (default: 7 days ago)
- `end_date` (optional): End date in ISO format (default: now)

**Example:**
```
POST /integrations/1a5fc123-2d4d-4513-acba-b2723ff144db/sync?start_date=2025-07-20T00:00:00Z&end_date=2025-07-27T00:00:00Z
```

**Response (200 OK):**
```json
{
  "success": true,
  "device_id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
  "data_points_synced": 324,
  "sync_status": "completed",
  "start_date": "2025-07-20T00:00:00Z",
  "end_date": "2025-07-27T00:00:00Z",
  "data_types": {
    "continuous_glucose": 288,
    "glucose_calibration": 12,
    "insulin_event": 8,
    "carb_event": 16
  }
}
```

### 4. Get Device Sync Status
**GET** `/integrations/{device_id}/sync-status`

Returns the current sync status and information for a device.

**Response (200 OK):**
```json
{
  "success": true,
  "device_id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
  "sync_status": "completed",
  "last_sync_at": "2025-07-27T00:20:00.000000Z",
  "total_data_points": 324,
  "sync_available": true,
  "needs_oauth": false
}
```

---

## 📊 Data Retrieval Endpoints

### 1. Get Data Summary
**GET** `/data/summary`

Returns a summary of all data points for the user or a specific device.

**Query Parameters:**
- `device_id` (optional): Specific device ID to filter by

**Response (200 OK):**
```json
{
  "total_data_points": 324,
  "data_types": {
    "continuous_glucose": {
      "count": 288,
      "latest_value": 120,
      "latest_timestamp": "2025-07-27T00:15:00Z"
    },
    "glucose_calibration": {
      "count": 12,
      "latest_value": 118,
      "latest_timestamp": "2025-07-26T12:00:00Z"
    },
    "insulin_event": {
      "count": 8,
      "latest_value": 5.0,
      "latest_timestamp": "2025-07-26T18:30:00Z"
    },
    "carb_event": {
      "count": 16,
      "latest_value": 45,
      "latest_timestamp": "2025-07-26T19:00:00Z"
    }
  },
  "date_range": {
    "start": "2025-07-20T00:00:00Z",
    "end": "2025-07-27T00:00:00Z"
  }
}
```

### 2. Get Data Points
**GET** `/data/points`

Retrieves specific data points with filtering options.

**Query Parameters:**
- `device_id` (optional): Filter by device ID
- `data_type` (optional): Filter by data type (e.g., "continuous_glucose")
- `limit` (optional): Number of points to return (default: 100, max: 1000)
- `timeRange` (optional): Time range in days (e.g., "7d", "30d")
- `start_date` (optional): Start date in ISO format
- `end_date` (optional): End date in ISO format

**Example:**
```
GET /data/points?device_id=1a5fc123-2d4d-4513-acba-b2723ff144db&data_type=continuous_glucose&limit=50&timeRange=7d
```

**Response (200 OK):**
```json
{
  "data_points": [
    {
      "id": "dp-123456",
      "device_id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
      "data_type": "continuous_glucose",
      "value": 120,
      "unit": "mg/dL",
      "timestamp": "2025-07-27T00:15:00Z",
      "metadata": {
        "trend": "rising",
        "trend_rate": 2.5
      }
    }
  ],
  "total_count": 288,
  "has_more": true
}
```

### 3. Get Device Statistics
**GET** `/devices/statistics/summary`

Returns comprehensive statistics for all devices.

**Response (200 OK):**
```json
{
  "total_devices": 3,
  "active_devices": 2,
  "total_data_points": 1250,
  "devices_by_type": {
    "continuous_glucose_monitor": {
      "count": 1,
      "data_points": 324,
      "devices": [
        {
          "id": "1a5fc123-2d4d-4513-acba-b2723ff144db",
          "name": "Dexcom G7",
          "status": "active",
          "data_points": 324,
          "last_sync": "2025-07-27T00:20:00Z"
        }
      ]
    }
  },
  "data_types_summary": {
    "continuous_glucose": 288,
    "glucose_calibration": 12,
    "insulin_event": 8,
    "carb_event": 16
  }
}
```

---

## 📊 Supported Data Types

### Dexcom CGM Data Types:
- **continuous_glucose**: Real-time glucose readings (mg/dL)
- **glucose_calibration**: Calibration data points
- **insulin_event**: Insulin administration events
- **carb_event**: Carbohydrate intake events
- **glucose_alert**: Glucose alerts and notifications
- **glucose_trend**: Glucose trend indicators
- **sensor_status**: Sensor status information
- **transmitter_status**: Transmitter status information
- **time_in_range**: Percentage of time glucose is within target range

### Data Point Structure:
```json
{
  "id": "uuid",
  "device_id": "device-uuid",
  "data_type": "continuous_glucose",
  "value": 120,
  "unit": "mg/dL",
  "timestamp": "2025-07-27T00:15:00Z",
  "metadata": {
    "trend": "rising|falling|stable",
    "trend_rate": 2.5,
    "system_time": "2025-07-27T00:15:00Z",
    "display_time": "2025-07-27T00:15:00Z"
  },
  "tags": [],
  "is_processed": true,
  "is_anomaly": false
}
```

---

## 🚨 Error Responses

### Common Error Codes:
- **401 Unauthorized**: Invalid or missing JWT token
- **403 Forbidden**: User doesn't have access to the device
- **404 Not Found**: Device or endpoint not found
- **400 Bad Request**: Invalid parameters or OAuth not completed
- **405 Method Not Allowed**: Wrong HTTP method (e.g., GET instead of POST for sync)
- **500 Internal Server Error**: Server error

### Error Response Format:
```json
{
  "detail": "Error message description"
}
```

---

## 🔄 Complete Integration Flow

### Step-by-Step Integration Process:

1. **Create Device**
   ```
   POST /devices/
   ```

2. **Start OAuth**
   ```
   GET /oauth/{device_id}/authorize
   ```

3. **Complete OAuth**
   ```
   POST /oauth/{device_id}/callback?sandbox_user=User7
   ```

4. **Test Connection**
   ```
   POST /integrations/{device_id}/test
   ```

5. **Sync Data**
   ```
   POST /integrations/{device_id}/sync
   ```

6. **Get Sync Status**
   ```
   GET /integrations/{device_id}/sync-status
   ```

7. **Retrieve Data**
   ```
   GET /data/summary?device_id={device_id}
   GET /data/points?device_id={device_id}&data_type=continuous_glucose
   ```

---

## ⚠️ Important Notes for Frontend

### HTTP Method Requirements:
- **Sync operations**: Use `POST` method (NOT GET)
- **Data retrieval**: Use `GET` method
- **Device updates**: Use `PUT` (full update) or `PATCH` (partial update)
- **OAuth operations**: Use specified methods (GET for authorize, POST for callback)

### Common Frontend Mistakes:
1. **❌ Wrong**: `GET /devices/{device_id}/sync` (Method Not Allowed)
2. **✅ Correct**: `POST /integrations/{device_id}/sync` (for syncing)
3. **✅ Correct**: `GET /integrations/{device_id}/sync-status` (for status)
4. **❌ Wrong**: `PATCH /devices/{device_id}` (Method Not Allowed) - **FIXED** ✅
5. **✅ Correct**: `PATCH /devices/{device_id}` (for partial updates) - **NOW SUPPORTED** ✅
6. **❌ Wrong**: `GET /data/points?data_type=insulin_event` (500 Error) - **FIXED** ✅
7. **✅ Correct**: `GET /data/points?data_type=insulin_event` (all Dexcom data types) - **NOW SUPPORTED** ✅
8. **❌ Wrong**: `POST /integrations/{device_id}/sync` (400 Error - metadata issue) - **FIXED** ✅
9. **✅ Correct**: `POST /integrations/{device_id}/sync` (after OAuth completion) - **NOW SUPPORTED** ✅
10. **❌ Wrong**: `GET /data/points?data_type=time_in_range` (422 Validation Error) - **FIXED** ✅
11. **✅ Correct**: `GET /data/points?data_type=time_in_range` (TIME_IN_RANGE data type) - **NOW SUPPORTED** ✅

### Recommended Frontend Flow:
1. Show device creation form
2. After device creation, automatically start OAuth flow
3. Present sandbox user selection UI
4. Complete OAuth and show success message
5. Enable data sync and display options
6. Show real-time glucose data with charts/graphs

---

## 🔧 Development Notes

- **Sandbox Users**: User7, User8, User6, User4 (all provide realistic test data)
- **Data Frequency**: Glucose readings every 5 minutes
- **Date Ranges**: Support up to 30 days of historical data
- **Real-time**: Data is simulated but follows realistic patterns
- **Production**: Real Dexcom API integration will replace sandbox when ready
- **Database**: All Dexcom data types have been added to the database enum (GLUCOSE_CALIBRATION, INSULIN_EVENT, CARB_EVENT, GLUCOSE_ALERT, GLUCOSE_TREND, SENSOR_STATUS, TRANSMITTER_STATUS, TIME_IN_RANGE)
- **Metadata**: Fixed device metadata attribute access (device.device_metadata instead of device.metadata) 