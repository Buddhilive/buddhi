"""
Tests for OpenAI-compatible API endpoints.

This module tests:
- Chat completions (streaming and non-streaming)
- Text completions (streaming and non-streaming)  
- Model listing
- Authentication requirements
- Error handling
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from backend.models.base import Model


class TestChatCompletions:
    """Test chat completion functionality."""
    
    def test_chat_completions_requires_auth(self, client):
        """Test that chat completions require authentication."""
        response = client.post("/v1/chat/completions", json={
            "model": "gpt2",
            "messages": [{"role": "user", "content": "Hello"}]
        })
        assert response.status_code == 401
    
    def test_chat_completions_model_not_available(self, client, authenticated_user):
        """Test chat completions with unavailable model."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.list_downloaded_models') as mock_list:
            mock_list.return_value = []
            
            response = client.post("/v1/chat/completions", json={
                "model": "unavailable-model",
                "messages": [{"role": "user", "content": "Hello"}]
            })
            assert response.status_code == 400
            assert "is not available" in response.json()["detail"]
    
    def test_chat_completions_success(self, client, authenticated_user):
        """Test successful chat completion."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.list_downloaded_models') as mock_list:
            with patch('backend.services.model_manager.model_manager.generate') as mock_generate:
                mock_list.return_value = [{"name": "gpt2"}]
                mock_generate.return_value = "Hello! How can I help you today?"
                
                response = client.post("/v1/chat/completions", json={
                    "model": "gpt2",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 50,
                    "temperature": 0.7
                })
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["object"] == "chat.completion"
                assert data["model"] == "gpt2"
                assert len(data["choices"]) == 1
                assert data["choices"][0]["message"]["role"] == "assistant"
                assert data["choices"][0]["message"]["content"] == "Hello! How can I help you today?"
                assert data["choices"][0]["finish_reason"] == "stop"
                assert "usage" in data
    
    def test_chat_completions_with_system_message(self, client, authenticated_user):
        """Test chat completion with system message."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.list_downloaded_models') as mock_list:
            with patch('backend.services.model_manager.model_manager.generate') as mock_generate:
                mock_list.return_value = [{"name": "gpt2"}]
                mock_generate.return_value = "I understand."
                
                response = client.post("/v1/chat/completions", json={
                    "model": "gpt2",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hello"}
                    ]
                })
                
                assert response.status_code == 200
                data = response.json()
                assert data["choices"][0]["message"]["content"] == "I understand."
    
    def test_chat_completions_streaming(self, client, authenticated_user):
        """Test streaming chat completion."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.list_downloaded_models') as mock_list:
            mock_list.return_value = [{"name": "gpt2"}]
            
            response = client.post("/v1/chat/completions", json={
                "model": "gpt2",
                "messages": [{"role": "user", "content": "Hello"}],
                "stream": True
            })
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"


class TestTextCompletions:
    """Test text completion functionality."""
    
    def test_completions_requires_auth(self, client):
        """Test that text completions require authentication."""
        response = client.post("/v1/completions", json={
            "model": "gpt2",
            "prompt": "The sky is"
        })
        assert response.status_code == 401
    
    def test_completions_success(self, client, authenticated_user):
        """Test successful text completion."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.list_downloaded_models') as mock_list:
            with patch('backend.services.model_manager.model_manager.generate') as mock_generate:
                mock_list.return_value = [{"name": "gpt2"}]
                mock_generate.return_value = " blue and beautiful today."
                
                response = client.post("/v1/completions", json={
                    "model": "gpt2",
                    "prompt": "The sky is",
                    "max_tokens": 20,
                    "temperature": 0.8
                })
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["object"] == "text_completion"
                assert data["model"] == "gpt2"
                assert len(data["choices"]) == 1
                assert data["choices"][0]["text"] == " blue and beautiful today."
                assert data["choices"][0]["finish_reason"] == "stop"
                assert "usage" in data
    
    def test_completions_streaming(self, client, authenticated_user):
        """Test streaming text completion."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.list_downloaded_models') as mock_list:
            mock_list.return_value = [{"name": "gpt2"}]
            
            response = client.post("/v1/completions", json={
                "model": "gpt2",
                "prompt": "The sky is",
                "stream": True
            })
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"


class TestModelListing:
    """Test OpenAI-compatible model listing."""
    
    def test_list_models_requires_auth(self, client):
        """Test that model listing requires authentication."""
        response = client.get("/v1/models")
        assert response.status_code == 401
    
    def test_list_models_success(self, client, authenticated_user, db_session):
        """Test successful model listing in OpenAI format."""
        # Add test models to database
        test_models = [
            Model(
                name="gpt2",
                local_path="/path/to/gpt2",
                status="downloaded",
                download_date="2024-01-01T10:00:00+00:00"
            ),
            Model(
                name="bert-base-uncased",
                local_path="/path/to/bert",
                status="downloaded",
                download_date="2024-01-02T10:00:00+00:00"
            )
        ]
        
        for model in test_models:
            db_session.add(model)
        db_session.commit()
        
        client.cookies.set("access_token", authenticated_user["token"])
        
        response = client.get("/v1/models")
        assert response.status_code == 200
        
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 2
        
        # Check first model
        assert data["data"][0]["id"] == "gpt2"
        assert data["data"][0]["object"] == "model"
        assert data["data"][0]["owned_by"] == "buddhi-ai"
        assert "created" in data["data"][0]
    
    def test_list_models_empty(self, client, authenticated_user):
        """Test model listing when no models are available."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        response = client.get("/v1/models")
        assert response.status_code == 200
        
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 0


class TestHelperFunctions:
    """Test helper functions in the OpenAI router."""
    
    def test_messages_to_prompt(self):
        """Test converting chat messages to prompt."""
        from backend.api.routers.openai import _messages_to_prompt
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        prompt = _messages_to_prompt(messages)
        expected = """System: You are a helpful assistant.
User: Hello
Assistant: Hi there!
User: How are you?
Assistant:"""
        
        assert prompt == expected
    
    def test_messages_to_prompt_user_only(self):
        """Test converting user-only messages to prompt."""
        from backend.api.routers.openai import _messages_to_prompt
        
        messages = [
            {"role": "user", "content": "What is AI?"}
        ]
        
        prompt = _messages_to_prompt(messages)
        expected = """User: What is AI?
Assistant:"""
        
        assert prompt == expected


class TestErrorHandling:
    """Test error handling in OpenAI-compatible API."""
    
    def test_chat_completions_generation_error(self, client, authenticated_user):
        """Test handling of generation errors in chat completions."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.list_downloaded_models') as mock_list:
            with patch('backend.services.model_manager.model_manager.generate') as mock_generate:
                mock_list.return_value = [{"name": "gpt2"}]
                mock_generate.side_effect = Exception("Model loading failed")
                
                response = client.post("/v1/chat/completions", json={
                    "model": "gpt2",
                    "messages": [{"role": "user", "content": "Hello"}]
                })
                
                assert response.status_code == 500
                assert "Error creating chat completion" in response.json()["detail"]
    
    def test_completions_generation_error(self, client, authenticated_user):
        """Test handling of generation errors in text completions."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.list_downloaded_models') as mock_list:
            with patch('backend.services.model_manager.model_manager.generate') as mock_generate:
                mock_list.return_value = [{"name": "gpt2"}]
                mock_generate.side_effect = Exception("Generation failed")
                
                response = client.post("/v1/completions", json={
                    "model": "gpt2",
                    "prompt": "Test prompt"
                })
                
                assert response.status_code == 500
                assert "Error creating completion" in response.json()["detail"]
    
    def test_models_listing_error(self, client, authenticated_user):
        """Test handling of errors in model listing."""
        client.cookies.set("access_token", authenticated_user["token"])
        
        with patch('backend.services.model_manager.model_manager.list_downloaded_models') as mock_list:
            mock_list.side_effect = Exception("Database error")
            
            response = client.get("/v1/models")
            assert response.status_code == 500
            assert "Error listing models" in response.json()["detail"]


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
