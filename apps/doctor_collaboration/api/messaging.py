"""
Messaging API endpoints for Doctor Collaboration Service.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, UploadFile, File
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc

from common.database.connection import get_async_db
from common.middleware.auth import get_current_user
from common.middleware.rate_limiter import rate_limit
from common.middleware.security import security_headers
from common.utils.logging import get_logger
from common.utils.resilience import with_resilience

from ..models.messaging import (
    Message, MessageCreate, MessageUpdate, MessageResponse,
    MessageType, MessagePriority, MessageStatus, MessageFilter, MessageThread
)
from ..services.messaging_service import MessagingService

logger = get_logger(__name__)

router = APIRouter()
security = HTTPBearer()


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=20)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def send_message(
    message_data: MessageCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send a new message.
    
    This endpoint allows users to send messages to other users.
    """
    try:
        service = MessagingService(db)
        
        # Check if user has permission to send messages
        if current_user["user_type"] not in ["patient", "doctor", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to send messages"
            )
        
        # Send message
        message = await service.send_message(
            message_data=message_data,
            sender_id=current_user["id"]
        )
        
        logger.info(f"Message sent: {message.id} from user {current_user['id']}")
        
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


@router.post("/with-attachment", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=60.0, max_retries=3)
async def send_message_with_attachment(
    recipient_id: UUID = Query(..., description="Recipient user ID"),
    message_type: MessageType = Query(MessageType.TEXT, description="Message type"),
    priority: MessagePriority = Query(MessagePriority.NORMAL, description="Message priority"),
    content: str = Query(..., description="Message content"),
    subject: Optional[str] = Query(None, description="Message subject"),
    appointment_id: Optional[UUID] = Query(None, description="Related appointment ID"),
    consultation_id: Optional[UUID] = Query(None, description="Related consultation ID"),
    thread_id: Optional[UUID] = Query(None, description="Message thread ID"),
    parent_message_id: Optional[UUID] = Query(None, description="Parent message ID"),
    file: UploadFile = File(..., description="Attachment file"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send a message with file attachment.
    
    This endpoint allows users to send messages with file attachments.
    """
    try:
        service = MessagingService(db)
        
        # Create message data
        message_data = MessageCreate(
            recipient_id=recipient_id,
            message_type=message_type,
            priority=priority,
            content=content,
            subject=subject,
            appointment_id=appointment_id,
            consultation_id=consultation_id,
            thread_id=thread_id,
            parent_message_id=parent_message_id
        )
        
        # Send message with attachment
        message = await service.send_message_with_attachment(
            message_data=message_data,
            file=file,
            sender_id=current_user["id"]
        )
        
        logger.info(f"Message with attachment sent: {message.id} from user {current_user['id']}")
        
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message with attachment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message with attachment"
        )


@router.get("/", response_model=List[MessageResponse])
@rate_limit(requests_per_minute=60)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=100, timeout=30.0, max_retries=3)
async def list_messages(
    sender_id: Optional[UUID] = Query(None, description="Filter by sender ID"),
    recipient_id: Optional[UUID] = Query(None, description="Filter by recipient ID"),
    message_type: Optional[MessageType] = Query(None, description="Filter by message type"),
    priority: Optional[MessagePriority] = Query(None, description="Filter by priority"),
    status: Optional[MessageStatus] = Query(None, description="Filter by status"),
    appointment_id: Optional[UUID] = Query(None, description="Filter by appointment ID"),
    consultation_id: Optional[UUID] = Query(None, description="Filter by consultation ID"),
    thread_id: Optional[UUID] = Query(None, description="Filter by thread ID"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    unread_only: bool = Query(False, description="Show only unread messages"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List messages with optional filtering.
    
    This endpoint returns messages based on the provided filters.
    Users can only see messages they are involved in.
    """
    try:
        service = MessagingService(db)
        
        # Create filter object
        message_filter = MessageFilter(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            priority=priority,
            status=status,
            appointment_id=appointment_id,
            consultation_id=consultation_id,
            thread_id=thread_id,
            start_date=start_date,
            end_date=end_date,
            unread_only=unread_only,
            limit=limit,
            offset=offset
        )
        
        # Get messages
        messages = await service.list_messages(
            filter_params=message_filter,
            current_user=current_user
        )
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list messages"
        )


@router.get("/{message_id}", response_model=MessageResponse)
@rate_limit(requests_per_minute=100)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=100, timeout=30.0, max_retries=3)
async def get_message(
    message_id: UUID = Path(..., description="Message ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get message by ID.
    
    This endpoint returns detailed information about a specific message.
    Users can only access messages they are involved in.
    """
    try:
        service = MessagingService(db)
        
        message = await service.get_message(
            message_id=message_id,
            current_user=current_user
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get message"
        )


@router.put("/{message_id}", response_model=MessageResponse)
@rate_limit(requests_per_minute=20)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def update_message(
    message_id: UUID = Path(..., description="Message ID"),
    message_data: MessageUpdate = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update message.
    
    This endpoint allows updating message details.
    Only the sender can update their own messages.
    """
    try:
        service = MessagingService(db)
        
        message = await service.update_message(
            message_id=message_id,
            message_data=message_data,
            current_user=current_user
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        logger.info(f"Message updated: {message_id} by user {current_user['id']}")
        
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update message"
        )


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
@rate_limit(requests_per_minute=10)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=20, timeout=30.0, max_retries=3)
async def delete_message(
    message_id: UUID = Path(..., description="Message ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete message.
    
    This endpoint allows deleting messages.
    Only the sender can delete their own messages.
    """
    try:
        service = MessagingService(db)
        
        success = await service.delete_message(
            message_id=message_id,
            current_user=current_user
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        logger.info(f"Message deleted: {message_id} by user {current_user['id']}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete message"
        )


@router.post("/{message_id}/read", response_model=MessageResponse)
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=100, timeout=30.0, max_retries=3)
async def mark_message_as_read(
    message_id: UUID = Path(..., description="Message ID"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Mark message as read.
    
    This endpoint marks a message as read by the recipient.
    """
    try:
        service = MessagingService(db)
        
        message = await service.mark_as_read(
            message_id=message_id,
            current_user=current_user
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        logger.info(f"Message marked as read: {message_id} by user {current_user['id']}")
        
        return message
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking message as read {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark message as read"
        )


@router.get("/threads/", response_model=List[MessageThread])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def list_message_threads(
    limit: int = Query(50, ge=1, le=100, description="Number of threads to return"),
    offset: int = Query(0, ge=0, description="Number of threads to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List message threads.
    
    This endpoint returns message threads for the current user.
    """
    try:
        service = MessagingService(db)
        
        threads = await service.list_message_threads(
            current_user=current_user,
            limit=limit,
            offset=offset
        )
        
        return threads
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing message threads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list message threads"
        )


@router.get("/unread/", response_model=List[MessageResponse])
@rate_limit(requests_per_minute=60)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=100, timeout=30.0, max_retries=3)
async def get_unread_messages(
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get unread messages.
    
    This endpoint returns unread messages for the current user.
    """
    try:
        service = MessagingService(db)
        
        messages = await service.get_unread_messages(
            current_user=current_user,
            limit=limit,
            offset=offset
        )
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting unread messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get unread messages"
        )


@router.post("/{message_id}/reply", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests_per_minute=20)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def reply_to_message(
    message_id: UUID = Path(..., description="Message ID to reply to"),
    content: str = Query(..., description="Reply content"),
    message_type: MessageType = Query(MessageType.TEXT, description="Message type"),
    priority: MessagePriority = Query(MessagePriority.NORMAL, description="Message priority"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Reply to a message.
    
    This endpoint allows users to reply to existing messages.
    """
    try:
        service = MessagingService(db)
        
        # Get original message to determine recipient
        original_message = await service.get_message(
            message_id=message_id,
            current_user=current_user
        )
        
        if not original_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original message not found"
            )
        
        # Create reply message
        reply_data = MessageCreate(
            recipient_id=original_message.sender_id,
            message_type=message_type,
            priority=priority,
            content=content,
            thread_id=original_message.thread_id or original_message.id,
            parent_message_id=message_id,
            appointment_id=original_message.appointment_id,
            consultation_id=original_message.consultation_id
        )
        
        reply = await service.send_message(
            message_data=reply_data,
            sender_id=current_user["id"]
        )
        
        logger.info(f"Reply sent: {reply.id} to message {message_id} by user {current_user['id']}")
        
        return reply
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replying to message {message_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reply to message"
        )


@router.get("/search/", response_model=List[MessageResponse])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def search_messages(
    query: str = Query(..., description="Search query"),
    search_in: str = Query("content", description="Search in: content, subject, or both"),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to return"),
    offset: int = Query(0, ge=0, description="Number of messages to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search messages.
    
    This endpoint allows searching through messages.
    """
    try:
        service = MessagingService(db)
        
        messages = await service.search_messages(
            query=query,
            search_in=search_in,
            current_user=current_user,
            limit=limit,
            offset=offset
        )
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search messages"
        )


@router.get("/stats/", response_model=Dict[str, Any])
@rate_limit(requests_per_minute=30)
@security_headers
@with_resilience("doctor_collaboration", max_concurrent=50, timeout=30.0, max_retries=3)
async def get_message_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get message statistics.
    
    This endpoint returns message statistics for the current user.
    """
    try:
        service = MessagingService(db)
        
        stats = await service.get_message_stats(
            current_user=current_user
        )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get message statistics"
        ) 