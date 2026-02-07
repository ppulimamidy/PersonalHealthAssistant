#!/usr/bin/env python3
"""
Kubernetes Cluster Setup Guide

This script helps you choose and set up a Kubernetes cluster for the authentication service.
It provides options for free and paid cloud providers, as well as local development.
"""

import subprocess
import json
import os
import sys
from pathlib import Path

def print_header():
    """Print setup header"""
    print("🚀 Kubernetes Cluster Setup for Authentication Service")
    print("=" * 60)
    print("This script will help you set up a Kubernetes cluster for deployment.")
    print("Choose from the following options:\n")

def print_options():
    """Print available cluster options"""
    options = [
        {
            "id": "1",
            "name": "Google Cloud Platform (GCP)",
            "description": "Free tier with $300 credit, GKE cluster",
            "cost": "Free tier eligible",
            "difficulty": "Medium",
            "script": "setup_gcp_cluster.py"
        },
        {
            "id": "2", 
            "name": "DigitalOcean",
            "description": "Free trial with $200 credit, managed Kubernetes",
            "cost": "Free trial, then ~$10/month",
            "difficulty": "Easy",
            "script": "setup_digitalocean_cluster.py"
        },
        {
            "id": "3",
            "name": "Minikube (Local)",
            "description": "Local development cluster, runs on your machine",
            "cost": "Completely free",
            "difficulty": "Easy",
            "script": "setup_minikube_cluster.py"
        },
        {
            "id": "4",
            "name": "Docker Desktop",
            "description": "Built-in Kubernetes in Docker Desktop",
            "cost": "Free with Docker Desktop",
            "difficulty": "Very Easy",
            "script": "setup_docker_desktop.py"
        }
    ]
    
    for option in options:
        print(f"{option['id']}. {option['name']}")
        print(f"   {option['description']}")
        print(f"   Cost: {option['cost']}")
        print(f"   Difficulty: {option['difficulty']}")
        print()

def get_user_choice():
    """Get user's cluster choice"""
    while True:
        try:
            choice = input("Enter your choice (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return choice
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
        except KeyboardInterrupt:
            print("\n\n👋 Setup cancelled. Goodbye!")
            sys.exit(0)

def run_setup_script(script_name):
    """Run the selected setup script"""
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"❌ Setup script not found: {script_path}")
        return False
    
    print(f"🔧 Running setup script: {script_name}")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            sys.executable, str(script_path)
        ], check=True)
        
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup script failed: {e}")
        return False

def setup_docker_desktop():
    """Setup Docker Desktop Kubernetes"""
    print("🐳 Setting up Docker Desktop Kubernetes...")
    
    # Check if Docker Desktop is running
    try:
        subprocess.run(["docker", "version"], capture_output=True, check=True)
        print("✅ Docker is running")
    except subprocess.CalledProcessError:
        print("❌ Docker is not running. Please start Docker Desktop.")
        return False
    
    # Check if Kubernetes is enabled
    try:
        result = subprocess.run([
            "kubectl", "cluster-info"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Kubernetes is already enabled in Docker Desktop")
        else:
            print("❌ Kubernetes is not enabled in Docker Desktop")
            print("Please enable Kubernetes in Docker Desktop settings:")
            print("1. Open Docker Desktop")
            print("2. Go to Settings → Kubernetes")
            print("3. Check 'Enable Kubernetes'")
            print("4. Click 'Apply & Restart'")
            return False
            
    except subprocess.CalledProcessError:
        print("❌ Failed to check Kubernetes status")
        return False
    
    # Install Helm
    print("📦 Installing Helm...")
    try:
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
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Helm: {e}")
        return False
    
    # Create namespaces
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
    
    # Generate kubeconfig
    print("🔧 Generating kubeconfig...")
    try:
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
        import base64
        kubeconfig_base64 = base64.b64encode(kubeconfig.encode()).decode()
        
        print("\n📋 Kubeconfig for GitHub Secrets:")
        print(f"KUBE_CONFIG_DEV: {kubeconfig_base64}")
        print(f"KUBE_CONFIG_STAGING: {kubeconfig_base64}")
        print(f"KUBE_CONFIG_PROD: {kubeconfig_base64}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate kubeconfig: {e}")
        return False
    
    print("\n🎉 Docker Desktop Kubernetes Setup Complete!")
    print("=" * 50)
    print("✅ Kubernetes is running in Docker Desktop")
    print("✅ Helm is installed and configured")
    print("✅ Namespaces are created")
    print("✅ Kubeconfig is generated")
    
    print("\n📝 Next Steps:")
    print("1. Update GitHub secrets with the kubeconfig above")
    print("2. Deploy the authentication service")
    print("3. Configure monitoring and alerting")
    
    return True

def main():
    """Main setup function"""
    print_header()
    print_options()
    
    choice = get_user_choice()
    
    print(f"\n🎯 You selected option {choice}")
    print("-" * 40)
    
    if choice == "1":
        print("Setting up Google Cloud Platform (GCP) cluster...")
        success = run_setup_script("setup_gcp_cluster.py")
    elif choice == "2":
        print("Setting up DigitalOcean cluster...")
        success = run_setup_script("setup_digitalocean_cluster.py")
    elif choice == "3":
        print("Setting up Minikube local cluster...")
        success = run_setup_script("setup_minikube_cluster.py")
    elif choice == "4":
        print("Setting up Docker Desktop Kubernetes...")
        success = setup_docker_desktop()
    
    if success:
        print("\n🎉 Kubernetes cluster setup completed successfully!")
        print("\n📋 Summary:")
        print("- Kubernetes cluster is ready")
        print("- Kubeconfig has been generated")
        print("- GitHub secrets are ready to be configured")
        
        print("\n🔄 Next Steps:")
        print("1. Add the kubeconfig to your GitHub repository secrets")
        print("2. Deploy the authentication service using the provided manifests")
        print("3. Test the deployment and monitoring")
        
        print("\n📚 Documentation:")
        print("- Deployment Guide: apps/auth/DEPLOYMENT_GUIDE.md")
        print("- API Documentation: apps/auth/API_DOCUMENTATION.md")
        print("- Security Guide: apps/auth/SECURITY_GUIDE.md")
        
    else:
        print("\n❌ Kubernetes cluster setup failed!")
        print("Please check the error messages above and try again.")
        print("You can also try a different cluster option.")

if __name__ == "__main__":
    main() 