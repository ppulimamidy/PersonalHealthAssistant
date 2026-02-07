#!/usr/bin/env python3
"""
DigitalOcean Kubernetes Cluster Setup

This script helps set up a DigitalOcean Kubernetes cluster.
DigitalOcean offers a free trial with $200 credit.
"""

import subprocess
import json
import os
import time
from pathlib import Path

def check_doctl_installed():
    """Check if doctl CLI is installed"""
    try:
        subprocess.run(["doctl", "version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_doctl():
    """Install DigitalOcean CLI"""
    print("📥 Installing DigitalOcean CLI...")
    
    if os.name == 'nt':  # Windows
        print("Please download from: https://github.com/digitalocean/doctl/releases")
        return False
    else:  # macOS/Linux
        try:
            # Download doctl
            subprocess.run([
                "curl", "-sL", "https://github.com/digitalocean/doctl/releases/latest/download/doctl-1.92.0-linux-amd64.tar.gz",
                "|", "tar", "-xzv"
            ], shell=True, check=True)
            
            # Move to PATH
            subprocess.run([
                "sudo", "mv", "doctl", "/usr/local/bin"
            ], check=True)
            
            print("✅ doctl installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("Failed to install doctl. Please install manually.")
            return False

def authenticate_doctl():
    """Authenticate with DigitalOcean"""
    print("🔐 Authenticating with DigitalOcean...")
    
    try:
        # Check if already authenticated
        result = subprocess.run([
            "doctl", "account", "get"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Already authenticated with DigitalOcean")
            return True
        
        # Request authentication
        print("Please enter your DigitalOcean API token:")
        print("Get it from: https://cloud.digitalocean.com/account/api/tokens")
        
        subprocess.run([
            "doctl", "auth", "init"
        ], check=True)
        
        print("✅ Authentication successful!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Authentication failed: {e}")
        return False

def create_doks_cluster(cluster_name="auth-service-cluster"):
    """Create a DigitalOcean Kubernetes cluster"""
    print(f"🚀 Creating DigitalOcean Kubernetes cluster: {cluster_name}")
    
    # Create cluster with minimal resources
    cluster_config = [
        "doctl", "kubernetes", "cluster", "create", cluster_name,
        "--region", "nyc1",  # New York region
        "--size", "s-1vcpu-1gb",  # Smallest size
        "--count", "1",  # Single node
        "--wait"
    ]
    
    try:
        subprocess.run(cluster_config, check=True)
        print("✅ DigitalOcean Kubernetes cluster created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create cluster: {e}")
        return False

def get_cluster_credentials(cluster_name):
    """Get cluster credentials"""
    print(f"🔑 Getting credentials for cluster: {cluster_name}")
    
    try:
        subprocess.run([
            "doctl", "kubernetes", "cluster", "kubeconfig", "save", cluster_name
        ], check=True)
        print("✅ Cluster credentials configured!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get credentials: {e}")
        return False

def verify_cluster():
    """Verify cluster is working"""
    print("🔍 Verifying cluster...")
    
    try:
        # Check nodes
        result = subprocess.run([
            "kubectl", "get", "nodes"
        ], capture_output=True, text=True, check=True)
        
        print("✅ Cluster nodes:")
        print(result.stdout)
        
        # Check cluster info
        result = subprocess.run([
            "kubectl", "cluster-info"
        ], capture_output=True, text=True, check=True)
        
        print("✅ Cluster info:")
        print(result.stdout)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Cluster verification failed: {e}")
        return False

def install_helm():
    """Install Helm package manager"""
    print("📦 Installing Helm...")
    
    try:
        # Add Helm repositories
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
        
        print("✅ Helm installed and configured!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Helm: {e}")
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

def install_ingress_controller():
    """Install NGINX Ingress Controller"""
    print("🌐 Installing NGINX Ingress Controller...")
    
    try:
        subprocess.run([
            "helm", "install", "ingress-nginx", "ingress-nginx/ingress-nginx",
            "--namespace", "ingress-nginx",
            "--create-namespace",
            "--set", "controller.service.type=LoadBalancer"
        ], check=True)
        
        print("✅ Ingress controller installed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install ingress controller: {e}")
        return False

def get_external_ip():
    """Get external IP of ingress controller"""
    print("🌍 Getting external IP...")
    
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            result = subprocess.run([
                "kubectl", "get", "service", "ingress-nginx-controller",
                "-n", "ingress-nginx",
                "-o", "jsonpath='{.status.loadBalancer.ingress[0].ip}'"
            ], capture_output=True, text=True, check=True)
            
            external_ip = result.stdout.strip("'")
            if external_ip and external_ip != "<pending>":
                print(f"✅ External IP: {external_ip}")
                return external_ip
            
            print(f"⏳ Waiting for external IP... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(30)
            
        except subprocess.CalledProcessError:
            print(f"⏳ Waiting for service... (attempt {attempt + 1}/{max_attempts})")
            time.sleep(30)
    
    print("❌ Failed to get external IP")
    return None

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
        kubeconfig_file = Path("kubeconfig-digitalocean.yaml")
        with open(kubeconfig_file, 'w') as f:
            f.write(kubeconfig)
        
        print(f"✅ Kubeconfig saved to: {kubeconfig_file}")
        
        # Encode for GitHub secrets
        import base64
        kubeconfig_base64 = base64.b64encode(kubeconfig.encode()).decode()
        
        print("\n📋 Kubeconfig for GitHub Secrets:")
        print(f"KUBE_CONFIG_DEV: {kubeconfig_base64}")
        print(f"KUBE_CONFIG_STAGING: {kubeconfig_base64}")
        print(f"KUBE_CONFIG_PROD: {kubeconfig_base64}")
        
        return kubeconfig_base64
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate kubeconfig: {e}")
        return None

def main():
    """Main setup function"""
    print("🚀 DigitalOcean Kubernetes Cluster Setup")
    print("=" * 50)
    
    # Check if doctl is installed
    if not check_doctl_installed():
        print("❌ DigitalOcean CLI not found")
        if not install_doctl():
            return False
    
    # Authenticate with DigitalOcean
    if not authenticate_doctl():
        return False
    
    # Create cluster
    cluster_name = "auth-service-cluster"
    if not create_doks_cluster(cluster_name):
        return False
    
    # Get credentials
    if not get_cluster_credentials(cluster_name):
        return False
    
    # Verify cluster
    if not verify_cluster():
        return False
    
    # Install Helm
    if not install_helm():
        return False
    
    # Create namespaces
    create_namespaces()
    
    # Install ingress controller
    if not install_ingress_controller():
        return False
    
    # Get external IP
    external_ip = get_external_ip()
    
    # Generate kubeconfig
    kubeconfig_base64 = generate_kubeconfig()
    
    print("\n🎉 DigitalOcean Kubernetes Cluster Setup Complete!")
    print("=" * 50)
    print(f"Cluster Name: {cluster_name}")
    print(f"Region: nyc1")
    if external_ip:
        print(f"External IP: {external_ip}")
    
    print("\n📝 Next Steps:")
    print("1. Update GitHub secrets with the kubeconfig above")
    print("2. Deploy the authentication service")
    print("3. Configure monitoring and alerting")
    
    print("\n💰 Cost Information:")
    print("- DigitalOcean offers $200 free trial")
    print("- s-1vcpu-1gb droplets cost ~$6/month")
    print("- Monitor usage in DigitalOcean Console")
    
    return True

if __name__ == "__main__":
    main() 