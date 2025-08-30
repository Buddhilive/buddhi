"""
Test utilities and helper functions for FastAPI testing
"""
from typing import Dict, Any
from fastapi.testclient import TestClient
from backend.models.base import User
from backend.api.deps import bcrypt_context
from sqlalchemy.orm import Session


def create_test_user(db: Session, username: str = "testuser", password: str = "testpass123") -> User:
    """Create a test user in the database"""
    hashed_password = bcrypt_context.hash(password)
    user = User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_test_user(client: TestClient, username: str = "testuser", password: str = "testpass123") -> Dict[str, Any]:
    """Authenticate a test user and return the response"""
    login_data = {
        "username": username,
        "password": password
    }
    response = client.post("/auth/login", data=login_data)
    return response


def get_auth_headers(client: TestClient, username: str = "testuser", password: str = "testpass123") -> Dict[str, str]:
    """Get authentication headers for API requests"""
    response = authenticate_test_user(client, username, password)
    if response.status_code == 200:
        token_data = response.json()
        return {"Authorization": f"Bearer {token_data['access_token']}"}
    return {}


def create_authenticated_client(client: TestClient, db_session: Session, username: str = "testuser", password: str = "testpass123"):
    """Create a test user and authenticate them, returning cookies for subsequent requests"""
    # Create user
    create_test_user(db_session, username, password)
    
    # Login to get cookies
    login_response = authenticate_test_user(client, username, password)
    assert login_response.status_code == 200
    
    # Extract cookies from response - handle httpx response cookies properly
    cookies = {}
    if hasattr(login_response, 'cookies'):
        for name, value in login_response.cookies.items():
            cookies[name] = value
    
    return cookies
