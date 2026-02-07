"""
Collaboration Service for Doctor Collaboration Service.

This is the main service that orchestrates all collaboration-related operations.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from common.utils.logging import get_logger
from common.utils.resilience import with_resilience
from common.exceptions import (
    NotFoundError,
    ValidationError,
    ConflictError,
    DatabaseError,
    ServiceError
)

from .appointment_service import AppointmentService
from .messaging_service import MessagingService
from .consultation_service import ConsultationService
from .notification_service import NotificationService

logger = get_logger(__name__)


class CollaborationService:
    """Main service for orchestrating collaboration operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.appointment_service = AppointmentService(db)
        self.messaging_service = MessagingService(db)
        self.consultation_service = ConsultationService(db)
        self.notification_service = NotificationService(db)
        self._running = False
        self._tasks = []
    
    async def start(self):
        """Start the collaboration service."""
        try:
            self._running = True
            
            # Start background tasks
            self._tasks = [
                asyncio.create_task(self._process_pending_notifications()),
                asyncio.create_task(self._process_appointment_reminders()),
                asyncio.create_task(self._process_message_delivery()),
                asyncio.create_task(self._process_consultation_updates())
            ]
            
            logger.info("Collaboration service started successfully")
            
        except Exception as e:
            logger.error(f"Error starting collaboration service: {e}")
            raise
    
    async def stop(self):
        """Stop the collaboration service."""
        try:
            self._running = False
            
            # Cancel all background tasks
            for task in self._tasks:
                task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
            logger.info("Collaboration service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping collaboration service: {e}")
            raise
    
    @with_resilience("collaboration_service", max_concurrent=50, timeout=60.0, max_retries=3)
    async def create_appointment_with_notifications(
        self,
        appointment_data: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create appointment with automatic notifications.
        
        Args:
            appointment_data: Appointment creation data
            current_user: Current authenticated user
            
        Returns:
            Created appointment with notification status
        """
        try:
            # Create appointment
            from ..models.appointment import AppointmentCreate
            appointment_create = AppointmentCreate(**appointment_data)
            
            appointment = await self.appointment_service.create_appointment(
                appointment_data=appointment_create,
                created_by=current_user["id"]
            )
            
            # Send notifications
            notification_tasks = []
            
            # Send notification to patient
            notification_tasks.append(
                self.notification_service.send_appointment_reminder(
                    appointment_id=appointment.id,
                    reminder_type="email",
                    current_user=current_user
                )
            )
            
            # Send notification to doctor
            notification_tasks.append(
                self.notification_service.send_appointment_reminder(
                    appointment_id=appointment.id,
                    reminder_type="push",
                    current_user=current_user
                )
            )
            
            # Wait for notifications to be sent
            notifications = await asyncio.gather(*notification_tasks, return_exceptions=True)
            
            return {
                "appointment": appointment,
                "notifications_sent": len([n for n in notifications if not isinstance(n, Exception)]),
                "notification_errors": len([n for n in notifications if isinstance(n, Exception)])
            }
            
        except Exception as e:
            logger.error(f"Error creating appointment with notifications: {e}")
            raise
    
    @with_resilience("collaboration_service", max_concurrent=50, timeout=60.0, max_retries=3)
    async def send_message_with_notifications(
        self,
        message_data: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send message with automatic notifications.
        
        Args:
            message_data: Message creation data
            current_user: Current authenticated user
            
        Returns:
            Sent message with notification status
        """
        try:
            # Send message
            from ..models.messaging import MessageCreate
            message_create = MessageCreate(**message_data)
            
            message = await self.messaging_service.send_message(
                message_data=message_create,
                sender_id=current_user["id"]
            )
            
            # Send notification to recipient
            notification = await self.notification_service.send_message_notification(
                message_id=message.id,
                notification_type="push",
                current_user=current_user
            )
            
            return {
                "message": message,
                "notification_sent": notification is not None
            }
            
        except Exception as e:
            logger.error(f"Error sending message with notifications: {e}")
            raise
    
    @with_resilience("collaboration_service", max_concurrent=50, timeout=60.0, max_retries=3)
    async def create_consultation_with_notifications(
        self,
        consultation_data: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create consultation with automatic notifications.
        
        Args:
            consultation_data: Consultation creation data
            current_user: Current authenticated user
            
        Returns:
            Created consultation with notification status
        """
        try:
            # Create consultation
            from ..models.consultation import ConsultationCreate
            consultation_create = ConsultationCreate(**consultation_data)
            
            consultation = await self.consultation_service.create_consultation(
                consultation_data=consultation_create,
                created_by=current_user["id"]
            )
            
            # Send notifications
            notification_tasks = []
            
            # Send notification to patient
            notification_tasks.append(
                self.notification_service.send_consultation_notification(
                    consultation_id=consultation.id,
                    notification_type="email",
                    current_user=current_user
                )
            )
            
            # Send notification to doctor
            notification_tasks.append(
                self.notification_service.send_consultation_notification(
                    consultation_id=consultation.id,
                    notification_type="push",
                    current_user=current_user
                )
            )
            
            # Wait for notifications to be sent
            notifications = await asyncio.gather(*notification_tasks, return_exceptions=True)
            
            return {
                "consultation": consultation,
                "notifications_sent": len([n for n in notifications if not isinstance(n, Exception)]),
                "notification_errors": len([n for n in notifications if isinstance(n, Exception)])
            }
            
        except Exception as e:
            logger.error(f"Error creating consultation with notifications: {e}")
            raise
    
    @with_resilience("collaboration_service", max_concurrent=100, timeout=30.0, max_retries=3)
    async def get_user_dashboard_data(
        self,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data for a user.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            Dashboard data including appointments, messages, consultations, and notifications
        """
        try:
            # Get upcoming appointments
            upcoming_appointments = await self.appointment_service.get_upcoming_appointments(
                end_date=datetime.utcnow() + timedelta(days=7),
                current_user=current_user
            )
            
            # Get unread messages
            unread_messages = await self.messaging_service.get_unread_messages(
                current_user=current_user,
                limit=10
            )
            
            # Get recent consultations
            from ..models.consultation import ConsultationFilter
            consultation_filter = ConsultationFilter(
                limit=5,
                offset=0
            )
            recent_consultations = await self.consultation_service.list_consultations(
                filter_params=consultation_filter,
                current_user=current_user
            )
            
            # Get unread notifications
            unread_notifications = await self.notification_service.get_unread_notifications(
                current_user=current_user,
                limit=10
            )
            
            # Get statistics
            appointment_stats = await self._get_appointment_stats(current_user)
            message_stats = await self.messaging_service.get_message_stats(current_user)
            consultation_stats = await self.consultation_service.get_consultation_stats(current_user)
            notification_stats = await self.notification_service.get_notification_stats(current_user)
            
            return {
                "upcoming_appointments": upcoming_appointments,
                "unread_messages": unread_messages,
                "recent_consultations": recent_consultations,
                "unread_notifications": unread_notifications,
                "statistics": {
                    "appointments": appointment_stats,
                    "messages": message_stats,
                    "consultations": consultation_stats,
                    "notifications": notification_stats
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting user dashboard data: {e}")
            raise
    
    @with_resilience("collaboration_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def get_doctor_patient_summary(
        self,
        doctor_id: UUID,
        patient_id: UUID,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get summary of doctor-patient interactions.
        
        Args:
            doctor_id: Doctor ID
            patient_id: Patient ID
            current_user: Current authenticated user
            
        Returns:
            Summary of interactions
        """
        try:
            # Check permissions
            if current_user["user_type"] not in ["doctor", "admin"]:
                raise PermissionDeniedException("Only doctors can access patient summaries")
            
            if current_user["user_type"] == "doctor" and current_user["id"] != doctor_id:
                raise PermissionDeniedException("Doctors can only access their own patient summaries")
            
            # Get appointments between doctor and patient
            from ..models.appointment import AppointmentFilter
            appointment_filter = AppointmentFilter(
                doctor_id=doctor_id,
                patient_id=patient_id,
                limit=50
            )
            appointments = await self.appointment_service.list_appointments(
                filter_params=appointment_filter,
                current_user=current_user
            )
            
            # Get messages between doctor and patient
            from ..models.messaging import MessageFilter
            message_filter = MessageFilter(
                limit=50
            )
            messages = await self.messaging_service.list_messages(
                filter_params=message_filter,
                current_user=current_user
            )
            
            # Filter messages for this doctor-patient pair
            doctor_patient_messages = [
                msg for msg in messages
                if (msg.sender_id == doctor_id and msg.recipient_id == patient_id) or
                   (msg.sender_id == patient_id and msg.recipient_id == doctor_id)
            ]
            
            # Get consultations between doctor and patient
            consultation_filter = ConsultationFilter(
                doctor_id=doctor_id,
                patient_id=patient_id,
                limit=50
            )
            consultations = await self.consultation_service.list_consultations(
                filter_params=consultation_filter,
                current_user=current_user
            )
            
            # Calculate statistics
            total_appointments = len(appointments)
            completed_appointments = len([a for a in appointments if a.status == "completed"])
            total_messages = len(doctor_patient_messages)
            total_consultations = len(consultations)
            completed_consultations = len([c for c in consultations if c.status == "completed"])
            
            return {
                "doctor_id": doctor_id,
                "patient_id": patient_id,
                "appointments": {
                    "total": total_appointments,
                    "completed": completed_appointments,
                    "upcoming": len([a for a in appointments if a.is_upcoming]),
                    "recent": appointments[:5]
                },
                "messages": {
                    "total": total_messages,
                    "unread": len([m for m in doctor_patient_messages if not m.is_read]),
                    "recent": doctor_patient_messages[:5]
                },
                "consultations": {
                    "total": total_consultations,
                    "completed": completed_consultations,
                    "active": len([c for c in consultations if c.is_active]),
                    "recent": consultations[:5]
                },
                "interaction_summary": {
                    "first_interaction": min([a.created_at for a in appointments]) if appointments else None,
                    "last_interaction": max([a.updated_at for a in appointments]) if appointments else None,
                    "interaction_frequency": "weekly" if total_appointments > 4 else "monthly" if total_appointments > 1 else "occasional"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting doctor-patient summary: {e}")
            raise
    
    @with_resilience("collaboration_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def get_system_health_status(self) -> Dict[str, Any]:
        """
        Get system health status.
        
        Returns:
            System health information
        """
        try:
            health_status = {
                "service_status": "healthy" if self._running else "stopped",
                "background_tasks": len(self._tasks),
                "active_tasks": len([task for task in self._tasks if not task.done()]),
                "last_health_check": datetime.utcnow().isoformat(),
                "service_components": {
                    "appointment_service": "healthy",
                    "messaging_service": "healthy",
                    "consultation_service": "healthy",
                    "notification_service": "healthy"
                }
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting system health status: {e}")
            return {
                "service_status": "unhealthy",
                "error": str(e),
                "last_health_check": datetime.utcnow().isoformat()
            }
    
    # Background task methods
    async def _process_pending_notifications(self):
        """Process pending notifications."""
        while self._running:
            try:
                # Get pending notifications
                from ..models.notification import NotificationFilter
                filter_params = NotificationFilter(
                    status="pending",
                    limit=10
                )
                
                # This would typically process notifications in batches
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error processing pending notifications: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _process_appointment_reminders(self):
        """Process appointment reminders."""
        while self._running:
            try:
                # Get upcoming appointments that need reminders
                # This would typically check for appointments in the next 24 hours
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error processing appointment reminders: {e}")
                await asyncio.sleep(600)  # Wait longer on error
    
    async def _process_message_delivery(self):
        """Process message delivery."""
        while self._running:
            try:
                # Process undelivered messages
                # This would typically retry failed message deliveries
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error processing message delivery: {e}")
                await asyncio.sleep(120)  # Wait longer on error
    
    async def _process_consultation_updates(self):
        """Process consultation updates."""
        while self._running:
            try:
                # Process consultation status updates
                # This would typically handle consultation lifecycle events
                await asyncio.sleep(180)  # Check every 3 minutes
                
            except Exception as e:
                logger.error(f"Error processing consultation updates: {e}")
                await asyncio.sleep(300)  # Wait longer on error
    
    async def _get_appointment_stats(self, current_user: Dict[str, Any]) -> Dict[str, Any]:
        """Get appointment statistics."""
        try:
            # Get upcoming appointments
            upcoming = await self.appointment_service.get_upcoming_appointments(
                end_date=datetime.utcnow() + timedelta(days=7),
                current_user=current_user
            )
            
            # Get overdue appointments
            overdue = await self.appointment_service.get_overdue_appointments(
                current_user=current_user
            )
            
            return {
                "upcoming_count": len(upcoming),
                "overdue_count": len(overdue),
                "total_today": len([a for a in upcoming if a.scheduled_date.date() == datetime.utcnow().date()])
            }
            
        except Exception as e:
            logger.error(f"Error getting appointment stats: {e}")
            return {
                "upcoming_count": 0,
                "overdue_count": 0,
                "total_today": 0
            } 