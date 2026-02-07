# 🚀 Deployment Next Steps - Authentication Service

## ✅ What's Already Done

- ✅ Authentication service code implemented
- ✅ CI/CD pipeline configured
- ✅ Kubernetes manifests created
- ✅ Docker Desktop Kubernetes enabled
- ✅ Helm installed and configured
- ✅ Namespaces created
- ✅ Kubeconfig generated

## 📋 GitHub Secrets Configuration

### Required Secrets to Add

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

#### 🔴 REQUIRED Secrets:

**KUBE_CONFIG_DEV**
```
Name: KUBE_CONFIG_DEV
Value: YXBpVmVyc2lvbjogdjEKY2x1c3RlcnM6Ci0gY2x1c3RlcjoKICAgIGNlcnRpZmljYXRlLWF1dGhvcml0eS1kYXRhOiBMUzB0TFMxQ1JVZEpUaUJEUlZKVVNVWkpRMEZVUlMwdExTMHRDazFKU1VSQ2VrTkRRV1VyWjBGM1NVSkJaMGxKWTFGR0wzSnBiMmRGY2tGM1JGRlpTa3R2V2tsb2RtTk9RVkZGVEVKUlFYZEdWRVZVVFVKRlIwRXhWVVVLUVhoTlMyRXpWbWxhV0VwMVdsaFNiR042UVdkR2R6QjVUbFJCTWsxcVFYbE5WRVY2VFdwT1lVZEJPSGxOVkVreFRVUlZlVTU2U1hoTlZHZDVUVEZ2ZHdwR1ZFVlVUVUpGUjBFeFZVVkJlRTFMWVROV2FWcFlTblZhV0ZKc1kzcERRMEZUU1hkRVVWbEtTMjlhU1doMlkwNUJVVVZDUWxGQlJHZG5SVkJCUkVORENrRlJiME5uWjBWQ1FVMXdUMDVWZG00NGEwb3JSek55VURjemFWTnlibTltT1c1MlkwTnNhMGQzUTI5TVNVMVlUa0l5V25WMVlXZGtOV052WTJaMk9VZ0tSVnB5TUhkSWJuUjBURUpHTmt0ck5YWkZkbkpUVldaT2MweE9Na0V3WmpReU16SnJTRFE0TW5Wc2R6SkVWVmhVZVZWTVpXeFVaalJ1ZDNadGJEVmtPUXBJUkdzeVZubDVka05qTkRVdk1FSTFkbmhaYW5nMFdUTm1OMDV1YUcxdEt6QlpUVWt2VG1GMksyNUNkMHRCUjI5TVozZ3ZaemhDYlZkQ2RsSm5kRWQxQ2l0cGJVNUpRbm8yV1UxbVkwSlZURkphWjA4MFpIQm5PRVJQWkhFdmFYUnFNbUZOWTI1aGJGVkdlVVJUWm0xQllqUTRaRFZWVlRsaGFVbHdLM1l2UzJzS1RHeGpSWFV5VUhWbWVWTnFUMmwxUjNkME5EbDRTM1U1VGtwVFJYQm1aM1Y1UTJwNk5GQjJZbTEwS3paallVSTNiRWhyZEdsa1QxaENZMmxqYmtWc2JRcHRaWFZwVTNaQlFUTTFiWGs1WWk5VE1rMWpUbUZFYTJGemNEbHBWbTB3UTBGM1JVRkJZVTVhVFVaamQwUm5XVVJXVWpCUVFWRklMMEpCVVVSQlowdHJDazFCT0VkQk1WVmtSWGRGUWk5M1VVWk5RVTFDUVdZNGQwaFJXVVJXVWpCUFFrSlpSVVpMWTNsTmFsVkhVQzlCU0Rod2R6aHVabklyZGpZeE1UaEJWbTRLVFVKVlIwRXhWV1JGVVZGUFRVRjVRME50ZERGWmJWWjVZbTFXTUZwWVRYZEVVVmxLUzI5YVNXaDJZMDVCVVVWTVFsRkJSR2RuUlVKQlFURldhM2xuUkFwdE9WTmtSMDVQV0ZKaVpYbERRV1kyTkdGNU9HRklZbFo0T1dOWlJXd3JLMkpLUW5wRGJVaDNhVWt2YUd0MVoyOXNZMVkzWVZOUU1XWlNUV2QxTWpCc0NrSjFlVUoyTjJOaFVscGlLMWhTVVRWNVlsUkphbU5oYnpOblRWRmhOakpEWkhkclVXdGtla0ZyTlRjeVR5OUZSMnQwVm1JclNIcFZUSE5GSzA5WWFuSUtSRTVNYjJVMVRuQmhkUzlRYTJweWRFOXJUR1ZLUkRNM1NHeFFVVkJvTUdaWlQwRnhTMUpYTXpCVVMweEJUek1yVDI1V1pqTXdRMnBsTjFOSE1YcGpRZ3BLWXk5UVR6Z3JVMGhLVXpSd0wwSlFWVzlJYVVkUGIycERiRmMxTW1WRGJWQTFTRGxRSzFZck56bFdZbUpJU1RFMk5XcEhPVXBrU1RKNVMwRmlSbkZOQ2tWR1lVTm9kMGxhUW5CRldXTklRbkJ3VmtORlVXTXljR0pITjNJMEwyaE9hRUpXVUhKdVIwZFdXR1I1YVdsSlZXTkplbTFNWkZvNWJXUldXR05NUzFVS2VEVlBlVlJNTDFZd1MxZDNaV0k0UFFvdExTMHRMVVZPUkNCRFJWSlVTVVpKUTBGVVJTMHRMUzB0Q2c9PQogICAgc2VydmVyOiBodHRwczovLzEyNy4wLjAuMTo2NDQzCiAgbmFtZTogZG9ja2VyLWRlc2t0b3AKY29udGV4dHM6Ci0gY29udGV4dDoKICAgIGNsdXN0ZXI6IGRvY2tlci1kZXNrdG9wCiAgICB1c2VyOiBkb2NrZXItZGVza3RvcAogIG5hbWU6IGRvY2tlci1kZXNrdG9wCmN1cnJlbnQtY29udGV4dDogZG9ja2VyLWRlc2t0b3AKa2luZDogQ29uZmlnCnByZWZlcmVuY2VzOiB7fQp1c2VyczoKLSBuYW1lOiBkb2NrZXItZGVza3RvcAogIHVzZXI6CiAgICBjbGllbnQtY2VydGlmaWNhdGUtZGF0YTogTFMwdExTMUNSVWRKVGlCU1UwRWdVRkpKVmtGVVJTQkxSVmt0TFMwdExRcE5TVWxGY0VGSlFrRkJTME5CVVVWQmNXYzBSVGRwZEdONVJGVkllWEJ5UVU1RFRHSmhjVWwzTkN0eFlsaEhRamx4YkZSMlVuUkpNRnBtY1VkUGJXWnVDbkJSVTJZelJVZEJXVTFYTWtaWlRrTXhNVFptUTJ3eGRGSXlURzlSYjI5UFJXdDBUMDFJV1ZablJ6WXhPRkkyTkhBNFNDdEZZMkppUTJSYU1IaHRlVkFLWlVVd1NHNWhTMGxGYkdoUGEydHZSU3Q1UldoSFEyeEtjR05QZUdWb1kyeFdORVJKTjNWRVFsSXZOamxWVnpKMlNFdGlPWEIzWVhBck1rMVZaemtyZFFwTVZXNXVTalZYV2xCSGFWSnpOR1JsYms4MU5HWnFkelZKVkUxSFEyb3hSSEE1Vnl0V2FGWk1NalppZDFoVVZFNXFZbVUwVUZOUk9EVlhTbFZzY3pOWUNrcDZNbGx3Yld3eFJFOHZOMDlxWjA5M1UwUjZiM0I2UnpSWVlrVlVkSGMwV0dSTU1qQm5kMHBYVFVOM2JIcENjRkZYYjBwSllVZHRaR1ZTV21WcWMyWUtSWFpXTkdkaFJWVjJWV3BHU1RCek0zbDFOVVI2VjNreVRFUXpRV0Z3YkM5eE9IaDZXbmRKUkVGUlFVSkJiMGxDUVVKME16ZEVMekJpVTFwQ2RYRktNUXBaVEhGTVRIUnZTVzVPUlZRMGEybEljRmxVVURreE5TOU5ZM1ZRVEdkT1pFdFZUekJtV1ZnNFduQnZOMFpZUW1kS1dHNVpXazlSZEhSNWMybDRUbGRMQ25GNk9ERlFjMjlDUzFCUU16ZG9aVzF0VEd0M1ZYSlFXVnBUVlhaeFQydHpUeTlvTkhGT1VrUnVjWE51TjBoclozbzNSVzgxYzIxaFZXSlZaVFpTYjBvS2FIaFRaRlIwWlZoSmJVWlpkVzltWlhGaWVEbEdUbVpZT0dKclZGRndjMHMwZURkcVZEazBWemRGVDNaQmRGQkNTRWxpWmpKS01Dc3ZlbGxQTm5wRmFRcHVhR2hTV21rM05qUjVVM2RLTm5WUVVXRnZZVXBZU3psMk1XdG1jRVF2UmpWVmJYQkRlVEF3VGtKNlJEVmlaMVJyTTA5MGVXWk1jRTltZUhKSVQya3dDblJqUTA4NFVrY3ZjVmRoTlRseVYyZEtZVGhCWVdadk1UTmpSbTFCYkhaTlJVVmFiREF5YkdVdk9IcDVSR3RpTmpZd1Z5c3JTMnczVjNsdFREZDJRakFLV1ZKU1pFZGxSVU5uV1VWQmVXeEpiVzF1VDFsV1ltbzJTRFptZDBkSFJsVlhjMDl1YUZoT1ltMWpVMEZXSzFsSE5rVTRMMGt6U1d4dlNVWlRTWFJrYUFvdmR6ZHdLM0JSTTJ0T1dEVXJXRFl5T0VWWVVsZHRkazR3VXpORFlYUmFlbWR2TTNaVFdFeFZlVFo1VUcxaU0yeDRSVmhhVlhaMmR6TXZTMU5tV1hWVUNtVTBVMlJNVDBJeGMxSjFkMFJxV25ReVJsWkhiWE56VkRSQ2JXRTBkRUV3YjNWS1ltcDBlRk16YkRGMWJGWlZZVmQxUkcxNWRXdERaMWxGUVRGNWVGSUtaVlZCYWpGdkszSnVkSEl4UVU0NGRqTlZNSHBpUVdJMFNHZEhjbTk0UWpjeFExRm1jVlpsZVhKV2FXSmhTRFZoVkVWTlNFNWtVRXg0THpaYWVsRktNd3BoWnpoeVQwTkVPVTVrTVZoQlNGRjFVMWRDYVRCRWRreDFNblUxU1RKdFlVdFNhVmRVYTBzemVXMVpLMmQ1V1d4S1RFOWlkblJXUm1aNFJrZFFiSE5oQ201SlpscGxlREZsUWxWd2JWSmxOMWxpVUVVMVozRXpSMlpyVEZBM2FUWmtZbkJUYzNWak9FTm5XVVZCYUVvd1YxZHdVemhZUTNZd1NIWXpTVWhYVEcwS2JFNTFPRWRZWjBWeFlWTnZZak5WUTFGQ1JqVnNSRlpGZG5CRmJHdHNjbFpFUVdKMGFrOWlUVU5UTmtsUVIxa3pZVkZUUzJSb1pFWm1MeTlpWlVsWU5ncHFjU3RWUldaUGJqQmFlbHBRTWlzcmFFVnJOR0YyUm1rNFNtVnBUalZLWldGRk9FUmhlQzk0V2s1YUsweHpTekJsTWtab09YbEtNMk0yVHpBMU1HbE1Dbmc1ZUZKSlZFZ3ZVekoxTkdsVUsxRkdPVTVyTURoclEyZFpSVUZ1TVc5RU9FazNkWFUxZW1zeFdqSkZZWEZRWmxZM05IWjNaVmxpV2tkWFMxUm9XVTBLUkhCNUswVm1VMUJ5T0RjMlRVNVhObGM1V1dOQ1pVbFlabU5LZHpseFNFZ3JMMVJHTldscFVWQlpOM2hQY2xoUUwyRnNla3BLU0ZWSVRGZ3paekpHVndwMVR6WnlhV05RYUZKMlUxaG5Vbk5FTUZBeGRUY3hTVlY1VEdweVZUUjVNakZaZGt0S1YwbHVWMnBYZVV4clNtNWFOamQ1UkROU1VXeDJjekU0UldZekNtTlphVXh5YjAxRFoxbENiMFpQVTB0SlVXVlZWemxCZW1jMVJqVklWa1JOUlhvNGJuQlRha2RZV25GeE1XWjVjbkpFYTNwRlJ5ODVWbGRuTVdkaFRpOEtUMng1YVZwYWNuVlBlbk5ITDJGcldqUXpWSGR5V1VWUWRGUkJlSGxwTDA4NVpHZGxiMk5uTlM5MlZtZHVWbmhRTlVGRVJGRkVSRXd6V2paeE0zaEVlQXBPYkZOdFoyZDVVbTh3V2poNGNEQk9SSFowTW5kVldFZFhWREZuZGlzMEx6UkZTMUUxYldkMlNFSXpNWFZwTUVkd1lWVmpSWGM5UFFvdExTMHRMVVZPUkNCU1UwRWdVRkpKVmtGVVJTQkxSVmt0TFMwdExRbz0K
```

**KUBE_CONFIG_STAGING**
```
Name: KUBE_CONFIG_STAGING
Value: [Same as above]
```

**KUBE_CONFIG_PROD**
```
Name: KUBE_CONFIG_PROD
Value: [Same as above]
```

**DOCKER_REGISTRY_TOKEN**
```
Name: DOCKER_REGISTRY_TOKEN
Value: your-docker-registry-token
```

**JWT_SECRET_KEY**
```
Name: JWT_SECRET_KEY
Value: QaCdqUh5fm9KDP8V7kRI7zCXMtOgtrAAGRCihw9KtSY
```

**ENCRYPTION_KEY**
```
Name: ENCRYPTION_KEY
Value: OkgDVbmYZj3bWo8OxERRrEouFpayH5hL_fSqct0jBgQ
```

#### 🟡 OPTIONAL Secrets:

**SLACK_WEBHOOK_URL**
```
Name: SLACK_WEBHOOK_URL
Value: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

**SENTRY_DSN**
```
Name: SENTRY_DSN
Value: https://your-sentry-dsn@sentry.io/project-id
```

## 🚀 Deploy to Kubernetes

### Step 1: Deploy the Authentication Service

```bash
# Apply Kubernetes manifests
kubectl apply -f apps/auth/kubernetes/secrets.yaml -n personal-health-assistant
kubectl apply -f apps/auth/kubernetes/deployment.yaml -n personal-health-assistant
kubectl apply -f apps/auth/kubernetes/network-policy.yaml -n personal-health-assistant
kubectl apply -f apps/auth/kubernetes/monitoring.yaml -n personal-health-assistant
```

### Step 2: Verify Deployment

```bash
# Check deployment status
kubectl get pods -n personal-health-assistant

# Check services
kubectl get services -n personal-health-assistant

# Check ingress
kubectl get ingress -n personal-health-assistant
```

### Step 3: Test the Service

```bash
# Port forward to access the service locally
kubectl port-forward svc/auth-service 8000:80 -n personal-health-assistant

# Test health endpoint
curl http://localhost:8000/health

# Test metrics endpoint
curl http://localhost:8000/metrics

# Test API documentation
open http://localhost:8000/docs
```

## 🧪 Test the CI/CD Pipeline

### Step 1: Make a Test Commit

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

### Step 2: Monitor Pipeline Execution

1. Go to your GitHub repository
2. Click the **"Actions"** tab
3. Monitor the pipeline execution
4. Check for any failures and fix them

### Step 3: Create Pull Request

1. Go to your GitHub repository
2. Click **"Compare & pull request"** for your test branch
3. Create a pull request to `develop` branch
4. Monitor the pipeline execution

## 📊 Set Up Monitoring

### Step 1: Install Prometheus Stack

```bash
# Install Prometheus and Grafana
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

### Step 2: Access Grafana Dashboard

```bash
# Port forward to Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring

# Access Grafana (default credentials: admin/prom-operator)
open http://localhost:3000
```

### Step 3: Import Dashboard

1. Login to Grafana with `admin` / `prom-operator`
2. Go to **Dashboards** → **Import**
3. Import the dashboard JSON from `monitoring/grafana/provisioning/dashboards/fastapi-dashboard.json`

## 🔧 Useful Commands

### Check Status
```bash
# Check pods
kubectl get pods -n personal-health-assistant

# Check logs
kubectl logs -f deployment/auth-service -n personal-health-assistant

# Check events
kubectl get events -n personal-health-assistant --sort-by='.lastTimestamp'
```

### Port Forwarding
```bash
# Port forward to service
kubectl port-forward svc/auth-service 8000:80 -n personal-health-assistant

# Port forward to Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring
```

### Cleanup
```bash
# Delete deployment
kubectl delete -f apps/auth/kubernetes/ -n personal-health-assistant

# Delete namespace
kubectl delete namespace personal-health-assistant
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Pods Not Starting
```bash
# Check pod status
kubectl get pods -n personal-health-assistant

# Check pod logs
kubectl logs -f deployment/auth-service -n personal-health-assistant

# Check events
kubectl get events -n personal-health-assistant --sort-by='.lastTimestamp'
```

#### 2. Service Not Accessible
```bash
# Check service status
kubectl get svc -n personal-health-assistant

# Check port forwarding
kubectl port-forward svc/auth-service 8000:80 -n personal-health-assistant
```

#### 3. GitHub Actions Failures
- Check workflow logs in GitHub Actions tab
- Verify all secrets are properly configured
- Check kubeconfig values are correct

## 📚 Documentation

- [Authentication Service README](apps/auth/README.md)
- [API Documentation](apps/auth/API_DOCUMENTATION.md)
- [Deployment Guide](apps/auth/DEPLOYMENT_GUIDE.md)
- [Security Guide](apps/auth/SECURITY_GUIDE.md)

## 🎯 Next Steps After Deployment

1. **Configure Domain and SSL**
   - Set up a custom domain for your service
   - Configure SSL certificates
   - Update ingress configuration

2. **Set Up Monitoring Alerts**
   - Configure Prometheus alerting rules
   - Set up notification channels
   - Test alerting functionality

3. **Implement Backup Strategy**
   - Set up database backups
   - Configure backup retention policies
   - Test restore procedures

4. **Security Hardening**
   - Review security policies
   - Implement network policies
   - Set up security scanning

5. **Performance Optimization**
   - Monitor resource usage
   - Optimize container resources
   - Implement horizontal pod autoscaling

---

**Status**: Ready for deployment  
**Last Updated**: January 2024  
**Version**: 1.0.0 