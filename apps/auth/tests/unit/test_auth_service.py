"""
Unit tests for the authentication service.

This module contains comprehensive unit tests for all authentication
functionality including user authentication, session management,
MFA, and security features.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.auth.services.auth_service import AuthService
from apps.auth.models.user import User, UserStatus, UserType, MFAStatus
from apps.auth.models.session import Session, SessionStatus
from apps.auth.models.roles import Role, UserRole
from apps.auth.models.mfa import MFADevice, MFADeviceStatus
from apps.auth.models.audit import AuditEventType, AuditSeverity


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def auth_service(mock_db):
    """Authentication service instance."""
    return AuthService(mock_db)


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        id=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        user_type=UserType.PATIENT,
        status=UserStatus.ACTIVE,
        mfa_status=MFAStatus.DISABLED,
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJ5qK6e"  # "password123"
    )


@pytest.fixture
def sample_session(sample_user):
    """Sample session for testing."""
    return Session(
        id=uuid4(),
        user_id=sample_user.id,
        session_token="test_session_token",
        refresh_token="test_refresh_token",
        status=SessionStatus.ACTIVE,
        access_token_expires_at=datetime.utcnow() + timedelta(minutes=15),
        refresh_token_expires_at=datetime.utcnow() + timedelta(days=7)
    )


class TestAuthService:
    """Test cases for AuthService."""
    
    @pytest.mark.asyncio
    async def test_verify_password_success(self, auth_service):
        """Test successful password verification."""
        plain_password = "password123"
        hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJ5qK6e"
        
        result = auth_service.verify_password(plain_password, hashed_password)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_password_failure(self, auth_service):
        """Test failed password verification."""
        plain_password = "wrongpassword"
        hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJ5qK6e"
        
        result = auth_service.verify_password(plain_password, hashed_password)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_password_hash(self, auth_service):
        """Test password hashing."""
        password = "testpassword"
        hash_result = auth_service.get_password_hash(password)
        
        assert hash_result != password
        assert hash_result.startswith("$2b$")
        assert auth_service.verify_password(password, hash_result)
    
    @pytest.mark.asyncio
    async def test_create_access_token(self, auth_service):
        """Test access token creation."""
        data = {"sub": "test_user", "email": "test@example.com"}
        token = auth_service.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = auth_service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test_user"
        assert payload["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self, auth_service):
        """Test refresh token creation."""
        data = {"sub": "test_user"}
        token = auth_service.create_refresh_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = auth_service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test_user"
        assert payload["type"] == "refresh"
    
    @pytest.mark.asyncio
    async def test_verify_token_valid(self, auth_service):
        """Test valid token verification."""
        data = {"sub": "test_user", "email": "test@example.com"}
        token = auth_service.create_access_token(data)
        
        payload = auth_service.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test_user"
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, auth_service):
        """Test invalid token verification."""
        invalid_token = "invalid.token.here"
        payload = auth_service.verify_token(invalid_token)
        assert payload is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, sample_user):
        """Test successful user authentication."""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        auth_service.db.execute.return_value = mock_result
        
        result = await auth_service.authenticate_user(
            "test@example.com", 
            "password123",
            "127.0.0.1",
            "test-user-agent"
        )
        
        assert result is not None
        assert result.email == "test@example.com"
        assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, auth_service, sample_user):
        """Test authentication with invalid password."""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        auth_service.db.execute.return_value = mock_result
        
        result = await auth_service.authenticate_user(
            "test@example.com", 
            "wrongpassword",
            "127.0.0.1",
            "test-user-agent"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service):
        """Test authentication with inactive user."""
        inactive_user = User(
            id=uuid4(),
            email="inactive@example.com",
            first_name="Inactive",
            last_name="User",
            user_type=UserType.PATIENT,
            status=UserStatus.INACTIVE,
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJ5qK6e"
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inactive_user
        auth_service.db.execute.return_value = mock_result
        
        result = await auth_service.authenticate_user(
            "inactive@example.com", 
            "password123",
            "127.0.0.1",
            "test-user-agent"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_locked(self, auth_service):
        """Test authentication with locked user."""
        locked_user = User(
            id=uuid4(),
            email="locked@example.com",
            first_name="Locked",
            last_name="User",
            user_type=UserType.PATIENT,
            status=UserStatus.ACTIVE,
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4tbQJ5qK6e",
            account_locked_until=datetime.utcnow() + timedelta(minutes=30)
        )
        
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = locked_user
        auth_service.db.execute.return_value = mock_result
        
        result = await auth_service.authenticate_user(
            "locked@example.com", 
            "password123",
            "127.0.0.1",
            "test-user-agent"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_session(self, auth_service, sample_user):
        """Test session creation."""
        with patch.object(auth_service, 'audit_service') as mock_audit:
            session = await auth_service.create_session(
                sample_user,
                "127.0.0.1",
                "test-user-agent",
                "test-device-id"
            )
            
            assert session is not None
            assert session.user_id == sample_user.id
            assert session.session_token is not None
            assert session.refresh_token is not None
            assert session.status == SessionStatus.ACTIVE
            assert session.ip_address == "127.0.0.1"
            assert session.user_agent == "test-user-agent"
            assert session.device_id == "test-device-id"
            
            # Verify audit log was called
            mock_audit.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_session_success(self, auth_service, sample_user, sample_session):
        """Test successful session refresh."""
        # Mock database queries
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = sample_user
        
        mock_session_result = MagicMock()
        mock_session_result.scalar_one_or_none.return_value = sample_session
        
        auth_service.db.execute.side_effect = [mock_user_result, mock_session_result]
        
        with patch.object(auth_service, 'audit_service') as mock_audit:
            # Create a valid refresh token
            refresh_token = auth_service.create_refresh_token({"sub": str(sample_user.id)})
            sample_session.refresh_token = refresh_token
            
            result = await auth_service.refresh_session(
                refresh_token,
                "127.0.0.1",
                "test-user-agent"
            )
            
            assert result is not None
            assert result.user_id == sample_user.id
            
            # Verify audit log was called
            mock_audit.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refresh_session_invalid_token(self, auth_service):
        """Test session refresh with invalid token."""
        result = await auth_service.refresh_session(
            "invalid_token",
            "127.0.0.1",
            "test-user-agent"
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_revoke_session_success(self, auth_service, sample_session):
        """Test successful session revocation."""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_session
        auth_service.db.execute.return_value = mock_result
        
        with patch.object(auth_service, 'audit_service') as mock_audit:
            result = await auth_service.revoke_session(
                sample_session.id,
                sample_session.user_id,
                "test_reason"
            )
            
            assert result is True
            assert sample_session.status == SessionStatus.REVOKED
            
            # Verify audit log was called
            mock_audit.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_revoke_session_not_found(self, auth_service):
        """Test session revocation with non-existent session."""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        auth_service.db.execute.return_value = mock_result
        
        result = await auth_service.revoke_session(
            uuid4(),
            uuid4(),
            "test_reason"
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_mfa_success(self, auth_service, sample_user):
        """Test successful MFA verification."""
        with patch.object(auth_service, 'mfa_service') as mock_mfa, \
             patch.object(auth_service, 'audit_service') as mock_audit:
            
            mock_mfa.verify_code.return_value = True
            
            result = await auth_service.verify_mfa(
                sample_user,
                "123456",
                uuid4()
            )
            
            assert result is True
            mock_mfa.verify_code.assert_called_once()
            mock_audit.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_mfa_failure(self, auth_service, sample_user):
        """Test failed MFA verification."""
        with patch.object(auth_service, 'mfa_service') as mock_mfa, \
             patch.object(auth_service, 'audit_service') as mock_audit:
            
            mock_mfa.verify_code.return_value = False
            
            result = await auth_service.verify_mfa(
                sample_user,
                "123456",
                uuid4()
            )
            
            assert result is False
            mock_mfa.verify_code.assert_called_once()
            mock_audit.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_setup_mfa_success(self, auth_service, sample_user):
        """Test successful MFA setup."""
        with patch.object(auth_service, 'mfa_service') as mock_mfa, \
             patch.object(auth_service, 'audit_service') as mock_audit:
            
            mock_mfa.create_device.return_value = MagicMock(id=uuid4())
            mock_mfa.generate_backup_codes.return_value = ["12345678", "87654321"]
            
            result = await auth_service.setup_mfa(sample_user, "Test Device")
            
            assert result is not None
            assert "device_id" in result
            assert "secret_key" in result
            assert "qr_code_url" in result
            assert "backup_codes" in result
            assert result["verification_required"] is True
            
            mock_mfa.create_device.assert_called_once()
            mock_mfa.generate_backup_codes.assert_called_once()
            mock_audit.log_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, auth_service, sample_user):
        """Test successful user retrieval by ID."""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        auth_service.db.execute.return_value = mock_result
        
        result = await auth_service._get_user_by_id(sample_user.id)
        
        assert result is not None
        assert result.id == sample_user.id
        assert result.email == sample_user.email
    
    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, auth_service):
        """Test user retrieval by ID when user doesn't exist."""
        # Mock database query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        auth_service.db.execute.return_value = mock_result
        
        result = await auth_service._get_user_by_id(uuid4())
        
        assert result is None


class TestUserModel:
    """Test cases for User model."""
    
    def test_user_full_name(self, sample_user):
        """Test user full name property."""
        assert sample_user.full_name == "Test User"
    
    def test_user_is_active(self, sample_user):
        """Test user is_active property."""
        assert sample_user.is_active is True
        
        # Test inactive user
        sample_user.status = UserStatus.INACTIVE
        assert sample_user.is_active is False
    
    def test_user_is_locked(self, sample_user):
        """Test user is_locked property."""
        assert sample_user.is_locked is False
        
        # Test locked user
        sample_user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
        assert sample_user.is_locked is True
    
    def test_increment_failed_login(self, sample_user):
        """Test failed login increment."""
        initial_attempts = sample_user.failed_login_attempts
        
        sample_user.increment_failed_login()
        assert sample_user.failed_login_attempts == initial_attempts + 1
        assert sample_user.last_failed_login is not None
        
        # Test account locking after 5 attempts
        sample_user.failed_login_attempts = 4
        sample_user.increment_failed_login()
        assert sample_user.account_locked_until is not None
    
    def test_reset_failed_login_attempts(self, sample_user):
        """Test failed login attempts reset."""
        sample_user.failed_login_attempts = 5
        sample_user.last_failed_login = datetime.utcnow()
        sample_user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        sample_user.reset_failed_login_attempts()
        
        assert sample_user.failed_login_attempts == 0
        assert sample_user.last_failed_login is None
        assert sample_user.account_locked_until is None


class TestSessionModel:
    """Test cases for Session model."""
    
    def test_session_is_active(self, sample_session):
        """Test session is_active property."""
        assert sample_session.is_active is True
        
        # Test expired session
        sample_session.access_token_expires_at = datetime.utcnow() - timedelta(minutes=1)
        assert sample_session.is_active is False
        
        # Test revoked session
        sample_session.status = SessionStatus.REVOKED
        assert sample_session.is_active is False
    
    def test_session_is_refresh_valid(self, sample_session):
        """Test session is_refresh_valid property."""
        assert sample_session.is_refresh_valid is True
        
        # Test expired refresh token
        sample_session.refresh_token_expires_at = datetime.utcnow() - timedelta(minutes=1)
        assert sample_session.is_refresh_valid is False
        
        # Test revoked session
        sample_session.status = SessionStatus.REVOKED
        assert sample_session.is_refresh_valid is False
    
    def test_session_update_activity(self, sample_session):
        """Test session activity update."""
        old_activity = sample_session.last_activity_at
        sample_session.update_activity()
        
        assert sample_session.last_activity_at > old_activity
    
    def test_session_revoke(self, sample_session):
        """Test session revocation."""
        sample_session.revoke("test_reason")
        
        assert sample_session.status == SessionStatus.REVOKED
        assert sample_session.logout_at is not None
    
    def test_session_expire(self, sample_session):
        """Test session expiration."""
        sample_session.expire()
        
        assert sample_session.status == SessionStatus.EXPIRED
        assert sample_session.logout_at is not None 