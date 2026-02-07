# Next Steps Guide - Authentication Service Setup

## Overview

This guide walks you through the complete setup process for the Authentication Service, from configuring GitHub secrets to deploying to Kubernetes.

## Prerequisites

- ✅ GitHub repository set up
- ✅ Authentication service code ready
- ✅ CI/CD pipeline configured
- ✅ Docker Desktop installed and running

## Step 1: Enable Kubernetes in Docker Desktop

### 1.1 Open Docker Desktop Settings
1. Open **Docker Desktop** application
2. Click the **gear icon** (Settings) in the top-right corner
3. In the left sidebar, click **"Kubernetes"**

### 1.2 Enable Kubernetes
1. Check the box for **"Enable Kubernetes"**
2. Click **"Apply & Restart"**
3. Wait for Docker to restart (this may take 2-5 minutes)
4. You'll see a green checkmark when Kubernetes is ready

### 1.3 Verify Kubernetes is Running
```bash
# Check if kubectl is available
kubectl version --client

# Check cluster status
kubectl cluster-info

# Check nodes
kubectl get nodes
```

## Step 2: Configure GitHub Secrets

### 2.1 Access GitHub Repository Settings
1. Go to your GitHub repository: `https://github.com/your-username/PersonalHealthAssistant`
2. Click the **"Settings"** tab
3. In the left sidebar, click **"Secrets and variables"** → **"Actions"**

### 2.2 Add Required Secrets
Click **"New repository secret"** for each of the following:

#### 🔴 REQUIRED Secrets:

**KUBE_CONFIG_DEV**
- **Name**: `KUBE_CONFIG_DEV`
- **Value**: (We'll generate this in Step 3)
- **Description**: Base64 encoded kubeconfig for development environment

**KUBE_CONFIG_STAGING**
- **Name**: `KUBE_CONFIG_STAGING`
- **Value**: (We'll generate this in Step 3)
- **Description**: Base64 encoded kubeconfig for staging environment

**KUBE_CONFIG_PROD**
- **Name**: `KUBE_CONFIG_PROD`
- **Value**: (We'll generate this in Step 3)
- **Description**: Base64 encoded kubeconfig for production environment

**DOCKER_REGISTRY_TOKEN**
- **Name**: `DOCKER_REGISTRY_TOKEN`
- **Value**: `your-docker-registry-token`
- **Description**: Docker registry authentication token

**JWT_SECRET_KEY**
- **Name**: `JWT_SECRET_KEY`
- **Value**: `QaCdqUh5fm9KDP8V7kRI7zCXMtOgtrAAGRCihw9KtSY`
- **Description**: Secure JWT secret key for token signing

**ENCRYPTION_KEY**
- **Name**: `ENCRYPTION_KEY`
- **Value**: `OkgDVbmYZj3bWo8OxERRrEouFpayH5hL_fSqct0jBgQ`
- **Description**: Encryption key for sensitive data

#### 🟡 OPTIONAL Secrets:

**SLACK_WEBHOOK_URL**
- **Name**: `SLACK_WEBHOOK_URL`
- **Value**: `https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK`
- **Description**: Slack webhook URL for notifications

**SENTRY_DSN**
- **Name**: `SENTRY_DSN`
- **Value**: `https://your-sentry-dsn@sentry.io/project-id`
- **Description**: Sentry DSN for error tracking

## Step 3: Generate Kubernetes Configuration

### 3.1 Run the Kubernetes Setup Script
```bash
# Make sure Kubernetes is enabled in Docker Desktop first
python3 scripts/setup/setup_kubernetes_cluster.py
```

### 3.2 Choose Option 4 (Docker Desktop)
When prompted, enter `4` to use Docker Desktop Kubernetes.

### 3.3 Copy the Generated Kubeconfig
The script will output base64-encoded kubeconfig values. Copy these and update your GitHub secrets:

- Update `KUBE_CONFIG_DEV` with the generated value
- Update `KUBE_CONFIG_STAGING` with the generated value  
- Update `KUBE_CONFIG_PROD` with the generated value

## Step 4: Deploy to Kubernetes

### 4.1 Create Namespaces
```bash
# Create required namespaces
kubectl create namespace personal-health-assistant
kubectl create namespace monitoring
kubectl create namespace ingress-nginx
```

### 4.2 Install Helm (if not already installed)
```bash
# Install Helm
curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar xz
sudo mv linux-amd64/helm /usr/local/bin/helm

# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### 4.3 Deploy the Authentication Service
```bash
# Apply Kubernetes manifests
kubectl apply -f apps/auth/kubernetes/secrets.yaml -n personal-health-assistant
kubectl apply -f apps/auth/kubernetes/deployment.yaml -n personal-health-assistant
kubectl apply -f apps/auth/kubernetes/network-policy.yaml -n personal-health-assistant
kubectl apply -f apps/auth/kubernetes/monitoring.yaml -n personal-health-assistant
```

### 4.4 Verify Deployment
```bash
# Check deployment status
kubectl get pods -n personal-health-assistant

# Check services
kubectl get services -n personal-health-assistant

# Check ingress
kubectl get ingress -n personal-health-assistant
```

## Step 5: Test the Deployment

### 5.1 Port Forward to Access the Service
```bash
# Port forward to access the service locally
kubectl port-forward svc/auth-service 8000:80 -n personal-health-assistant
```

### 5.2 Test Health Endpoint
```bash
# Test health check
curl http://localhost:8000/health

# Test metrics endpoint
curl http://localhost:8000/metrics

# Test API documentation
open http://localhost:8000/docs
```

### 5.3 Test Authentication Endpoints
```bash
# Test registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!",
    "confirm_password": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User",
    "user_type": "patient"
  }'

# Test login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123!"
  }'
```

## Step 6: Set Up Monitoring

### 6.1 Install Prometheus Stack
```bash
# Install Prometheus and Grafana
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

### 6.2 Access Grafana Dashboard
```bash
# Port forward to Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring

# Access Grafana (default credentials: admin/prom-operator)
open http://localhost:3000
```

### 6.3 Import Dashboard
1. Login to Grafana with `admin` / `prom-operator`
2. Go to **Dashboards** → **Import**
3. Import the dashboard JSON from `monitoring/grafana/provisioning/dashboards/fastapi-dashboard.json`

## Step 7: Test the CI/CD Pipeline

### 7.1 Make a Test Commit
```bash
# Create a test branch
git checkout -b test-cicd

# Make a small change
echo "# Test CI/CD" >> apps/auth/README.md

# Commit and push
git add .
git commit -m "test: Test CI/CD pipeline"
git push origin test-cicd
```

### 7.2 Monitor Pipeline Execution
1. Go to your GitHub repository
2. Click the **"Actions"** tab
3. Monitor the pipeline execution
4. Check for any failures and fix them

### 7.3 Create Pull Request
1. Go to your GitHub repository
2. Click **"Compare & pull request"** for your test branch
3. Create a pull request to `develop` branch
4. Monitor the pipeline execution

## Step 8: Production Deployment

### 8.1 Merge to Main Branch
```bash
# Merge your changes to main
git checkout main
git merge develop
git push origin main
```

### 8.2 Monitor Production Deployment
1. Go to GitHub Actions
2. Monitor the production deployment pipeline
3. Verify the deployment is successful

### 8.3 Test Production Endpoints
```bash
# Test production health endpoint
curl https://your-production-domain.com/health

# Test production API
curl https://your-production-domain.com/api/v1/auth/health
```

## Troubleshooting

### Common Issues

#### 1. Kubernetes Not Starting
```bash
# Check Docker Desktop status
docker version

# Restart Docker Desktop
# Go to Docker Desktop → Troubleshoot → Reset to factory defaults
```

#### 2. Pods Not Starting
```bash
# Check pod status
kubectl get pods -n personal-health-assistant

# Check pod logs
kubectl logs -f deployment/auth-service -n personal-health-assistant

# Check events
kubectl get events -n personal-health-assistant --sort-by='.lastTimestamp'
```

#### 3. GitHub Actions Failures
```bash
# Check workflow logs in GitHub Actions tab
# Common issues:
# - Missing secrets
# - Invalid kubeconfig
# - Network connectivity issues
```

#### 4. Service Not Accessible
```bash
# Check service status
kubectl get svc -n personal-health-assistant

# Check ingress status
kubectl get ingress -n personal-health-assistant

# Check port forwarding
kubectl port-forward svc/auth-service 8000:80 -n personal-health-assistant
```

### Debug Commands
```bash
# Get cluster info
kubectl cluster-info

# Check node resources
kubectl top nodes

# Check pod resources
kubectl top pods -n personal-health-assistant

# Check service endpoints
kubectl get endpoints -n personal-health-assistant
```

## Next Steps After Setup

### 1. Configure Domain and SSL
- Set up a custom domain for your service
- Configure SSL certificates
- Update ingress configuration

### 2. Set Up Monitoring Alerts
- Configure Prometheus alerting rules
- Set up notification channels
- Test alerting functionality

### 3. Implement Backup Strategy
- Set up database backups
- Configure backup retention policies
- Test restore procedures

### 4. Security Hardening
- Review security policies
- Implement network policies
- Set up security scanning

### 5. Performance Optimization
- Monitor resource usage
- Optimize container resources
- Implement horizontal pod autoscaling

## Support Resources

### Documentation
- [Authentication Service README](apps/auth/README.md)
- [API Documentation](apps/auth/API_DOCUMENTATION.md)
- [Deployment Guide](apps/auth/DEPLOYMENT_GUIDE.md)
- [Security Guide](apps/auth/SECURITY_GUIDE.md)

### Community
- GitHub Issues for bug reports
- GitHub Discussions for questions
- Stack Overflow for technical questions

### Professional Support
- Contact DevOps team for infrastructure issues
- Contact Security team for security concerns
- Contact Compliance team for compliance questions

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**Maintainer**: DevOps Team 