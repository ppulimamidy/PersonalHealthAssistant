# Apple Watch Data Integration Guide

This guide explains how to ingest real Apple Watch data into your VitaSense PPA platform.

## 🍎 Overview

Apple Watch collects comprehensive health data including:
- **Activity**: Steps, calories, exercise minutes, stand hours
- **Heart Health**: Heart rate, ECG, blood oxygen, irregular rhythm notifications
- **Sleep**: Sleep stages, sleep duration, respiratory rate
- **Fitness**: Workouts, distance, pace, elevation
- **Health**: Weight, blood pressure, blood glucose (with compatible devices)

## 📱 Methods to Get Apple Watch Data

### 1. Apple Health Export (Recommended for Testing)

**Steps:**
1. Open the **Health** app on your iPhone
2. Tap your profile picture in the top right
3. Scroll down and tap **Export All Health Data**
4. Choose **Export** and wait for the file to be generated
5. The file will be saved as a ZIP containing XML data

**What you get:**
- Complete health data in XML format
- Includes all Apple Watch metrics
- Historical data up to when you started using Health app
- Data is anonymized and privacy-compliant

**Integration:**
```python
from apps.device_data.services.apple_health_real import AppleHealthExportService

# Process export file
export_service = AppleHealthExportService()
data_points = await export_service.process_export_file(
    file_path="path/to/export.zip",
    user_id="your-user-id",
    device_id="your-device-id"
)
```

### 2. Third-Party Health Services

Several services can access Apple Health data:

#### A. HealthKit API (Requires iOS App)
- **Requirement**: iOS app with HealthKit entitlements
- **Process**: User grants permission → App reads HealthKit data → Sends to your API
- **Pros**: Real-time, comprehensive data
- **Cons**: Requires iOS app development

#### B. Apple Health Records API
- **Requirement**: Healthcare provider integration
- **Process**: Access health records through FHIR API
- **Pros**: Clinical-grade data
- **Cons**: Limited to health records, not all Apple Watch data

#### C. Third-Party Aggregators
- **Services**: Validic, Human API, Apple HealthKit
- **Process**: Connect to their API → Get aggregated health data
- **Pros**: Easy integration, multiple data sources
- **Cons**: Additional cost, data dependency

### 3. Direct HealthKit Integration (Advanced)

For real-time data, create an iOS app:

```swift
import HealthKit

class HealthKitManager {
    let healthStore = HKHealthStore()
    
    func requestAuthorization() {
        let typesToRead: Set<HKObjectType> = [
            HKObjectType.quantityType(forIdentifier: .stepCount)!,
            HKObjectType.quantityType(forIdentifier: .heartRate)!,
            HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)!,
            HKObjectType.categoryType(forIdentifier: .sleepAnalysis)!
        ]
        
        healthStore.requestAuthorization(toShare: nil, read: typesToRead) { success, error in
            if success {
                self.startObservingData()
            }
        }
    }
    
    func startObservingData() {
        // Observe real-time data changes
        let heartRateType = HKQuantityType.quantityType(forIdentifier: .heartRate)!
        let query = HKObserverQuery(sampleType: heartRateType, predicate: nil) { query, completion, error in
            // Send data to your API
            self.sendDataToAPI()
            completion()
        }
        healthStore.execute(query)
    }
}
```

## 🚀 Quick Start Guide

### Step 1: Export Your Apple Health Data

1. **On your iPhone:**
   - Open Health app
   - Tap profile → Export All Health Data
   - Wait for export to complete
   - Share the ZIP file to your computer

2. **Test the integration:**
   ```bash
   python test_apple_watch_integration.py
   ```

### Step 2: Upload to Your Platform

**Using the API:**
```bash
curl -X POST "http://localhost:8001/apple-health/upload-export" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/health_export.zip"
```

**Using Python:**
```python
import aiohttp
import asyncio

async def upload_health_export(file_path: str):
    async with aiohttp.ClientSession() as session:
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename='health_export.zip')
            
            async with session.post(
                'http://localhost:8001/apple-health/upload-export',
                data=data,
                headers={'Authorization': 'Bearer YOUR_TOKEN'}
            ) as response:
                result = await response.json()
                print(f"Upload result: {result}")

# Run the upload
asyncio.run(upload_health_export('path/to/health_export.zip'))
```

### Step 3: View Your Data

**Get device summary:**
```bash
curl "http://localhost:8001/apple-health/devices/YOUR_DEVICE_ID/summary" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Get specific data:**
```bash
curl "http://localhost:8001/apple-health/devices/YOUR_DEVICE_ID/data?data_type=steps&start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📊 Supported Data Types

| Data Type | Apple Health Identifier | Unit | Description |
|-----------|------------------------|------|-------------|
| Steps | `HKQuantityTypeIdentifierStepCount` | steps | Daily step count |
| Heart Rate | `HKQuantityTypeIdentifierHeartRate` | bpm | Heart rate readings |
| Sleep | `HKCategoryTypeIdentifierSleepAnalysis` | hours | Sleep duration |
| Weight | `HKQuantityTypeIdentifierBodyMass` | kg | Body weight |
| Calories | `HKQuantityTypeIdentifierActiveEnergyBurned` | calories | Active calories burned |
| Distance | `HKQuantityTypeIdentifierDistanceWalkingRunning` | m | Walking/running distance |
| Flights | `HKQuantityTypeIdentifierFlightsClimbed` | flights | Flights of stairs climbed |
| Exercise Time | `HKQuantityTypeIdentifierAppleExerciseTime` | minutes | Exercise minutes |
| Stand Time | `HKQuantityTypeIdentifierAppleStandTime` | minutes | Stand hours |
| Blood Pressure | `HKQuantityTypeIdentifierBloodPressureSystolic/Diastolic` | mmHg | Blood pressure readings |
| Blood Oxygen | `HKQuantityTypeIdentifierOxygenSaturation` | % | Blood oxygen saturation |
| Respiratory Rate | `HKQuantityTypeIdentifierRespiratoryRate` | breaths/min | Breathing rate |
| Mindful Minutes | `HKQuantityTypeIdentifierMindfulSession` | minutes | Mindfulness sessions |

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Apple Health Integration
APPLE_HEALTH_ENABLED=true
APPLE_HEALTH_CLIENT_ID=your_client_id
APPLE_HEALTH_CLIENT_SECRET=your_client_secret
APPLE_HEALTH_REDIRECT_URI=http://localhost:8001/auth/apple-health/callback

# Third-party service (if using)
HEALTHKIT_API_KEY=your_api_key
HEALTHKIT_API_URL=https://api.healthkit.com/v1
```

### Database Schema

The platform automatically creates the necessary tables:

```sql
-- Device data tables
CREATE TABLE device_data.devices (...);
CREATE TABLE device_data.device_data_points (...);
CREATE TABLE device_data.device_data_types (...);

-- Health tracking tables
CREATE TABLE health_tracking.vital_signs (...);
CREATE TABLE health_tracking.symptoms (...);
CREATE TABLE health_tracking.devices (...);
```

## 🧪 Testing

### Run Integration Tests

```bash
# Test Apple Watch integration
python test_apple_watch_integration.py

# Test with real export file
python -c "
import asyncio
from apps.device_data.services.apple_health_real import AppleHealthExportService

async def test():
    service = AppleHealthExportService()
    data = await service.process_export_file('path/to/export.zip', 'user-id', 'device-id')
    print(f'Processed {len(data)} data points')

asyncio.run(test())
"
```

### Test API Endpoints

```bash
# Start the device data service
cd apps/device_data
python main.py

# Test endpoints
curl http://localhost:8001/apple-health/devices
curl http://localhost:8001/integrations/supported
```

## 🔒 Privacy & Security

### Data Privacy
- Apple Health exports are anonymized
- No personal identifiers in the data
- Data is encrypted in transit and at rest
- User consent required for data access

### Security Best Practices
- Use HTTPS for all API communications
- Implement proper authentication and authorization
- Store sensitive data encrypted
- Regular security audits
- Compliance with HIPAA/GDPR if applicable

## 🚨 Troubleshooting

### Common Issues

**1. Export file not found**
```
Error: Invalid Apple Health export file format
```
**Solution**: Ensure you're using the correct export format (ZIP, XML, or JSON)

**2. Authentication failed**
```
Error: Apple Health authentication failed
```
**Solution**: Check your API credentials and network connectivity

**3. No data points found**
```
Warning: No data points to save
```
**Solution**: Verify the date range and data types in your export

**4. Database connection issues**
```
Error: Database connection failed
```
**Solution**: Check your database configuration and ensure tables are created

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Next Steps

### For Production Use

1. **Set up proper authentication**
   - Implement OAuth 2.0 for Apple Health
   - Use secure token storage
   - Add rate limiting

2. **Scale the infrastructure**
   - Use message queues for data processing
   - Implement data caching
   - Add monitoring and alerting

3. **Add real-time features**
   - WebSocket connections for live data
   - Push notifications for health alerts
   - Real-time analytics dashboard

4. **Enhance data processing**
   - Machine learning for health insights
   - Anomaly detection
   - Predictive analytics

### For iOS App Development

1. **Create iOS app with HealthKit**
   - Request HealthKit permissions
   - Implement data reading/writing
   - Handle background updates

2. **Set up secure communication**
   - Use certificate pinning
   - Implement proper error handling
   - Add offline data caching

3. **User experience**
   - Clear privacy explanations
   - Easy permission management
   - Data visualization

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review the API documentation
- Test with the provided examples
- Contact the development team

---

**Note**: This integration requires proper Apple Health permissions and user consent. Always follow Apple's guidelines and privacy requirements when accessing health data. 