# Oura Ring Integration Guide

This guide explains how to set up and use Oura Ring integration with the Personal Health Assistant device data service.

## 📋 Overview

The Oura Ring integration allows you to:
- Sync sleep, activity, readiness, and heart rate data from your Oura Ring
- Process and store data in a standardized format
- Access data through the device data service API
- Integrate with other health services in the platform

## 🔧 Setup Instructions

### 1. Get Oura Access Token

1. Go to [Oura Cloud Personal Access Tokens](https://cloud.ouraring.com/personal-access-tokens)
2. Sign in to your Oura account
3. Click "Create new token"
4. Give your token a name (e.g., "Personal Health Assistant")
5. Copy the generated token

### 2. Set Environment Variables

Set your Oura access token as an environment variable:

```bash
export OURA_ACCESS_TOKEN="your_token_here"
```

For permanent setup, add it to your `.env` file:

```env
OURA_ACCESS_TOKEN=your_token_here
```

### 3. Test the Integration

Run the test script to verify everything is working:

```bash
cd /path/to/PersonalHealthAssistant
python scripts/test_oura_integration.py
```

## 🚀 Usage

### Using the Device Data Service API

The Oura integration is available through the device data service API endpoints:

#### 1. Connect Oura Device

```bash
curl -X POST "http://localhost:8006/api/v1/device-data/integrations/{device_id}/connect" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_type": "oura_ring",
    "api_key": "your_oura_token",
    "name": "My Oura Ring"
  }'
```

#### 2. Sync Data

```bash
curl -X POST "http://localhost:8006/api/v1/device-data/integrations/{device_id}/sync" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-07"
  }'
```

#### 3. Get Device Info

```bash
curl -X GET "http://localhost:8006/api/v1/device-data/integrations/{device_id}/info" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 4. Test Connection

```bash
curl -X POST "http://localhost:8006/api/v1/device-data/integrations/{device_id}/test" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Using the Oura API Client Directly

You can also use the Oura API client directly in your code:

```python
from apps.device_data.services.oura_client import OuraAPIClient
from datetime import datetime, timedelta

async def fetch_oura_data():
    async with OuraAPIClient("your_token") as client:
        # Get user info
        user_info = await client.get_user_info()
        
        # Get sleep data for last week
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        sleep_data = await client.get_daily_sleep(start_date, end_date)
        activity_data = await client.get_daily_activity(start_date, end_date)
        readiness_data = await client.get_daily_readiness(start_date, end_date)
        
        return {
            "user": user_info,
            "sleep": sleep_data,
            "activity": activity_data,
            "readiness": readiness_data
        }
```

## 📊 Data Types

The Oura integration supports the following data types:

### Sleep Data
- **Sleep Duration**: Total sleep time in hours
- **Sleep Efficiency**: Sleep efficiency percentage
- **Sleep Latency**: Time to fall asleep in minutes
- **Sleep Stages**: REM, Deep, Light, and Awake durations
- **Sleep Score**: Overall sleep quality score
- **Heart Rate**: Lowest and average heart rate during sleep
- **Respiratory Rate**: Breathing rate during sleep
- **Temperature Deviation**: Body temperature changes

### Activity Data
- **Steps**: Daily step count
- **Calories**: Total and active calories burned
- **Activity Score**: Overall activity score
- **Daily Movement**: Movement score
- **MET Minutes**: Metabolic equivalent minutes by intensity level

### Readiness Data
- **Readiness Score**: Overall readiness score
- **Component Scores**: Individual readiness components
- **Resting Heart Rate**: Morning resting heart rate
- **HRV Balance**: Heart rate variability balance

### Heart Rate Data
- **Heart Rate**: Continuous heart rate measurements
- **Heart Rate Variability**: HRV measurements

### Workout Data
- **Workout Duration**: Exercise session duration
- **Workout Calories**: Calories burned during workouts

### Session Data
- **Session Duration**: Session length
- **Session Type**: Type of session (meditation, etc.)

## ⚙️ Configuration

The Oura integration can be configured through environment variables:

```env
# API Configuration
OURA_API_BASE_URL=https://api.ouraring.com/v2
OURA_RATE_LIMIT_PER_MINUTE=60
OURA_REQUEST_TIMEOUT=30
OURA_MAX_RETRIES=3
OURA_RETRY_DELAY=1.0

# Data Sync Configuration
OURA_DEFAULT_SYNC_DAYS=30
OURA_MAX_SYNC_DAYS=365
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Authentication Failed
- **Problem**: "Invalid or expired access token"
- **Solution**: Check that your `OURA_ACCESS_TOKEN` is correct and not expired

#### 2. Rate Limit Exceeded
- **Problem**: "Rate limit exceeded"
- **Solution**: The Oura API has rate limits. Wait a minute and try again

#### 3. No Data Returned
- **Problem**: API calls succeed but return no data
- **Solution**: Check the date range - Oura may not have data for the requested period

#### 4. Connection Errors
- **Problem**: Network connection issues
- **Solution**: Check your internet connection and firewall settings

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Individual Components

Test specific components:

```bash
# Test API client only
python -c "
import asyncio
from apps.device_data.services.oura_client import OuraAPIClient
async def test():
    async with OuraAPIClient('your_token') as client:
        print(await client.get_user_info())
asyncio.run(test())
"
```

## 📈 Best Practices

### 1. Data Sync Frequency
- Sync data daily for optimal results
- Use the bulk sync endpoint for historical data
- Implement incremental sync for new data

### 2. Error Handling
- Always handle API errors gracefully
- Implement retry logic for transient failures
- Log errors for debugging

### 3. Rate Limiting
- Respect Oura's rate limits
- Implement exponential backoff for retries
- Batch requests when possible

### 4. Data Storage
- Store raw API responses for debugging
- Process data into standardized format
- Implement data validation

## 🔗 API Reference

### OuraAPIClient Methods

- `get_user_info()` - Get user information
- `get_daily_sleep(start_date, end_date)` - Get daily sleep data
- `get_daily_activity(start_date, end_date)` - Get daily activity data
- `get_daily_readiness(start_date, end_date)` - Get daily readiness data
- `get_heart_rate(start_date, end_date)` - Get heart rate data
- `get_workout(start_date, end_date)` - Get workout data
- `get_session(start_date, end_date)` - Get session data
- `get_all_data(start_date, end_date)` - Get all data types at once
- `test_connection()` - Test API connection

### Device Integration Methods

- `authenticate()` - Authenticate with Oura API
- `sync_data(start_date, end_date)` - Sync all data types
- `get_device_info()` - Get device information
- `test_connection()` - Test device connection

## 📚 Additional Resources

- [Oura API Documentation](https://cloud.ouraring.com/docs)
- [Oura Personal Access Tokens](https://cloud.ouraring.com/personal-access-tokens)
- [Device Data Service API](http://localhost:8006/docs)
- [Personal Health Assistant Documentation](../README.md)

## 🤝 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs for error messages
3. Test with the provided test script
4. Check the Oura API status
5. Contact the development team

---

**Note**: This integration requires a valid Oura Ring account and personal access token. The Oura Ring must be actively worn and syncing data to the Oura cloud for data to be available through the API. 