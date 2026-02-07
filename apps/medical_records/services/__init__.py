"""
Medical Records Services

This package contains all service layer modules for the medical records microservice.
"""

from .service_integration import ServiceIntegrationManager, service_integration

__all__ = [
    "ServiceIntegrationManager",
    "service_integration"
] 