"""
Profile Service Tests

This module contains unit tests for the profile service.
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.profile import ProfileCreate, ProfileUpdate, Gender
from ..services.profile_service import ProfileService


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def profile_service(mock_db):
    """Profile service instance with mocked database."""
    return ProfileService(mock_db)


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing."""
    return ProfileCreate(
        user_id=1,
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1),
        gender=Gender.MALE,
        email="john.doe@example.com"
    )


class TestProfileService:
    """Test cases for ProfileService."""

    @pytest.mark.asyncio
    async def test_create_profile_success(self, profile_service, sample_profile_data, mock_db):
        """Test successful profile creation."""
        # Mock database operations
        mock_db.add = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Mock profile query result
        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Test profile creation
        result = await profile_service.create_profile(sample_profile_data)
        
        # Verify database operations were called
        assert mock_db.add.call_count >= 1  # Profile + preferences + privacy + health
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_profile_already_exists(self, profile_service, sample_profile_data, mock_db):
        """Test profile creation when profile already exists."""
        # Mock existing profile
        mock_db.execute.return_value.scalar_one_or_none.return_value = MagicMock()
        
        # Test that it raises an exception
        with pytest.raises(Exception) as exc_info:
            await profile_service.create_profile(sample_profile_data)
        
        assert "Profile already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_profile_success(self, profile_service, mock_db):
        """Test successful profile retrieval."""
        # Mock profile
        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.user_id = 1
        mock_profile.first_name = "John"
        mock_profile.last_name = "Doe"
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_profile
        
        # Test profile retrieval
        result = await profile_service.get_profile(1)
        
        assert result is not None
        assert result.user_id == 1

    @pytest.mark.asyncio
    async def test_get_profile_not_found(self, profile_service, mock_db):
        """Test profile retrieval when profile doesn't exist."""
        # Mock no profile found
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Test profile retrieval
        result = await profile_service.get_profile(1)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_update_profile_success(self, profile_service, mock_db):
        """Test successful profile update."""
        # Mock existing profile
        mock_profile = MagicMock()
        mock_profile.id = 1
        mock_profile.user_id = 1
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_profile
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Test profile update
        update_data = ProfileUpdate(first_name="Jane")
        result = await profile_service.update_profile(1, update_data)
        
        # Verify profile was updated
        assert mock_profile.first_name == "Jane"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_not_found(self, profile_service, mock_db):
        """Test profile update when profile doesn't exist."""
        # Mock no profile found
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Test that it raises an exception
        update_data = ProfileUpdate(first_name="Jane")
        with pytest.raises(Exception) as exc_info:
            await profile_service.update_profile(1, update_data)
        
        assert "Profile not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_profile_data_valid(self, profile_service):
        """Test profile data validation with valid data."""
        update_data = ProfileUpdate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            date_of_birth=date(1990, 1, 1)
        )
        
        result = await profile_service.validate_profile_data(update_data)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_profile_data_invalid_email(self, profile_service):
        """Test profile data validation with invalid email."""
        update_data = ProfileUpdate(
            first_name="John",
            last_name="Doe",
            email="invalid-email",
            date_of_birth=date(1990, 1, 1)
        )
        
        result = await profile_service.validate_profile_data(update_data)
        
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert any("email" in error.lower() for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_profile_data_future_date(self, profile_service):
        """Test profile data validation with future date of birth."""
        from datetime import date, timedelta
        
        future_date = date.today() + timedelta(days=1)
        update_data = ProfileUpdate(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            date_of_birth=future_date
        )
        
        result = await profile_service.validate_profile_data(update_data)
        
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert any("future" in error.lower() for error in result["errors"])


if __name__ == "__main__":
    pytest.main([__file__]) 