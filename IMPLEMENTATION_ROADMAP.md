# Personal Health Assistant - Detailed Implementation Roadmap

## Overview
This document provides a comprehensive, step-by-step implementation guide for the Personal Health Assistant project. Each phase is designed to be completed in 1-2 weeks with clear deliverables and success criteria.

## Phase 1: Foundation Setup (Week 1-2)

### Day 1-2: Environment Setup
**Objective**: Set up complete development environment

**Steps**:
1. **Run the enhanced setup script** (Recommended):
   ```bash
   # One-command setup with virtual environment management
   chmod +x setup.sh
   ./setup.sh
   ```
   
   **What this does automatically**:
   - ✅ Checks prerequisites (Docker, Python, Git)
   - ✅ Creates/activates Python virtual environment
   - ✅ Upgrades pip in virtual environment
   - ✅ Installs all Python dependencies
   - ✅ Starts all Docker services
   - ✅ Sets up database schema
   - ✅ Runs comprehensive validation
   - ✅ Provides setup status and next steps

2. **Alternative setup methods**:
   ```bash
   # Option A: Python master setup script
   python scripts/setup_master.py
   
   # Option B: Dedicated virtual environment setup
   python scripts/setup_venv.py
   
   # Option C: Manual setup
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Validate virtual environment**:
   ```bash
   # Check virtual environment status
   python scripts/setup_venv.py validate
   
   # Comprehensive environment validation
   python scripts/validate_requirements.py
   ```

4. **Update .env file** with your API keys:
   ```bash
   # Edit .env file and add your actual API keys
   nano .env
   ```

5. **Start all services** (if not already started):
   ```bash
   docker-compose up -d
   ```

6. **Initialize database** (if not already done):
   ```bash
   python scripts/setup/db_setup.py
   ```

7. **Run comprehensive tests**:
   ```bash
   python scripts/test_setup.py
   ```

**Deliverables**:
- ✅ Working development environment with virtual environment
- ✅ All services running (PostgreSQL, Qdrant, Kafka, DuckDB)
- ✅ Database schema initialized with sample data
- ✅ All tests passing
- ✅ Virtual environment properly configured and active

**Virtual Environment Status Check**:
```bash
# Verify virtual environment is active (should show (venv) in prompt)
echo $VIRTUAL_ENV

# Check Python location (should point to venv)
which python

# Validate all requirements
python scripts/validate_requirements.py
```

**Troubleshooting Virtual Environment**:
```bash
# If virtual environment is not active
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\activate  # Windows

# If virtual environment doesn't exist
python scripts/setup_venv.py create

# If dependencies are missing
python scripts/install_missing_dependencies.py

# If setup fails, start fresh
rm -rf venv/
python scripts/setup_venv.py
```

### Day 3-4: Core Infrastructure & Non-Functional Requirements
**Objective**: Set up core infrastructure components and foundational non-functional requirements

**Steps**:
1. **Create database connection pool**:
   ```bash
   # Create common/database/connection.py
   ```
2. **Set up logging infrastructure**:
   ```bash
   # Create common/utils/logging.py
   ```
3. **Create base service classes**:
   ```bash
   # Create common/services/base.py
   ```
4. **Set up middleware**:
   ```bash
   # Create common/middleware/auth.py
   # Create common/middleware/error_handling.py
   ```
5. **Implement distributed tracing and metrics (OpenTelemetry, Prometheus)**:
   ```bash
   # Create common/utils/opentelemetry_config.py
   # Integrate tracing and metrics in FastAPI app
   ```
6. **Implement resilience patterns (circuit breaking, retries, timeouts)**:
   ```bash
   # Create common/utils/resilience.py
   ```
7. **Implement rate limiting middleware**:
   ```bash
   # Create common/middleware/rate_limiter.py
   ```
8. **Implement feature flags system**:
   ```bash
   # Create common/config/feature_flags.py
   ```
9. **Implement enhanced security middleware (mTLS, security headers, threat detection)**:
   ```bash
   # Create common/middleware/security.py
   ```
10. **Update settings to support all non-functional requirements**:
    ```bash
    # Update common/config/settings.py
    ```
11. **Write comprehensive tests for all non-functional requirements**:
    ```bash
    # Create tests/test_non_functional_requirements.py
    ```
12. **Document all non-functional requirements**:
    ```bash
    # Create docs/NON_FUNCTIONAL_REQUIREMENTS.md
    ```
13. **Set up monitoring stack (Prometheus + Grafana)**:
    ```bash
    # Add Prometheus and Grafana services to docker-compose.yml
    # Create monitoring/prometheus/prometheus.yml
    # Create monitoring/grafana/provisioning/datasources/prometheus.yml
    # Create monitoring/grafana/provisioning/dashboards/dashboard.yml
    # Create monitoring/grafana/provisioning/dashboards/fastapi-dashboard.json
    ```
14. **Add Redis service for rate limiting and feature flags**:
    ```bash
    # Add Redis service to docker-compose.yml
    ```
15. **Fix test isolation and Prometheus registry conflicts**:
    ```bash
    # Refactor ResilienceMetrics to accept registry parameter
    # Update test fixtures for isolated testing
    # Fix OpenTelemetry configuration issues
    ```

**Deliverables**:
- ✅ Database connection management
- ✅ Structured logging system
- ✅ Base service architecture
- ✅ Authentication middleware
- ✅ Distributed tracing and metrics (OpenTelemetry, Prometheus)
- ✅ Circuit breaking, retries, and timeouts (with isolated test metrics)
- ✅ Rate limiting middleware (with Redis backend)
- ✅ Feature flags system (with Redis backend)
- ✅ Enhanced security middleware (mTLS, headers, threat detection)
- ✅ Settings updated for all NFRs
- ✅ Comprehensive NFR tests (with isolated Prometheus registries)
- ✅ NFR documentation
- ✅ Monitoring stack (Prometheus + Grafana with auto-provisioned dashboards)
- ✅ Redis service for caching and state management
- ✅ Test isolation and registry conflict resolution

**Validation Steps**:
```bash
# 1. Start the full monitoring stack
docker-compose up -d

# 2. Check all services are running
docker-compose ps

# 3. Validate metrics endpoints
curl http://localhost:8000/metrics  # FastAPI metrics
curl http://localhost:9090/api/v1/targets  # Prometheus targets
curl http://localhost:3002  # Grafana UI (admin/admin)

# 4. Run comprehensive NFR tests
pytest tests/test_non_functional_requirements.py -v

# 5. Check environment validation
python scripts/validate_requirements.py
python scripts/setup_venv.py validate

# 6. Verify monitoring dashboard
# Visit http://localhost:3002 and check "Health Assistant - FastAPI Metrics" dashboard
```

**Monitoring Stack Access**:
- **Prometheus UI**: http://localhost:9090
- **Grafana UI**: http://localhost:3002 (admin/admin)
- **FastAPI Metrics**: http://localhost:8000/metrics
- **Redis**: localhost:6379

**Key Features Implemented**:
- **Resilience Patterns**: Circuit breakers, retries, timeouts with Prometheus metrics
- **Rate Limiting**: Redis-backed rate limiting with configurable limits
- **Feature Flags**: Redis-backed feature flags with multiple evaluation rules
- **Security**: mTLS, security headers, threat detection
- **Monitoring**: Comprehensive FastAPI/Python metrics dashboard
- **Testing**: Isolated test environments with separate Prometheus registries

### Day 5-6: Authentication Service ✅ **COMPLETED**
**Objective**: Implement comprehensive authentication service with Supabase Auth, Auth0 integration, and security features

**Steps Completed**:
1. ✅ **Set up authentication models**:
   - Created comprehensive user models with role-based access control
   - Implemented session management with refresh tokens
   - Added MFA models for TOTP and backup codes
   - Created audit logging models for HIPAA compliance
   - Added consent management models for data governance

2. ✅ **Implemented authentication services**:
   - Created main AuthService with Supabase integration
   - Added Auth0 OAuth provider support
   - Implemented MFA service with TOTP and backup codes
   - Created role service for RBAC
   - Added audit service for security monitoring
   - Implemented consent service for HIPAA compliance

3. ✅ **Created API endpoints**:
   - Implemented comprehensive authentication endpoints
   - Added session management endpoints
   - Created MFA setup and verification endpoints
   - Added user management endpoints
   - Implemented audit and compliance endpoints

4. ✅ **Set up CI/CD pipeline**:
   - Created GitHub Actions workflow for auth service
   - Added security scanning with Bandit and Trivy
   - Implemented code quality checks with Black, Flake8, MyPy
   - Added comprehensive testing pipeline
   - Created multi-stage Dockerfile with security best practices
   - Added Kubernetes deployment configuration

5. ✅ **Implemented security features**:
   - Multi-factor authentication (TOTP)
   - Session management with refresh token rotation
   - Rate limiting and security headers
   - Comprehensive audit logging
   - HIPAA compliance features
   - Role-based access control (RBAC)

**Deliverables**:
- ✅ Complete authentication service with Supabase Auth integration
- ✅ Auth0 OAuth provider support
- ✅ Multi-factor authentication system
- ✅ Session management with security features
- ✅ Role-based access control system
- ✅ Comprehensive audit logging
- ✅ HIPAA compliance features
- ✅ CI/CD pipeline with security scanning
- ✅ Docker containerization
- ✅ Kubernetes deployment configuration
- ✅ Comprehensive test suite

**Key Features Implemented**:
- **Supabase Auth Integration**: Primary authentication system
- **Auth0 OAuth Support**: Multiple OAuth providers (Google, GitHub, etc.)
- **MFA System**: TOTP with backup codes and device management
- **Session Management**: Secure session handling with refresh tokens
- **RBAC System**: Fine-grained role-based access control
- **Audit Logging**: Comprehensive security event tracking
- **HIPAA Compliance**: Privacy and consent management
- **Security Features**: Rate limiting, security headers, threat detection
- **CI/CD Pipeline**: Automated testing, security scanning, deployment

**Access Information**:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/auth/health
- **Authentication Endpoints**: http://localhost:8000/api/v1/auth/auth/
- **User Management**: http://localhost:8000/api/v1/auth/users/
- **MFA Endpoints**: http://localhost:8000/api/v1/auth/mfa/
- **Role Management**: http://localhost:8000/api/v1/auth/roles/

**Testing**:
```bash
# Run authentication service tests
pytest apps/auth/tests/ -v

# Run specific test categories
pytest apps/auth/tests/unit/ -v
pytest apps/auth/tests/integration/ -v

# Run with coverage
pytest apps/auth/tests/ --cov=apps/auth --cov-report=html
```

**Deployment**:
```bash
# Build Docker image
docker build -f apps/auth/Dockerfile -t auth-service .

# Run locally
docker run -p 8000:8000 auth-service

# Deploy to Kubernetes
kubectl apply -f apps/auth/kubernetes/
```

**Next Steps**: Ready to proceed to Day 7-8: User Profile Service

## Phase 2: Core Services (Week 3-4)

### Day 8-10: User Profile Service
**Objective**: Implement user profile management

**Steps**:
1. **Create profile models**:
   ```bash
   # Create apps/user_profile/models/profile.py
   # Create apps/user_profile/models/preferences.py
   ```

2. **Implement profile service**:
   ```bash
   # Create apps/user_profile/services/profile_service.py
   ```

3. **Create profile API**:
   ```bash
   # Create apps/user_profile/api/profile.py
   ```

4. **Add profile validation**:
   ```bash
   # Create apps/user_profile/utils/validation.py
   ```

**Deliverables**:
- ✅ User profile CRUD operations
- ✅ Profile preferences management
- ✅ Profile validation and sanitization
- ✅ Profile privacy controls

### Day 11-14: Health Tracking Service
**Objective**: Implement health data tracking

**Steps**:
1. **Create health models**:
   ```bash
   # Create apps/health_tracking/models/vitals.py
   # Create apps/health_tracking/models/symptoms.py
   # Create apps/health_tracking/models/goals.py
   ```

2. **Implement health service**:
   ```bash
   # Create apps/health_tracking/services/vitals_service.py
   # Create apps/health_tracking/services/symptoms_service.py
   # Create apps/health_tracking/services/goals_service.py
   ```

3. **Create health API**:
   ```bash
   # Create apps/health_tracking/api/vitals.py
   # Create apps/health_tracking/api/symptoms.py
   # Create apps/health_tracking/api/goals.py
   ```

4. **Add data validation**:
   ```bash
   # Create apps/health_tracking/utils/validation.py
   ```

**Deliverables**:
- ✅ Vital signs tracking
- ✅ Symptoms logging
- ✅ Health goals management
- ✅ Data validation and normalization

## Phase 3: Device Integration (Week 5-6)

### Day 15-17: Device Data Service
**Objective**: Implement device data integration

**Steps**:
1. **Create device models**:
   ```bash
   # Create apps/device_data/models/device.py
   # Create apps/device_data/models/data_point.py
   ```

2. **Implement device service**:
   ```bash
   # Create apps/device_data/services/device_service.py
   # Create apps/device_data/services/data_service.py
   ```

3. **Create device API**:
   ```bash
   # Create apps/device_data/api/devices.py
   # Create apps/device_data/api/data.py
   ```

4. **Add data processing**:
   ```bash
   # Create apps/device_data/utils/processor.py
   ```

**Deliverables**:
- ✅ Device registration and management
- ✅ Data ingestion and processing
- ✅ Data validation and cleaning
- ✅ Device health monitoring

### Day 18-21: Message Bus Integration
**Objective**: Set up Kafka message bus

**Steps**:
1. **Create Kafka producers**:
   ```bash
   # Create common/messaging/producers.py
   ```

2. **Create Kafka consumers**:
   ```bash
   # Create common/messaging/consumers.py
   ```

3. **Implement event handlers**:
   ```bash
   # Create common/messaging/handlers.py
   ```

4. **Add message schemas**:
   ```bash
   # Create common/messaging/schemas.py
   ```

**Deliverables**:
- ✅ Kafka message bus setup
- ✅ Event-driven architecture
- ✅ Message validation and routing
- ✅ Error handling and retry logic

## Phase 4: Medical Records (Week 7-8)

### Day 22-24: Medical Records Service
**Objective**: Implement medical records management

**Steps**:
1. **Create medical models**:
   ```bash
   # Create apps/medical_records/models/lab_results.py
   # Create apps/medical_records/models/imaging.py
   # Create apps/medical_records/models/reports.py
   ```

2. **Implement medical service**:
   ```bash
   # Create apps/medical_records/services/lab_service.py
   # Create apps/medical_records/services/imaging_service.py
   # Create apps/medical_records/services/reports_service.py
   ```

3. **Create medical API**:
   ```bash
   # Create apps/medical_records/api/labs.py
   # Create apps/medical_records/api/imaging.py
   # Create apps/medical_records/api/reports.py
   ```

4. **Add OCR processing**:
   ```bash
   # Create apps/medical_records/utils/ocr.py
   ```

**Deliverables**:
- ✅ Lab results management
- ✅ Medical imaging storage
- ✅ Report generation
- ✅ OCR document processing

### Day 25-28: Analytics Service
**Objective**: Implement analytics and reporting

**Steps**:
1. **Set up DuckDB integration**:
   ```bash
   # Create apps/analytics/services/duckdb_service.py
   ```

2. **Create analytics models**:
   ```bash
   # Create apps/analytics/models/metrics.py
   # Create apps/analytics/models/reports.py
   ```

3. **Implement analytics service**:
   ```bash
   # Create apps/analytics/services/metrics_service.py
   # Create apps/analytics/services/reporting_service.py
   ```

4. **Create analytics API**:
   ```bash
   # Create apps/analytics/api/metrics.py
   # Create apps/analytics/api/reports.py
   ```

**Deliverables**:
- ✅ Analytics data processing
- ✅ Report generation
- ✅ Metrics aggregation
- ✅ Data visualization endpoints

## Phase 5: AI & Advanced Features (Week 9-10)

### Day 29-31: AI Insights Service
**Objective**: Implement AI-powered health insights

**Steps**:
1. **Create AI models**:
   ```bash
   # Create apps/ai_insights/models/insights.py
   # Create apps/ai_insights/models/predictions.py
   ```

2. **Implement AI service**:
   ```bash
   # Create apps/ai_insights/services/insights_service.py
   # Create apps/ai_insights/services/prediction_service.py
   ```

3. **Create AI API**:
   ```bash
   # Create apps/ai_insights/api/insights.py
   # Create apps/ai_insights/api/predictions.py
   ```

4. **Add model management**:
   ```bash
   # Create apps/ai_insights/utils/model_manager.py
   ```

**Deliverables**:
- ✅ Health insights generation
- ✅ Risk prediction models
- ✅ Anomaly detection
- ✅ Personalized recommendations

### Day 32-35: Voice & Input Service
**Objective**: Implement voice and multimodal input processing

**Steps**:
1. **Create voice models**:
   ```bash
   # Create apps/voice_input/models/voice_log.py
   # Create apps/voice_input/models/transcription.py
   ```

2. **Implement voice service**:
   ```bash
   # Create apps/voice_input/services/voice_service.py
   # Create apps/voice_input/services/transcription_service.py
   ```

3. **Create voice API**:
   ```bash
   # Create apps/voice_input/api/voice.py
   # Create apps/voice_input/api/transcription.py
   ```

4. **Add speech processing**:
   ```bash
   # Create apps/voice_input/utils/speech_processor.py
   ```

**Deliverables**:
- ✅ Voice input processing
- ✅ Speech-to-text conversion
- ✅ Intent recognition
- ✅ Multimodal input support

## Phase 6: Integration & Testing (Week 11-12)

### Day 36-38: Service Integration
**Objective**: Connect all services and implement end-to-end functionality

**Steps**:
1. **Update main application**:
   ```bash
   # Update main.py to include all service routers
   ```

2. **Implement service communication**:
   ```bash
   # Create common/services/communication.py
   ```

3. **Add service discovery**:
   ```bash
   # Create common/services/discovery.py
   ```

4. **Implement error handling**:
   ```bash
   # Create common/utils/error_handler.py
   ```

**Deliverables**:
- ✅ All services integrated
- ✅ Service communication working
- ✅ Error handling and recovery
- ✅ End-to-end functionality

### Day 39-42: Comprehensive Testing
**Objective**: Implement comprehensive testing suite

**Steps**:
1. **Create unit tests**:
   ```bash
   # Create tests/unit/ for each service
   ```

2. **Create integration tests**:
   ```bash
   # Create tests/integration/ for service interactions
   ```

3. **Create end-to-end tests**:
   ```bash
   # Create tests/e2e/ for complete workflows
   ```

4. **Add performance tests**:
   ```bash
   # Create tests/performance/ for load testing
   ```

**Deliverables**:
- ✅ Unit test coverage > 80%
- ✅ Integration tests for all services
- ✅ End-to-end test scenarios
- ✅ Performance benchmarks

## Phase 7: Deployment & Monitoring (Week 13-14)

### Day 43-45: Production Deployment
**Objective**: Deploy to production environment

**Steps**:
1. **Create production configuration**:
   ```bash
   # Create production.env
   # Update docker-compose.prod.yml
   ```

2. **Set up monitoring**:
   ```bash
   # Create monitoring/grafana/
   # Create monitoring/prometheus/
   ```

3. **Implement logging**:
   ```bash
   # Create common/utils/monitoring.py
   ```

4. **Add health checks**:
   ```bash
   # Create common/utils/health_checks.py
   ```

**Deliverables**:
- ✅ Production deployment
- ✅ Monitoring and alerting
- ✅ Logging and tracing
- ✅ Health monitoring

### Day 46-49: Performance Optimization
**Objective**: Optimize performance and scalability

**Steps**:
1. **Database optimization**:
   ```bash
   # Optimize database queries
   # Add database indexes
   ```

2. **Caching implementation**:
   ```bash
   # Create common/cache/redis_cache.py
   ```

3. **Load balancing**:
   ```bash
   # Create infrastructure/nginx/
   ```

4. **Resource scaling**:
   ```bash
   # Create infrastructure/kubernetes/
   ```

**Deliverables**:
- ✅ Optimized database performance
- ✅ Caching layer implemented
- ✅ Load balancing configured
- ✅ Auto-scaling setup

## Phase 8: Security & Compliance (Week 15-16)

### Day 50-52: Security Implementation
**Objective**: Implement comprehensive security measures

**Steps**:
1. **Add security middleware**:
   ```bash
   # Create common/middleware/security.py
   ```

2. **Implement rate limiting**:
   ```bash
   # Create common/utils/rate_limiter.py
   ```

3. **Add input validation**:
   ```bash
   # Create common/utils/validators.py
   ```

4. **Implement audit logging**:
   ```bash
   # Create common/utils/audit.py
   ```

**Deliverables**:
- ✅ Security middleware
- ✅ Rate limiting
- ✅ Input validation
- ✅ Audit logging

### Day 53-56: Compliance & Documentation
**Objective**: Ensure compliance and create documentation

**Steps**:
1. **Create API documentation**:
   ```bash
   # Generate OpenAPI documentation
   # Create user guides
   ```

2. **Implement compliance features**:
   ```bash
   # Create apps/consent_audit/
   # Create apps/privacy/
   ```

3. **Add data export/import**:
   ```bash
   # Create common/utils/data_portability.py
   ```

4. **Create deployment guides**:
   ```bash
   # Create docs/deployment/
   # Create docs/architecture/
   ```

**Deliverables**:
- ✅ Complete API documentation
- ✅ Compliance features
- ✅ Data portability
- ✅ Deployment documentation

## Success Criteria

### Technical Criteria
- ✅ All services running and communicating
- ✅ Database schema properly implemented
- ✅ API endpoints responding correctly
- ✅ Authentication and authorization working
- ✅ Data validation and sanitization
- ✅ Error handling and logging
- ✅ Performance benchmarks met
- ✅ Security measures implemented

### Functional Criteria
- ✅ User registration and login
- ✅ Health data tracking
- ✅ Device integration
- ✅ Medical records management
- ✅ AI insights generation
- ✅ Voice input processing
- ✅ Analytics and reporting
- ✅ Mobile API compatibility

### Quality Criteria
- ✅ Test coverage > 80%
- ✅ Code quality standards met
- ✅ Documentation complete
- ✅ Performance requirements met
- ✅ Security requirements met
- ✅ Compliance requirements met

## Daily Development Workflow

### Morning Routine (30 minutes)
1. **Check virtual environment**:
   ```bash
   # Ensure virtual environment is active
   python scripts/setup_venv.py validate
   
   # If not active, activate it
   source venv/bin/activate
   ```

2. **Check system health**:
   ```bash
   # Check all services
   docker-compose ps
   
   # Check service logs
   docker-compose logs --tail=50
   ```

3. **Run validation**:
   ```bash
   # Quick validation
   python scripts/validate_requirements.py
   
   # Run tests
   python scripts/test_setup.py
   ```

### Development Session (4-6 hours)
1. **Create feature branch**:
   ```bash
   git checkout -b feature/phase1-day1
   ```

2. **Implement features**:
   - Follow the daily steps above
   - Write tests for each feature
   - Document code changes
   - Ensure virtual environment stays active

3. **Test locally**:
   ```bash
   # Run tests
   python scripts/test_setup.py
   
   # Run linting (if available)
   # flake8 apps/
   
   # Run formatting (if available)
   # black apps/
   ```

### Evening Routine (30 minutes)
1. **Final validation**:
   ```bash
   # Ensure virtual environment is still active
   python scripts/setup_venv.py validate
   
   # Run final tests
   python scripts/test_setup.py
   ```

2. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: implement [feature name]"
   ```

3. **Push to remote**:
   ```bash
   git push origin feature/phase1-day1
   ```

4. **Update progress**:
   - Update this roadmap with completed items
   - Note any issues or blockers
   - Plan next day's tasks

## Troubleshooting Guide

### Common Issues

1. **Virtual Environment Issues**:
   ```bash
   # Check if virtual environment is active
   python scripts/setup_venv.py validate
   
   # If not active, activate it
   source venv/bin/activate  # macOS/Linux
   # .\venv\Scripts\activate  # Windows
   
   # If virtual environment doesn't exist
   python scripts/setup_venv.py create
   
   # If dependencies are missing
   python scripts/install_missing_dependencies.py
   
   # Start fresh if needed
   rm -rf venv/
   python scripts/setup_venv.py
   ```

2. **Database Connection Issues**:
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps postgres
   
   # Check database logs
   docker-compose logs postgres
   
   # Restart database
   docker-compose restart postgres
   ```

3. **Kafka Connection Issues**:
   ```bash
   # Check if Kafka is running
   docker-compose ps kafka
   
   # Check Kafka logs
   docker-compose logs kafka
   
   # Restart Kafka
   docker-compose restart kafka
   ```

4. **Monitoring Stack Issues**:
   ```bash
   # Check if Prometheus is running
   docker-compose ps prometheus
   
   # Check Prometheus logs
   docker-compose logs prometheus
   
   # Check Prometheus targets
   curl http://localhost:9090/api/v1/targets
   
   # Check if Grafana is running
   docker-compose ps grafana
   
   # Check Grafana logs
   docker-compose logs grafana
   
   # Check Redis connection
   docker-compose ps redis
   docker-compose logs redis
   
   # Restart monitoring services
   docker-compose restart prometheus grafana redis
   ```

5. **Prometheus Registry Conflicts in Tests**:
   ```bash
   # Run tests with isolated registries
   pytest tests/test_non_functional_requirements.py -v
   
   # If tests fail with registry conflicts, check:
   # - ResilienceMetrics registry parameter usage
   # - Test fixtures for isolated_prometheus_registry
   # - OpenTelemetry configuration
   ```

6. **Python Import Issues**:
   ```bash
   # Ensure virtual environment is active
   source venv/bin/activate
   
   # Reinstall dependencies
   pip install -r requirements.txt
   
   # Or use the dependency installer
   python scripts/install_missing_dependencies.py
   ```

7. **Test Failures**:
   ```bash
   # Run specific test
   pytest tests/unit/test_auth.py -v
   
   # Run with coverage
   pytest --cov=apps tests/ -v
   
   # Run comprehensive setup test
   python scripts/test_setup.py
   ```

8. **Setup Script Issues**:
   ```bash
   # Check if setup script is executable
   chmod +x setup.sh
   
   # Run with verbose output
   bash -x setup.sh
   
   # Use alternative setup method
   python scripts/setup_master.py
   ```

### Performance Issues

1. **Database Performance**:
   ```bash
   # Check slow queries
   docker-compose exec postgres psql -U postgres -d health_assistant -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
   ```

2. **Memory Usage**:
   ```bash
   # Check container resource usage
   docker stats
   ```

3. **API Performance**:
   ```bash
   # Run load test
   python -m pytest tests/performance/ -v
   ```

### Environment Validation

**Daily Environment Check**:
```bash
# Quick validation
python scripts/setup_venv.py validate

# Comprehensive validation
python scripts/validate_requirements.py

# Service health check
docker-compose ps

# Test API endpoints
curl http://localhost:3000/

# Check monitoring stack
curl http://localhost:8000/metrics  # FastAPI metrics
curl http://localhost:9090/api/v1/targets  # Prometheus targets
curl http://localhost:3002  # Grafana UI (admin/admin)
```

**Complete Environment Reset**:
```bash
# Stop all services
docker-compose down

# Remove virtual environment
rm -rf venv/

# Clean Docker volumes (optional)
docker-compose down -v

# Start fresh setup
./setup.sh
```

**Monitoring Stack Validation**:
```bash
# Check all monitoring services
docker-compose ps prometheus grafana redis

# Validate Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana datasources
curl -u admin:admin http://localhost:3002/api/datasources

# Test Redis connection
docker-compose exec redis redis-cli ping

# Run NFR tests
pytest tests/test_non_functional_requirements.py -v
```

## Next Steps After Implementation

1. **User Testing**: Conduct user acceptance testing
2. **Performance Tuning**: Optimize based on real usage
3. **Feature Enhancement**: Add new features based on feedback
4. **Scaling**: Prepare for production scaling
5. **Maintenance**: Set up ongoing maintenance procedures

## Support and Resources

- **Setup Documentation**: 
  - [JUNIOR_DEV_SETUP.md](JUNIOR_DEV_SETUP.md) - Complete setup guide for new developers
  - [VIRTUAL_ENVIRONMENT_SETUP.md](VIRTUAL_ENVIRONMENT_SETUP.md) - Virtual environment management guide
  - [SETUP_SUMMARY.md](SETUP_SUMMARY.md) - Setup system overview
- **Scripts Documentation**: [scripts/README.md](scripts/README.md) - All setup and maintenance scripts
- **Requirements**: [REQUIRED_TOOLS_FRAMEWORKS.md](REQUIRED_TOOLS_FRAMEWORKS.md) - System requirements and dependencies
- **API Reference**: Available at `/docs` when running
- **Logs**: Check `logs/` directory
- **Issues**: Create GitHub issues for bugs
- **Questions**: Check setup guides for common questions

**Quick Reference Commands**:
```bash
# Setup
./setup.sh                                    # One-command setup
python scripts/setup_venv.py                  # Virtual environment only
python scripts/setup_master.py                # Detailed setup

# Validation
python scripts/setup_venv.py validate         # Check virtual environment
python scripts/validate_requirements.py       # Comprehensive validation
python scripts/test_setup.py                  # Test everything

# Monitoring
docker-compose ps prometheus grafana redis    # Check monitoring services
curl http://localhost:8000/metrics            # Check FastAPI metrics
curl http://localhost:9090/api/v1/targets     # Check Prometheus targets
pytest tests/test_non_functional_requirements.py -v  # Run NFR tests

# Troubleshooting
python scripts/install_missing_dependencies.py # Install missing packages
docker-compose logs [service-name]            # Check service logs
docker-compose ps                             # Check service status
```

---

**Remember**: This roadmap is a living document. Update it as you progress and adjust timelines based on actual development speed and any blockers encountered.

## Documentation Update Summary

**Last Updated**: January 2024

### Recent Updates Made:

#### ✅ Day 3-4 Core Infrastructure & Non-Functional Requirements
- **Added monitoring stack setup** (Prometheus + Grafana + Redis)
- **Updated deliverables** to reflect all implemented NFRs
- **Added validation steps** for monitoring stack
- **Added monitoring stack access information**
- **Added key features implemented** section

#### ✅ Troubleshooting Guide Updates
- **Added monitoring stack troubleshooting** (Prometheus, Grafana, Redis)
- **Added Prometheus registry conflict resolution**
- **Updated environment validation** to include monitoring services
- **Added monitoring stack validation commands**
- **Fixed numbering in troubleshooting section**

#### ✅ Quick Reference Commands
- **Added monitoring commands** for Prometheus, Grafana, Redis
- **Added NFR test commands**
- **Updated service health check commands**

### Current Implementation Status:

#### ✅ Completed Components:
1. **Environment Setup** - Virtual environment, Docker services, validation
2. **Core Infrastructure** - Database, logging, base services, middleware
3. **Non-Functional Requirements** - All NFRs implemented with tests
4. **Monitoring Stack** - Prometheus, Grafana, Redis with auto-provisioning
5. **Resilience Patterns** - Circuit breakers, retries, timeouts with metrics
6. **Security** - mTLS, security headers, threat detection
7. **Rate Limiting** - Redis-backed with configurable limits
8. **Feature Flags** - Redis-backed with multiple evaluation rules
9. **Testing** - Comprehensive test suite with isolated registries

#### 🔄 Next Phase:
- **Day 5-7: Authentication Service** - Ready to implement
- **Phase 2: Core Services** - Ready to begin
- **Phase 3: AI Integration** - Ready to begin

### Documentation Files Updated:
- ✅ `IMPLEMENTATION_ROADMAP.md` - Complete roadmap with current status
- ✅ `IMPLEMENTATION_GUIDE.md` - Updated NFR section with implementation status
- ✅ `docs/CORE_INFRASTRUCTURE.md` - Added monitoring stack and NFR documentation
- ✅ `docs/NON_FUNCTIONAL_REQUIREMENTS.md` - Comprehensive NFR documentation
- ✅ `scripts/README.md` - Updated with new scripts and validation
- ✅ `JUNIOR_DEV_SETUP.md` - Complete setup guide for new developers
- ✅ `VIRTUAL_ENVIRONMENT_SETUP.md` - Virtual environment management guide

### Validation Commands:
```bash
# Complete environment validation
./setup.sh

# Run all tests
pytest tests/test_non_functional_requirements.py -v

# Check monitoring stack
docker-compose ps prometheus grafana redis
curl http://localhost:8000/metrics
curl http://localhost:9090/api/v1/targets
curl http://localhost:3002  # Grafana UI

# Validate virtual environment
python scripts/setup_venv.py validate
python scripts/validate_requirements.py
```

Health Tracking Service
├── API Layer (RESTful endpoints)
├── Service Layer (Business logic)
├── Agentic Layer (Autonomous agents)
├── Analytics Layer (ML/AI insights)
└── Integration Layer (External devices/APIs) 