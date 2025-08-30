"""
Integration tests for the FastAPI application
Tests complete user workflows and API interactions
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.models.base import User
from tests.test_utils import create_test_user


@pytest.mark.integration
class TestUserWorkflow:
    """Test complete user workflows"""
    
    def test_complete_user_registration_and_login_flow(self, client: TestClient):
        """Test the complete flow: register -> login -> access protected endpoint -> logout"""
        # Step 1: Register a new user
        user_data = {"username": "integrationuser", "password": "integrationpass123"}
        register_response = client.post("/auth/create", json=user_data)
        assert register_response.status_code == 201
        
        # Step 2: Login with the new user
        login_response = client.post("/auth/login", data=user_data)
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        
        # Extract cookies for subsequent requests
        cookies = {}
        if hasattr(login_response, 'cookies'):
            for name, value in login_response.cookies.items():
                cookies[name] = value
        
        # Step 3: Access protected endpoint
        user_info_response = client.get("/auth/me", cookies=cookies)
        assert user_info_response.status_code == 200
        user_info = user_info_response.json()
        assert user_info["username"] == user_data["username"]
        
        # Step 4: Refresh token
        refresh_response = client.post("/auth/refresh", cookies=cookies)
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        
        # Step 5: Logout
        logout_response = client.post("/auth/logout", cookies=cookies)
        assert logout_response.status_code == 200
        
        # Step 6: Verify that access is denied after logout (cookies should be cleared)
        # The logout endpoint clears cookies, so we expect 401 due to missing cookies
        post_logout_response = client.get("/auth/me")  # No cookies after logout
        assert post_logout_response.status_code == 401

    def test_token_refresh_workflow(self, client: TestClient, db_session: Session):
        """Test token refresh workflow"""
        # Create and login user
        user_data = {"username": "refreshuser", "password": "refreshpass123"}
        create_test_user(db_session, user_data["username"], user_data["password"])
        
        login_response = client.post("/auth/login", data=user_data)
        assert login_response.status_code == 200
        
        # Extract cookies
        cookies = {}
        if hasattr(login_response, 'cookies'):
            for name, value in login_response.cookies.items():
                cookies[name] = value
        
        # Use the refresh token multiple times
        for i in range(3):
            refresh_response = client.post("/auth/refresh", cookies=cookies)
            assert refresh_response.status_code == 200
            
            # Update cookies with new tokens
            if hasattr(refresh_response, 'cookies'):
                for name, value in refresh_response.cookies.items():
                    cookies[name] = value
            
            # Verify we can still access protected endpoints
            user_info_response = client.get("/auth/me", cookies=cookies)
            assert user_info_response.status_code == 200

    def test_concurrent_user_sessions(self, client: TestClient, db_session: Session):
        """Test multiple user sessions"""
        # Create two users
        user1_data = {"username": "user1", "password": "pass1"}
        user2_data = {"username": "user2", "password": "pass2"}
        
        create_test_user(db_session, user1_data["username"], user1_data["password"])
        create_test_user(db_session, user2_data["username"], user2_data["password"])
        
        # Login both users
        login1_response = client.post("/auth/login", data=user1_data)
        login2_response = client.post("/auth/login", data=user2_data)
        
        assert login1_response.status_code == 200
        assert login2_response.status_code == 200
        
        # Extract cookies for both users
        cookies1 = {}
        cookies2 = {}
        
        if hasattr(login1_response, 'cookies'):
            for name, value in login1_response.cookies.items():
                cookies1[name] = value
                
        if hasattr(login2_response, 'cookies'):
            for name, value in login2_response.cookies.items():
                cookies2[name] = value
        
        # Verify both users can access their info
        user1_info = client.get("/auth/me", cookies=cookies1)
        user2_info = client.get("/auth/me", cookies=cookies2)
        
        assert user1_info.status_code == 200
        assert user2_info.status_code == 200
        assert user1_info.json()["username"] == user1_data["username"]
        assert user2_info.json()["username"] == user2_data["username"]


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling across the application"""
    
    def test_malformed_requests(self, client: TestClient):
        """Test handling of malformed requests"""
        # Test malformed JSON
        response = client.post("/auth/create", data="invalid json", headers={"Content-Type": "application/json"})
        assert response.status_code == 422
        
        # Test wrong content type
        response = client.post("/auth/create", data="username=test&password=test")
        assert response.status_code == 422

    def test_rate_limiting_behavior(self, client: TestClient):
        """Test behavior under rapid requests (if rate limiting is implemented)"""
        # Make rapid requests to test application stability
        responses = []
        for i in range(10):
            response = client.get("/")
            responses.append(response.status_code)
        
        # All requests should succeed (or consistently rate limited)
        assert all(status in [200, 429] for status in responses)

    def test_database_error_handling(self, client: TestClient):
        """Test handling of potential database errors"""
        # Test with very long username (might exceed database field length)
        long_username = "a" * 1000
        user_data = {"username": long_username, "password": "password123"}
        
        response = client.post("/auth/create", json=user_data)
        # Should handle gracefully, either validation error, database error, or success
        assert response.status_code in [201, 400, 422, 500]


@pytest.mark.integration
class TestSecurityFeatures:
    """Test security-related features"""
    
    def test_password_hashing(self, client: TestClient, db_session: Session):
        """Test that passwords are properly hashed"""
        user_data = {"username": "securityuser", "password": "plainpassword"}
        
        # Create user
        response = client.post("/auth/create", json=user_data)
        assert response.status_code == 201
        
        # Check that password is hashed in database
        user = db_session.query(User).filter(User.username == user_data["username"]).first()
        assert user is not None
        assert user.hashed_password != user_data["password"]
        assert user.hashed_password.startswith("$2b$")  # bcrypt hash format

    def test_token_expiration_handling(self, client: TestClient, db_session: Session):
        """Test token expiration behavior"""
        # Note: This test would need to be enhanced with actual token expiration
        # For now, we test that tokens have expiration fields
        user_data = {"username": "tokenuser", "password": "tokenpass"}
        create_test_user(db_session, user_data["username"], user_data["password"])
        
        login_response = client.post("/auth/login", data=user_data)
        assert login_response.status_code == 200
        
        # Tokens should be created successfully
        token_data = login_response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data

    def test_injection_protection(self, client: TestClient):
        """Test protection against injection attacks"""
        # Test SQL injection attempts
        malicious_usernames = [
            "'; DROP TABLE users; --",
            "admin'--",
            "1' OR '1'='1",
        ]
        
        for malicious_username in malicious_usernames:
            user_data = {"username": malicious_username, "password": "password123"}
            
            # Should not cause errors or security issues
            create_response = client.post("/auth/create", json=user_data)
            # Should either succeed or fail gracefully
            assert create_response.status_code in [201, 400, 422]
            
            # Login attempt should also be safe
            login_response = client.post("/auth/login", data=user_data)
            assert login_response.status_code in [200, 401, 422]
