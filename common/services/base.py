"""
Base Service Classes
Common service functionality and base classes for all services.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic, Union
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, update, delete, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel

from common.models.base import (
    BaseEntityModel, PaginationModel, SortModel, FilterModel, 
    PaginatedResponseModel, ResponseModel, ErrorResponseModel
)
from common.database.connection import get_db_manager
from common.utils.logging import get_logger, log_database_operation
from common.config.settings import get_settings

# Type variables for generic service
T = TypeVar('T', bound=BaseEntityModel)
T_Create = TypeVar('T_Create', bound=BaseModel)
T_Update = TypeVar('T_Update', bound=BaseModel)
T_DB = TypeVar('T_DB')  # SQLAlchemy model


class ServiceError(Exception):
    """Base exception for service errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(ServiceError):
    """Exception raised when a resource is not found"""
    
    def __init__(self, resource_type: str, resource_id: Union[str, UUID]):
        super().__init__(
            message=f"{resource_type} with id {resource_id} not found",
            error_code="NOT_FOUND"
        )


class ValidationError(ServiceError):
    """Exception raised when validation fails"""
    
    def __init__(self, message: str, field_errors: Optional[Dict[str, str]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field_errors": field_errors or {}}
        )


class DuplicateError(ServiceError):
    """Exception raised when a duplicate resource is created"""
    
    def __init__(self, resource_type: str, field: str, value: str):
        super().__init__(
            message=f"{resource_type} with {field} '{value}' already exists",
            error_code="DUPLICATE_ERROR"
        )


class BaseService(ABC, Generic[T, T_Create, T_Update, T_DB]):
    """Base service class with common CRUD operations"""
    
    def __init__(self, db=None):
        self.logger = get_logger(self.__class__.__name__)
        self.settings = get_settings()
        self.db_manager = get_db_manager()
        self.db = db
    
    @property
    @abstractmethod
    def model_class(self) -> Type[T_DB]:
        """Return the SQLAlchemy model class"""
        pass
    
    @property
    @abstractmethod
    def schema_class(self) -> Type[T]:
        """Return the Pydantic schema class"""
        pass
    
    @property
    @abstractmethod
    def create_schema_class(self) -> Type[T_Create]:
        """Return the Pydantic create schema class"""
        pass
    
    @property
    @abstractmethod
    def update_schema_class(self) -> Type[T_Update]:
        """Return the Pydantic update schema class"""
        pass
    
    def _to_schema(self, db_obj: T_DB) -> T:
        """Convert SQLAlchemy model to Pydantic schema"""
        return self.schema_class.model_validate(db_obj)
    
    def _to_schema_list(self, db_objs: List[T_DB]) -> List[T]:
        """Convert list of SQLAlchemy models to Pydantic schemas"""
        return [self._to_schema(obj) for obj in db_objs]
    
    async def create(self, data: T_Create, session: Optional[AsyncSession] = None) -> T:
        """Create a new resource"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if session is None:
                async with self.db_manager.get_async_session() as session:
                    return await self._create_internal(data, session, start_time)
            else:
                return await self._create_internal(data, session, start_time)
        except IntegrityError as e:
            self.logger.error(f"Integrity error creating {self.model_class.__name__}: {e}")
            raise DuplicateError(
                self.model_class.__name__,
                "id",
                str(data.id) if hasattr(data, 'id') else "unknown"
            )
        except Exception as e:
            self.logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise ServiceError(f"Failed to create {self.model_class.__name__}: {str(e)}")
    
    async def _create_internal(self, data: T_Create, session: AsyncSession, start_time: float) -> T:
        """Internal create method"""
        # Convert Pydantic model to dict
        create_data = data.model_dump(exclude_unset=True)
        
        # Create SQLAlchemy model instance
        db_obj = self.model_class(**create_data)
        
        # Add to session and commit
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        
        # Log operation
        duration = asyncio.get_event_loop().time() - start_time
        log_database_operation(
            operation="CREATE",
            table=self.model_class.__tablename__,
            duration=duration,
            rows_affected=1
        )
        
        return self._to_schema(db_obj)
    
    async def get_by_id(self, id: UUID, session: Optional[AsyncSession] = None) -> T:
        """Get a resource by ID"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if session is None:
                async with self.db_manager.get_async_session() as session:
                    return await self._get_by_id_internal(id, session, start_time)
            else:
                return await self._get_by_id_internal(id, session, start_time)
        except Exception as e:
            self.logger.error(f"Error getting {self.model_class.__name__} by id {id}: {e}")
            raise ServiceError(f"Failed to get {self.model_class.__name__}: {str(e)}")
    
    async def _get_by_id_internal(self, id: UUID, session: AsyncSession, start_time: float) -> T:
        """Internal get by ID method"""
        query = select(self.model_class).where(self.model_class.id == id)
        result = await session.execute(query)
        db_obj = result.scalar_one_or_none()
        
        if db_obj is None:
            raise NotFoundError(self.model_class.__name__, id)
        
        # Log operation
        duration = asyncio.get_event_loop().time() - start_time
        log_database_operation(
            operation="SELECT",
            table=self.model_class.__tablename__,
            duration=duration,
            rows_affected=1
        )
        
        return self._to_schema(db_obj)
    
    async def get_all(
        self,
        pagination: Optional[PaginationModel] = None,
        sort: Optional[SortModel] = None,
        filters: Optional[List[FilterModel]] = None,
        session: Optional[AsyncSession] = None
    ) -> PaginatedResponseModel:
        """Get all resources with pagination, sorting, and filtering"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if session is None:
                async with self.db_manager.get_async_session() as session:
                    return await self._get_all_internal(pagination, sort, filters, session, start_time)
            else:
                return await self._get_all_internal(pagination, sort, filters, session, start_time)
        except Exception as e:
            self.logger.error(f"Error getting all {self.model_class.__name__}: {e}")
            raise ServiceError(f"Failed to get {self.model_class.__name__} list: {str(e)}")
    
    async def _get_all_internal(
        self,
        pagination: Optional[PaginationModel],
        sort: Optional[SortModel],
        filters: Optional[List[FilterModel]],
        session: AsyncSession,
        start_time: float
    ) -> PaginatedResponseModel:
        """Internal get all method"""
        # Build base query
        query = select(self.model_class)
        
        # Apply filters
        if filters:
            filter_conditions = []
            for filter_obj in filters:
                field = getattr(self.model_class, filter_obj.field, None)
                if field is not None:
                    if filter_obj.operator == "eq":
                        filter_conditions.append(field == filter_obj.value)
                    elif filter_obj.operator == "ne":
                        filter_conditions.append(field != filter_obj.value)
                    elif filter_obj.operator == "gt":
                        filter_conditions.append(field > filter_obj.value)
                    elif filter_obj.operator == "gte":
                        filter_conditions.append(field >= filter_obj.value)
                    elif filter_obj.operator == "lt":
                        filter_conditions.append(field < filter_obj.value)
                    elif filter_obj.operator == "lte":
                        filter_conditions.append(field <= filter_obj.value)
                    elif filter_obj.operator == "like":
                        filter_conditions.append(field.like(f"%{filter_obj.value}%"))
                    elif filter_obj.operator == "in":
                        filter_conditions.append(field.in_(filter_obj.value))
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        # Get total count
        count_query = select(self.model_class).where(query.whereclause) if query.whereclause else select(self.model_class)
        count_result = await session.execute(count_query)
        total = len(count_result.scalars().all())
        
        # Apply sorting
        if sort:
            field = getattr(self.model_class, sort.field, None)
            if field is not None:
                if sort.order == "desc":
                    query = query.order_by(desc(field))
                else:
                    query = query.order_by(asc(field))
        
        # Apply pagination
        if pagination:
            offset = (pagination.page - 1) * pagination.size
            query = query.offset(offset).limit(pagination.size)
        
        # Execute query
        result = await session.execute(query)
        db_objs = result.scalars().all()
        
        # Calculate pagination info
        if pagination:
            pages = (total + pagination.size - 1) // pagination.size
            has_next = pagination.page < pages
            has_prev = pagination.page > 1
        else:
            pages = 1
            has_next = False
            has_prev = False
        
        # Log operation
        duration = asyncio.get_event_loop().time() - start_time
        log_database_operation(
            operation="SELECT",
            table=self.model_class.__tablename__,
            duration=duration,
            rows_affected=len(db_objs)
        )
        
        return PaginatedResponseModel(
            items=self._to_schema_list(db_objs),
            total=total,
            page=pagination.page if pagination else 1,
            size=pagination.size if pagination else total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
    
    async def update(
        self,
        id: UUID,
        data: T_Update,
        session: Optional[AsyncSession] = None
    ) -> T:
        """Update a resource"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if session is None:
                async with self.db_manager.get_async_session() as session:
                    return await self._update_internal(id, data, session, start_time)
            else:
                return await self._update_internal(id, data, session, start_time)
        except IntegrityError as e:
            self.logger.error(f"Integrity error updating {self.model_class.__name__} {id}: {e}")
            raise DuplicateError(
                self.model_class.__name__,
                "id",
                str(id)
            )
        except Exception as e:
            self.logger.error(f"Error updating {self.model_class.__name__} {id}: {e}")
            raise ServiceError(f"Failed to update {self.model_class.__name__}: {str(e)}")
    
    async def _update_internal(
        self,
        id: UUID,
        data: T_Update,
        session: AsyncSession,
        start_time: float
    ) -> T:
        """Internal update method"""
        # Check if resource exists
        await self._get_by_id_internal(id, session, start_time)
        
        # Convert Pydantic model to dict
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Update resource
        query = (
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**update_data)
        )
        result = await session.execute(query)
        await session.commit()
        
        if result.rowcount == 0:
            raise NotFoundError(self.model_class.__name__, id)
        
        # Get updated resource
        return await self._get_by_id_internal(id, session, start_time)
    
    async def delete(self, id: UUID, session: Optional[AsyncSession] = None) -> bool:
        """Delete a resource"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if session is None:
                async with self.db_manager.get_async_session() as session:
                    return await self._delete_internal(id, session, start_time)
            else:
                return await self._delete_internal(id, session, start_time)
        except Exception as e:
            self.logger.error(f"Error deleting {self.model_class.__name__} {id}: {e}")
            raise ServiceError(f"Failed to delete {self.model_class.__name__}: {str(e)}")
    
    async def _delete_internal(self, id: UUID, session: AsyncSession, start_time: float) -> bool:
        """Internal delete method"""
        # Check if resource exists
        await self._get_by_id_internal(id, session, start_time)
        
        # Delete resource
        query = delete(self.model_class).where(self.model_class.id == id)
        result = await session.execute(query)
        await session.commit()
        
        if result.rowcount == 0:
            raise NotFoundError(self.model_class.__name__, id)
        
        # Log operation
        duration = asyncio.get_event_loop().time() - start_time
        log_database_operation(
            operation="DELETE",
            table=self.model_class.__tablename__,
            duration=duration,
            rows_affected=1
        )
        
        return True
    
    async def count(self, filters: Optional[List[FilterModel]] = None, session: Optional[AsyncSession] = None) -> int:
        """Count resources with optional filters"""
        try:
            if session is None:
                async with self.db_manager.get_async_session() as session:
                    return await self._count_internal(filters, session)
            else:
                return await self._count_internal(filters, session)
        except Exception as e:
            self.logger.error(f"Error counting {self.model_class.__name__}: {e}")
            raise ServiceError(f"Failed to count {self.model_class.__name__}: {str(e)}")
    
    async def _count_internal(self, filters: Optional[List[FilterModel]], session: AsyncSession) -> int:
        """Internal count method"""
        query = select(self.model_class)
        
        # Apply filters
        if filters:
            filter_conditions = []
            for filter_obj in filters:
                field = getattr(self.model_class, filter_obj.field, None)
                if field is not None:
                    if filter_obj.operator == "eq":
                        filter_conditions.append(field == filter_obj.value)
                    elif filter_obj.operator == "ne":
                        filter_conditions.append(field != filter_obj.value)
                    elif filter_obj.operator == "gt":
                        filter_conditions.append(field > filter_obj.value)
                    elif filter_obj.operator == "gte":
                        filter_conditions.append(field >= filter_obj.value)
                    elif filter_obj.operator == "lt":
                        filter_conditions.append(field < filter_obj.value)
                    elif filter_obj.operator == "lte":
                        filter_conditions.append(field <= filter_obj.value)
                    elif filter_obj.operator == "like":
                        filter_conditions.append(field.like(f"%{filter_obj.value}%"))
                    elif filter_obj.operator == "in":
                        filter_conditions.append(field.in_(filter_obj.value))
            
            if filter_conditions:
                query = query.where(and_(*filter_conditions))
        
        result = await session.execute(query)
        return len(result.scalars().all())


class SyncBaseService(ABC, Generic[T, T_Create, T_Update, T_DB]):
    """Synchronous base service class with common CRUD operations"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.settings = get_settings()
        self.db_manager = get_db_manager()
    
    @property
    @abstractmethod
    def model_class(self) -> Type[T_DB]:
        """Return the SQLAlchemy model class"""
        pass
    
    @property
    @abstractmethod
    def schema_class(self) -> Type[T]:
        """Return the Pydantic schema class"""
        pass
    
    @property
    @abstractmethod
    def create_schema_class(self) -> Type[T_Create]:
        """Return the Pydantic create schema class"""
        pass
    
    @property
    @abstractmethod
    def update_schema_class(self) -> Type[T_Update]:
        """Return the Pydantic update schema class"""
        pass
    
    def _to_schema(self, db_obj: T_DB) -> T:
        """Convert SQLAlchemy model to Pydantic schema"""
        return self.schema_class.model_validate(db_obj)
    
    def _to_schema_list(self, db_objs: List[T_DB]) -> List[T]:
        """Convert list of SQLAlchemy models to Pydantic schemas"""
        return [self._to_schema(obj) for obj in db_objs]
    
    def create(self, data: T_Create, session: Optional[Session] = None) -> T:
        """Create a new resource (synchronous)"""
        try:
            if session is None:
                with self.db_manager.get_session() as session:
                    return self._create_internal(data, session)
            else:
                return self._create_internal(data, session)
        except IntegrityError as e:
            self.logger.error(f"Integrity error creating {self.model_class.__name__}: {e}")
            raise DuplicateError(
                self.model_class.__name__,
                "id",
                str(data.id) if hasattr(data, 'id') else "unknown"
            )
        except Exception as e:
            self.logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise ServiceError(f"Failed to create {self.model_class.__name__}: {str(e)}")
    
    def _create_internal(self, data: T_Create, session: Session) -> T:
        """Internal create method (synchronous)"""
        # Convert Pydantic model to dict
        create_data = data.model_dump(exclude_unset=True)
        
        # Create SQLAlchemy model instance
        db_obj = self.model_class(**create_data)
        
        # Add to session and commit
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        
        return self._to_schema(db_obj)
    
    def get_by_id(self, id: UUID, session: Optional[Session] = None) -> T:
        """Get a resource by ID (synchronous)"""
        try:
            if session is None:
                with self.db_manager.get_session() as session:
                    return self._get_by_id_internal(id, session)
            else:
                return self._get_by_id_internal(id, session)
        except Exception as e:
            self.logger.error(f"Error getting {self.model_class.__name__} by id {id}: {e}")
            raise ServiceError(f"Failed to get {self.model_class.__name__}: {str(e)}")
    
    def _get_by_id_internal(self, id: UUID, session: Session) -> T:
        """Internal get by ID method (synchronous)"""
        db_obj = session.query(self.model_class).filter(self.model_class.id == id).first()
        
        if db_obj is None:
            raise NotFoundError(self.model_class.__name__, id)
        
        return self._to_schema(db_obj) 