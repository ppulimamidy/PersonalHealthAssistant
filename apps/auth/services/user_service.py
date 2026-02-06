"""
User management service for authentication.

This service handles user-related operations including:
- User CRUD operations
- User profile management
- User preferences
- User status management
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from ..models.user import User, UserCreate, UserUpdate, UserResponse
from ..models.roles import UserRole, Role
from common.utils.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            user = User(**user_data.dict())
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Created user: {user.id}")
            return user
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Get user by ID."""
        try:
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            result = await self.db.execute(
                select(User).where(User.email == email)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            raise
    
    async def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        try:
            update_data = user_data.dict(exclude_unset=True)
            if update_data:
                await self.db.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(**update_data, updated_at=datetime.utcnow())
                )
                await self.db.commit()
                
                # Return updated user
                return await self.get_user_by_id(user_id)
            return None
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Delete a user."""
        try:
            result = await self.db.execute(
                delete(User).where(User.id == user_id)
            )
            await self.db.commit()
            deleted = result.rowcount > 0
            if deleted:
                logger.info(f"Deleted user: {user_id}")
            return deleted
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise
    
    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List users with pagination."""
        try:
            result = await self.db.execute(
                select(User)
                .offset(skip)
                .limit(limit)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise
    
    async def get_user_roles(self, user_id: uuid.UUID) -> List[Role]:
        """Get all roles for a user."""
        try:
            result = await self.db.execute(
                select(Role)
                .join(UserRole)
                .where(UserRole.user_id == user_id)
                .where(UserRole.is_active == True)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to get roles for user {user_id}: {e}")
            raise
    
    async def assign_role_to_user(self, user_id: uuid.UUID, role_id: uuid.UUID, assigned_by: Optional[uuid.UUID] = None) -> bool:
        """Assign a role to a user."""
        try:
            # Check if role assignment already exists
            existing = await self.db.execute(
                select(UserRole)
                .where(UserRole.user_id == user_id)
                .where(UserRole.role_id == role_id)
            )
            
            if existing.scalar_one_or_none():
                return False  # Role already assigned
            
            user_role = UserRole(
                user_id=user_id,
                role_id=role_id,
                assigned_by=assigned_by
            )
            self.db.add(user_role)
            await self.db.commit()
            logger.info(f"Assigned role {role_id} to user {user_id}")
            return True
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to assign role {role_id} to user {user_id}: {e}")
            raise
    
    async def remove_role_from_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> bool:
        """Remove a role from a user."""
        try:
            result = await self.db.execute(
                delete(UserRole)
                .where(UserRole.user_id == user_id)
                .where(UserRole.role_id == role_id)
            )
            await self.db.commit()
            removed = result.rowcount > 0
            if removed:
                logger.info(f"Removed role {role_id} from user {user_id}")
            return removed
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to remove role {role_id} from user {user_id}: {e}")
            raise
    
    async def update_last_login(self, user_id: uuid.UUID) -> None:
        """Update user's last login timestamp."""
        try:
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(last_login_at=datetime.utcnow())
            )
            await self.db.commit()
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update last login for user {user_id}: {e}")
            raise 