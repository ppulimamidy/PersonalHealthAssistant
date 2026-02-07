"""
Notifications API endpoints for Doctor Collaboration Service.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from common.middleware.rate_limiter import rate_limit
from common.middleware.security import security_headers
from common.utils.logging import get_logger
from common.utils.resilience import with_resilience

from ..models.notification import (
    Notification, NotificationCreate, NotificationUpdate, NotificationResponse,
    NotificationType, NotificationPriority, NotificationStatus, NotificationFilter
)
from ..services.notification_service import NotificationService

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=20)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new notification.
    
    This endpoint allows creating notifications for users.
    """
    try:
        service = NotificationService(db)
        
        # Check if user has permission to create notifications
        if current_user["user_type"] not in ["doctor", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create notifications"
            )
        
        # Create notification
        notification = await service.create_notification(
            notification_data=notification_data,
            created_by=current_user["id"]
        )
        
        logger.info(f"Notification created: {notification.id} by user {current_user['id']}")
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create notification"
        )


@router.get("/", response_model=List[NotificationResponse])
@rate_limit(requests_per_minute=60)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=100, timeout=30.0, max_retries=3)
async def list_notifications(
    recipient_id: Optional[UUID] = Query(None, description="Filter by recipient ID"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    priority: Optional[NotificationPriority] = Query(None, description="Filter by priority"),
    status: Optional[NotificationStatus] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List notifications with optional filtering.
    
    This endpoint returns notifications based on the provided filters.
    Users can only see notifications sent to them.
    """
    try:
        service = NotificationService(db)
        
        # Create filter object
        notification_filter = NotificationFilter(
            recipient_id=recipient_id,
            notification_type=notification_type,
            priority=priority,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
        
        # Get notifications
        notifications = await service.list_notifications(
            filter_params=notification_filter,
            current_user=current_user
        )
        
        return notifications
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list notifications"
        )


@router.get("/{notification_id}", response_model=NotificationResponse)
@rate_limit(requests_per_minute=100)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=100, timeout=30.0, max_retries=3)
async def get_notification(
    notification_id: UUID = Path(..., description="Notification ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get notification by ID.
    
    This endpoint returns detailed information about a specific notification.
    Users can only access notifications sent to them.
    """
    try:
        service = NotificationService(db)
        
        notification = await service.get_notification(
            notification_id=notification_id,
            current_user=current_user
        )
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification {notification_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification"
        )


@router.put("/{notification_id}", response_model=NotificationResponse)
@rate_limit(requests_per_minute=20)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def update_notification(
    notification_id: UUID = Path(..., description="Notification ID"),
    notification_data: NotificationUpdate = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update notification.
    
    This endpoint allows updating notification details.
    Only the sender or admin can update notifications.
    """
    try:
        service = NotificationService(db)
        
        notification = await service.update_notification(
            notification_id=notification_id,
            notification_data=notification_data,
            current_user=current_user
        )
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        logger.info(f"Notification updated: {notification_id} by user {current_user['id']}")
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification {notification_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification"
        )


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def delete_notification(
    notification_id: UUID = Path(..., description="Notification ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete notification.
    
    This endpoint allows deleting notifications.
    Only the sender or admin can delete notifications.
    """
    try:
        service = NotificationService(db)
        
        success = await service.delete_notification(
            notification_id=notification_id,
            current_user=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        logger.info(f"Notification deleted: {notification_id} by user {current_user['id']}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification {notification_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )


@router.post("/{notification_id}/mark-read", response_model=NotificationResponse)
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=100, timeout=30.0, max_retries=3)
async def mark_notification_as_read(
    notification_id: UUID = Path(..., description="Notification ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Mark notification as read.
    
    This endpoint marks a notification as read by the recipient.
    """
    try:
        service = NotificationService(db)
        
        notification = await service.mark_as_read(
            notification_id=notification_id,
            current_user=current_user
        )
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        logger.info(f"Notification marked as read: {notification_id} by user {current_user['id']}")
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read {notification_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )


@router.post("/mark-all-read", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def mark_all_notifications_as_read(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Mark all notifications as read.
    
    This endpoint marks all unread notifications as read for the current user.
    """
    try:
        service = NotificationService(db)
        
        result = await service.mark_all_as_read(
            current_user=current_user
        )
        
        logger.info(f"All notifications marked as read by user {current_user['id']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking all notifications as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark all notifications as read"
        )


@router.get("/unread/", response_model=List[NotificationResponse])
@rate_limit(requests_per_minute=60)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=100, timeout=30.0, max_retries=3)
async def get_unread_notifications(
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get unread notifications.
    
    This endpoint returns unread notifications for the current user.
    """
    try:
        service = NotificationService(db)
        
        notifications = await service.get_unread_notifications(
            current_user=current_user,
            limit=limit,
            offset=offset
        )
        
        return notifications
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unread notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread notifications"
        )


@router.post("/send-appointment-reminder", response_model=NotificationResponse)
@rate_limit(requests_per_minute=5)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=10, timeout=30.0, max_retries=3)
async def send_appointment_reminder(
    appointment_id: UUID = Query(..., description="Appointment ID"),
    reminder_type: str = Query("email", description="Reminder type: email, sms, push"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send appointment reminder.
    
    This endpoint sends appointment reminders to patients.
    """
    try:
        service = NotificationService(db)
        
        notification = await service.send_appointment_reminder(
            appointment_id=appointment_id,
            reminder_type=reminder_type,
            current_user=current_user
        )
        
        logger.info(f"Appointment reminder sent: {appointment_id} by user {current_user['id']}")
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending appointment reminder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send appointment reminder"
        )


@router.post("/send-message-notification", response_model=NotificationResponse)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def send_message_notification(
    message_id: UUID = Query(..., description="Message ID"),
    notification_type: str = Query("push", description="Notification type: email, sms, push"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send message notification.
    
    This endpoint sends notifications for new messages.
    """
    try:
        service = NotificationService(db)
        
        notification = await service.send_message_notification(
            message_id=message_id,
            notification_type=notification_type,
            current_user=current_user
        )
        
        logger.info(f"Message notification sent: {message_id} by user {current_user['id']}")
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message notification"
        )


@router.post("/send-consultation-notification", response_model=NotificationResponse)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def send_consultation_notification(
    consultation_id: UUID = Query(..., description="Consultation ID"),
    notification_type: str = Query("email", description="Notification type: email, sms, push"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send consultation notification.
    
    This endpoint sends notifications for consultation updates.
    """
    try:
        service = NotificationService(db)
        
        notification = await service.send_consultation_notification(
            consultation_id=consultation_id,
            notification_type=notification_type,
            current_user=current_user
        )
        
        logger.info(f"Consultation notification sent: {consultation_id} by user {current_user['id']}")
        
        return notification
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending consultation notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send consultation notification"
        )


@router.get("/preferences/", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def get_notification_preferences(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get notification preferences.
    
    This endpoint returns notification preferences for the current user.
    """
    try:
        service = NotificationService(db)
        
        preferences = await service.get_notification_preferences(
            current_user=current_user
        )
        
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification preferences"
        )


@router.put("/preferences/", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def update_notification_preferences(
    preferences: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update notification preferences.
    
    This endpoint allows updating notification preferences for the current user.
    """
    try:
        service = NotificationService(db)
        
        updated_preferences = await service.update_notification_preferences(
            preferences=preferences,
            current_user=current_user
        )
        
        logger.info(f"Notification preferences updated by user {current_user['id']}")
        
        return updated_preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification preferences"
        )


@router.get("/stats/", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def get_notification_stats(
    start_date: Optional[datetime] = Query(None, description="Start date for stats"),
    end_date: Optional[datetime] = Query(None, description="End date for stats"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get notification statistics.
    
    This endpoint returns notification statistics for the current user.
    """
    try:
        service = NotificationService(db)
        
        stats = await service.get_notification_stats(
            current_user=current_user,
            start_date=start_date,
            end_date=end_date
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification statistics"
        ) 