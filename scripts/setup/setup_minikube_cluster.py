#!/usr/bin/env python3
"""
Minikube Local Kubernetes Cluster Setup

This script helps set up a local Minikube cluster for development.
Minikube is free and runs locally on your machine.
"""

import subprocess
import json
import os
import time
from pathlib import Path

def check_minikube_installed():
    """Check if Minikube is installed"""
    try:
        subprocess.run(["minikube", "version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_minikube():
    """Install Minikube"""
    print("📥 Installing Minikube...")
    
    if os.name == 'nt':  # Windows
        print("Please download from: https://minikube.sigs.k8s.io/docs/start/")
        return False
    else:  # macOS/Linux
        try:
            # Download and install Minikube
            subprocess.run([
                "curl", "-LO", "https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64"
            ], check=True)
            
            subprocess.run([
                "sudo", "install", "minikube-linux-amd64", "/usr/local/bin/minikube"
            ], check=True)
            
            print("✅ Minikube installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("Failed to install Minikube. Please install manually.")
            return False

def check_kubectl_installed():
    """Check if kubectl is installed"""
    try:
        subprocess.run(["kubectl", "version", "--client"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_kubectl():
    """Install kubectl"""
    print("📥 Installing kubectl...")
    
    try:
        # Download kubectl
        subprocess.run([
            "curl", "-LO", "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
        ], check=True)
        
        # Make executable and move to PATH
        subprocess.run(["chmod", "+x", "kubectl"], check=True)
        subprocess.run(["sudo", "mv", "kubectl", "/usr/local/bin/"], check=True)
        
        print("✅ kubectl installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("Failed to install kubectl. Please install manually.")
        return False

def start_minikube_cluster():
    """Start Minikube cluster"""
    print("🚀 Starting Minikube cluster...")
    
    try:
        # Start cluster with more resources
        subprocess.run([
            "minikube", "start",
            "--cpus", "2",
            "--memory", "4096",
            "--disk-size", "20g",
            "--driver", "docker"
        ], check=True)
        
        print("✅ Minikube cluster started successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start cluster: {e}")
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
        # Download and install Helm
        subprocess.run([
            "curl", "https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz", "|", "tar", "xz"
        ], shell=True, check=True)
        
        subprocess.run([
            "sudo", "mv", "linux-amd64/helm", "/usr/local/bin/"
        ], check=True)
        
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
            "--set", "controller.service.type=NodePort"
        ], check=True)
        
        print("✅ Ingress controller installed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install ingress controller: {e}")
        return False

def get_minikube_ip():
    """Get Minikube IP"""
    print("🌍 Getting Minikube IP...")
    
    try:
        result = subprocess.run([
            "minikube", "ip"
        ], capture_output=True, text=True, check=True)
        
        minikube_ip = result.stdout.strip()
        print(f"✅ Minikube IP: {minikube_ip}")
        return minikube_ip
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get Minikube IP: {e}")
        return None

def enable_ingress_addon():
    """Enable Minikube ingress addon"""
    print("🔧 Enabling Minikube ingress addon...")
    
    try:
        subprocess.run([
            "minikube", "addons", "enable", "ingress"
        ], check=True)
        
        print("✅ Ingress addon enabled!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to enable ingress addon: {e}")
        return False

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
        kubeconfig_file = Path("kubeconfig-minikube.yaml")
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

def setup_docker_env():
    """Setup Docker environment for Minikube"""
    print("🐳 Setting up Docker environment...")
    
    try:
        # Point shell to minikube's docker-daemon
        subprocess.run([
            "eval", "$(minikube docker-env)"
        ], shell=True, check=True)
        
        print("✅ Docker environment configured!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to setup Docker environment: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Minikube Local Kubernetes Cluster Setup")
    print("=" * 50)
    
    # Check if kubectl is installed
    if not check_kubectl_installed():
        print("❌ kubectl not found")
        if not install_kubectl():
            return False
    
    # Check if Minikube is installed
    if not check_minikube_installed():
        print("❌ Minikube not found")
        if not install_minikube():
            return False
    
    # Start cluster
    if not start_minikube_cluster():
        return False
    
    # Verify cluster
    if not verify_cluster():
        return False
    
    # Install Helm
    if not install_helm():
        return False
    
    # Create namespaces
    create_namespaces()
    
    # Enable ingress addon
    if not enable_ingress_addon():
        return False
    
    # Install ingress controller
    if not install_ingress_controller():
        return False
    
    # Get Minikube IP
    minikube_ip = get_minikube_ip()
    
    # Setup Docker environment
    setup_docker_env()
    
    # Generate kubeconfig
    kubeconfig_base64 = generate_kubeconfig()
    
    print("\n🎉 Minikube Local Kubernetes Cluster Setup Complete!")
    print("=" * 50)
    if minikube_ip:
        print(f"Minikube IP: {minikube_ip}")
    
    print("\n📝 Next Steps:")
    print("1. Update GitHub secrets with the kubeconfig above")
    print("2. Deploy the authentication service")
    print("3. Configure monitoring and alerting")
    
    print("\n🔧 Useful Commands:")
    print("- Start cluster: minikube start")
    print("- Stop cluster: minikube stop")
    print("- Delete cluster: minikube delete")
    print("- Open dashboard: minikube dashboard")
    print("- Get IP: minikube ip")
    
    print("\n💰 Cost Information:")
    print("- Minikube is completely free")
    print("- Runs locally on your machine")
    print("- No cloud costs involved")
    
    return True

if __name__ == "__main__":
    main() 