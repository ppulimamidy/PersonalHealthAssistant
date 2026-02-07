"""
Doctor Collaboration Service API

This module contains all the API endpoints for the Doctor Collaboration service.
"""

from . import appointments, messaging, consultations, notifications

__all__ = [
    "appointments",
    "messaging", 
    "consultations",
    "notifications"
] 