# Epic FHIR Quick Reference Card

## 🚀 Quick Start

**Base URL:** `http://localhost:8005/api/v1/medical-records/epic-fhir`

**Authentication:** All requests need `Authorization: Bearer YOUR_JWT_TOKEN`

## 📋 Essential Endpoints

### 1. Start OAuth2 Flow
```javascript
GET /authorize
// Returns authorization_url to redirect user to Epic
```

### 2. Get Test Patients
```javascript
GET /test-patients
// Returns list of available test patients (anna, henry, john, omar, kyle)
```

### 3. Get Patient Vital Signs
```javascript
GET /test-patients/{patient_name}/observations-with-auth?category=vital-signs
// Returns patient observations (blood pressure, heart rate, etc.)
```

### 4. Get Patient Lab Results
```javascript
GET /test-patients/{patient_name}/observations-with-auth?category=laboratory
// Returns lab test results
```

### 5. Get Patient Reports
```javascript
GET /test-patients/{patient_name}/diagnostic-reports
// Returns diagnostic reports
```

## 🔧 Quick Implementation

```javascript
// 1. Initialize service
const epicService = new EpicFHIRService();
epicService.setToken('your-jwt-token');

// 2. Get patients
const patients = await epicService.getPatients();

// 3. Get patient vital signs
const vitals = await epicService.getPatientObservations('anna', {
  category: 'vital-signs',
  dateFrom: '2025-07-01',
  dateTo: '2025-07-28'
});
```

## 📊 Data Categories

- `vital-signs` - Blood pressure, heart rate, temperature
- `laboratory` - Lab test results
- `survey` - Patient assessments
- `imaging` - Imaging results

## 🧪 Test Patients

- `anna` - Female test patient
- `henry` - Male test patient  
- `john` - Male test patient
- `omar` - Male test patient
- `kyle` - Male test patient

## ⚠️ Important Notes

1. **OAuth2 Required** - Must complete authorization flow first
2. **Date Format** - Use ISO format (YYYY-MM-DD)
3. **Error Handling** - Always implement proper error handling
4. **Security** - Never expose JWT tokens in client code

## 📞 Support

For detailed API documentation, see: `EPIC_FHIR_FRONTEND_API_SPECIFICATION.md` 