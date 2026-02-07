#!/usr/bin/env python3
"""
Quick Setup for Docker Desktop Kubernetes

This script quickly sets up Docker Desktop Kubernetes for the authentication service.
"""

import subprocess
import base64
import json
import time
from pathlib import Path

def check_docker_running():
    """Check if Docker is running"""
    try:
        subprocess.run(["docker", "version"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_kubernetes_enabled():
    """Check if Kubernetes is enabled in Docker Desktop"""
    try:
        result = subprocess.run([
            "kubectl", "cluster-info"
        ], capture_output=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def wait_for_kubernetes():
    """Wait for Kubernetes to be ready"""
    print("⏳ Waiting for Kubernetes to be ready...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        if check_kubernetes_enabled():
            print("✅ Kubernetes is ready!")
            return True
        
        print(f"⏳ Attempt {attempt + 1}/{max_attempts} - Waiting...")
        time.sleep(10)
    
    print("❌ Kubernetes did not start in time")
    return False

def install_helm():
    """Install Helm package manager"""
    print("📦 Installing Helm...")
    
    try:
        # Check if Helm is already installed
        subprocess.run(["helm", "version"], capture_output=True, check=True)
        print("✅ Helm is already installed")
        return True
    except subprocess.CalledProcessError:
        print("Installing Helm...")
        try:
            # Download and install Helm
            subprocess.run([
                "curl", "https://get.helm.sh/helm-v3.12.0-darwin-amd64.tar.gz", "|", "tar", "xz"
            ], shell=True, check=True)
            
            subprocess.run([
                "sudo", "mv", "darwin-amd64/helm", "/usr/local/bin/"
            ], check=True)
            
            print("✅ Helm installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install Helm: {e}")
            return False

def setup_helm_repos():
    """Setup Helm repositories"""
    print("🔧 Setting up Helm repositories...")
    
    try:
        # Add repositories
        subprocess.run([
            "helm", "repo", "add", "prometheus-community",
            "https://prometheus-community.github.io/helm-charts"
        ], check=True)
        
        subprocess.run([
            "helm", "repo", "add", "grafana",
            "https://grafana.github.io/helm-charts"
        ], check=True)
        
        subprocess.run([
            "helm", "repo", "update"
        ], check=True)
        
        print("✅ Helm repositories configured!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to setup Helm repositories: {e}")
        return False

def create_namespaces():
    """Create required namespaces"""
    print("📁 Creating namespaces...")
    
    namespaces = [
        "personal-health-assistant",
        "monitoring",
        "ingress-nginx"
    ]
    
    for namespace in namespaces:
        try:
            subprocess.run([
                "kubectl", "create", "namespace", namespace
            ], check=True)
            print(f"✅ Created namespace: {namespace}")
        except subprocess.CalledProcessError:
            print(f"⚠️  Namespace {namespace} already exists")

def generate_kubeconfig():
    """Generate kubeconfig for GitHub secrets"""
    print("🔧 Generating kubeconfig...")
    
    try:
        # Get current kubeconfig
        result = subprocess.run([
            "kubectl", "config", "view", "--raw"
        ], capture_output=True, text=True, check=True)
        
        kubeconfig = result.stdout
        
        # Save kubeconfig
        kubeconfig_file = Path("kubeconfig-docker-desktop.yaml")
        with open(kubeconfig_file, 'w') as f:
            f.write(kubeconfig)
        
        print(f"✅ Kubeconfig saved to: {kubeconfig_file}")
        
        # Encode for GitHub secrets
        kubeconfig_base64 = base64.b64encode(kubeconfig.encode()).decode()
        
        print("\n📋 Kubeconfig for GitHub Secrets:")
        print("=" * 50)
        print(f"KUBE_CONFIG_DEV: {kubeconfig_base64}")
        print(f"KUBE_CONFIG_STAGING: {kubeconfig_base64}")
        print(f"KUBE_CONFIG_PROD: {kubeconfig_base64}")
        print("=" * 50)
        
        return kubeconfig_base64
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate kubeconfig: {e}")
        return None

def deploy_auth_service():
    """Deploy the authentication service"""
    print("🚀 Deploying authentication service...")
    
    try:
        # Apply Kubernetes manifests
        manifests = [
            "apps/auth/kubernetes/secrets.yaml",
            "apps/auth/kubernetes/deployment.yaml",
            "apps/auth/kubernetes/network-policy.yaml",
            "apps/auth/kubernetes/monitoring.yaml"
        ]
        
        for manifest in manifests:
            manifest_path = Path(manifest)
            if manifest_path.exists():
                print(f"Applying {manifest}...")
                subprocess.run([
                    "kubectl", "apply", "-f", str(manifest_path),
                    "-n", "personal-health-assistant"
                ], check=True)
            else:
                print(f"⚠️  Manifest not found: {manifest}")
        
        print("✅ Authentication service deployed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to deploy authentication service: {e}")
        return False

def verify_deployment():
    """Verify the deployment"""
    print("🔍 Verifying deployment...")
    
    try:
        # Check pods
        result = subprocess.run([
            "kubectl", "get", "pods", "-n", "personal-health-assistant"
        ], capture_output=True, text=True, check=True)
        
        print("✅ Pods:")
        print(result.stdout)
        
        # Check services
        result = subprocess.run([
            "kubectl", "get", "services", "-n", "personal-health-assistant"
        ], capture_output=True, text=True, check=True)
        
        print("✅ Services:")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment verification failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Quick Setup for Docker Desktop Kubernetes")
    print("=" * 50)
    
    # Check Docker
    if not check_docker_running():
        print("❌ Docker is not running. Please start Docker Desktop.")
        return False
    
    print("✅ Docker is running")
    
    # Check Kubernetes
    if not check_kubernetes_enabled():
        print("❌ Kubernetes is not enabled in Docker Desktop.")
        print("Please enable Kubernetes in Docker Desktop settings:")
        print("1. Open Docker Desktop")
        print("2. Go to Settings → Kubernetes")
        print("3. Check 'Enable Kubernetes'")
        print("4. Click 'Apply & Restart'")
        print("5. Wait for restart to complete")
        print("6. Run this script again")
        return False
    
    print("✅ Kubernetes is enabled")
    
    # Wait for Kubernetes to be ready
    if not wait_for_kubernetes():
        return False
    
    # Install Helm
    if not install_helm():
        return False
    
    # Setup Helm repositories
    if not setup_helm_repos():
        return False
    
    # Create namespaces
    create_namespaces()
    
    # Generate kubeconfig
    kubeconfig_base64 = generate_kubeconfig()
    if not kubeconfig_base64:
        return False
    
    # Deploy authentication service
    if not deploy_auth_service():
        return False
    
    # Verify deployment
    if not verify_deployment():
        return False
    
    print("\n🎉 Quick Setup Complete!")
    print("=" * 50)
    print("✅ Docker Desktop Kubernetes is ready")
    print("✅ Helm is installed and configured")
    print("✅ Namespaces are created")
    print("✅ Authentication service is deployed")
    print("✅ Kubeconfig is generated")
    
    print("\n📝 Next Steps:")
    print("1. Copy the kubeconfig values above")
    print("2. Add them to your GitHub repository secrets")
    print("3. Test the deployment:")
    print("   kubectl port-forward svc/auth-service 8000:80 -n personal-health-assistant")
    print("   curl http://localhost:8000/health")
    
    print("\n🔧 Useful Commands:")
    print("- Check pods: kubectl get pods -n personal-health-assistant")
    print("- Check logs: kubectl logs -f deployment/auth-service -n personal-health-assistant")
    print("- Port forward: kubectl port-forward svc/auth-service 8000:80 -n personal-health-assistant")
    print("- Delete deployment: kubectl delete -f apps/auth/kubernetes/ -n personal-health-assistant")
    
    return True

if __name__ == "__main__":
    main() 