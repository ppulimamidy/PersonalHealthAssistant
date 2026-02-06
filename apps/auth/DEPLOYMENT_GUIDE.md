# Authentication Service Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Authentication Service in various environments, from local development to production.

## Prerequisites

### System Requirements

- **CPU**: 2+ cores (4+ for production)
- **Memory**: 4GB RAM (8GB+ for production)
- **Storage**: 20GB+ available space
- **Network**: Stable internet connection

### Software Requirements

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Kubernetes**: 1.24+ (for K8s deployment)
- **PostgreSQL**: 15+
- **Redis**: 7+
- **Python**: 3.11+ (for local development)

### External Services

- **Supabase**: Account and project setup
- **Auth0**: Account and application setup (optional)
- **GitHub**: Repository access
- **Container Registry**: Docker Hub, GitHub Container Registry, or AWS ECR

## Environment Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/health_assistant
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://localhost:6379
REDIS_POOL_SIZE=10

# JWT
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# Auth0 (Optional)
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret

# Security
CORS_ORIGINS=["https://your-domain.com", "https://app.your-domain.com"]
ALLOWED_HOSTS=["your-domain.com", "api.your-domain.com"]
TRUSTED_PROXIES=["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]

# Rate Limiting
RATE_LIMIT_MAX_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_LOGIN_ATTEMPTS=5
RATE_LIMIT_LOGIN_WINDOW=300

# MFA
MFA_MAX_ATTEMPTS=5
MFA_LOCKOUT_DURATION_MINUTES=30
MFA_BACKUP_CODES_COUNT=10

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
SENTRY_DSN=your-sentry-dsn
SENTRY_ENVIRONMENT=production

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true

# Webhooks
WEBHOOK_URL=https://your-webhook-endpoint.com
WEBHOOK_SECRET=your-webhook-secret
```

### Environment-Specific Configurations

#### Development
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

#### Staging
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=["https://staging.your-domain.com"]
```

#### Production
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
CORS_ORIGINS=["https://your-domain.com"]
```

## Local Development Deployment

### 1. Clone Repository

```bash
git clone https://github.com/your-org/PersonalHealthAssistant.git
cd PersonalHealthAssistant
```

### 2. Set Up Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start Dependencies

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait for services to be ready
docker-compose ps
```

### 4. Set Up Database

```bash
# Run database setup
python scripts/setup/db_setup.py

# Run migrations
alembic upgrade head
```

### 5. Start the Service

```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 6. Verify Deployment

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

## Docker Deployment

### 1. Build Docker Image

```bash
# Build the image
docker build -f apps/auth/Dockerfile -t auth-service:latest .

# Tag for registry
docker tag auth-service:latest your-registry/auth-service:latest
```

### 2. Run with Docker Compose

Create `docker-compose.auth.yml`:

```yaml
version: '3.8'

services:
  auth-service:
    image: your-registry/auth-service:latest
    container_name: auth-service
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/health_assistant
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  postgres:
    image: postgres:15
    container_name: auth-postgres
    environment:
      POSTGRES_DB: health_assistant
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: auth-redis
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres_data:
```

Run the services:

```bash
docker-compose -f docker-compose.auth.yml up -d
```

### 3. Run Standalone Container

```bash
docker run -d \
  --name auth-service \
  -p 8000:8000 \
  --env-file .env \
  --network auth-network \
  your-registry/auth-service:latest
```

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace personal-health-assistant
```

### 2. Create Secrets

```bash
# Create secret for sensitive data
kubectl create secret generic auth-service-secrets \
  --from-literal=database-url="postgresql://user:password@postgres:5432/health_assistant" \
  --from-literal=redis-url="redis://redis:6379" \
  --from-literal=jwt-secret-key="your-jwt-secret" \
  --from-literal=supabase-url="https://your-project.supabase.co" \
  --from-literal=supabase-key="your-supabase-key" \
  --namespace=personal-health-assistant
```

### 3. Create ConfigMap

```bash
kubectl create configmap auth-service-config \
  --from-literal=environment="production" \
  --from-literal=log-level="INFO" \
  --from-literal=cors-origins='["https://your-domain.com"]' \
  --namespace=personal-health-assistant
```

### 4. Deploy Services

```bash
# Apply all Kubernetes manifests
kubectl apply -f apps/auth/kubernetes/ -n personal-health-assistant

# Check deployment status
kubectl get pods -n personal-health-assistant
kubectl get services -n personal-health-assistant
kubectl get ingress -n personal-health-assistant
```

### 5. Verify Deployment

```bash
# Check pod logs
kubectl logs -f deployment/auth-service -n personal-health-assistant

# Test health endpoint
kubectl port-forward svc/auth-service 8000:80 -n personal-health-assistant
curl http://localhost:8000/health
```

## CI/CD Pipeline Deployment

### GitHub Actions Workflow

The service includes a comprehensive CI/CD pipeline in `.github/workflows/auth-service-ci.yml`:

1. **Security Scanning**: Bandit, Trivy, Safety
2. **Code Quality**: Black, Flake8, MyPy
3. **Testing**: Unit, integration, security tests
4. **Building**: Docker image creation
5. **Deployment**: Multi-environment deployment

### Manual Deployment Steps

```bash
# 1. Run security checks
bandit -r apps/auth/
safety check

# 2. Run tests
pytest apps/auth/tests/ -v --cov=apps/auth

# 3. Build and push image
docker build -f apps/auth/Dockerfile -t your-registry/auth-service:$TAG .
docker push your-registry/auth-service:$TAG

# 4. Deploy to environment
kubectl set image deployment/auth-service auth-service=your-registry/auth-service:$TAG -n personal-health-assistant
```

### Automated Deployment

The pipeline automatically deploys based on branch:

- **`develop`** → Development environment
- **`main`** → Staging → Production (with approval)

## Production Deployment

### 1. Infrastructure Setup

#### Load Balancer Configuration

```nginx
# Nginx configuration
upstream auth_service {
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
    server 10.0.1.12:8000;
}

server {
    listen 443 ssl http2;
    server_name auth.your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://auth_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### SSL/TLS Configuration

```bash
# Generate SSL certificate
certbot certonly --nginx -d auth.your-domain.com

# Auto-renewal
crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Database Setup

#### PostgreSQL Configuration

```sql
-- Create database
CREATE DATABASE health_assistant;

-- Create user
CREATE USER auth_user WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE health_assistant TO auth_user;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

#### Redis Configuration

```bash
# Redis configuration file
cat > /etc/redis/redis.conf << EOF
bind 127.0.0.1
port 6379
requirepass your_redis_password
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
EOF
```

### 3. Monitoring Setup

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'auth-service'
    static_configs:
      - targets: ['auth-service:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

#### Grafana Dashboard

Import the provided dashboard JSON from `monitoring/grafana/provisioning/dashboards/fastapi-dashboard.json`.

### 4. Security Hardening

#### Firewall Configuration

```bash
# UFW firewall rules
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5432/tcp  # PostgreSQL (if external)
ufw enable
```

#### System Hardening

```bash
# Update system
apt update && apt upgrade -y

# Install security tools
apt install -y fail2ban ufw

# Configure fail2ban
cat > /etc/fail2ban/jail.local << EOF
[auth-service]
enabled = true
port = 8000
filter = auth-service
logpath = /var/log/auth-service/access.log
maxretry = 5
bantime = 3600
EOF
```

## Scaling and Performance

### Horizontal Scaling

```bash
# Scale the deployment
kubectl scale deployment auth-service --replicas=5 -n personal-health-assistant

# Check scaling
kubectl get pods -n personal-health-assistant
```

### Load Testing

```bash
# Install k6
curl -L https://github.com/grafana/k6/releases/download/v0.45.0/k6-v0.45.0-linux-amd64.tar.gz | tar xz

# Run load test
./k6 run apps/auth/tests/load/auth-service-load-test.js
```

### Performance Tuning

#### Database Optimization

```sql
-- Create indexes for performance
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_sessions_user_id ON sessions(user_id);
CREATE INDEX CONCURRENTLY idx_audit_logs_user_id ON auth_audit_logs(user_id);
CREATE INDEX CONCURRENTLY idx_audit_logs_event_timestamp ON auth_audit_logs(event_timestamp);
```

#### Application Tuning

```python
# Database connection pooling
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30

# Redis connection pooling
REDIS_POOL_SIZE = 10

# Worker processes
WORKERS = 4
```

## Backup and Recovery

### Database Backup

```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="health_assistant"

# Create backup
pg_dump -h localhost -U auth_user -d $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/backup_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
```

### Recovery Procedures

```bash
# Restore from backup
gunzip -c backup_20240101_120000.sql.gz | psql -h localhost -U auth_user -d health_assistant

# Point-in-time recovery
pg_restore -h localhost -U auth_user -d health_assistant --clean backup_file.dump
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check database connectivity
psql -h localhost -U auth_user -d health_assistant -c "SELECT 1;"

# Check connection pool
psql -h localhost -U auth_user -d health_assistant -c "SELECT * FROM pg_stat_activity;"
```

#### 2. Redis Connection Issues

```bash
# Test Redis connection
redis-cli -h localhost -p 6379 ping

# Check Redis memory usage
redis-cli -h localhost -p 6379 info memory
```

#### 3. Service Health Issues

```bash
# Check service logs
docker logs auth-service
kubectl logs deployment/auth-service -n personal-health-assistant

# Check service health
curl -f http://localhost:8000/health
```

#### 4. Performance Issues

```bash
# Check resource usage
docker stats auth-service
kubectl top pods -n personal-health-assistant

# Check slow queries
psql -h localhost -U auth_user -d health_assistant -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Restart service
docker restart auth-service
```

### Monitoring Alerts

Set up alerts for:

- **High CPU/Memory usage**: >80%
- **High error rate**: >5%
- **High response time**: >2s
- **Database connection issues**
- **Redis connection issues**
- **Service health check failures**

## Security Checklist

- [ ] SSL/TLS certificates installed and valid
- [ ] Firewall rules configured
- [ ] Database passwords are strong and unique
- [ ] JWT secrets are secure and rotated
- [ ] Rate limiting enabled
- [ ] Audit logging enabled
- [ ] MFA enabled for admin accounts
- [ ] Regular security updates applied
- [ ] Backup encryption enabled
- [ ] Network segmentation implemented
- [ ] Monitoring and alerting configured
- [ ] Incident response plan documented

## Maintenance

### Regular Tasks

#### Daily
- Check service health and logs
- Monitor resource usage
- Review security alerts

#### Weekly
- Review audit logs
- Check backup status
- Update security patches
- Review performance metrics

#### Monthly
- Rotate secrets and certificates
- Review access logs
- Update dependencies
- Conduct security assessments

#### Quarterly
- Full security audit
- Performance optimization review
- Disaster recovery testing
- Capacity planning

### Update Procedures

```bash
# 1. Backup current deployment
kubectl get deployment auth-service -o yaml > auth-service-backup.yaml

# 2. Update image
kubectl set image deployment/auth-service auth-service=your-registry/auth-service:new-version

# 3. Monitor rollout
kubectl rollout status deployment/auth-service

# 4. Rollback if needed
kubectl rollout undo deployment/auth-service
```

## Support

For deployment support:

- **Documentation**: This deployment guide
- **Issues**: GitHub Issues
- **Email**: devops@your-domain.com
- **Slack**: #deployment channel
- **Emergency**: 24/7 on-call rotation 