# FastAPI Testing Documentation

This document describes the testing setup for the Buddhi AI FastAPI backend, implemented according to the [official FastAPI testing documentation](https://fastapi.tiangolo.com/tutorial/testing/).

## Testing Architecture

### Overview
The testing setup uses:
- **pytest** as the testing framework
- **FastAPI TestClient** for API testing
- **SQLite in-memory database** for isolated testing
- **pytest fixtures** for test setup and teardown
- **httpx** as the underlying HTTP client

### Test Structure
```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                # Pytest configuration and fixtures
├── test_utils.py              # Testing utilities and helpers
├── test_main.py               # Main application tests
├── test_auth.py               # Authentication endpoint tests
├── test_database.py           # Database model tests
└── test_integration.py        # Integration tests
```

## Test Categories

### 1. Unit Tests (`test_main.py`, `test_database.py`)
- Test individual components in isolation
- Database model functionality
- Utility functions
- Password hashing

### 2. API Endpoint Tests (`test_auth.py`)
- Authentication endpoints (`/auth/create`, `/auth/login`, etc.)
- Request/response validation
- Error handling
- Security features

### 3. Integration Tests (`test_integration.py`)
- Complete user workflows
- Multi-step processes
- Security testing
- Error handling across components

## Key Testing Features

### Database Isolation
Each test uses a fresh SQLite in-memory database:
```python
# In conftest.py
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
```

### Test Client Setup
FastAPI TestClient with dependency overrides:
```python
@pytest.fixture(scope="function")
def client(test_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

### Test Utilities
Helper functions for common operations:
- `create_test_user()` - Create users in test database
- `authenticate_test_user()` - Login and get tokens
- `create_authenticated_client()` - Get authenticated session

## Running Tests

### Basic Test Execution
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_auth.py -v

# Run specific test class
python -m pytest tests/test_auth.py::TestUserCreation -v

# Run specific test
python -m pytest tests/test_auth.py::TestUserCreation::test_create_user_success -v
```

### Using the Test Runner Script
```bash
# Run all tests
python run_tests.py

# Run with coverage
python run_tests.py coverage

# Run specific category
python run_tests.py auth
python run_tests.py database
python run_tests.py integration
python run_tests.py unit
```

### Test Markers
Tests are organized using pytest markers:
```bash
# Run only authentication tests
pytest -m auth

# Run only database tests
pytest -m database

# Run only integration tests
pytest -m integration

# Run only unit tests
pytest -m unit
```

## Test Coverage

### Authentication Tests
- [x] User registration
- [x] User login/logout
- [x] Token refresh
- [x] Protected endpoint access
- [x] Token blacklisting
- [x] Password hashing
- [x] Invalid credentials handling

### Database Tests
- [x] User model CRUD operations
- [x] BlacklistedToken model operations
- [x] Database constraints
- [x] Query operations

### Security Tests
- [x] Password hashing verification
- [x] Token validation
- [x] SQL injection protection
- [x] Malformed request handling

### Integration Tests
- [x] Complete user workflows
- [x] Multi-user sessions
- [x] Token refresh workflows
- [x] Error handling across components

## Test Configuration

### pytest.ini Configuration
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    auth: Authentication related tests
    database: Database related tests
    integration: Integration tests
    unit: Unit tests
asyncio_mode = auto
```

### Environment Variables for Testing
The tests use environment variables for configuration. Ensure you have a `.env` file with:
```
AUTH_SECRET_KEY=your_test_secret_key
AUTH_ALGORITHM=HS256
```

## Best Practices Implemented

### 1. Test Isolation
- Each test uses a fresh database
- No test dependencies on others
- Clean setup and teardown

### 2. Realistic Test Data
- Meaningful test usernames and passwords
- Edge cases and error conditions
- Security-focused test scenarios

### 3. Comprehensive Coverage
- Happy path testing
- Error condition testing
- Security vulnerability testing
- Integration testing

### 4. FastAPI Best Practices
- Using TestClient as recommended
- Dependency overrides for database
- Cookie-based authentication testing
- Proper status code assertions

## Adding New Tests

### For New Endpoints
1. Add tests to appropriate file (`test_auth.py` for auth endpoints)
2. Use existing fixtures (`client`, `db_session`)
3. Follow naming convention (`test_*`)
4. Add appropriate markers

### For New Models
1. Add tests to `test_database.py`
2. Test CRUD operations
3. Test model constraints
4. Test relationships (if any)

### For Integration Scenarios
1. Add to `test_integration.py`
2. Test complete workflows
3. Test error propagation
4. Mark with `@pytest.mark.integration`

## Continuous Integration

The testing setup is designed to work in CI/CD environments:
- No external dependencies
- Fast execution with in-memory database
- Comprehensive coverage reporting
- Clear success/failure indicators

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure the backend package is in Python path
2. **Database errors**: Check that SQLAlchemy models are properly imported
3. **Authentication errors**: Verify JWT secret keys in test environment
4. **Fixture errors**: Ensure proper pytest fixture scope and dependencies

### Debug Mode
Run tests with more verbose output:
```bash
pytest tests/ -v -s --tb=long
```

This testing setup provides comprehensive coverage of your FastAPI backend while following the official FastAPI testing recommendations and best practices.
