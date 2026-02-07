# Consent Audit Service

Comprehensive consent audit and compliance service providing GDPR and HIPAA compliance monitoring, consent management, audit logging, data processing audits, and compliance reporting for the Personal Health Assistant platform.

## Port
- **Port**: 8009

## API Endpoints

### Infrastructure

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Service health check (includes sub-service status) |
| GET | `/ready` | No | Readiness probe |
| GET | `/metrics` | No | Prometheus metrics |

### Audit (`/api/v1/audit`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/audit/logs` | Yes | Create an audit log entry |
| GET | `/api/v1/audit/logs` | Yes | List audit logs (with filters) |
| GET | `/api/v1/audit/logs/{log_id}` | Yes | Get a specific audit log |
| GET | `/api/v1/audit/violations` | Yes | Get compliance violations |
| GET | `/api/v1/audit/high-risk` | Yes | Get high-risk audit events |
| GET | `/api/v1/audit/summary` | Yes | Get audit summary statistics |
| POST | `/api/v1/audit/data-processing` | Yes | Create a data processing audit |
| GET | `/api/v1/audit/data-processing` | Yes | List data processing audits |

### Consent (`/api/v1/consent`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/consent/records` | Yes | Create a consent record |
| GET | `/api/v1/consent/status` | Yes | Get consent status for a user |
| GET | `/api/v1/consent/records/{record_id}` | Yes | Get a specific consent record |
| POST | `/api/v1/consent/revoke` | Yes | Revoke a consent record |

### GDPR (`/api/v1/gdpr`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/gdpr/compliance` | Yes | Get GDPR compliance status |
| POST | `/api/v1/gdpr/rights/exercise` | Yes | Exercise a data subject right (access, erasure, portability, etc.) |
| GET | `/api/v1/gdpr/audit-trail` | Yes | Get GDPR-specific audit trail |
| GET | `/api/v1/gdpr/summary` | Yes | Get GDPR compliance summary |

### HIPAA (`/api/v1/hipaa`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/hipaa/compliance` | Yes | Get HIPAA compliance status |
| GET | `/api/v1/hipaa/privacy-rule` | Yes | Privacy Rule compliance check |
| GET | `/api/v1/hipaa/security-rule` | Yes | Security Rule compliance check |
| GET | `/api/v1/hipaa/breach-notifications` | Yes | List breach notifications |
| GET | `/api/v1/hipaa/audit-trail` | Yes | Get HIPAA-specific audit trail |

### Compliance (`/api/v1/compliance`)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/compliance/status` | Yes | Overall compliance status |
| POST | `/api/v1/compliance/reports` | Yes | Create a compliance report |
| GET | `/api/v1/compliance/reports` | Yes | List compliance reports |
| GET | `/api/v1/compliance/summary` | Yes | Get compliance summary |

## Database
- **Schema**: `consent_audit`
- **Tables**:
  - `consent_audit_logs` — audit event log entries
  - `data_processing_audits` — records of data processing activities
  - `compliance_reports` — generated compliance reports
  - `consent_records` — user consent records and status

## Dependencies
- **PostgreSQL** — primary data store for audit logs, consent records, and compliance reports
- **No inter-service dependencies** — this service is called by other services, not the other way around

## Configuration
Key environment variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `ENVIRONMENT` | Environment name (`development`, `production`) |
| `CORS_ORIGINS` | Allowed CORS origins |
| `LOG_LEVEL` | Logging level (default: `info`) |

## Running Locally
```bash
cd apps/consent_audit
uvicorn main:app --host 0.0.0.0 --port 8009 --reload
```

## Docker
```bash
docker build -t consent-audit-service -f apps/consent_audit/Dockerfile .
docker run -p 8009:8009 consent-audit-service
```
