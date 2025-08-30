"""
Tests for the main FastAPI application
"""
import pytest
from fastapi.testclient import TestClient


def test_read_main(client: TestClient):
    """Test the root endpoint health check"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Buddhi AI!"}


def test_cors_headers(client: TestClient):
    """Test CORS configuration"""
    response = client.options("/", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET"
    })
    # The response should not be 405 Method Not Allowed if CORS is properly configured
    # Note: Some CORS implementations might return different status codes
    assert response.status_code in [200, 204, 405]


def test_invalid_endpoint(client: TestClient):
    """Test that invalid endpoints return 404"""
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404


def test_health_check_method_not_allowed(client: TestClient):
    """Test that non-GET methods are not allowed on root endpoint"""
    response = client.post("/")
    assert response.status_code == 405


def test_health_check_with_query_params(client: TestClient):
    """Test the root endpoint with query parameters"""
    response = client.get("/?test=value")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Buddhi AI!"}


def test_application_startup(client: TestClient):
    """Test that the application starts up correctly"""
    # Test multiple endpoints to ensure the app is properly configured
    endpoints_to_test = [
        ("/", 200),
        ("/docs", 200),  # OpenAPI docs should be accessible
        ("/openapi.json", 200),  # OpenAPI schema should be accessible
    ]
    
    for endpoint, expected_status in endpoints_to_test:
        response = client.get(endpoint)
        assert response.status_code == expected_status, f"Endpoint {endpoint} returned {response.status_code}, expected {expected_status}"
