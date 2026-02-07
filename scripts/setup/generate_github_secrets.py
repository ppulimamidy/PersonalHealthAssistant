#!/usr/bin/env python3
"""
GitHub Secrets Generator for Authentication Service CI/CD

This script helps generate the necessary secrets for the GitHub Actions CI/CD pipeline.
"""

import secrets
import base64
import json
import os
from pathlib import Path

def generate_jwt_secret():
    """Generate a secure JWT secret key"""
    return secrets.token_urlsafe(32)

def generate_encryption_key():
    """Generate a secure encryption key"""
    return secrets.token_urlsafe(32)

def create_sample_kubeconfig():
    """Create a sample kubeconfig for testing"""
    sample_config = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [
            {
                "name": "sample-cluster",
                "cluster": {
                    "server": "https://sample-cluster.example.com",
                    "certificate-authority-data": "sample-ca-data"
                }
            }
        ],
        "users": [
            {
                "name": "sample-user",
                "user": {
                    "token": "sample-token"
                }
            }
        ],
        "contexts": [
            {
                "name": "sample-context",
                "context": {
                    "cluster": "sample-cluster",
                    "user": "sample-user"
                }
            }
        ],
        "current-context": "sample-context"
    }
    return json.dumps(sample_config, indent=2)

def main():
    """Generate GitHub secrets configuration"""
    
    print("🔐 GitHub Secrets Generator for Authentication Service")
    print("=" * 60)
    
    # Generate secure secrets
    jwt_secret = generate_jwt_secret()
    encryption_key = generate_encryption_key()
    
    # Create sample kubeconfig
    sample_kubeconfig = create_sample_kubeconfig()
    kubeconfig_base64 = base64.b64encode(sample_kubeconfig.encode()).decode()
    
    # Define all required secrets
    secrets_config = {
        "KUBE_CONFIG_DEV": {
            "value": kubeconfig_base64,
            "description": "Base64 encoded kubeconfig for development environment",
            "required": True
        },
        "KUBE_CONFIG_STAGING": {
            "value": kubeconfig_base64,
            "description": "Base64 encoded kubeconfig for staging environment",
            "required": True
        },
        "KUBE_CONFIG_PROD": {
            "value": kubeconfig_base64,
            "description": "Base64 encoded kubeconfig for production environment",
            "required": True
        },
        "DOCKER_REGISTRY_TOKEN": {
            "value": "your-docker-registry-token",
            "description": "Docker registry authentication token",
            "required": True
        },
        "SLACK_WEBHOOK_URL": {
            "value": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
            "description": "Slack webhook URL for notifications",
            "required": False
        },
        "SENTRY_DSN": {
            "value": "https://your-sentry-dsn@sentry.io/project-id",
            "description": "Sentry DSN for error tracking",
            "required": False
        },
        "JWT_SECRET_KEY": {
            "value": jwt_secret,
            "description": "Secure JWT secret key for token signing",
            "required": True
        },
        "ENCRYPTION_KEY": {
            "value": encryption_key,
            "description": "Encryption key for sensitive data",
            "required": True
        }
    }
    
    print("\n📋 Required GitHub Secrets:")
    print("-" * 40)
    
    for secret_name, config in secrets_config.items():
        status = "🔴 REQUIRED" if config["required"] else "🟡 OPTIONAL"
        print(f"\n{status} - {secret_name}")
        print(f"   Description: {config['description']}")
        print(f"   Value: {config['value']}")
        print(f"   Length: {len(config['value'])} characters")
    
    # Create secrets file for reference
    secrets_file = Path("github-secrets-reference.json")
    with open(secrets_file, 'w') as f:
        json.dump(secrets_config, f, indent=2)
    
    print(f"\n💾 Secrets reference saved to: {secrets_file}")
    
    print("\n📝 Instructions to add secrets in GitHub:")
    print("1. Go to your GitHub repository")
    print("2. Click Settings → Secrets and variables → Actions")
    print("3. Click 'New repository secret'")
    print("4. Add each secret above with the exact name and value")
    
    print("\n⚠️  Important Notes:")
    print("- Keep these secrets secure and never commit them to version control")
    print("- Update the kubeconfig values with your actual cluster configurations")
    print("- Replace placeholder values with your actual service credentials")
    print("- The JWT and encryption keys are randomly generated - keep them safe!")

if __name__ == "__main__":
    main() 