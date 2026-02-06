# CI/CD Pipeline Setup Guide

## Overview

This guide provides step-by-step instructions for setting up the complete CI/CD pipeline for the Authentication Service, including GitHub Actions, Kubernetes deployment, monitoring, and security scanning.

## Prerequisites

### Required Tools
- **Git**: Version control
- **Docker**: Containerization
- **kubectl**: Kubernetes CLI
- **helm**: Kubernetes package manager
- **GitHub Account**: Repository access

### Required Services
- **GitHub Repository**: For source code and CI/CD
- **Kubernetes Cluster**: For deployment
- **Container Registry**: For Docker images
- **Monitoring Stack**: Prometheus + Grafana

## Step 1: Repository Setup

### 1.1 Fork/Clone Repository
```bash
# Fork the repository on GitHub, then clone
git clone https://github.com/your-username/PersonalHealthAssistant.git
cd PersonalHealthAssistant

# Add upstream remote
git remote add upstream https://github.com/original-org/PersonalHealthAssistant.git
```

### 1.2 Branch Strategy
```bash
# Create development branch
git checkout -b develop
git push -u origin develop

# Create feature branch
git checkout -b feature/auth-service-cicd
```

## Step 2: GitHub Repository Configuration

### 2.1 Repository Settings
1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Add the following secrets:

#### Required Secrets
```bash
# Kubernetes Configuration
KUBE_CONFIG_DEV=<base64-encoded-kubeconfig-for-dev>
KUBE_CONFIG_STAGING=<base64-encoded-kubeconfig-for-staging>
KUBE_CONFIG_PROD=<base64-encoded-kubeconfig-for-production>

# Container Registry
DOCKER_REGISTRY_TOKEN=<your-registry-token>

# External Services
SLACK_WEBHOOK_URL=<slack-webhook-url>
SENTRY_DSN=<sentry-dsn>
```

#### Optional Secrets
```bash
# Monitoring
GRAFANA_API_KEY=<grafana-api-key>
PROMETHEUS_URL=<prometheus-url>

# Security Scanning
SONAR_TOKEN=<sonarqube-token>
TRIVY_TOKEN=<trivy-token>
```

### 2.2 Branch Protection Rules
1. Go to **Settings** → **Branches**
2. Add rule for `main` branch:
   - ✅ Require pull request reviews
   - ✅ Require status checks to pass
   - ✅ Require branches to be up to date
   - ✅ Include administrators

### 2.3 GitHub Actions Permissions
1. Go to **Settings** → **Actions** → **General**
2. Set **Workflow permissions** to "Read and write permissions"
3. Enable **Allow GitHub Actions to create and approve pull requests**

## Step 3: Kubernetes Cluster Setup

### 3.1 Cluster Requirements
```bash
# Minimum cluster specifications
Nodes: 3
CPU: 4 cores per node
Memory: 8GB per node
Storage: 100GB per node
```

### 3.2 Install Required Tools
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar xz
sudo mv linux-amd64/helm /usr/local/bin/helm

# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.12.0/cert-manager.yaml
```

### 3.3 Create Namespaces
```bash
# Create namespaces
kubectl create namespace personal-health-assistant
kubectl create namespace monitoring
kubectl create namespace ingress-nginx

# Label namespaces
kubectl label namespace personal-health-assistant name=personal-health-assistant
kubectl label namespace monitoring name=monitoring
```

## Step 4: Monitoring Stack Setup

### 4.1 Install Prometheus Stack
```bash
# Add Helm repositories
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Prometheus Stack
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false
```

### 4.2 Install Grafana
```bash
# Install Grafana
helm install grafana grafana/grafana \
  --namespace monitoring \
  --set adminPassword=admin123 \
  --set service.type=LoadBalancer
```

### 4.3 Configure Dashboards
```bash
# Get Grafana admin password
kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" | base64 --decode

# Port forward to access Grafana
kubectl port-forward --namespace monitoring svc/grafana 3000:80
```

## Step 5: Ingress Controller Setup

### 5.1 Install NGINX Ingress
```bash
# Add NGINX Ingress Helm repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install NGINX Ingress
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer
```

### 5.2 Configure SSL Certificates
```bash
# Create ClusterIssuer for Let's Encrypt
cat << EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

## Step 6: Database Setup

### 6.1 Install PostgreSQL
```bash
# Add Bitnami Helm repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install PostgreSQL
helm install postgres bitnami/postgresql \
  --namespace personal-health-assistant \
  --set auth.postgresPassword=postgres123 \
  --set auth.database=health_assistant \
  --set primary.persistence.size=10Gi
```

### 6.2 Install Redis
```bash
# Install Redis
helm install redis bitnami/redis \
  --namespace personal-health-assistant \
  --set auth.password=redis123 \
  --set master.persistence.size=5Gi
```

## Step 7: Deploy Authentication Service

### 7.1 Create Secrets
```bash
# Create Kubernetes secrets
kubectl create secret generic auth-service-secrets \
  --namespace personal-health-assistant \
  --from-literal=database-url="postgresql://postgres:postgres123@postgres:5432/health_assistant" \
  --from-literal=redis-url="redis://:redis123@redis:6379" \
  --from-literal=jwt-secret-key="your-super-secret-jwt-key" \
  --from-literal=supabase-url="https://your-project.supabase.co" \
  --from-literal=supabase-key="your-supabase-anon-key"
```

### 7.2 Apply Kubernetes Manifests
```bash
# Apply all manifests
kubectl apply -f apps/auth/kubernetes/secrets.yaml
kubectl apply -f apps/auth/kubernetes/deployment.yaml
kubectl apply -f apps/auth/kubernetes/network-policy.yaml
kubectl apply -f apps/auth/kubernetes/monitoring.yaml

# Verify deployment
kubectl get pods -n personal-health-assistant
kubectl get services -n personal-health-assistant
```

## Step 8: Security Scanning Setup

### 8.1 Install Security Tools
```bash
# Install Bandit
pip install bandit

# Install Safety
pip install safety

# Install Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Install SonarQube Scanner
wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.7.2.2744-linux.zip
unzip sonar-scanner-cli-4.7.2.2744-linux.zip
sudo mv sonar-scanner-4.7.2.2744-linux /opt/sonar-scanner
export PATH=$PATH:/opt/sonar-scanner/bin
```

### 8.2 Configure Security Scanning
```bash
# Create security configuration files
cat > .bandit << EOF
exclude_dirs: ['tests', 'venv', '__pycache__']
skips: ['B101', 'B601']
severity: ['low', 'medium', 'high']
EOF

cat > .safety << EOF
ignore: ['CVE-2021-1234']
full_report: true
EOF
```

## Step 9: Load Testing Setup

### 9.1 Install k6
```bash
# Install k6
curl -L https://github.com/grafana/k6/releases/download/v0.45.0/k6-v0.45.0-linux-amd64.tar.gz | tar xz
sudo mv k6-v0.45.0-linux-amd64/k6 /usr/local/bin/

# Verify installation
k6 version
```

### 9.2 Configure Load Testing
```bash
# Create load test configuration
cat > k6-config.json << EOF
{
  "stages": [
    {"duration": "2m", "target": 10},
    {"duration": "5m", "target": 10},
    {"duration": "2m", "target": 50},
    {"duration": "5m", "target": 50},
    {"duration": "2m", "target": 0}
  ],
  "thresholds": {
    "http_req_duration": ["p(95)<2000"],
    "http_req_failed": ["rate<0.1"]
  }
}
EOF
```

## Step 10: CI/CD Pipeline Verification

### 10.1 Test Pipeline
```bash
# Make a test commit
git add .
git commit -m "test: Add CI/CD pipeline configuration"
git push origin feature/auth-service-cicd

# Create pull request
# Go to GitHub and create PR from feature branch to develop
```

### 10.2 Monitor Pipeline Execution
1. Go to **Actions** tab in GitHub
2. Monitor the pipeline execution
3. Check for any failures and fix them
4. Verify all stages pass

### 10.3 Verify Deployment
```bash
# Check deployment status
kubectl get pods -n personal-health-assistant
kubectl get services -n personal-health-assistant
kubectl get ingress -n personal-health-assistant

# Test health endpoint
curl -f https://auth.your-domain.com/health

# Check metrics endpoint
curl -f https://auth.your-domain.com/metrics
```

## Step 11: Monitoring and Alerting

### 11.1 Configure Grafana Dashboards
1. Access Grafana at `http://localhost:3000`
2. Login with admin/admin123
3. Import the provided dashboard JSON
4. Configure data sources

### 11.2 Set Up Alerting
```bash
# Create alerting rules
kubectl apply -f apps/auth/kubernetes/monitoring.yaml

# Verify alerting configuration
kubectl get prometheusrules -n personal-health-assistant
```

### 11.3 Configure Notifications
1. Go to Grafana → Alerting → Notification channels
2. Add Slack notification channel
3. Configure alert rules with notifications

## Step 12: Production Deployment

### 12.1 Production Environment Setup
```bash
# Create production namespace
kubectl create namespace personal-health-assistant-prod

# Apply production-specific configurations
kubectl apply -f apps/auth/kubernetes/production/
```

### 12.2 Production Secrets
```bash
# Create production secrets
kubectl create secret generic auth-service-secrets-prod \
  --namespace personal-health-assistant-prod \
  --from-file=secrets/
```

### 12.3 Production Monitoring
```bash
# Deploy production monitoring
helm install prometheus-prod prometheus-community/kube-prometheus-stack \
  --namespace monitoring-prod \
  --create-namespace \
  --values production-monitoring-values.yaml
```

## Troubleshooting

### Common Issues

#### 1. Pipeline Failures
```bash
# Check pipeline logs
# Go to GitHub Actions → Workflows → View logs

# Common fixes:
# - Verify secrets are correctly set
# - Check Kubernetes cluster connectivity
# - Verify Docker registry access
```

#### 2. Deployment Issues
```bash
# Check pod status
kubectl get pods -n personal-health-assistant

# Check pod logs
kubectl logs -f deployment/auth-service -n personal-health-assistant

# Check events
kubectl get events -n personal-health-assistant --sort-by='.lastTimestamp'
```

#### 3. Monitoring Issues
```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
# Open http://localhost:9090

# Check Grafana connectivity
kubectl port-forward -n monitoring svc/grafana 3000:80
# Open http://localhost:3000
```

#### 4. Security Scanning Issues
```bash
# Run security scans locally
bandit -r apps/auth/
safety check
trivy fs .
```

### Debug Commands
```bash
# Get cluster info
kubectl cluster-info

# Check node resources
kubectl top nodes

# Check pod resources
kubectl top pods -n personal-health-assistant

# Check ingress status
kubectl get ingress -n personal-health-assistant

# Check service endpoints
kubectl get endpoints -n personal-health-assistant
```

## Maintenance

### Regular Tasks

#### Daily
- Monitor pipeline execution
- Check deployment health
- Review security alerts

#### Weekly
- Update dependencies
- Review monitoring dashboards
- Check resource usage

#### Monthly
- Update security tools
- Review and update secrets
- Performance testing

#### Quarterly
- Security audit
- Compliance review
- Infrastructure review

### Backup and Recovery
```bash
# Backup Kubernetes resources
kubectl get all -n personal-health-assistant -o yaml > backup.yaml

# Backup secrets
kubectl get secrets -n personal-health-assistant -o yaml > secrets-backup.yaml

# Backup monitoring data
# Configure Prometheus retention and backup
```

## Security Considerations

### Access Control
- Use RBAC for Kubernetes access
- Implement least privilege principle
- Regular access reviews

### Secret Management
- Use Kubernetes secrets or external secret managers
- Rotate secrets regularly
- Encrypt secrets at rest

### Network Security
- Use network policies
- Implement ingress/egress rules
- Monitor network traffic

### Compliance
- HIPAA compliance for healthcare data
- GDPR compliance for user data
- Regular compliance audits

## Support

### Documentation
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

### Community
- GitHub Issues for bug reports
- GitHub Discussions for questions
- Slack channel for real-time support

### Professional Support
- Contact DevOps team for infrastructure issues
- Contact Security team for security concerns
- Contact Compliance team for compliance questions

---

**Last Updated**: January 2024  
**Version**: 1.0.0  
**Maintainer**: DevOps Team 