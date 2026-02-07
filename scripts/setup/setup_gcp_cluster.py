#!/usr/bin/env python3
"""
Google Cloud Platform (GCP) Kubernetes Cluster Setup

This script helps set up a free GKE cluster on Google Cloud Platform.
GCP offers a free tier with $300 credit and free GKE cluster.
"""

import subprocess
import json
import os
import time
from pathlib import Path

def check_gcloud_installed():
    """Check if gcloud CLI is installed"""
    try:
        subprocess.run(["gcloud", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_gcloud():
    """Install Google Cloud SDK"""
    print("📥 Installing Google Cloud SDK...")
    
    if os.name == 'nt':  # Windows
        print("Please download and install from: https://cloud.google.com/sdk/docs/install")
        return False
    else:  # macOS/Linux
        try:
            # Download and install gcloud
            subprocess.run([
                "curl", "https://sdk.cloud.google.com", "|", "bash"
            ], shell=True, check=True)
            
            # Reload shell
            subprocess.run(["exec", "-l", "$SHELL"], shell=True)
            return True
        except subprocess.CalledProcessError:
            print("Failed to install gcloud. Please install manually.")
            return False

def setup_gcp_project():
    """Set up GCP project and enable APIs"""
    print("🔧 Setting up GCP project...")
    
    # Get current project
    result = subprocess.run(["gcloud", "config", "get-value", "project"], 
                          capture_output=True, text=True)
    project_id = result.stdout.strip()
    
    if not project_id or project_id == "(unset)":
        print("❌ No GCP project configured")
        print("Please run: gcloud auth login")
        print("Then run: gcloud config set project YOUR_PROJECT_ID")
        return None
    
    print(f"✅ Using project: {project_id}")
    
    # Enable required APIs
    apis = [
        "container.googleapis.com",
        "compute.googleapis.com",
        "iam.googleapis.com"
    ]
    
    for api in apis:
        print(f"Enabling API: {api}")
        subprocess.run([
            "gcloud", "services", "enable", api
        ], check=True)
    
    return project_id

def create_gke_cluster(project_id, cluster_name="auth-service-cluster"):
    """Create a free GKE cluster"""
    print(f"🚀 Creating GKE cluster: {cluster_name}")
    
    # Create cluster with minimal resources (free tier friendly)
    cluster_config = [
        "gcloud", "container", "clusters", "create", cluster_name,
        "--project", project_id,
        "--zone", "us-central1-a",  # Free tier zone
        "--num-nodes", "1",  # Single node for free tier
        "--machine-type", "e2-micro",  # Smallest machine type
        "--disk-size", "10",  # 10GB disk
        "--disk-type", "pd-standard",
        "--enable-autoscaling",
        "--min-nodes", "1",
        "--max-nodes", "3",
        "--enable-autorepair",
        "--enable-autoupgrade",
        "--enable-stackdriver-kubernetes",
        "--no-enable-basic-auth",
        "--no-issue-client-certificate"
    ]
    
    try:
        subprocess.run(cluster_config, check=True)
        print("✅ GKE cluster created successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create cluster: {e}")
        return False

def get_cluster_credentials(cluster_name):
    """Get cluster credentials"""
    print(f"🔑 Getting credentials for cluster: {cluster_name}")
    
    try:
        subprocess.run([
            "gcloud", "container", "clusters", "get-credentials", cluster_name,
            "--zone", "us-central1-a"
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
        kubeconfig_file = Path("kubeconfig.yaml")
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
    print("🚀 GCP Kubernetes Cluster Setup")
    print("=" * 50)
    
    # Check if gcloud is installed
    if not check_gcloud_installed():
        print("❌ Google Cloud SDK not found")
        if not install_gcloud():
            return False
    
    # Setup GCP project
    project_id = setup_gcp_project()
    if not project_id:
        return False
    
    # Create cluster
    cluster_name = "auth-service-cluster"
    if not create_gke_cluster(project_id, cluster_name):
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
    
    print("\n🎉 GCP Kubernetes Cluster Setup Complete!")
    print("=" * 50)
    print(f"Cluster Name: {cluster_name}")
    print(f"Project ID: {project_id}")
    print(f"Zone: us-central1-a")
    if external_ip:
        print(f"External IP: {external_ip}")
    
    print("\n📝 Next Steps:")
    print("1. Update GitHub secrets with the kubeconfig above")
    print("2. Deploy the authentication service")
    print("3. Configure monitoring and alerting")
    
    print("\n💰 Cost Information:")
    print("- GCP offers $300 free credit")
    print("- e2-micro instances are free tier eligible")
    print("- Monitor usage in GCP Console")
    
    return True

if __name__ == "__main__":
    main() 