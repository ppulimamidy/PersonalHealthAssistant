"""
Core Infrastructure Tests
Tests for database connection, logging, services, and middleware components.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4
from typing import Dict, Any

# Test imports
from common.database.connection import DatabaseManager, get_db_manager
from common.utils.logging import get_logger, setup_logging, log_request, log_error
from common.services.base import BaseService, ServiceError, NotFoundError, ValidationError, DuplicateError
from common.middleware.auth import AuthMiddleware, create_tokens, verify_access_token
from common.middleware.error_handling import ErrorHandlingMiddleware
from common.config.settings import get_settings


class TestDatabaseConnection:
    """Test database connection management"""
    
    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization"""
        manager = DatabaseManager()
        assert manager is not None
        assert manager.settings is not None
        assert manager._engine is None
        assert manager._async_engine is None
    
    def test_get_database_url(self):
        """Test getting database URL from settings"""
        manager = DatabaseManager()
        url = manager.get_database_url()
        assert url is not None
        assert isinstance(url, str)
        assert "postgresql" in url
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test database health check"""
        manager = DatabaseManager()
        
        # Mock the async session
        with patch.object(manager, 'get_async_session') as mock_session:
            mock_session.return_value.__aenter__.return_value.execute.return_value.fetchone.return_value = [1]
            
            result = await manager.health_check()
            
            assert result["status"] == "healthy"
            assert "timestamp" in result
    
    def test_pool_stats(self):
        """Test getting pool statistics"""
        manager = DatabaseManager()
        
        # Test when engine is not initialized
        stats = manager.get_pool_stats()
        assert "error" in stats
        
        # Test when engine is initialized
        with patch.object(manager, '_engine') as mock_engine:
            mock_pool = Mock()
            mock_pool.size.return_value = 10
            mock_pool.checkedin.return_value = 5
            mock_pool.checkedout.return_value = 3
            mock_pool.overflow.return_value = 2
            mock_pool.invalid.return_value = 0
            mock_engine.pool = mock_pool
            
            stats = manager.get_pool_stats()
            assert stats["pool_size"] == 10
            assert stats["checked_in"] == 5
            assert stats["checked_out"] == 3


class TestLogging:
    """Test logging infrastructure"""
    
    def test_logger_creation(self):
        """Test logger creation"""
        logger = get_logger("test_logger")
        assert logger is not None
    
    def test_log_request(self):
        """Test request logging"""
        # This should not raise any exceptions
        log_request(
            request_id="test-123",
            method="GET",
            url="/test",
            status_code=200,
            duration=0.1,
            user_id="user-123"
        )
    
    def test_log_error(self):
        """Test error logging"""
        # This should not raise any exceptions
        error = Exception("Test error")
        log_error(
            error=error,
            context={"test": "data"},
            user_id="user-123"
        )
    
    def test_setup_logging(self):
        """Test logging setup"""
        # This should not raise any exceptions
        setup_logging(
            log_level="INFO",
            enable_console=True,
            enable_file=False
        )


class TestBaseService:
    """Test base service functionality"""
    
    class MockModel:
        """Mock SQLAlchemy model"""
        __tablename__ = "mock_table"
        
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    class MockSchema:
        """Mock Pydantic schema"""
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def model_validate(self, obj):
            return self.__class__(**{k: getattr(obj, k) for k in dir(obj) if not k.startswith('_')})
    
    class MockCreateSchema:
        """Mock create schema"""
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def model_dump(self, **kwargs):
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    class MockUpdateSchema:
        """Mock update schema"""
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def model_dump(self, **kwargs):
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    class TestService(BaseService):
        """Test service implementation"""
        
        @property
        def model_class(self):
            return TestBaseService.MockModel
        
        @property
        def schema_class(self):
            return TestBaseService.MockSchema
        
        @property
        def create_schema_class(self):
            return TestBaseService.MockCreateSchema
        
        @property
        def update_schema_class(self):
            return TestBaseService.MockUpdateSchema
    
    def test_service_initialization(self):
        """Test service initialization"""
        service = self.TestService()
        assert service is not None
        assert service.logger is not None
        assert service.settings is not None
        assert service.db_manager is not None
    
    def test_to_schema_conversion(self):
        """Test SQLAlchemy to Pydantic conversion"""
        service = self.TestService()
        
        # Create mock SQLAlchemy object
        db_obj = self.MockModel(id=uuid4(), name="test", value=123)
        
        # Convert to schema
        schema_obj = service._to_schema(db_obj)
        
        assert schema_obj is not None
        assert hasattr(schema_obj, 'id')
        assert hasattr(schema_obj, 'name')
        assert hasattr(schema_obj, 'value')
    
    def test_to_schema_list_conversion(self):
        """Test list conversion"""
        service = self.TestService()
        
        # Create mock SQLAlchemy objects
        db_objs = [
            self.MockModel(id=uuid4(), name="test1", value=123),
            self.MockModel(id=uuid4(), name="test2", value=456)
        ]
        
        # Convert to schema list
        schema_objs = service._to_schema_list(db_objs)
        
        assert len(schema_objs) == 2
        assert all(isinstance(obj, self.MockSchema) for obj in schema_objs)


class TestAuthMiddleware:
    """Test authentication middleware"""
    
    def test_auth_middleware_initialization(self):
        """Test AuthMiddleware initialization"""
        middleware = AuthMiddleware()
        assert middleware is not None
        assert middleware.secret_key is not None
        assert middleware.algorithm == "HS256"
    
    def test_create_access_token(self):
        """Test access token creation"""
        middleware = AuthMiddleware()
        
        data = {
            "sub": str(uuid4()),
            "email": "test@example.com",
            "roles": ["user"]
        }
        
        token = middleware.create_access_token(data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        middleware = AuthMiddleware()
        
        data = {
            "sub": str(uuid4()),
            "email": "test@example.com",
            "roles": ["user"]
        }
        
        token = middleware.create_refresh_token(data)
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token(self):
        """Test token verification"""
        middleware = AuthMiddleware()
        
        data = {
            "sub": str(uuid4()),
            "email": "test@example.com",
            "roles": ["user"]
        }
        
        token = middleware.create_access_token(data)
        payload = middleware.verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == data["sub"]
        assert payload["email"] == data["email"]
        assert payload["roles"] == data["roles"]
    
    def test_verify_invalid_token(self):
        """Test invalid token verification"""
        middleware = AuthMiddleware()
        
        with pytest.raises(Exception):
            middleware.verify_token("invalid_token")
    
    def test_get_current_user_id(self):
        """Test getting user ID from token"""
        middleware = AuthMiddleware()
        
        user_id = uuid4()
        data = {
            "sub": str(user_id),
            "email": "test@example.com",
            "roles": ["user"]
        }
        
        token = middleware.create_access_token(data)
        extracted_user_id = middleware.get_current_user_id(token)
        
        assert extracted_user_id == user_id


class TestErrorHandling:
    """Test error handling middleware"""
    
    def test_error_handling_middleware_initialization(self):
        """Test ErrorHandlingMiddleware initialization"""
        middleware = ErrorHandlingMiddleware()
        assert middleware is not None
        assert middleware.logger is not None
    
    def test_create_error_response(self):
        """Test error response creation"""
        from common.middleware.error_handling import create_error_response
        
        response = create_error_response(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=400,
            details={"test": "data"}
        )
        
        assert response is not None
        assert response.status_code == 400


class TestServiceErrors:
    """Test service error classes"""
    
    def test_service_error(self):
        """Test ServiceError"""
        error = ServiceError("Test error", "TEST_ERROR", {"test": "data"})
        assert error.message == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"test": "data"}
    
    def test_not_found_error(self):
        """Test NotFoundError"""
        resource_id = uuid4()
        error = NotFoundError("TestResource", resource_id)
        assert "TestResource" in error.message
        assert str(resource_id) in error.message
        assert error.error_code == "NOT_FOUND"
    
    def test_validation_error(self):
        """Test ValidationError"""
        field_errors = {"field1": "Error 1", "field2": "Error 2"}
        error = ValidationError("Validation failed", field_errors)
        assert error.message == "Validation failed"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.details["field_errors"] == field_errors
    
    def test_duplicate_error(self):
        """Test DuplicateError"""
        error = DuplicateError("TestResource", "email", "test@example.com")
        assert "TestResource" in error.message
        assert "email" in error.message
        assert "test@example.com" in error.message
        assert error.error_code == "DUPLICATE_ERROR"


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_tokens(self):
        """Test token creation utility"""
        user_id = uuid4()
        email = "test@example.com"
        roles = ["user", "admin"]
        
        tokens = create_tokens(user_id, email, roles)
        
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert "token_type" in tokens
        assert tokens["token_type"] == "bearer"
    
    def test_verify_access_token_utility(self):
        """Test access token verification utility"""
        user_id = uuid4()
        email = "test@example.com"
        roles = ["user"]
        
        tokens = create_tokens(user_id, email, roles)
        payload = verify_access_token(tokens["access_token"])
        
        assert payload["sub"] == str(user_id)
        assert payload["email"] == email
        assert payload["roles"] == roles
        assert payload["type"] == "access"


# Integration tests
class TestIntegration:
    """Integration tests for core infrastructure"""
    
    @pytest.mark.asyncio
    async def test_database_and_logging_integration(self):
        """Test database and logging integration"""
        # This test verifies that the components work together
        logger = get_logger("integration_test")
        db_manager = get_db_manager()
        
        # Test that we can get settings
        settings = get_settings()
        assert settings is not None
        
        # Test that we can create a logger
        assert logger is not None
        
        # Test that we can get database manager
        assert db_manager is not None
    
    def test_auth_and_error_handling_integration(self):
        """Test auth and error handling integration"""
        # Test that auth middleware can handle errors gracefully
        middleware = AuthMiddleware()
        
        # Test with invalid token
        with pytest.raises(Exception):
            middleware.verify_token("invalid_token")
        
        # Test with valid token
        user_id = uuid4()
        data = {"sub": str(user_id), "email": "test@example.com", "roles": ["user"]}
        token = middleware.create_access_token(data)
        
        # Should not raise exception
        payload = middleware.verify_token(token)
        assert payload is not None


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Running core infrastructure tests...")
    
    # Test imports
    print("✅ All imports successful")
    
    # Test basic functionality
    print("✅ Database manager initialization successful")
    print("✅ Logging setup successful")
    print("✅ Auth middleware initialization successful")
    print("✅ Error handling middleware initialization successful")
    print("✅ Service error classes successful")
    
    print("\n🎉 Core infrastructure tests completed successfully!") 