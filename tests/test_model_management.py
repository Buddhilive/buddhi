"""
Tests for model management functionality.

This module tests:
- Model search functionality
- Model download operations
- Model status tracking
- Model listing operations
- Authentication requirements
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from backend.models.base import Model
from backend.services.model_manager import ModelManager


class TestModelSearch:
    """Test model search functionality."""
    
    def test_search_models_requires_auth(self, client):
        """Test that model search requires authentication."""
        response = client.get("/models/search?q=gpt2")
        assert response.status_code == 401
    
    @patch('backend.services.model_manager.model_manager.search_models')
    def test_search_models_success(self, mock_search, client, authenticated_user):
        """Test successful model search."""
        # Mock the search results
        mock_search.return_value = [
            {
                "id": "gpt2",
                "author": "openai",
                "downloads": 1000000,
                "likes": 5000,
                "created_at": "2024-01-01T00:00:00Z",
                "last_modified": "2024-01-15T00:00:00Z",
                "tags": ["text-generation", "pytorch"],
                "pipeline_tag": "text-generation",
                "library_name": "transformers",
                "model_type": "text-generation"
            }
        ]
        
        # Set up authentication
        client.cookies.set("access_token", authenticated_user["token"])
        
        response = client.get("/models/search?q=gpt2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "gpt2"
        assert data[0]["author"] == "openai"
        assert data[0]["model_type"] == "text-generation"
    
    def test_search_models_with_filters(self, client, authenticated_user):
        """Test model search with filters."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.search_models') as mock_search:
            mock_search.return_value = []
            
            response = client.get(
                "/models/search?q=bert&limit=10&model_type=text-classification&language=en"
            )
            assert response.status_code == 200
            
            # Verify the search was called with correct parameters
            mock_search.assert_called_once_with(
                query="bert",
                limit=10,
                model_type="text-classification",
                language="en"
            )
    
    def test_search_models_empty_query(self, client, authenticated_user):
        """Test model search with empty query."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        response = client.get("/models/search")
        assert response.status_code == 422  # Missing required parameter


class TestModelDownload:
    """Test model download functionality."""
    
    def test_download_model_requires_auth(self, client):
        """Test that model download requires authentication."""
        response = client.post("/models/download", json={"model_name": "gpt2"})
        assert response.status_code == 401
    
    def test_download_model_success(self, client, authenticated_user):
        """Test successful model download initiation."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.download_model') as mock_download:
            with patch('backend.services.model_manager.model_manager.get_download_status') as mock_status:
                mock_status.return_value = {
                    "status": "started",
                    "progress": 0,
                    "message": "Download queued",
                    "started_at": datetime.now().isoformat()
                }
                
                response = client.post("/models/download", json={"model_name": "gpt2"})
                assert response.status_code == 200
                
                data = response.json()
                assert data["status"] == "started"
                assert data["progress"] == 0
                assert "started_at" in data
    
    def test_download_model_empty_name(self, client, authenticated_user):
        """Test model download with empty model name."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        response = client.post("/models/download", json={"model_name": ""})
        assert response.status_code == 400
        assert "Model name cannot be empty" in response.json()["detail"]
    
    def test_download_model_already_downloading(self, client, authenticated_user):
        """Test download when model is already being downloaded."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.get_download_status') as mock_status:
            mock_status.return_value = {
                "status": "downloading",
                "progress": 50,
                "message": "Downloading model files...",
                "started_at": datetime.now().isoformat()
            }
            
            response = client.post("/models/download", json={"model_name": "gpt2"})
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "downloading"
            assert data["progress"] == 50


class TestModelStatus:
    """Test model status functionality."""
    
    def test_get_model_status_requires_auth(self, client):
        """Test that model status requires authentication."""
        response = client.get("/models/status?model_name=gpt2")
        assert response.status_code == 401
    
    def test_get_model_status_success(self, client, authenticated_user):
        """Test successful model status retrieval."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.get_download_status') as mock_status:
            mock_status.return_value = {
                "status": "completed",
                "progress": 100,
                "message": "Model downloaded successfully",
                "started_at": "2024-01-01T10:00:00Z",
                "completed_at": "2024-01-01T10:05:00Z",
                "local_path": "/path/to/model",
                "size_bytes": 1000000
            }
            
            response = client.get("/models/status?model_name=gpt2")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "completed"
            assert data["progress"] == 100
            assert data["local_path"] == "/path/to/model"
    
    def test_get_model_status_empty_name(self, client, authenticated_user):
        """Test model status with empty model name."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        response = client.get("/models/status?model_name=")
        assert response.status_code == 400
        assert "Model name cannot be empty" in response.json()["detail"]
    
    def test_get_model_status_not_started(self, client, authenticated_user):
        """Test model status for model that hasn't been downloaded."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.get_download_status') as mock_status:
            mock_status.return_value = {"status": "not_started"}
            
            response = client.get("/models/status?model_name=unknown-model")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "not_started"


class TestModelListing:
    """Test model listing functionality."""
    
    def test_list_models_requires_auth(self, client):
        """Test that model listing requires authentication."""
        response = client.get("/models/")
        assert response.status_code == 401
    
    def test_list_models_success(self, client, authenticated_user, db_session):
        """Test successful model listing."""
        # Add a test model to the database
        test_model = Model(
            name="test-model",
            local_path="/path/to/test-model",
            status="downloaded",
            size_bytes=500000,
            model_type="text-generation",
            description="A test model",
            author="test-author",
            tags='["test", "demo"]'
        )
        db_session.add(test_model)
        db_session.commit()
        
        client.cookies.set("access_token", authenticated_user["token"])
        
        response = client.get("/models/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test-model"
        assert data[0]["status"] == "downloaded"
        assert data[0]["model_type"] == "text-generation"
    
    def test_list_models_empty(self, client, authenticated_user):
        """Test model listing when no models are downloaded."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        response = client.get("/models/")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 0


class TestModelManager:
    """Test ModelManager service directly."""
    
    @pytest.fixture
    def model_manager(self):
        """Create a ModelManager instance for testing."""
        return ModelManager(cache_dir="./test_cache")
    
    @patch('backend.services.model_manager.list_models')
    def test_search_models(self, mock_list_models, model_manager):
        """Test ModelManager search_models method."""
        # Mock huggingface_hub.list_models response
        mock_model = MagicMock()
        mock_model.id = "gpt2"
        mock_model.author = "openai"
        mock_model.downloads = 1000000
        mock_model.likes = 5000
        mock_model.tags = ["text-generation"]
        mock_model.pipeline_tag = "text-generation"
        mock_list_models.return_value = [mock_model]
        
        # Test search
        result = model_manager.search_models("gpt2", limit=10)
        
        assert len(result) == 1
        assert result[0]["id"] == "gpt2"
        assert result[0]["author"] == "openai"
    
    def test_get_download_status_not_started(self, model_manager):
        """Test getting download status for model that hasn't been downloaded."""
        status = model_manager.get_download_status("unknown-model")
        assert status["status"] == "not_started"
    
    def test_get_download_status_existing(self, model_manager):
        """Test getting download status for model with existing status."""
        # Set up existing status
        model_manager.download_status["test-model"] = {
            "status": "downloading",
            "progress": 50,
            "message": "Downloading..."
        }
        
        status = model_manager.get_download_status("test-model")
        assert status["status"] == "downloading"
        assert status["progress"] == 50
    
    @patch('backend.services.model_manager.SessionLocal')
    def test_list_downloaded_models(self, mock_session, model_manager):
        """Test listing downloaded models from database."""
        # Mock database query
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        
        mock_model = MagicMock()
        mock_model.id = 1
        mock_model.name = "test-model"
        mock_model.local_path = "/path/to/model"
        mock_model.status = "downloaded"
        mock_model.download_date = datetime.now(timezone.utc)
        mock_model.size_bytes = 1000000
        mock_model.model_type = "text-generation"
        mock_model.tags = '["test"]'
        mock_model.created_at = datetime.now(timezone.utc)
        mock_model.updated_at = datetime.now(timezone.utc)
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_model]
        
        result = model_manager.list_downloaded_models()
        
        assert len(result) == 1
        assert result[0]["name"] == "test-model"
        assert result[0]["status"] == "downloaded"


@pytest.fixture
def authenticated_user(client, sample_user_data):
    """Create and authenticate a test user."""
    # Create user
    user_response = client.post("/auth/", json=sample_user_data)
    assert user_response.status_code == 200
    
    # Login user
    login_response = client.post("/auth/token", data={
        "username": sample_user_data["username"],
        "password": sample_user_data["password"]
    })
    assert login_response.status_code == 200
    
    login_data = login_response.json()
    return {
        "token": login_data["access_token"],
        "user_data": sample_user_data
    }
