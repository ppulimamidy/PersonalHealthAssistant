"""
Notification Service for Doctor Collaboration Service.

This service handles all notification-related business logic.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc, func
from sqlalchemy.orm import selectinload

from common.utils.logging import get_logger
from common.utils.resilience import with_resilience
from common.exceptions import (
    NotFoundError,
    ValidationError,
    ConflictError,
    DatabaseError,
    ServiceError,
    NotificationError
)

from ..models.notification import (
    Notification, NotificationCreate, NotificationUpdate, NotificationResponse,
    NotificationType, NotificationPriority, NotificationStatus, NotificationFilter,
    NotificationPreferences
)

logger = get_logger(__name__)


class NotificationService:
    """Service for managing notifications."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @with_resilience("notification_service", max_concurrent=100, timeout=30.0, max_retries=3)
    async def create_notification(
        self, 
        notification_data: NotificationCreate, 
        created_by: UUID
    ) -> NotificationResponse:
        """
        Create a new notification.
        
        Args:
            notification_data: Notification creation data
            created_by: ID of user creating the notification
            
        Returns:
            Created notification
            
        Raises:
            ValidationException: If notification data is invalid
            BusinessLogicException: If notification cannot be created
        """
        try:
            # Validate notification data
            await self._validate_notification_data(notification_data)
            
            # Check user preferences
            preferences = await self._get_user_notification_preferences(notification_data.recipient_id)
            if not self._should_send_notification(notification_data, preferences):
                raise BusinessLogicException("Notification blocked by user preferences")
            
            # Create notification
            notification = Notification(
                **notification_data.model_dump(),
                status=NotificationStatus.PENDING,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(notification)
            await self.db.commit()
            await self.db.refresh(notification)
            
            # Send notification (async)
            asyncio.create_task(self._deliver_notification(notification))
            
            logger.info(f"Notification created: {notification.id}")
            
            return NotificationResponse.model_validate(notification)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating notification: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=200, timeout=30.0, max_retries=3)
    async def list_notifications(
        self, 
        filter_params: NotificationFilter,
        current_user: Dict[str, Any]
    ) -> List[NotificationResponse]:
        """
        List notifications with filtering.
        
        Args:
            filter_params: Filter parameters
            current_user: Current authenticated user
            
        Returns:
            List of notifications
        """
        try:
            # Build query
            query = select(Notification).options(
                selectinload(Notification.recipient)
            )
            
            # Apply filters
            conditions = []
            
            # User-based filtering (users can only see notifications sent to them)
            conditions.append(Notification.recipient_id == current_user["id"])
            
            # Apply additional filters
            if filter_params.recipient_id:
                conditions.append(Notification.recipient_id == filter_params.recipient_id)
            
            if filter_params.notification_type:
                conditions.append(Notification.notification_type == filter_params.notification_type)
            
            if filter_params.priority:
                conditions.append(Notification.priority == filter_params.priority)
            
            if filter_params.status:
                conditions.append(Notification.status == filter_params.status)
            
            if filter_params.channel:
                conditions.append(Notification.channel == filter_params.channel)
            
            if filter_params.start_date:
                conditions.append(Notification.created_at >= filter_params.start_date)
            
            if filter_params.end_date:
                conditions.append(Notification.created_at <= filter_params.end_date)
            
            if filter_params.appointment_id:
                conditions.append(Notification.appointment_id == filter_params.appointment_id)
            
            if filter_params.message_id:
                conditions.append(Notification.message_id == filter_params.message_id)
            
            if filter_params.consultation_id:
                conditions.append(Notification.consultation_id == filter_params.consultation_id)
            
            if filter_params.unread_only:
                conditions.append(Notification.status == NotificationStatus.DELIVERED)
            
            # Apply conditions
            if conditions:
                query = query.where(and_(*conditions))
            
            # Apply ordering and pagination
            query = query.order_by(desc(Notification.created_at))
            query = query.offset(filter_params.offset).limit(filter_params.limit)
            
            # Execute query
            result = await self.db.execute(query)
            notifications = result.scalars().all()
            
            return [NotificationResponse.model_validate(notification) for notification in notifications]
            
        except Exception as e:
            logger.error(f"Error listing notifications: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=200, timeout=30.0, max_retries=3)
    async def get_notification(
        self, 
        notification_id: UUID,
        current_user: Dict[str, Any]
    ) -> Optional[NotificationResponse]:
        """
        Get notification by ID.
        
        Args:
            notification_id: Notification ID
            current_user: Current authenticated user
            
        Returns:
            Notification if found and accessible
            
        Raises:
            ResourceNotFoundException: If notification not found
            PermissionDeniedException: If user cannot access notification
        """
        try:
            query = select(Notification).options(
                selectinload(Notification.recipient)
            ).where(Notification.id == notification_id)
            
            result = await self.db.execute(query)
            notification = result.scalar_one_or_none()
            
            if not notification:
                raise ResourceNotFoundException(f"Notification {notification_id} not found")
            
            # Check permissions
            if not self._can_access_notification(notification, current_user):
                raise PermissionDeniedException("Cannot access this notification")
            
            return NotificationResponse.model_validate(notification)
            
        except (ResourceNotFoundException, PermissionDeniedException):
            raise
        except Exception as e:
            logger.error(f"Error getting notification {notification_id}: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=100, timeout=30.0, max_retries=3)
    async def update_notification(
        self,
        notification_id: UUID,
        notification_data: NotificationUpdate,
        current_user: Dict[str, Any]
    ) -> Optional[NotificationResponse]:
        """
        Update notification.
        
        Args:
            notification_id: Notification ID
            notification_data: Update data
            current_user: Current authenticated user
            
        Returns:
            Updated notification
            
        Raises:
            ResourceNotFoundException: If notification not found
            PermissionDeniedException: If user cannot update notification
            ValidationException: If update data is invalid
        """
        try:
            # Get notification
            notification = await self._get_notification_by_id(notification_id)
            if not notification:
                raise ResourceNotFoundException(f"Notification {notification_id} not found")
            
            # Check permissions
            if not self._can_modify_notification(notification, current_user):
                raise PermissionDeniedException("Cannot modify this notification")
            
            # Check if notification can be updated
            if notification.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED, NotificationStatus.READ]:
                raise BusinessLogicException("Cannot update sent, delivered, or read notifications")
            
            # Update notification
            update_data = notification_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(notification, field, value)
            
            notification.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(notification)
            
            logger.info(f"Notification updated: {notification_id}")
            
            return NotificationResponse.model_validate(notification)
            
        except (ResourceNotFoundException, PermissionDeniedException, ValidationException, BusinessLogicException):
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating notification {notification_id}: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def delete_notification(
        self,
        notification_id: UUID,
        current_user: Dict[str, Any]
    ) -> bool:
        """
        Delete notification.
        
        Args:
            notification_id: Notification ID
            current_user: Current authenticated user
            
        Returns:
            True if deleted successfully
            
        Raises:
            ResourceNotFoundException: If notification not found
            PermissionDeniedException: If user cannot delete notification
        """
        try:
            # Get notification
            notification = await self._get_notification_by_id(notification_id)
            if not notification:
                raise ResourceNotFoundException(f"Notification {notification_id} not found")
            
            # Check permissions
            if not self._can_modify_notification(notification, current_user):
                raise PermissionDeniedException("Cannot delete this notification")
            
            # Delete notification
            await self.db.delete(notification)
            await self.db.commit()
            
            logger.info(f"Notification deleted: {notification_id}")
            
            return True
            
        except (ResourceNotFoundException, PermissionDeniedException):
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting notification {notification_id}: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=200, timeout=30.0, max_retries=3)
    async def mark_as_read(
        self,
        notification_id: UUID,
        current_user: Dict[str, Any]
    ) -> Optional[NotificationResponse]:
        """
        Mark notification as read.
        
        Args:
            notification_id: Notification ID
            current_user: Current authenticated user
            
        Returns:
            Updated notification
        """
        try:
            notification = await self._get_notification_by_id(notification_id)
            if not notification:
                raise ResourceNotFoundException(f"Notification {notification_id} not found")
            
            # Check permissions
            if not self._can_access_notification(notification, current_user):
                raise PermissionDeniedException("Cannot access this notification")
            
            # Check if user is the recipient
            if notification.recipient_id != current_user["id"]:
                raise PermissionDeniedException("Only the recipient can mark notifications as read")
            
            # Mark as read
            notification.status = NotificationStatus.READ
            notification.read_at = datetime.utcnow()
            notification.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(notification)
            
            logger.info(f"Notification marked as read: {notification_id}")
            
            return NotificationResponse.model_validate(notification)
            
        except (ResourceNotFoundException, PermissionDeniedException):
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking notification as read {notification_id}: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def mark_all_as_read(
        self,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Mark all notifications as read.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            Result of the operation
        """
        try:
            # Update all unread notifications for the user
            query = select(Notification).where(
                and_(
                    Notification.recipient_id == current_user["id"],
                    Notification.status == NotificationStatus.DELIVERED
                )
            )
            
            result = await self.db.execute(query)
            notifications = result.scalars().all()
            
            updated_count = 0
            for notification in notifications:
                notification.status = NotificationStatus.READ
                notification.read_at = datetime.utcnow()
                notification.updated_at = datetime.utcnow()
                updated_count += 1
            
            await self.db.commit()
            
            logger.info(f"All notifications marked as read by user {current_user['id']}")
            
            return {
                "updated_count": updated_count,
                "message": f"Marked {updated_count} notifications as read"
            }
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking all notifications as read: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=100, timeout=30.0, max_retries=3)
    async def get_unread_notifications(
        self,
        current_user: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> List[NotificationResponse]:
        """
        Get unread notifications.
        
        Args:
            current_user: Current authenticated user
            limit: Number of notifications to return
            offset: Number of notifications to skip
            
        Returns:
            List of unread notifications
        """
        try:
            query = select(Notification).options(
                selectinload(Notification.recipient)
            ).where(
                and_(
                    Notification.recipient_id == current_user["id"],
                    Notification.status == NotificationStatus.DELIVERED
                )
            ).order_by(desc(Notification.created_at))
            
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            notifications = result.scalars().all()
            
            return [NotificationResponse.model_validate(notification) for notification in notifications]
            
        except Exception as e:
            logger.error(f"Error getting unread notifications: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def send_appointment_reminder(
        self,
        appointment_id: UUID,
        reminder_type: str,
        current_user: Dict[str, Any]
    ) -> NotificationResponse:
        """
        Send appointment reminder.
        
        Args:
            appointment_id: Appointment ID
            reminder_type: Type of reminder (email, sms, push)
            current_user: Current authenticated user
            
        Returns:
            Created notification
        """
        try:
            # Get appointment details (this would integrate with appointment service)
            # For now, create a basic notification
            notification_data = NotificationCreate(
                recipient_id=current_user["id"],  # This should be the patient ID
                notification_type=NotificationType.REMINDER,
                priority=NotificationPriority.NORMAL,
                title="Appointment Reminder",
                content=f"You have an upcoming appointment scheduled.",
                channel=NotificationChannel(reminder_type),
                appointment_id=appointment_id
            )
            
            notification = await self.create_notification(
                notification_data=notification_data,
                created_by=current_user["id"]
            )
            
            logger.info(f"Appointment reminder sent: {appointment_id}")
            
            return notification
            
        except Exception as e:
            logger.error(f"Error sending appointment reminder: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def send_message_notification(
        self,
        message_id: UUID,
        notification_type: str,
        current_user: Dict[str, Any]
    ) -> NotificationResponse:
        """
        Send message notification.
        
        Args:
            message_id: Message ID
            notification_type: Type of notification (email, sms, push)
            current_user: Current authenticated user
            
        Returns:
            Created notification
        """
        try:
            # Get message details (this would integrate with messaging service)
            # For now, create a basic notification
            notification_data = NotificationCreate(
                recipient_id=current_user["id"],  # This should be the message recipient ID
                notification_type=NotificationType.MESSAGE,
                priority=NotificationPriority.NORMAL,
                title="New Message",
                content="You have received a new message.",
                channel=NotificationChannel(notification_type),
                message_id=message_id
            )
            
            notification = await self.create_notification(
                notification_data=notification_data,
                created_by=current_user["id"]
            )
            
            logger.info(f"Message notification sent: {message_id}")
            
            return notification
            
        except Exception as e:
            logger.error(f"Error sending message notification: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def send_consultation_notification(
        self,
        consultation_id: UUID,
        notification_type: str,
        current_user: Dict[str, Any]
    ) -> NotificationResponse:
        """
        Send consultation notification.
        
        Args:
            consultation_id: Consultation ID
            notification_type: Type of notification (email, sms, push)
            current_user: Current authenticated user
            
        Returns:
            Created notification
        """
        try:
            # Get consultation details (this would integrate with consultation service)
            # For now, create a basic notification
            notification_data = NotificationCreate(
                recipient_id=current_user["id"],  # This should be the patient ID
                notification_type=NotificationType.CONSULTATION,
                priority=NotificationPriority.NORMAL,
                title="Consultation Update",
                content="Your consultation has been updated.",
                channel=NotificationChannel(notification_type),
                consultation_id=consultation_id
            )
            
            notification = await self.create_notification(
                notification_data=notification_data,
                created_by=current_user["id"]
            )
            
            logger.info(f"Consultation notification sent: {consultation_id}")
            
            return notification
            
        except Exception as e:
            logger.error(f"Error sending consultation notification: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def get_notification_preferences(
        self,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get notification preferences.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            Notification preferences
        """
        try:
            # This would typically fetch from a preferences table
            # For now, return default preferences
            preferences = {
                "email_notifications": True,
                "sms_notifications": False,
                "push_notifications": True,
                "in_app_notifications": True,
                "appointment_notifications": True,
                "message_notifications": True,
                "consultation_notifications": True,
                "reminder_notifications": True,
                "system_notifications": True,
                "security_notifications": True,
                "low_priority": True,
                "normal_priority": True,
                "high_priority": True,
                "urgent_priority": True,
                "critical_priority": True,
                "quiet_hours_start": None,
                "quiet_hours_end": None,
                "timezone": "UTC",
                "max_notifications_per_day": 50,
                "batch_notifications": False,
                "batch_interval_minutes": 15
            }
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=20, timeout=30.0, max_retries=3)
    async def update_notification_preferences(
        self,
        preferences: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update notification preferences.
        
        Args:
            preferences: New preferences
            current_user: Current authenticated user
            
        Returns:
            Updated preferences
        """
        try:
            # This would typically update a preferences table
            # For now, just return the updated preferences
            logger.info(f"Notification preferences updated by user {current_user['id']}")
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}")
            raise
    
    @with_resilience("notification_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def get_notification_stats(
        self,
        current_user: Dict[str, Any],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get notification statistics.
        
        Args:
            current_user: Current authenticated user
            start_date: Start date for stats
            end_date: End date for stats
            
        Returns:
            Notification statistics
        """
        try:
            # Build base conditions
            base_conditions = [Notification.recipient_id == current_user["id"]]
            
            if start_date:
                base_conditions.append(Notification.created_at >= start_date)
            if end_date:
                base_conditions.append(Notification.created_at <= end_date)
            
            # Get total notifications
            total_query = select(func.count(Notification.id)).where(and_(*base_conditions))
            result = await self.db.execute(total_query)
            total_notifications = result.scalar()
            
            # Get notifications by status
            stats = {
                "total_notifications": total_notifications,
                "pending": 0,
                "sent": 0,
                "delivered": 0,
                "read": 0,
                "failed": 0,
                "cancelled": 0,
                "unread_notifications": 0,
                "by_type": {},
                "by_priority": {},
                "by_channel": {},
                "delivery_rate": 0.0,
                "read_rate": 0.0,
                "failure_rate": 0.0,
                "notifications_today": 0,
                "notifications_this_week": 0,
                "notifications_this_month": 0
            }
            
            # Count by status
            for status in NotificationStatus:
                status_query = select(func.count(Notification.id)).where(
                    and_(*base_conditions, Notification.status == status)
                )
                result = await self.db.execute(status_query)
                stats[status.value] = result.scalar()
            
            # Count unread
            unread_query = select(func.count(Notification.id)).where(
                and_(*base_conditions, Notification.status == NotificationStatus.DELIVERED)
            )
            result = await self.db.execute(unread_query)
            stats["unread_notifications"] = result.scalar()
            
            # Calculate rates
            if total_notifications > 0:
                stats["delivery_rate"] = (stats["delivered"] + stats["read"]) / total_notifications
                stats["read_rate"] = stats["read"] / total_notifications
                stats["failure_rate"] = stats["failed"] / total_notifications
            
            # Count by type
            for notification_type in NotificationType:
                type_query = select(func.count(Notification.id)).where(
                    and_(*base_conditions, Notification.notification_type == notification_type)
                )
                result = await self.db.execute(type_query)
                stats["by_type"][notification_type.value] = result.scalar()
            
            # Count by priority
            for priority in NotificationPriority:
                priority_query = select(func.count(Notification.id)).where(
                    and_(*base_conditions, Notification.priority == priority)
                )
                result = await self.db.execute(priority_query)
                stats["by_priority"][priority.value] = result.scalar()
            
            # Count by channel
            from ..models.notification import NotificationChannel
            for channel in NotificationChannel:
                channel_query = select(func.count(Notification.id)).where(
                    and_(*base_conditions, Notification.channel == channel)
                )
                result = await self.db.execute(channel_query)
                stats["by_channel"][channel.value] = result.scalar()
            
            # Time-based stats
            today = datetime.utcnow().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            today_query = select(func.count(Notification.id)).where(
                and_(*base_conditions, func.date(Notification.created_at) == today)
            )
            result = await self.db.execute(today_query)
            stats["notifications_today"] = result.scalar()
            
            week_query = select(func.count(Notification.id)).where(
                and_(*base_conditions, func.date(Notification.created_at) >= week_ago)
            )
            result = await self.db.execute(week_query)
            stats["notifications_this_week"] = result.scalar()
            
            month_query = select(func.count(Notification.id)).where(
                and_(*base_conditions, func.date(Notification.created_at) >= month_ago)
            )
            result = await self.db.execute(month_query)
            stats["notifications_this_month"] = result.scalar()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            raise
    
    # Private helper methods
    async def _get_notification_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Get notification by ID."""
        query = select(Notification).where(Notification.id == notification_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    def _can_access_notification(self, notification: Notification, current_user: Dict[str, Any]) -> bool:
        """Check if user can access notification."""
        if current_user["user_type"] == "admin":
            return True
        
        return notification.recipient_id == current_user["id"]
    
    def _can_modify_notification(self, notification: Notification, current_user: Dict[str, Any]) -> bool:
        """Check if user can modify notification."""
        if current_user["user_type"] == "admin":
            return True
        
        # Only sender or recipient can modify notifications
        return notification.recipient_id == current_user["id"]
    
    async def _validate_notification_data(self, notification_data: NotificationCreate) -> None:
        """Validate notification data."""
        # Check if recipient exists and is valid
        # This would typically check against user service
        if not notification_data.recipient_id:
            raise ValidationException("Recipient ID is required")
        
        # Check content length
        if len(notification_data.title.strip()) == 0:
            raise ValidationException("Notification title cannot be empty")
        
        if len(notification_data.content.strip()) == 0:
            raise ValidationException("Notification content cannot be empty")
        
        if len(notification_data.title) > 200:
            raise ValidationException("Notification title too long")
        
        if len(notification_data.content) > 2000:
            raise ValidationException("Notification content too long")
    
    async def _get_user_notification_preferences(self, user_id: UUID) -> Dict[str, Any]:
        """Get user notification preferences."""
        # This would typically fetch from a preferences table
        # For now, return default preferences
        return {
            "email_notifications": True,
            "sms_notifications": False,
            "push_notifications": True,
            "in_app_notifications": True,
            "appointment_notifications": True,
            "message_notifications": True,
            "consultation_notifications": True,
            "reminder_notifications": True,
            "system_notifications": True,
            "security_notifications": True
        }
    
    def _should_send_notification(self, notification_data: NotificationCreate, preferences: Dict[str, Any]) -> bool:
        """Check if notification should be sent based on user preferences."""
        # Check channel preferences
        if notification_data.channel.value == "email" and not preferences.get("email_notifications", True):
            return False
        
        if notification_data.channel.value == "sms" and not preferences.get("sms_notifications", False):
            return False
        
        if notification_data.channel.value == "push" and not preferences.get("push_notifications", True):
            return False
        
        if notification_data.channel.value == "in_app" and not preferences.get("in_app_notifications", True):
            return False
        
        # Check type preferences
        type_preference_key = f"{notification_data.notification_type.value}_notifications"
        if not preferences.get(type_preference_key, True):
            return False
        
        return True
    
    async def _deliver_notification(self, notification: Notification) -> None:
        """Deliver notification asynchronously."""
        try:
            # Simulate delivery delay
            await asyncio.sleep(1)
            
            # Update notification status
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            notification.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            # Simulate delivery
            await asyncio.sleep(0.5)
            
            notification.status = NotificationStatus.DELIVERED
            notification.delivered_at = datetime.utcnow()
            notification.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Notification delivered: {notification.id}")
            
        except Exception as e:
            logger.error(f"Error delivering notification {notification.id}: {e}")
            notification.status = NotificationStatus.FAILED
            notification.delivery_attempts += 1
            notification.last_error = str(e)
            notification.error_count += 1
            await self.db.commit() 