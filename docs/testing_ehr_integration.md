# Testing EHR Integration: FHIR & HL7

This guide explains how to test the EHR integration endpoints of the Medical Records microservice using both real and simulated FHIR and HL7 data.

---

## 1. Prerequisites
- The Medical Records service is running and accessible (e.g., http://localhost:8005)
- You have a valid JWT token with appropriate permissions (admin/ehr_management/data_sync)
- The EHR integration endpoints are available at `/api/v1/medical-records/ehr-integration/...`

---

## 2. Register an EHR Integration (FHIR)

**Example:** Register a simulated Epic FHIR server

```bash
curl -X POST http://localhost:8005/api/v1/medical-records/ehr-integration/integrations \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "system_name": "epic-sim",
    "system_type": "epic",
    "fhir_base_url": "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/",
    "fhir_client_id": "your-client-id",
    "fhir_client_secret": "your-client-secret",
    "fhir_scope": "launch/patient patient/*.read patient/*.write",
    "sync_schedule": "DAILY"
  }'
```

---

## 3. Sync Patient Data from FHIR

**Example:** Sync all FHIR data for a patient

```bash
curl -X POST http://localhost:8005/api/v1/medical-records/ehr-integration/integrations/epic-sim/sync \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "12345"
  }'
```

- You can specify `last_sync` (ISO8601) to only pull new/updated data.

---

## 4. Ingest HL7v2 Message (Simulated or Real)

**Example HL7 ORU^R01 message:**
```
MSH|^~\&|LAB|HOSP|EHR|HOSP|202406101200||ORU^R01|123456|P|2.3
PID|1||12345^^^HOSP||Doe^John||19800101|M
OBR|1||54321|88304^CBC^L
OBX|1|NM|718-7^Hemoglobin^LN||13.5|g/dL|12.0-16.0|N|||F
```

**Ingest via API:**
```bash
curl -X POST http://localhost:8005/api/v1/medical-records/ehr-integration/integrations/epic-sim/hl7 \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "raw_message": "MSH|^~\\&|LAB|HOSP|EHR|HOSP|202406101200||ORU^R01|123456|P|2.3\rPID|1||12345^^^HOSP||Doe^John||19800101|M\rOBR|1||54321|88304^CBC^L\rOBX|1|NM|718-7^Hemoglobin^LN||13.5|g/dL|12.0-16.0|N|||F\r",
    "system_name": "epic-sim"
  }'
```

---

## 5. List and Monitor Integrations

```bash
curl -X GET http://localhost:8005/api/v1/medical-records/ehr-integration/integrations \
  -H "Authorization: Bearer <YOUR_JWT_TOKEN>"
```

---

## 6. Tips for Simulated Data
- Use [https://github.com/synthetichealth/synthea](https://github.com/synthetichealth/synthea) to generate FHIR patient data.
- Use online HL7 message generators or copy real messages (de-identified) for HL7 testing.
- You can use [https://fhir.epic.com/](https://fhir.epic.com/) for public FHIR sandbox endpoints.

---

## 7. Troubleshooting
- Ensure your JWT token is valid and not expired.
- Check logs for detailed error messages.
- For HL7, ensure your message uses `\r` as segment separator and is properly escaped in JSON.

---

## 8. References
- [HL7 v2 Standard](https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185)
- [HL7 FHIR R4](https://www.hl7.org/fhir/)
- [Epic FHIR API](https://fhir.epic.com/)
- [Synthea FHIR Generator](https://github.com/synthetichealth/synthea) 