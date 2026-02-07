# Personal Health Assistant

[![CI](https://github.com/ppulimamidy/PersonalHealthAssistant/actions/workflows/ci.yml/badge.svg)](https://github.com/ppulimamidy/PersonalHealthAssistant/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, AI-powered personal health management platform built with microservices architecture. Track vitals, analyze health data, integrate with wearables, and receive personalized AI-driven health insights.

## Features

- **Health Tracking**: Monitor vitals, symptoms, medications, and health goals
- **Wearable Integration**: Oura Ring, Dexcom CGM, Apple Watch/HealthKit
- **AI-Powered Insights**: LLM-based health analysis and recommendations (GPT-4, Claude)
- **Medical Records**: Lab results, imaging, EPIC FHIR integration
- **Voice Input**: Speech-to-text for hands-free symptom logging
- **Knowledge Graph**: Medical relationships and drug interactions (Neo4j)
- **HIPAA Compliant**: Audit logging, consent management, encryption

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Git

### Option 1: One-Command Setup (Recommended)

```bash
git clone https://github.com/ppulimamidy/PersonalHealthAssistant.git
cd PersonalHealthAssistant
./setup.sh
```

### Option 2: Docker Compose

```bash
# Clone the repository
git clone https://github.com/ppulimamidy/PersonalHealthAssistant.git
cd PersonalHealthAssistant

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys and credentials

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f auth-service
```

### Option 3: Run Individual Service

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run a service
cd apps/auth
uvicorn main:app --reload --port 8000
```

---

## Access Services

| Service | URL | Description |
|---------|-----|-------------|
| API Gateway | http://localhost:80 | Traefik reverse proxy |
| Auth Service | http://localhost:8000/docs | Authentication API |
| User Profile | http://localhost:8001/docs | Profile management |
| Health Tracking | http://localhost:8002/docs | Vitals & symptoms |
| GraphQL BFF | http://localhost:8400/graphql | Unified GraphQL API |
| Grafana | http://localhost:3002 | Monitoring dashboards |
| Supabase Studio | http://localhost:3001 | Database management |
| Prometheus | http://localhost:9090 | Metrics |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     API Gateway (Traefik)                        │
│                    Ports: 80 (HTTP) / 443 (HTTPS)                │
└─────────────────────────────────────────────────────────────────┘
                                  │
    ┌─────────────────────────────┼─────────────────────────────┐
    │                             │                             │
    ▼                             ▼                             ▼
┌────────────┐            ┌────────────┐            ┌────────────┐
│   Auth     │            │   User     │            │   Health   │
│  Service   │            │  Profile   │            │  Tracking  │
│   :8000    │            │   :8001    │            │   :8002    │
└────────────┘            └────────────┘            └────────────┘
    │                             │                             │
    ├─────────────────────────────┼─────────────────────────────┤
    │                             │                             │
    ▼                             ▼                             ▼
┌────────────┐            ┌────────────┐            ┌────────────┐
│  Device    │            │  Medical   │            │    AI      │
│   Data     │            │  Records   │            │  Insights  │
│   :8004    │            │   :8005    │            │   :8200    │
└────────────┘            └────────────┘            └────────────┘
    │                             │                             │
    └─────────────────────────────┼─────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Infrastructure Layer                         │
├─────────┬─────────┬─────────┬─────────┬─────────┬───────────────┤
│PostgreSQL│  Redis  │  Kafka  │  Neo4j  │ Qdrant  │  Prometheus   │
│  :5432   │  :6379  │  :9092  │  :7687  │  :6333  │    :9090      │
└─────────┴─────────┴─────────┴─────────┴─────────┴───────────────┘
```

---

## Microservices

### Core Services (MVP)
| Service | Port | Description |
|---------|------|-------------|
| Auth | 8000 | JWT/OAuth authentication, MFA, RBAC |
| User Profile | 8001 | Profile, preferences, health attributes |
| Health Tracking | 8002 | Vitals, symptoms, goals with AI agents |

### Data Services
| Service | Port | Description |
|---------|------|-------------|
| Voice Input | 8003 | Speech-to-text, OCR processing |
| Device Data | 8004 | Wearable integrations (Oura, Dexcom, Apple Watch) |
| Medical Records | 8005 | Labs, imaging, EPIC FHIR |
| Nutrition | 8007 | Food logging, dietary analysis |

### AI/ML Services
| Service | Port | Description |
|---------|------|-------------|
| Medical Analysis | 8006 | AI-powered medical analysis |
| Health Analysis | 8008 | Health scoring, recommendations |
| AI Insights | 8200 | AI recommendations, risk assessment |
| Analytics | 8210 | Cross-service analytics |
| AI Orchestrator | 8300 | Multi-agent coordination |

### Specialized Services
| Service | Port | Description |
|---------|------|-------------|
| Consent Audit | 8009 | HIPAA compliance, audit logs |
| Knowledge Graph | 8010 | Medical relationships (Neo4j) |
| Doctor Collaboration | 8011 | Provider communication |
| Genomics | 8012 | Genetic data analysis |
| GraphQL BFF | 8400 | Unified API layer |

---

## Deployment

### Kubernetes (Helm)

```bash
# Add Helm repos
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Create namespace and secrets
kubectl create namespace health-assistant
kubectl create secret generic health-assistant-secrets \
  --namespace health-assistant \
  --from-literal=DATABASE_URL="your-db-url" \
  --from-literal=JWT_SECRET_KEY="your-jwt-secret" \
  --from-literal=OPENAI_API_KEY="your-openai-key"

# Install with Helm
helm install health-assistant ./helm/personal-health-assistant \
  --namespace health-assistant
```

See [helm/README.md](helm/README.md) for detailed Kubernetes deployment instructions.

---

## Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Key variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/health_db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Authentication
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Integrations
OURA_CLIENT_ID=your-oura-client-id
DEXCOM_CLIENT_ID=your-dexcom-client-id
EPIC_CLIENT_ID=your-epic-client-id
```

---

## Development

### Project Structure

```
PersonalHealthAssistant/
├── apps/                    # Microservices
│   ├── auth/               # Authentication service
│   ├── user_profile/       # User profile service
│   ├── health_tracking/    # Health tracking with AI agents
│   ├── ai_insights/        # AI insights service
│   ├── medical_records/    # Medical records + FHIR
│   └── ...                 # 16 total services
├── common/                  # Shared libraries
│   ├── config/             # Settings, feature flags
│   ├── middleware/         # Auth, rate limiting, security
│   ├── models/             # Base SQLAlchemy models
│   └── utils/              # Logging, resilience patterns
├── helm/                    # Kubernetes Helm charts
├── monitoring/              # Prometheus & Grafana configs
├── traefik/                # API Gateway configuration
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml      # Local development
└── requirements.txt        # Python dependencies
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run specific service tests
pytest apps/auth/tests/ -v

# With coverage
pytest --cov=apps --cov-report=html
```

### Code Quality

```bash
# Format code
black apps/ common/

# Lint
flake8 apps/ common/ --max-line-length=120

# Type checking
mypy apps/ common/ --ignore-missing-imports
```

---

## CI/CD

The project includes GitHub Actions workflows for:

- **Lint & Test**: Black, Flake8, MyPy, Pytest
- **Security Scan**: Bandit, Safety, Trivy
- **Docker Build**: Build and push to GitHub Container Registry
- **Service-specific pipelines**: Each service has its own CI workflow

---

## Documentation

- [Junior Developer Setup](JUNIOR_DEV_SETUP.md) - New developer onboarding
- [Core Infrastructure](docs/CORE_INFRASTRUCTURE.md) - Architecture details
- [API Documentation](docs/BACKEND_API_SPECIFICATION.md) - API specs
- [EPIC FHIR Integration](EPIC_FHIR_INTEGRATION_GUIDE.md) - EHR integration
- [Helm Charts](helm/README.md) - Kubernetes deployment

---

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   lsof -i :8000  # Find process using port
   kill -9 <PID>  # Kill it
   ```

2. **Docker Issues**
   ```bash
   docker-compose down -v
   docker system prune -a
   docker-compose up -d --build
   ```

3. **Database Connection**
   ```bash
   docker-compose logs supabase-db
   python scripts/fix_supabase_connection.py
   ```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests (`pytest`)
4. Commit changes (`git commit -m 'Add amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- [Issues](https://github.com/ppulimamidy/PersonalHealthAssistant/issues)
- [Documentation](docs/)

---

**Ready to start?** Run `./setup.sh` or `docker-compose up -d` and begin developing!
