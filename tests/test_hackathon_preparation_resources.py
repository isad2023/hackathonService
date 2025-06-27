import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient
from presentations.fastapi_app import app

client = TestClient(app)


@pytest.fixture
def mock_hackathon():
    """Мок объект хакатона для тестов."""
    return {
        "id": uuid4(),
        "name": "Test Hackathon",
        "task_description": "Создать мобильное приложение для решения социальных проблем",
        "type": "mobile",
        "city": "Moscow"
    }


@pytest.fixture
def mock_resources():
    """Мок ресурсов для подготовки."""
    return {
        "recommended_technologies": ["React Native", "Flutter", "Swift"],
        "learning_resources": [
            {
                "title": "Mobile Development Guide",
                "url": "https://example.com/guide",
                "type": "tutorial"
            }
        ],
        "preparation_timeline": "2-3 weeks",
        "difficulty_level": "intermediate"
    }


class TestHackathonPreparationResources:
    
    @patch('services.hackathon_service.HackathonService.get_hackathon_by_id')
    @patch('services.recommendations_service.RecommendationsService.get_preparation_resources')
    async def test_get_preparation_resources_success(
        self, 
        mock_get_resources, 
        mock_get_hackathon,
        mock_hackathon,
        mock_resources
    ):
        """Тест успешного получения ресурсов для подготовки."""
        # Arrange
        hackathon_id = mock_hackathon["id"]
        mock_get_hackathon.return_value = AsyncMock(**mock_hackathon)
        mock_get_resources.return_value = mock_resources
        
        # Act
        response = client.get(f"/hackathons/{hackathon_id}/preparation-resources")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["hackathon_id"] == str(hackathon_id)
        assert data["hackathon_name"] == mock_hackathon["name"]
        assert data["resources"] == mock_resources
        assert data["error_message"] is None
    
    @patch('services.hackathon_service.HackathonService.get_hackathon_by_id')
    async def test_get_preparation_resources_hackathon_not_found(
        self, 
        mock_get_hackathon
    ):
        """Тест случая, когда хакатон не найден."""
        # Arrange
        hackathon_id = uuid4()
        mock_get_hackathon.return_value = None
        
        # Act
        response = client.get(f"/hackathons/{hackathon_id}/preparation-resources")
        
        # Assert
        assert response.status_code == 404
        assert "Хакатон не найден" in response.json()["detail"]
    
    @patch('services.hackathon_service.HackathonService.get_hackathon_by_id')
    async def test_get_preparation_resources_no_description(
        self, 
        mock_get_hackathon,
        mock_hackathon
    ):
        """Тест случая, когда у хакатона отсутствует описание."""
        # Arrange
        hackathon_id = mock_hackathon["id"]
        hackathon_without_description = {**mock_hackathon, "task_description": None}
        mock_get_hackathon.return_value = AsyncMock(**hackathon_without_description)
        
        # Act
        response = client.get(f"/hackathons/{hackathon_id}/preparation-resources")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["hackathon_id"] == str(hackathon_id)
        assert data["resources"] is None
        assert "отсутствует описание" in data["error_message"]
    
    @patch('services.hackathon_service.HackathonService.get_hackathon_by_id')
    @patch('services.recommendations_service.RecommendationsService.get_preparation_resources')
    async def test_get_preparation_resources_api_failure(
        self, 
        mock_get_resources, 
        mock_get_hackathon,
        mock_hackathon
    ):
        """Тест случая, когда внешний API не отвечает."""
        # Arrange
        hackathon_id = mock_hackathon["id"]
        mock_get_hackathon.return_value = AsyncMock(**mock_hackathon)
        mock_get_resources.return_value = None  # API не отвечает
        
        # Act
        response = client.get(f"/hackathons/{hackathon_id}/preparation-resources")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["hackathon_id"] == str(hackathon_id)
        assert data["resources"] is None
        assert "Не удалось получить ресурсы" in data["error_message"] 