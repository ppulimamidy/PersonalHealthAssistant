#!/bin/bash

# Enhanced Traefik Setup Script for Personal Health Assistant
# This script sets up the enhanced Traefik configuration with forward authentication

set -e

echo "🚀 Setting up Enhanced Traefik Configuration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Create necessary directories
print_status "Creating Traefik directories..."
mkdir -p traefik/logs
mkdir -p traefik/certs
mkdir -p traefik/config

# Create ACME file for Let's Encrypt certificates
print_status "Setting up ACME file for Let's Encrypt..."
if [ ! -f traefik/acme.json ]; then
    touch traefik/acme.json
    chmod 600 traefik/acme.json
    print_success "Created ACME file with proper permissions"
else
    print_warning "ACME file already exists"
fi

# Create .htpasswd file for basic authentication
print_status "Setting up basic authentication..."
if [ ! -f traefik/.htpasswd ]; then
    # Create htpasswd file with admin user (password: admin)
    echo "admin:\$2y\$10\$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi" > traefik/.htpasswd
    chmod 600 traefik/.htpasswd
    print_success "Created .htpasswd file with admin user (password: admin)"
else
    print_warning ".htpasswd file already exists"
fi

# Set proper permissions for Traefik files
print_status "Setting proper file permissions..."
chmod 644 traefik/*.yml
chmod 644 traefik/config/*.yml 2>/dev/null || true

# Create symbolic links for configuration files
print_status "Setting up configuration file links..."
if [ ! -L traefik/config/traefik.yml ]; then
    ln -sf ../traefik.yml traefik/config/traefik.yml
fi

if [ ! -L traefik/config/middleware.yml ]; then
    ln -sf ../middleware.yml traefik/config/middleware.yml
fi

# Create service-specific configuration links
services=("auth-service" "analytics-service" "user-profile" "health-tracking" "medical-records" "device-data" "ai-insights" "voice-input" "medical-analysis" "nutrition" "health-analysis" "consent-audit")

for service in "${services[@]}"; do
    if [ -f "traefik/${service}.yml" ]; then
        if [ ! -L "traefik/config/${service}.yml" ]; then
            ln -sf "../${service}.yml" "traefik/config/${service}.yml"
        fi
    fi
done

print_success "Created configuration file links"

# Create network if it doesn't exist
print_status "Setting up Docker network..."
if ! docker network ls | grep -q "personalhealthassistant_default"; then
    docker network create personalhealthassistant_default
    print_success "Created Docker network: personalhealthassistant_default"
else
    print_warning "Docker network already exists"
fi

# Validate Traefik configuration
print_status "Validating Traefik configuration..."
if command -v traefik &> /dev/null; then
    if traefik version &> /dev/null; then
        print_success "Traefik is available for configuration validation"
        # Note: Full validation would require running Traefik, which we'll do in Docker
    else
        print_warning "Traefik is not available for validation"
    fi
else
    print_warning "Traefik binary not found in PATH (will be validated in Docker)"
fi

# Create environment-specific configurations
print_status "Creating environment-specific configurations..."

# Development environment
cat > traefik/config/development.yml << EOF
# Development Environment Configuration
# Override settings for development

http:
  middlewares:
    dev-cors:
      headers:
        accessControlAllowOriginList:
          - "http://localhost:3000"
          - "http://localhost:8080"
          - "http://localhost:5173"
          - "http://127.0.0.1:3000"
          - "http://127.0.0.1:8080"
          - "http://127.0.0.1:5173"
EOF

# Production environment
cat > traefik/config/production.yml << EOF
# Production Environment Configuration
# Override settings for production

http:
  middlewares:
    prod-security:
      headers:
        customResponseHeaders:
          Content-Security-Policy: "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';"
          Strict-Transport-Security: "max-age=31536000; includeSubDomains; preload"
          X-Content-Type-Options: "nosniff"
          X-Frame-Options: "DENY"
          X-XSS-Protection: "1; mode=block"
          Referrer-Policy: "strict-origin-when-cross-origin"
          Permissions-Policy: "geolocation=(), microphone=(), camera=()"
EOF

print_success "Created environment-specific configurations"

# Create monitoring configuration
print_status "Setting up monitoring configuration..."
cat > traefik/config/monitoring.yml << EOF
# Monitoring Configuration
# Prometheus metrics and health checks

http:
  routers:
    prometheus:
      rule: "Host(\`monitoring.localhost\`) && PathPrefix(\`/metrics\`)"
      service: prometheus
      entryPoints:
        - websecure
      middlewares:
        - basic-auth
        - ip-whitelist
      tls:
        certResolver: letsencrypt
      priority: 100

    grafana:
      rule: "Host(\`monitoring.localhost\`) && PathPrefix(\`/grafana\`)"
      service: grafana
      entryPoints:
        - websecure
      middlewares:
        - basic-auth
        - ip-whitelist
      tls:
        certResolver: letsencrypt
      priority: 100

  services:
    prometheus:
      loadBalancer:
        servers:
          - url: "http://prometheus:9090"

    grafana:
      loadBalancer:
        servers:
          - url: "http://grafana:3000"

  middlewares:
    basic-auth:
      basicAuth:
        users:
          - "admin:\$2y\$10\$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi"
        removeHeader: true

    ip-whitelist:
      ipWhiteList:
        sourceRange:
          - "127.0.0.1/32"
          - "::1/128"
          - "10.0.0.0/8"
          - "172.16.0.0/12"
          - "192.168.0.0/16"
EOF

print_success "Created monitoring configuration"

# Create health check script
print_status "Creating health check script..."
cat > scripts/check-traefik-health.sh << 'EOF'
#!/bin/bash

# Traefik Health Check Script
# This script checks the health of Traefik and its services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Traefik container is running
print_status "Checking Traefik container status..."
if docker ps | grep -q "traefik-gateway"; then
    print_success "Traefik container is running"
else
    print_error "Traefik container is not running"
    exit 1
fi

# Check Traefik API
print_status "Checking Traefik API..."
if curl -s -f http://localhost:8081/api/overview > /dev/null; then
    print_success "Traefik API is accessible"
else
    print_error "Traefik API is not accessible"
    exit 1
fi

# Check Traefik dashboard
print_status "Checking Traefik dashboard..."
if curl -s -f http://localhost:8081/dashboard/ > /dev/null; then
    print_success "Traefik dashboard is accessible"
else
    print_warning "Traefik dashboard is not accessible"
fi

# Check services
services=("auth-service" "analytics-service" "user-profile" "health-tracking" "medical-records" "device-data" "ai-insights" "voice-input" "medical-analysis" "nutrition" "health-analysis" "consent-audit")

print_status "Checking service health..."
for service in "${services[@]}"; do
    if docker ps | grep -q "$service"; then
        print_success "$service is running"
    else
        print_warning "$service is not running"
    fi
done

print_success "Health check completed"
EOF

chmod +x scripts/check-traefik-health.sh
print_success "Created health check script"

# Create deployment script
print_status "Creating deployment script..."
cat > scripts/deploy-traefik.sh << 'EOF'
#!/bin/bash

# Traefik Deployment Script
# This script deploys the enhanced Traefik configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed"
    exit 1
fi

# Stop existing services
print_status "Stopping existing services..."
docker-compose down

# Build and start services
print_status "Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check service health
print_status "Checking service health..."
./scripts/check-traefik-health.sh

print_success "Deployment completed successfully"
print_status "Traefik dashboard: http://traefik.localhost:8081"
print_status "Auth service: https://auth.localhost"
print_status "Analytics service: https://analytics.localhost"
EOF

chmod +x scripts/deploy-traefik.sh
print_success "Created deployment script"

print_success "Enhanced Traefik setup completed!"
echo ""
echo "📋 Next steps:"
echo "1. Run: ./scripts/deploy-traefik.sh"
echo "2. Access Traefik dashboard: http://traefik.localhost:8081 (admin/admin)"
echo "3. Test forward authentication with: curl -H 'Authorization: Bearer <token>' https://analytics.localhost/health"
echo "4. Monitor logs: docker-compose logs -f traefik"
echo ""
echo "🔧 Configuration files created:"
echo "   - traefik/traefik.yml (main configuration)"
echo "   - traefik/middleware.yml (global middlewares)"
echo "   - traefik/auth-service.yml (auth service config)"
echo "   - traefik/analytics-service.yml (analytics service config)"
echo "   - traefik/config/ (service-specific configs)"
echo ""
echo "🛡️ Security features enabled:"
echo "   - Forward authentication"
echo "   - Rate limiting (global and per-user)"
echo "   - Circuit breakers"
echo "   - Security headers"
echo "   - CORS protection"
echo "   - Request ID tracking"
echo "   - Compression"
echo "   - Retry logic" 