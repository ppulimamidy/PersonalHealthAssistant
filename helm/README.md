# Personal Health Assistant Helm Charts

Kubernetes Helm charts for deploying the Personal Health Assistant microservices platform.

## Prerequisites

- Kubernetes 1.25+
- Helm 3.10+
- PV provisioner support (for persistence)
- Ingress controller (nginx-ingress recommended)

## Quick Start

```bash
# Add required Helm repositories
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add neo4j https://helm.neo4j.com/neo4j
helm repo update

# Create namespace
kubectl create namespace health-assistant

# Create secrets (replace with your values)
kubectl create secret generic health-assistant-secrets \
  --namespace health-assistant \
  --from-literal=DATABASE_URL="postgresql://user:pass@host:5432/db" \
  --from-literal=JWT_SECRET_KEY="your-secret-key" \
  --from-literal=OPENAI_API_KEY="your-openai-key"

# Install the chart
helm install health-assistant ./personal-health-assistant \
  --namespace health-assistant \
  --values ./personal-health-assistant/values.yaml

# Or with custom values
helm install health-assistant ./personal-health-assistant \
  --namespace health-assistant \
  -f custom-values.yaml
```

## Configuration

### Key Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `environment` | Deployment environment | `production` |
| `namespace` | Kubernetes namespace | `health-assistant` |
| `ingress.enabled` | Enable ingress | `true` |
| `postgresql.enabled` | Deploy PostgreSQL | `true` |
| `redis.enabled` | Deploy Redis | `true` |
| `kafka.enabled` | Deploy Kafka | `true` |
| `monitoring.enabled` | Deploy Prometheus/Grafana | `true` |

### Service Configuration

Each service can be configured with:

```yaml
serviceName:
  enabled: true
  replicaCount: 2
  image:
    repository: service-name
    tag: latest
  port: 8000
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "500m"
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
```

## Upgrade

```bash
helm upgrade health-assistant ./personal-health-assistant \
  --namespace health-assistant \
  -f custom-values.yaml
```

## Uninstall

```bash
helm uninstall health-assistant --namespace health-assistant
kubectl delete namespace health-assistant
```

## Production Considerations

1. **Secrets Management**: Use external secrets (AWS Secrets Manager, Vault)
2. **TLS**: Configure proper TLS certificates via cert-manager
3. **Persistence**: Configure appropriate storage classes
4. **Resource Limits**: Adjust based on actual usage patterns
5. **Network Policies**: Enable and customize for security
6. **Monitoring**: Configure alerting rules in Prometheus
