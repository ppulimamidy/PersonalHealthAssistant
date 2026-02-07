"""
Doctor Collaboration Service Models

This module contains all the data models for the Doctor Collaboration service.
"""

from .appointment import *
from .messaging import *
from .consultation import *
from .notification import *

__all__ = [
    # Appointment models
    "Appointment",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentResponse",
    "AppointmentStatus",
    "AppointmentType",
    
    # Messaging models
    "Message",
    "MessageCreate",
    "MessageUpdate",
    "MessageResponse",
    "MessageType",
    "MessagePriority",
    
    # Consultation models
    "Consultation",
    "ConsultationCreate",
    "ConsultationUpdate",
    "ConsultationResponse",
    "ConsultationType",
    "ConsultationStatus",
    
    # Notification models
    "Notification",
    "NotificationCreate",
    "NotificationUpdate",
    "NotificationResponse",
    "NotificationType",
    "NotificationPriority",
] 