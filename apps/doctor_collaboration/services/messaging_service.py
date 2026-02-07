"""
Messaging Service for Doctor Collaboration Service.

This service handles all messaging-related business logic.
"""

import asyncio
import aiofiles
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc, func
from sqlalchemy.orm import selectinload
from fastapi import UploadFile

from common.utils.logging import get_logger
from common.utils.resilience import with_resilience
from common.exceptions import (
    NotFoundError,
    ValidationError,
    ConflictError,
    DatabaseError,
    ServiceError
)

from ..models.messaging import (
    Message, MessageCreate, MessageUpdate, MessageResponse,
    MessageType, MessagePriority, MessageStatus, MessageFilter, MessageThread
)

logger = get_logger(__name__)


class MessagingService:
    """Service for managing messages."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.upload_dir = "uploads/messages"
        os.makedirs(self.upload_dir, exist_ok=True)
    
    @with_resilience("messaging_service", max_concurrent=100, timeout=30.0, max_retries=3)
    async def send_message(
        self, 
        message_data: MessageCreate, 
        sender_id: UUID
    ) -> MessageResponse:
        """
        Send a new message.
        
        Args:
            message_data: Message creation data
            sender_id: ID of user sending the message
            
        Returns:
            Sent message
            
        Raises:
            ValidationException: If message data is invalid
            BusinessLogicException: If message cannot be sent
        """
        try:
            # Validate message data
            await self._validate_message_data(message_data, sender_id)
            
            # Create message
            message = Message(
                **message_data.model_dump(),
                sender_id=sender_id,
                status=MessageStatus.PENDING,
                sent_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(message)
            await self.db.commit()
            await self.db.refresh(message)
            
            # Send message (async)
            asyncio.create_task(self._deliver_message(message))
            
            # Send notifications
            asyncio.create_task(self._send_message_notifications(message))
            
            logger.info(f"Message sent: {message.id}")
            
            return MessageResponse.model_validate(message)
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error sending message: {e}")
            raise
    
    @with_resilience("messaging_service", max_concurrent=50, timeout=60.0, max_retries=3)
    async def send_message_with_attachment(
        self, 
        message_data: MessageCreate, 
        file: UploadFile,
        sender_id: UUID
    ) -> MessageResponse:
        """
        Send a message with file attachment.
        
        Args:
            message_data: Message creation data
            file: Uploaded file
            sender_id: ID of user sending the message
            
        Returns:
            Sent message with attachment
        """
        try:
            # Validate file
            await self._validate_file(file)
            
            # Save file
            file_path = await self._save_file(file, sender_id)
            
            # Create attachment metadata
            attachment_metadata = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": file.size if hasattr(file, 'size') else 0,
                "path": file_path
            }
            
            # Update message data with attachment
            message_data.attachments = [attachment_metadata]
            message_data.media_url = file_path
            message_data.media_type = file.content_type
            
            # Send message
            return await self.send_message(message_data, sender_id)
            
        except Exception as e:
            logger.error(f"Error sending message with attachment: {e}")
            raise
    
    @with_resilience("messaging_service", max_concurrent=200, timeout=30.0, max_retries=3)
    async def list_messages(
        self, 
        filter_params: MessageFilter,
        current_user: Dict[str, Any]
    ) -> List[MessageResponse]:
        """
        List messages with filtering.
        
        Args:
            filter_params: Filter parameters
            current_user: Current authenticated user
            
        Returns:
            List of messages
        """
        try:
            # Build query
            query = select(Message).options(
                selectinload(Message.sender),
                selectinload(Message.recipient),
                selectinload(Message.appointment),
                selectinload(Message.consultation)
            )
            
            # Apply filters
            conditions = []
            
            # User-based filtering (users can only see their own messages)
            conditions.append(
                or_(
                    Message.sender_id == current_user["id"],
                    Message.recipient_id == current_user["id"]
                )
            )
            
            # Apply additional filters
            if filter_params.sender_id:
                conditions.append(Message.sender_id == filter_params.sender_id)
            
            if filter_params.recipient_id:
                conditions.append(Message.recipient_id == filter_params.recipient_id)
            
            if filter_params.message_type:
                conditions.append(Message.message_type == filter_params.message_type)
            
            if filter_params.priority:
                conditions.append(Message.priority == filter_params.priority)
            
            if filter_params.status:
                conditions.append(Message.status == filter_params.status)
            
            if filter_params.appointment_id:
                conditions.append(Message.appointment_id == filter_params.appointment_id)
            
            if filter_params.consultation_id:
                conditions.append(Message.consultation_id == filter_params.consultation_id)
            
            if filter_params.thread_id:
                conditions.append(Message.thread_id == filter_params.thread_id)
            
            if filter_params.start_date:
                conditions.append(Message.sent_at >= filter_params.start_date)
            
            if filter_params.end_date:
                conditions.append(Message.sent_at <= filter_params.end_date)
            
            if filter_params.unread_only:
                conditions.append(Message.status == MessageStatus.DELIVERED)
            
            # Apply conditions
            if conditions:
                query = query.where(and_(*conditions))
            
            # Apply ordering and pagination
            query = query.order_by(desc(Message.sent_at))
            query = query.offset(filter_params.offset).limit(filter_params.limit)
            
            # Execute query
            result = await self.db.execute(query)
            messages = result.scalars().all()
            
            return [MessageResponse.model_validate(message) for message in messages]
            
        except Exception as e:
            logger.error(f"Error listing messages: {e}")
            raise
    
    @with_resilience("messaging_service", max_concurrent=200, timeout=30.0, max_retries=3)
    async def get_message(
        self, 
        message_id: UUID,
        current_user: Dict[str, Any]
    ) -> Optional[MessageResponse]:
        """
        Get message by ID.
        
        Args:
            message_id: Message ID
            current_user: Current authenticated user
            
        Returns:
            Message if found and accessible
            
        Raises:
            ResourceNotFoundException: If message not found
            PermissionDeniedException: If user cannot access message
        """
        try:
            query = select(Message).options(
                selectinload(Message.sender),
                selectinload(Message.recipient),
                selectinload(Message.appointment),
                selectinload(Message.consultation)
            ).where(Message.id == message_id)
            
            result = await self.db.execute(query)
            message = result.scalar_one_or_none()
            
            if not message:
                raise ResourceNotFoundException(f"Message {message_id} not found")
            
            # Check permissions
            if not self._can_access_message(message, current_user):
                raise PermissionDeniedException("Cannot access this message")
            
            return MessageResponse.model_validate(message)
            
        except (ResourceNotFoundException, PermissionDeniedException):
            raise
        except Exception as e:
            logger.error(f"Error getting message {message_id}: {e}")
            raise
    
    @with_resilience("messaging_service", max_concurrent=100, timeout=30.0, max_retries=3)
    async def update_message(
        self,
        message_id: UUID,
        message_data: MessageUpdate,
        current_user: Dict[str, Any]
    ) -> Optional[MessageResponse]:
        """
        Update message.
        
        Args:
            message_id: Message ID
            message_data: Update data
            current_user: Current authenticated user
            
        Returns:
            Updated message
            
        Raises:
            ResourceNotFoundException: If message not found
            PermissionDeniedException: If user cannot update message
            ValidationException: If update data is invalid
        """
        try:
            # Get message
            message = await self._get_message_by_id(message_id)
            if not message:
                raise ResourceNotFoundException(f"Message {message_id} not found")
            
            # Check permissions
            if not self._can_modify_message(message, current_user):
                raise PermissionDeniedException("Cannot modify this message")
            
            # Check if message can be updated
            if message.status in [MessageStatus.DELIVERED, MessageStatus.READ]:
                raise BusinessLogicException("Cannot update delivered or read messages")
            
            # Update message
            update_data = message_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(message, field, value)
            
            message.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(message)
            
            logger.info(f"Message updated: {message_id}")
            
            return MessageResponse.model_validate(message)
            
        except (ResourceNotFoundException, PermissionDeniedException, ValidationException, BusinessLogicException):
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating message {message_id}: {e}")
            raise
    
    @with_resilience("messaging_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def delete_message(
        self,
        message_id: UUID,
        current_user: Dict[str, Any]
    ) -> bool:
        """
        Delete message.
        
        Args:
            message_id: Message ID
            current_user: Current authenticated user
            
        Returns:
            True if deleted successfully
            
        Raises:
            ResourceNotFoundException: If message not found
            PermissionDeniedException: If user cannot delete message
        """
        try:
            # Get message
            message = await self._get_message_by_id(message_id)
            if not message:
                raise ResourceNotFoundException(f"Message {message_id} not found")
            
            # Check permissions
            if not self._can_modify_message(message, current_user):
                raise PermissionDeniedException("Cannot delete this message")
            
            # Check if message can be deleted
            if message.status in [MessageStatus.DELIVERED, MessageStatus.READ]:
                raise BusinessLogicException("Cannot delete delivered or read messages")
            
            # Delete message
            await self.db.delete(message)
            await self.db.commit()
            
            logger.info(f"Message deleted: {message_id}")
            
            return True
            
        except (ResourceNotFoundException, PermissionDeniedException, BusinessLogicException):
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting message {message_id}: {e}")
            raise
    
    @with_resilience("messaging_service", max_concurrent=200, timeout=30.0, max_retries=3)
    async def mark_as_read(
        self,
        message_id: UUID,
        current_user: Dict[str, Any]
    ) -> Optional[MessageResponse]:
        """
        Mark message as read.
        
        Args:
            message_id: Message ID
            current_user: Current authenticated user
            
        Returns:
            Updated message
        """
        try:
            message = await self._get_message_by_id(message_id)
            if not message:
                raise ResourceNotFoundException(f"Message {message_id} not found")
            
            # Check permissions
            if not self._can_access_message(message, current_user):
                raise PermissionDeniedException("Cannot access this message")
            
            # Check if user is the recipient
            if message.recipient_id != current_user["id"]:
                raise PermissionDeniedException("Only the recipient can mark messages as read")
            
            # Mark as read
            message.status = MessageStatus.READ
            message.read_at = datetime.utcnow()
            message.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(message)
            
            logger.info(f"Message marked as read: {message_id}")
            
            return MessageResponse.model_validate(message)
            
        except (ResourceNotFoundException, PermissionDeniedException):
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error marking message as read {message_id}: {e}")
            raise
    
    @with_resilience("messaging_service", max_concurrent=100, timeout=30.0, max_retries=3)
    async def list_message_threads(
        self,
        current_user: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> List[MessageThread]:
        """
        List message threads.
        
        Args:
            current_user: Current authenticated user
            limit: Number of threads to return
            offset: Number of threads to skip
            
        Returns:
            List of message threads
        """
        try:
            # Get threads for current user
            query = select(Message.thread_id).where(
                and_(
                    or_(
                        Message.sender_id == current_user["id"],
                        Message.recipient_id == current_user["id"]
                    ),
                    Message.thread_id.isnot(None)
                )
            ).distinct()
            
            result = await self.db.execute(query)
            thread_ids = result.scalars().all()
            
            threads = []
            for thread_id in thread_ids[offset:offset + limit]:
                thread = await self._get_message_thread(thread_id, current_user)
                if thread:
                    threads.append(thread)
            
            return threads
            
        except Exception as e:
            logger.error(f"Error listing message threads: {e}")
            raise
    
    @with_resilience("messaging_service", max_concurrent=100, timeout=30.0, max_retries=3)
    async def get_unread_messages(
        self,
        current_user: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> List[MessageResponse]:
        """
        Get unread messages.
        
        Args:
            current_user: Current authenticated user
            limit: Number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of unread messages
        """
        try:
            query = select(Message).options(
                selectinload(Message.sender),
                selectinload(Message.recipient)
            ).where(
                and_(
                    Message.recipient_id == current_user["id"],
                    Message.status == MessageStatus.DELIVERED
                )
            ).order_by(desc(Message.sent_at))
            
            query = query.offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            messages = result.scalars().all()
            
            return [MessageResponse.model_validate(message) for message in messages]
            
        except Exception as e:
            logger.error(f"Error getting unread messages: {e}")
            raise
    
    @with_resilience("messaging_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def search_messages(
        self,
        query: str,
        search_in: str,
        current_user: Dict[str, Any],
        limit: int = 50,
        offset: int = 0
    ) -> List[MessageResponse]:
        """
        Search messages.
        
        Args:
            query: Search query
            search_in: Search in: content, subject, or both
            current_user: Current authenticated user
            limit: Number of messages to return
            offset: Number of messages to skip
            
        Returns:
            List of matching messages
        """
        try:
            # Build search conditions
            search_conditions = []
            
            if search_in in ["content", "both"]:
                search_conditions.append(Message.content.ilike(f"%{query}%"))
            
            if search_in in ["subject", "both"]:
                search_conditions.append(Message.subject.ilike(f"%{query}%"))
            
            if not search_conditions:
                search_conditions.append(Message.content.ilike(f"%{query}%"))
            
            # Build query
            query_builder = select(Message).options(
                selectinload(Message.sender),
                selectinload(Message.recipient)
            ).where(
                and_(
                    or_(
                        Message.sender_id == current_user["id"],
                        Message.recipient_id == current_user["id"]
                    ),
                    or_(*search_conditions)
                )
            ).order_by(desc(Message.sent_at))
            
            query_builder = query_builder.offset(offset).limit(limit)
            
            result = await self.db.execute(query_builder)
            messages = result.scalars().all()
            
            return [MessageResponse.model_validate(message) for message in messages]
            
        except Exception as e:
            logger.error(f"Error searching messages: {e}")
            raise
    
    @with_resilience("messaging_service", max_concurrent=50, timeout=30.0, max_retries=3)
    async def get_message_stats(
        self,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get message statistics.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            Message statistics
        """
        try:
            # Get total messages
            total_query = select(func.count(Message.id)).where(
                or_(
                    Message.sender_id == current_user["id"],
                    Message.recipient_id == current_user["id"]
                )
            )
            result = await self.db.execute(total_query)
            total_messages = result.scalar()
            
            # Get unread messages
            unread_query = select(func.count(Message.id)).where(
                and_(
                    Message.recipient_id == current_user["id"],
                    Message.status == MessageStatus.DELIVERED
                )
            )
            result = await self.db.execute(unread_query)
            unread_messages = result.scalar()
            
            # Get sent messages
            sent_query = select(func.count(Message.id)).where(
                Message.sender_id == current_user["id"]
            )
            result = await self.db.execute(sent_query)
            sent_messages = result.scalar()
            
            # Get received messages
            received_query = select(func.count(Message.id)).where(
                Message.recipient_id == current_user["id"]
            )
            result = await self.db.execute(received_query)
            received_messages = result.scalar()
            
            return {
                "total_messages": total_messages,
                "unread_messages": unread_messages,
                "sent_messages": sent_messages,
                "received_messages": received_messages,
                "read_rate": (received_messages - unread_messages) / received_messages if received_messages > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting message stats: {e}")
            raise
    
    # Private helper methods
    async def _get_message_by_id(self, message_id: UUID) -> Optional[Message]:
        """Get message by ID."""
        query = select(Message).where(Message.id == message_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    def _can_access_message(self, message: Message, current_user: Dict[str, Any]) -> bool:
        """Check if user can access message."""
        if current_user["user_type"] == "admin":
            return True
        
        return (
            message.sender_id == current_user["id"] or
            message.recipient_id == current_user["id"]
        )
    
    def _can_modify_message(self, message: Message, current_user: Dict[str, Any]) -> bool:
        """Check if user can modify message."""
        if current_user["user_type"] == "admin":
            return True
        
        # Only sender can modify messages
        return message.sender_id == current_user["id"]
    
    async def _validate_message_data(self, message_data: MessageCreate, sender_id: UUID) -> None:
        """Validate message data."""
        # Check if recipient exists and is valid
        # This would typically check against user service
        if message_data.recipient_id == sender_id:
            raise ValidationException("Cannot send message to yourself")
        
        # Check content length
        if len(message_data.content.strip()) == 0:
            raise ValidationException("Message content cannot be empty")
        
        if len(message_data.content) > 10000:
            raise ValidationException("Message content too long")
    
    async def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        # Check file size (max 10MB)
        if hasattr(file, 'size') and file.size > 10 * 1024 * 1024:
            raise ValidationException("File size too large (max 10MB)")
        
        # Check file type
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif',
            'application/pdf', 'text/plain', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        
        if file.content_type not in allowed_types:
            raise ValidationException(f"File type {file.content_type} not allowed")
    
    async def _save_file(self, file: UploadFile, sender_id: UUID) -> str:
        """Save uploaded file."""
        # Create unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{sender_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(self.upload_dir, filename)
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return file_path
    
    async def _deliver_message(self, message: Message) -> None:
        """Deliver message asynchronously."""
        try:
            # Simulate delivery delay
            await asyncio.sleep(1)
            
            # Update message status
            message.status = MessageStatus.DELIVERED
            message.delivered_at = datetime.utcnow()
            message.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Message delivered: {message.id}")
            
        except Exception as e:
            logger.error(f"Error delivering message {message.id}: {e}")
            message.status = MessageStatus.FAILED
            message.delivery_attempts += 1
            message.last_error = str(e)
            await self.db.commit()
    
    async def _send_message_notifications(self, message: Message) -> None:
        """Send notifications for new messages."""
        try:
            # This would integrate with the notification service
            logger.info(f"Message notification sent for: {message.id}")
            
        except Exception as e:
            logger.error(f"Error sending message notification for {message.id}: {e}")
    
    async def _get_message_thread(self, thread_id: UUID, current_user: Dict[str, Any]) -> Optional[MessageThread]:
        """Get message thread details."""
        try:
            # Get messages in thread
            query = select(Message).where(
                and_(
                    Message.thread_id == thread_id,
                    or_(
                        Message.sender_id == current_user["id"],
                        Message.recipient_id == current_user["id"]
                    )
                )
            ).order_by(asc(Message.sent_at))
            
            result = await self.db.execute(query)
            messages = result.scalars().all()
            
            if not messages:
                return None
            
            # Get participants
            participants = set()
            for message in messages:
                participants.add(message.sender_id)
                participants.add(message.recipient_id)
            
            # Get unread count
            unread_query = select(func.count(Message.id)).where(
                and_(
                    Message.thread_id == thread_id,
                    Message.recipient_id == current_user["id"],
                    Message.status == MessageStatus.DELIVERED
                )
            )
            result = await self.db.execute(unread_query)
            unread_count = result.scalar()
            
            return MessageThread(
                thread_id=thread_id,
                participants=list(participants),
                messages=[MessageResponse.model_validate(msg) for msg in messages],
                unread_count=unread_count,
                last_message_at=messages[-1].sent_at,
                created_at=messages[0].created_at
            )
            
        except Exception as e:
            logger.error(f"Error getting message thread {thread_id}: {e}")
            return None 