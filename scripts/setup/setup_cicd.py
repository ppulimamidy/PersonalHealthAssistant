#!/usr/bin/env python3
"""
CI/CD Pipeline Setup Script for Authentication Service

This script sets up the CI/CD pipeline infrastructure including:
- GitHub repository configuration
- Kubernetes cluster setup
- Monitoring and alerting
- Security scanning tools
"""

import os
import sys
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from common.utils.logging import setup_logging

class CICDSetup:
    """CI/CD Pipeline Setup Manager"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.project_root = project_root
        self.auth_service_dir = self.project_root / "apps" / "auth"
        self.kubernetes_dir = self.auth_service_dir / "kubernetes"
        self.github_workflows_dir = self.project_root / ".github" / "workflows"
        
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger(__name__)
    
    def setup_github_repository(self) -> bool:
        """Setup GitHub repository for CI/CD"""
        try:
            self.logger.info("Setting up GitHub repository for CI/CD...")
            
            # Create GitHub workflows directory
            self.github_workflows_dir.mkdir(parents=True, exist_ok=True)
            
            # Verify CI/CD workflow exists
            workflow_file = self.github_workflows_dir / "auth-service-ci.yml"
            if not workflow_file.exists():
                self.logger.error("CI/CD workflow file not found")
                return False
            
            # Setup GitHub secrets (manual step)
            self.logger.info("Please configure the following GitHub secrets:")
            secrets = [
                "KUBE_CONFIG_DEV",
                "KUBE_CONFIG_STAGING", 
                "KUBE_CONFIG_PROD",
                "DOCKER_REGISTRY_TOKEN",
                "SLACK_WEBHOOK_URL"
            ]
            
            for secret in secrets:
                self.logger.info(f"  - {secret}")
            
            self.logger.info("GitHub repository setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup GitHub repository: {e}")
            return False
    
    def setup_kubernetes_cluster(self) -> bool:
        """Setup Kubernetes cluster for deployment"""
        try:
            self.logger.info("Setting up Kubernetes cluster...")
            
            # Check if kubectl is available
            if not self._check_command("kubectl"):
                self.logger.error("kubectl not found. Please install kubectl first.")
                return False
            
            # Create namespace
            self._run_command([
                "kubectl", "create", "namespace", "personal-health-assistant",
                "--dry-run=client", "-o", "yaml"
            ])
            
            # Apply Kubernetes manifests
            manifests = [
                "secrets.yaml",
                "deployment.yaml", 
                "network-policy.yaml",
                "monitoring.yaml"
            ]
            
            for manifest in manifests:
                manifest_path = self.kubernetes_dir / manifest
                if manifest_path.exists():
                    self.logger.info(f"Applying {manifest}...")
                    self._run_command([
                        "kubectl", "apply", "-f", str(manifest_path),
                        "-n", "personal-health-assistant"
                    ])
            
            # Verify deployment
            self._run_command([
                "kubectl", "get", "pods", "-n", "personal-health-assistant",
                "-l", "app=auth-service"
            ])
            
            self.logger.info("Kubernetes cluster setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup Kubernetes cluster: {e}")
            return False
    
    def setup_monitoring(self) -> bool:
        """Setup monitoring and alerting"""
        try:
            self.logger.info("Setting up monitoring and alerting...")
            
            # Check if Prometheus is installed
            if not self._check_prometheus():
                self.logger.warning("Prometheus not found. Installing...")
                self._install_prometheus()
            
            # Check if Grafana is installed
            if not self._check_grafana():
                self.logger.warning("Grafana not found. Installing...")
                self._install_grafana()
            
            # Apply monitoring configuration
            monitoring_config = self.kubernetes_dir / "monitoring.yaml"
            if monitoring_config.exists():
                self._run_command([
                    "kubectl", "apply", "-f", str(monitoring_config),
                    "-n", "personal-health-assistant"
                ])
            
            # Setup alerting rules
            self._setup_alerting_rules()
            
            self.logger.info("Monitoring setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup monitoring: {e}")
            return False
    
    def setup_security_scanning(self) -> bool:
        """Setup security scanning tools"""
        try:
            self.logger.info("Setting up security scanning tools...")
            
            # Install security tools
            tools = [
                ("bandit", "pip install bandit"),
                ("safety", "pip install safety"),
                ("trivy", "curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin")
            ]
            
            for tool_name, install_command in tools:
                if not self._check_command(tool_name):
                    self.logger.info(f"Installing {tool_name}...")
                    self._run_command(install_command.split())
            
            # Create security scanning configuration
            self._create_security_config()
            
            self.logger.info("Security scanning setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup security scanning: {e}")
            return False
    
    def setup_load_testing(self) -> bool:
        """Setup load testing infrastructure"""
        try:
            self.logger.info("Setting up load testing infrastructure...")
            
            # Install k6
            if not self._check_command("k6"):
                self.logger.info("Installing k6...")
                self._run_command([
                    "curl", "-L", 
                    "https://github.com/grafana/k6/releases/download/v0.45.0/k6-v0.45.0-linux-amd64.tar.gz",
                    "|", "tar", "xz"
                ])
            
            # Create load test configuration
            self._create_load_test_config()
            
            self.logger.info("Load testing setup completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup load testing: {e}")
            return False
    
    def validate_setup(self) -> bool:
        """Validate the CI/CD setup"""
        try:
            self.logger.info("Validating CI/CD setup...")
            
            checks = [
                ("GitHub workflow", self._check_github_workflow),
                ("Kubernetes manifests", self._check_kubernetes_manifests),
                ("Monitoring", self._check_monitoring),
                ("Security tools", self._check_security_tools),
                ("Load testing", self._check_load_testing)
            ]
            
            all_passed = True
            for check_name, check_func in checks:
                if check_func():
                    self.logger.info(f"✓ {check_name} - OK")
                else:
                    self.logger.error(f"✗ {check_name} - FAILED")
                    all_passed = False
            
            if all_passed:
                self.logger.info("All CI/CD setup checks passed!")
            else:
                self.logger.error("Some CI/CD setup checks failed!")
            
            return all_passed
            
        except Exception as e:
            self.logger.error(f"Failed to validate setup: {e}")
            return False
    
    def _check_command(self, command: str) -> bool:
        """Check if a command is available"""
        try:
            subprocess.run([command, "--version"], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _run_command(self, command: List[str]) -> bool:
        """Run a command and return success status"""
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error(f"Command failed: {' '.join(command)}")
                self.logger.error(f"Error: {result.stderr}")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Failed to run command {' '.join(command)}: {e}")
            return False
    
    def _check_prometheus(self) -> bool:
        """Check if Prometheus is available"""
        try:
            result = subprocess.run([
                "kubectl", "get", "pods", "-n", "monitoring",
                "-l", "app=prometheus"
            ], capture_output=True, text=True)
            return "Running" in result.stdout
        except:
            return False
    
    def _check_grafana(self) -> bool:
        """Check if Grafana is available"""
        try:
            result = subprocess.run([
                "kubectl", "get", "pods", "-n", "monitoring",
                "-l", "app=grafana"
            ], capture_output=True, text=True)
            return "Running" in result.stdout
        except:
            return False
    
    def _install_prometheus(self) -> bool:
        """Install Prometheus"""
        try:
            # Add Prometheus Helm repository
            self._run_command([
                "helm", "repo", "add", "prometheus-community",
                "https://prometheus-community.github.io/helm-charts"
            ])
            
            # Install Prometheus
            self._run_command([
                "helm", "install", "prometheus", "prometheus-community/kube-prometheus-stack",
                "-n", "monitoring", "--create-namespace"
            ])
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to install Prometheus: {e}")
            return False
    
    def _install_grafana(self) -> bool:
        """Install Grafana"""
        try:
            # Add Grafana Helm repository
            self._run_command([
                "helm", "repo", "add", "grafana",
                "https://grafana.github.io/helm-charts"
            ])
            
            # Install Grafana
            self._run_command([
                "helm", "install", "grafana", "grafana/grafana",
                "-n", "monitoring", "--create-namespace"
            ])
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to install Grafana: {e}")
            return False
    
    def _setup_alerting_rules(self) -> bool:
        """Setup alerting rules"""
        try:
            # Create alerting configuration
            alerting_config = {
                "receivers": [
                    {
                        "name": "auth-service-alerts",
                        "slack_configs": [
                            {
                                "api_url": "${SLACK_WEBHOOK_URL}",
                                "channel": "#alerts",
                                "title": "Auth Service Alert",
                                "text": "{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}"
                            }
                        ]
                    }
                ],
                "route": {
                    "group_by": ["alertname"],
                    "group_wait": "10s",
                    "group_interval": "10s",
                    "repeat_interval": "1h",
                    "receiver": "auth-service-alerts"
                }
            }
            
            # Write alerting configuration
            alerting_file = self.project_root / "monitoring" / "alertmanager" / "config.yml"
            alerting_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(alerting_file, 'w') as f:
                yaml.dump(alerting_config, f)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup alerting rules: {e}")
            return False
    
    def _create_security_config(self) -> bool:
        """Create security scanning configuration"""
        try:
            # Bandit configuration
            bandit_config = {
                "exclude_dirs": ["tests", "venv", "__pycache__"],
                "skips": ["B101", "B601"],
                "severity": ["low", "medium", "high"]
            }
            
            bandit_file = self.project_root / ".bandit"
            with open(bandit_file, 'w') as f:
                json.dump(bandit_config, f, indent=2)
            
            # Safety configuration
            safety_config = {
                "ignore": ["CVE-2021-1234"],
                "full_report": True
            }
            
            safety_file = self.project_root / ".safety"
            with open(safety_file, 'w') as f:
                json.dump(safety_config, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to create security config: {e}")
            return False
    
    def _create_load_test_config(self) -> bool:
        """Create load testing configuration"""
        try:
            # k6 configuration
            k6_config = {
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
            
            k6_file = self.project_root / "k6-config.json"
            with open(k6_file, 'w') as f:
                json.dump(k6_config, f, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to create load test config: {e}")
            return False
    
    def _check_github_workflow(self) -> bool:
        """Check GitHub workflow configuration"""
        workflow_file = self.github_workflows_dir / "auth-service-ci.yml"
        return workflow_file.exists()
    
    def _check_kubernetes_manifests(self) -> bool:
        """Check Kubernetes manifests"""
        required_manifests = [
            "deployment.yaml",
            "secrets.yaml",
            "network-policy.yaml"
        ]
        
        for manifest in required_manifests:
            if not (self.kubernetes_dir / manifest).exists():
                return False
        
        return True
    
    def _check_monitoring(self) -> bool:
        """Check monitoring setup"""
        return self._check_prometheus() and self._check_grafana()
    
    def _check_security_tools(self) -> bool:
        """Check security tools"""
        tools = ["bandit", "safety", "trivy"]
        return all(self._check_command(tool) for tool in tools)
    
    def _check_load_testing(self) -> bool:
        """Check load testing setup"""
        return self._check_command("k6")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Setup CI/CD Pipeline for Auth Service")
    parser.add_argument("--config", type=str, default="cicd-config.json",
                       help="Configuration file path")
    parser.add_argument("--skip-github", action="store_true",
                       help="Skip GitHub repository setup")
    parser.add_argument("--skip-kubernetes", action="store_true",
                       help="Skip Kubernetes cluster setup")
    parser.add_argument("--skip-monitoring", action="store_true",
                       help="Skip monitoring setup")
    parser.add_argument("--skip-security", action="store_true",
                       help="Skip security scanning setup")
    parser.add_argument("--skip-load-testing", action="store_true",
                       help="Skip load testing setup")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate existing setup")
    
    args = parser.parse_args()
    
    # Load configuration
    config_file = Path(args.config)
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
    else:
        config = {
            "github": {
                "repository": "your-org/PersonalHealthAssistant",
                "branch": "main"
            },
            "kubernetes": {
                "namespace": "personal-health-assistant",
                "cluster": "production"
            },
            "monitoring": {
                "prometheus": True,
                "grafana": True,
                "alerting": True
            }
        }
    
    # Initialize setup
    setup = CICDSetup(config)
    
    if args.validate_only:
        success = setup.validate_setup()
        sys.exit(0 if success else 1)
    
    # Run setup steps
    success = True
    
    if not args.skip_github:
        success &= setup.setup_github_repository()
    
    if not args.skip_kubernetes:
        success &= setup.setup_kubernetes_cluster()
    
    if not args.skip_monitoring:
        success &= setup.setup_monitoring()
    
    if not args.skip_security:
        success &= setup.setup_security_scanning()
    
    if not args.skip_load_testing:
        success &= setup.setup_load_testing()
    
    # Validate setup
    success &= setup.validate_setup()
    
    if success:
        print("\n✅ CI/CD Pipeline setup completed successfully!")
        print("\nNext steps:")
        print("1. Configure GitHub secrets in your repository")
        print("2. Set up your Kubernetes cluster")
        print("3. Configure monitoring dashboards")
        print("4. Test the pipeline with a commit")
    else:
        print("\n❌ CI/CD Pipeline setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 