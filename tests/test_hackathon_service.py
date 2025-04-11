import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from services.hackathon_service import HackathonService


@pytest.mark.asyncio
async def test_get_hackathon_by_id():
    """
    Test the get_hackathon_by_id method of HackathonService
    """
    # Arrange
    test_id = uuid4()
    mock_hackathon = AsyncMock()
    mock_hackathon.id = test_id
    mock_hackathon.name = "Test Hackathon"

    # Create service instance
    service = HackathonService()
    
    # Mock the repository method
    service.hackathon_repository.get_hackathon_by_id = AsyncMock(return_value=mock_hackathon)
    
    # Act
    result = await service.get_hackathon_by_id(test_id)
    
    # Assert
    assert result is not None
    assert result.id == test_id
    assert result.name == "Test Hackathon"
    service.hackathon_repository.get_hackathon_by_id.assert_called_once_with(test_id)


@pytest.mark.asyncio
async def test_get_hackathon_by_id_not_found():
    """
    Test the get_hackathon_by_id method when hackathon is not found
    """
    # Arrange
    test_id = uuid4()
    
    # Create service instance
    service = HackathonService()
    
    # Mock the repository method to return None (not found)
    service.hackathon_repository.get_hackathon_by_id = AsyncMock(return_value=None)
    
    # Act
    result = await service.get_hackathon_by_id(test_id)
    
    # Assert
    assert result is None
    service.hackathon_repository.get_hackathon_by_id.assert_called_once_with(test_id) 