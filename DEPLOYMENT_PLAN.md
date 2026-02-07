# PersonalHealthAssistant - Deployment Plan

## Architecture Overview

18 microservices organized in dependency layers, with PostgreSQL, Redis, Neo4j, Qdrant, and Kafka as infrastructure.

---

## Free-Tier Cloud Services Mapping

| Component | Provider | Free Tier Limits | Purpose |
|-----------|----------|-----------------|---------|
| PostgreSQL | **Supabase** | 500 MB, 2 projects | Primary DB + Auth |
| Redis | **Upstash** | 10K commands/day, 256 MB | Caching, sessions, rate limiting |
| Kafka | **Upstash Kafka** | 10K messages/day, 1 cluster | Event streaming |
| Neo4j | **AuraDB Free** | 200K nodes, 400K relationships | Knowledge graph |
| Qdrant | **Qdrant Cloud** | 1 GB, 1 cluster | Vector search |
| App Hosting | **Render** | 750 free hours/month | Services (auto-sleep after 15 min) |
| Container Registry | **GHCR** | Unlimited for public repos | Docker images (already configured) |
| Monitoring | **Grafana Cloud** | 10K metrics, 50 GB logs | Prometheus + Grafana |
| DNS/SSL | **Cloudflare** | Free tier | DNS, SSL, CDN |

---

## Deployment Order (5 Phases)

### Phase 1: Infrastructure + Foundation (Week 1)

**Goal**: Get databases running and deploy the two services everything else depends on.

#### Step 1.1 - Provision Infrastructure

```
1. Supabase (PostgreSQL + Auth)
   - Create project at https://supabase.com
   - Note: DATABASE_URL, SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_ROLE_KEY
   - Run DB migrations from apps/auth/migrations/
   - Run DB migrations from apps/user_profile/migrations/

2. Upstash Redis
   - Create database at https://upstash.com
   - Note: REDIS_URL (TLS endpoint)

3. Upstash Kafka (defer until Phase 2)
   - Create cluster at https://upstash.com
   - Create topics: health-events, device-data, medical-records
```

#### Step 1.2 - Deploy Auth Service (Port 8000)

| Attribute | Value |
|-----------|-------|
| Service | `auth-service` |
| Image | `ghcr.io/ppulimamidy/personalhealthassistant/auth-service:latest` |
| Memory | 512 MB |
| Depends on | PostgreSQL, Redis, Supabase Auth |

**Environment Variables:**
```env
DATABASE_URL=postgresql://...@db.xxx.supabase.co:5432/postgres
REDIS_URL=rediss://...@us1-xxx.upstash.io:6379
JWT_SECRET_KEY=<generate-random-64-char>
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=<supabase-anon-key>
AUTH0_DOMAIN=<optional>
AUTH0_CLIENT_ID=<optional>
AUTH0_CLIENT_SECRET=<optional>
```

**Smoke Test:**
```bash
# Health check
curl https://auth-service.onrender.com/health

# Register user
curl -X POST https://auth-service.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123!", "full_name": "Test User"}'

# Login
curl -X POST https://auth-service.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "TestPass123!"}'
# Save the JWT token for subsequent tests
```

#### Step 1.3 - Deploy User Profile Service (Port 8001)

| Attribute | Value |
|-----------|-------|
| Service | `user-profile-service` |
| Image | `ghcr.io/ppulimamidy/personalhealthassistant/user-profile-service:latest` |
| Memory | 512 MB |
| Depends on | PostgreSQL, Redis, Auth Service |

**Environment Variables:**
```env
DATABASE_URL=postgresql://...@db.xxx.supabase.co:5432/postgres
REDIS_URL=rediss://...@us1-xxx.upstash.io:6379
AUTH_SERVICE_URL=https://auth-service.onrender.com
SECRET_KEY=<generate-random-64-char>
```

**Smoke Test:**
```bash
curl https://user-profile-service.onrender.com/health

curl -X GET https://user-profile-service.onrender.com/api/v1/profile \
  -H "Authorization: Bearer <jwt-token>"
```

---

### Phase 2: Data Collection Layer (Week 2)

**Goal**: Deploy services that collect and store health data.

#### Step 2.1 - Provision Kafka

```
Upstash Kafka:
- Create topics: health-events, device-data-events, medical-record-events
- Note: KAFKA_BOOTSTRAP_SERVERS, KAFKA_SASL_USERNAME, KAFKA_SASL_PASSWORD
```

#### Step 2.2 - Deploy Health Tracking Service (Port 8002)

| Attribute | Value |
|-----------|-------|
| Service | `health-tracking-service` |
| Image | `ghcr.io/ppulimamidy/personalhealthassistant/health-tracking-service:latest` |
| Memory | 512 MB |
| Depends on | PostgreSQL, Redis |

**Environment Variables:**
```env
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
AUTH_SERVICE_URL=https://auth-service.onrender.com
```

**Smoke Test:**
```bash
curl https://health-tracking-service.onrender.com/health

# Create a health metric
curl -X POST https://health-tracking-service.onrender.com/api/v1/metrics \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"metric_type": "weight", "value": 75.5, "unit": "kg"}'

# Get metrics
curl https://health-tracking-service.onrender.com/api/v1/metrics \
  -H "Authorization: Bearer <jwt-token>"
```

#### Step 2.3 - Deploy Device Data Service (Port 8004)

| Attribute | Value |
|-----------|-------|
| Service | `device-data-service` |
| Image | `ghcr.io/ppulimamidy/personalhealthassistant/device-data-service:latest` |
| Memory | 512 MB |
| Depends on | PostgreSQL, Redis, Kafka, Health Tracking |

**Environment Variables:**
```env
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
KAFKA_BOOTSTRAP_SERVERS=xxx.upstash.io:9092
KAFKA_SASL_USERNAME=<upstash-kafka-user>
KAFKA_SASL_PASSWORD=<upstash-kafka-pass>
AUTH_SERVICE_URL=https://auth-service.onrender.com
HEALTH_TRACKING_SERVICE_URL=https://health-tracking-service.onrender.com
DEXCOM_CLIENT_ID=<optional>
DEXCOM_CLIENT_SECRET=<optional>
```

**Smoke Test:**
```bash
curl https://device-data-service.onrender.com/health

# List connected devices
curl https://device-data-service.onrender.com/api/v1/devices \
  -H "Authorization: Bearer <jwt-token>"
```

---

### Phase 3: Medical Data + AI Analysis Layer (Week 3)

**Goal**: Deploy services that handle medical records and AI-powered analysis.

#### Step 3.1 - Deploy Medical Records Service (Port 8005)

| Attribute | Value |
|-----------|-------|
| Service | `medical-records-service` |
| Image | `ghcr.io/ppulimamidy/personalhealthassistant/medical-records-service:latest` |
| Memory | 1 GB (OCR + document processing) |
| Depends on | PostgreSQL, Redis, Kafka, Auth, User Profile, Health Tracking |

**Environment Variables:**
```env
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
KAFKA_BOOTSTRAP_SERVERS=xxx.upstash.io:9092
AUTH_SERVICE_URL=https://auth-service.onrender.com
USER_PROFILE_SERVICE_URL=https://user-profile-service.onrender.com
HEALTH_TRACKING_SERVICE_URL=https://health-tracking-service.onrender.com
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=<supabase-service-role-key>
EPIC_FHIR_CLIENT_ID=<optional>
EPIC_FHIR_CLIENT_SECRET=<optional>
```

**Smoke Test:**
```bash
curl https://medical-records-service.onrender.com/health

# List records
curl https://medical-records-service.onrender.com/api/v1/records \
  -H "Authorization: Bearer <jwt-token>"
```

#### Step 3.2 - Deploy AI Insights Service (Port 8200)

| Attribute | Value |
|-----------|-------|
| Service | `ai-insights-service` |
| Image | `ghcr.io/ppulimamidy/personalhealthassistant/ai-insights-service:latest` |
| Memory | 512 MB |
| Depends on | PostgreSQL, Redis, Auth, User Profile, Health Tracking, Medical Records |

**Environment Variables:**
```env
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
AUTH_SERVICE_URL=https://auth-service.onrender.com
USER_PROFILE_SERVICE_URL=https://user-profile-service.onrender.com
HEALTH_TRACKING_SERVICE_URL=https://health-tracking-service.onrender.com
MEDICAL_RECORDS_SERVICE_URL=https://medical-records-service.onrender.com
OPENAI_API_KEY=<optional>
```

#### Step 3.3 - Deploy Nutrition Service (Port 8007)

| Attribute | Value |
|-----------|-------|
| Service | `nutrition-service` |
| Image | `ghcr.io/ppulimamidy/personalhealthassistant/nutrition-service:latest` |
| Memory | 512 MB |
| Depends on | PostgreSQL, Redis, Auth, User Profile, Health Tracking |

**Environment Variables:**
```env
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
AUTH_SERVICE_URL=https://auth-service.onrender.com
USER_PROFILE_SERVICE_URL=https://user-profile-service.onrender.com
HEALTH_TRACKING_SERVICE_URL=https://health-tracking-service.onrender.com
OPENAI_API_KEY=<optional>
NUTRITIONIX_APP_ID=<optional>
NUTRITIONIX_APP_KEY=<optional>
```

**Smoke Test:**
```bash
curl https://nutrition-service.onrender.com/health

# Log a meal
curl -X POST https://nutrition-service.onrender.com/api/v1/meals \
  -H "Authorization: Bearer <jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Breakfast", "description": "Oatmeal with berries"}'
```

---

### Phase 4: Advanced Services (Week 4)

**Goal**: Deploy knowledge graph, analytics, and collaboration services.

#### Step 4.1 - Provision Neo4j + Qdrant

```
1. AuraDB Free (Neo4j)
   - Create instance at https://neo4j.com/cloud/aura-free/
   - Note: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

2. Qdrant Cloud
   - Create cluster at https://cloud.qdrant.io
   - Note: QDRANT_URL, QDRANT_API_KEY
```

#### Step 4.2 - Deploy Services in Order

| Order | Service | Port | Memory |
|-------|---------|------|--------|
| 1 | Consent Audit Service | 8009 | 512 MB |
| 2 | Knowledge Graph Service | 8010 | 512 MB |
| 3 | Analytics Service | 8210 | 512 MB |
| 4 | Voice Input Service | 8003 | 1 GB |
| 5 | Health Analysis Service | 8008 | 512 MB |
| 6 | Medical Analysis Service | 8006 | 512 MB |

**Knowledge Graph needs:**
```env
NEO4J_URI=neo4j+s://xxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<auradb-password>
QDRANT_URL=https://xxx.us-east4-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=<qdrant-key>
```

---

### Phase 5: Orchestration + Gateway (Week 5)

**Goal**: Deploy the top-layer orchestration, BFF, and gateway.

| Order | Service | Port | Memory |
|-------|---------|------|--------|
| 1 | Doctor Collaboration Service | 8011 | 512 MB |
| 2 | Genomics Service | 8012 | 1 GB |
| 3 | AI Reasoning Orchestrator | 8300 | 512 MB |
| 4 | GraphQL BFF | 8400 | 512 MB |
| 5 | API Gateway | 8080 | 256 MB |

---

## Render Deployment Steps (for each service)

### Option A: Deploy from Docker Image (Recommended)

```bash
# 1. On Render Dashboard -> New -> Web Service
# 2. Select "Deploy an existing image from a registry"
# 3. Image URL: ghcr.io/ppulimamidy/personalhealthassistant/<service-name>:latest
# 4. Set instance type: Free
# 5. Add environment variables
# 6. Deploy
```

### Option B: Deploy from GitHub Repo

```bash
# 1. On Render Dashboard -> New -> Web Service
# 2. Connect your GitHub repo: ppulimamidy/PersonalHealthAssistant
# 3. Root Directory: apps/<service-name>
# 4. Build Command: pip install -r requirements.txt
# 5. Start Command: uvicorn apps.<service>.main:app --host 0.0.0.0 --port $PORT
# 6. Add environment variables
# 7. Deploy
```

---

## End-to-End Test Script

Run after each phase to validate the deployment:

```bash
#!/bin/bash
# test_deployment.sh

BASE_URL="https://your-service.onrender.com"
TOKEN=""

echo "=== Phase 1: Auth + Profile ==="

# 1. Register
echo "Registering user..."
REGISTER=$(curl -s -X POST $BASE_URL/auth/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!","full_name":"Test"}')
echo "$REGISTER"

# 2. Login
echo "Logging in..."
LOGIN=$(curl -s -X POST $BASE_URL/auth/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!"}')
TOKEN=$(echo $LOGIN | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo "Token: ${TOKEN:0:20}..."

# 3. Get profile
echo "Getting profile..."
curl -s $BASE_URL/user-profile/api/v1/profile \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== Phase 2: Health Data ==="

# 4. Add health metric
echo "Adding health metric..."
curl -s -X POST $BASE_URL/health-tracking/api/v1/metrics \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"metric_type":"heart_rate","value":72,"unit":"bpm"}'

# 5. Get metrics
echo "Getting metrics..."
curl -s $BASE_URL/health-tracking/api/v1/metrics \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== Phase 3: Medical + AI ==="

# 6. Get medical records
echo "Getting medical records..."
curl -s $BASE_URL/medical-records/api/v1/records \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 7. Get AI insights
echo "Getting AI insights..."
curl -s $BASE_URL/ai-insights/api/v1/insights \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

# 8. Get nutrition data
echo "Getting nutrition data..."
curl -s $BASE_URL/nutrition/api/v1/meals \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "=== Health Checks ==="
for svc in auth user-profile health-tracking device-data medical-records \
           ai-insights nutrition voice-input knowledge-graph consent-audit \
           analytics health-analysis medical-analysis doctor-collaboration \
           genomics ai-reasoning graphql-bff; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE_URL/$svc/health 2>/dev/null)
  if [ "$STATUS" = "200" ]; then
    echo "  ✅ $svc: UP"
  else
    echo "  ❌ $svc: DOWN ($STATUS)"
  fi
done
```

---

## Cost Summary (All Free Tiers)

| Provider | What | Monthly Cost |
|----------|------|-------------|
| Supabase | PostgreSQL (500 MB) + Auth | $0 |
| Upstash | Redis (256 MB) + Kafka | $0 |
| Neo4j AuraDB | Graph DB (200K nodes) | $0 |
| Qdrant Cloud | Vector DB (1 GB) | $0 |
| Render | Up to 750 instance-hours | $0 |
| GHCR | Container images | $0 |
| Grafana Cloud | Monitoring | $0 |
| **Total** | | **$0/month** |

### Free Tier Limitations to Be Aware Of

| Limitation | Impact | Workaround |
|-----------|--------|------------|
| Render free instances sleep after 15 min | ~30s cold start on first request | Use UptimeRobot free plan to ping /health every 14 min |
| Upstash Redis 10K commands/day | Limits high-traffic caching | Increase local caching, reduce TTL checks |
| Upstash Kafka 10K messages/day | Limits event throughput | Batch events, reduce frequency |
| Supabase 500 MB DB | Storage limit | Implement data retention/cleanup |
| Render 750 hours/month | ~1 always-on service | Deploy max 3-4 services on free tier; use paid ($7/svc) for more |

### Realistic Free-Tier Strategy

Given Render's 750 free hours = ~31 days of one service, you realistically can keep **1 service running 24/7** or **3-4 services running with sleep**. For a demo:

**Always deploy (Phase 1-2):**
- Auth Service
- User Profile Service
- Health Tracking Service
- Device Data Service

**Deploy on-demand (Phase 3-5):**
- Remaining services via Render's free tier (they'll sleep when idle)

**Alternative**: Use **Railway** ($5 free credit/month) or **Fly.io** (3 free VMs) alongside Render to spread the load.

---

## Service Dependency Diagram

```
                    ┌─────────────┐
                    │ API Gateway  │ (8080)
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
        ┌─────┴─────┐          ┌───────┴────────┐
        │ GraphQL    │          │ AI Reasoning   │
        │ BFF (8400) │          │ Orchestrator   │
        └─────┬──────┘          │ (8300)         │
              │                 └───────┬────────┘
              │                         │
    ┌─────────┴─────────────────────────┴──────────┐
    │                                               │
    │  ┌──────────┐  ┌───────────┐  ┌───────────┐  │
    │  │ Knowledge │  │ Doctor    │  │ Genomics  │  │
    │  │ Graph     │  │ Collab    │  │ (8012)    │  │
    │  │ (8010)    │  │ (8011)    │  │           │  │
    │  └────┬─────┘  └─────┬─────┘  └─────┬─────┘  │
    │       │              │               │         │
    │  ┌────┴──────────────┴───────────────┴────┐    │
    │  │         Analytics (8210)                │    │
    │  │         Consent Audit (8009)            │    │
    │  └────────────────┬───────────────────────┘    │
    │                   │                            │
    │  ┌────────────────┴───────────────────────┐    │
    │  │  ┌─────────────┐  ┌─────────────────┐  │   │
    │  │  │ Medical     │  │ Health          │   │   │
    │  │  │ Analysis    │  │ Analysis (8008) │   │   │
    │  │  │ (8006)      │  │                 │   │   │
    │  │  └──────┬──────┘  └────────┬────────┘   │   │
    │  │         │                  │             │   │
    │  │  ┌──────┴──────┐  ┌───────┴──────────┐  │   │
    │  │  │ Nutrition   │  │ AI Insights      │  │   │
    │  │  │ (8007)      │  │ (8200)           │  │   │
    │  │  └──────┬──────┘  └───────┬──────────┘  │   │
    │  └─────────┴─────────────────┴─────────────┘   │
    │                      │                          │
    │  ┌───────────────────┴─────────────────────┐    │
    │  │  ┌──────────┐ ┌────────┐ ┌───────────┐  │   │
    │  │  │ Medical  │ │ Voice  │ │ Device    │   │   │
    │  │  │ Records  │ │ Input  │ │ Data      │   │   │
    │  │  │ (8005)   │ │ (8003) │ │ (8004)    │   │   │
    │  │  └────┬─────┘ └───┬───┘ └─────┬─────┘   │   │
    │  └───────┴───────────┴───────────┴──────────┘   │
    │                      │                          │
    │         ┌────────────┴──────────────┐           │
    │         │  Health Tracking (8002)   │           │
    │         └────────────┬──────────────┘           │
    │                      │                          │
    │         ┌────────────┴──────────────┐           │
    │         │  User Profile (8001)      │           │
    │         └────────────┬──────────────┘           │
    │                      │                          │
    │         ┌────────────┴──────────────┐           │
    │         │  Auth Service (8000)      │           │
    │         └───────────────────────────┘           │
    │                                                 │
    │  ┌─────────────────────────────────────────┐    │
    │  │  PostgreSQL │ Redis │ Kafka │ Neo4j     │    │
    │  │  Qdrant                                 │    │
    │  └─────────────────────────────────────────┘    │
    └─────────────────────────────────────────────────┘
```

---

## Post-Deployment Checklist

- [ ] All health endpoints return 200
- [ ] User registration + login works end-to-end
- [ ] JWT tokens propagate correctly across services
- [ ] Health metrics can be created and retrieved
- [ ] Medical records upload works
- [ ] AI insights generate without errors
- [ ] Kafka events flow between services
- [ ] Neo4j knowledge graph queries work
- [ ] API Gateway routes correctly to all services
- [ ] Monitoring dashboards show service metrics
- [ ] Set up UptimeRobot pings for critical services
