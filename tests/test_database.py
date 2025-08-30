"""
Tests for database models and dependencies
"""
import pytest
from sqlalchemy.orm import Session
from backend.models.base import User, BlacklistedToken
from backend.api.deps import bcrypt_context
from datetime import datetime, timezone


@pytest.mark.database
class TestUserModel:
    """Test User model functionality"""
    
    def test_create_user(self, db_session: Session):
        """Test creating a user in the database"""
        user = User(
            username="testuser",
            hashed_password="hashed_password_123",
            email="test@example.com",
            age=25
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.age == 25

    def test_user_unique_email_constraint(self, db_session: Session):
        """Test that email should be unique (if constraint exists)"""
        # Create first user
        user1 = User(
            username="user1",
            hashed_password="hash1",
            email="unique@example.com"
        )
        db_session.add(user1)
        db_session.commit()
        
        # Try to create second user with same email
        user2 = User(
            username="user2",
            hashed_password="hash2",
            email="unique@example.com"
        )
        db_session.add(user2)
        
        # This should raise an integrity error
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db_session.commit()

    def test_user_optional_fields(self, db_session: Session):
        """Test that optional fields can be None"""
        user = User(
            username="minimaluser",
            hashed_password="hash123"
            # email and age are optional
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.username == "minimaluser"
        assert user.email is None
        assert user.age is None


@pytest.mark.database
class TestBlacklistedTokenModel:
    """Test BlacklistedToken model functionality"""
    
    def test_create_blacklisted_token(self, db_session: Session):
        """Test creating a blacklisted token"""
        token = BlacklistedToken(token="sample_token_123")
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)
        
        assert token.id is not None
        assert token.token == "sample_token_123"
        assert token.blacklisted_on is not None
        assert isinstance(token.blacklisted_on, datetime)

    def test_blacklisted_token_unique_constraint(self, db_session: Session):
        """Test that tokens should be unique"""
        # Create first token
        token1 = BlacklistedToken(token="duplicate_token")
        db_session.add(token1)
        db_session.commit()
        
        # Try to create second token with same value
        token2 = BlacklistedToken(token="duplicate_token")
        db_session.add(token2)
        
        # This should raise an integrity error
        with pytest.raises(Exception):  # SQLAlchemy IntegrityError
            db_session.commit()

    def test_blacklisted_token_automatic_timestamp(self, db_session: Session):
        """Test that blacklisted_on is automatically set"""
        from datetime import datetime, timezone
        
        before_creation = datetime.now(timezone.utc)
        
        token = BlacklistedToken(token="timestamped_token")
        db_session.add(token)
        db_session.commit()
        db_session.refresh(token)
        
        after_creation = datetime.now(timezone.utc)
        
        # Ensure both datetimes are timezone-aware for comparison
        if token.blacklisted_on.tzinfo is None:
            # If the stored datetime is naive, convert it to UTC
            token_time = token.blacklisted_on.replace(tzinfo=timezone.utc)
        else:
            token_time = token.blacklisted_on
        
        assert before_creation <= token_time <= after_creation


@pytest.mark.unit
class TestBcryptContext:
    """Test bcrypt password hashing functionality"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        hashed = bcrypt_context.hash(password)
        
        # Hash should be different from original password
        assert hashed != password
        # Hash should start with bcrypt prefix
        assert hashed.startswith("$2b$")
        # Should be able to verify the password
        assert bcrypt_context.verify(password, hashed)

    def test_password_verification_failure(self):
        """Test password verification with wrong password"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = bcrypt_context.hash(password)
        
        # Wrong password should not verify
        assert not bcrypt_context.verify(wrong_password, hashed)

    def test_hash_uniqueness(self):
        """Test that same password produces different hashes (due to salt)"""
        password = "same_password"
        hash1 = bcrypt_context.hash(password)
        hash2 = bcrypt_context.hash(password)
        
        # Hashes should be different due to random salt
        assert hash1 != hash2
        # But both should verify the original password
        assert bcrypt_context.verify(password, hash1)
        assert bcrypt_context.verify(password, hash2)


@pytest.mark.database
class TestDatabaseQueries:
    """Test database query operations"""
    
    def test_find_user_by_username(self, db_session: Session):
        """Test finding user by username"""
        # Create a user
        user = User(username="findme", hashed_password="hash123")
        db_session.add(user)
        db_session.commit()
        
        # Find the user
        found_user = db_session.query(User).filter(User.username == "findme").first()
        assert found_user is not None
        assert found_user.username == "findme"
        
        # Try to find non-existent user
        not_found = db_session.query(User).filter(User.username == "notfound").first()
        assert not_found is None

    def test_find_user_by_id(self, db_session: Session):
        """Test finding user by ID"""
        # Create a user
        user = User(username="idtest", hashed_password="hash123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        user_id = user.id
        
        # Find the user by ID
        found_user = db_session.query(User).filter(User.id == user_id).first()
        assert found_user is not None
        assert found_user.id == user_id
        assert found_user.username == "idtest"

    def test_find_blacklisted_token(self, db_session: Session):
        """Test finding blacklisted tokens"""
        # Create a blacklisted token
        token_value = "blacklisted_token_123"
        token = BlacklistedToken(token=token_value)
        db_session.add(token)
        db_session.commit()
        
        # Find the token
        found_token = db_session.query(BlacklistedToken).filter(
            BlacklistedToken.token == token_value
        ).first()
        assert found_token is not None
        assert found_token.token == token_value
        
        # Try to find non-existent token
        not_found = db_session.query(BlacklistedToken).filter(
            BlacklistedToken.token == "not_blacklisted"
        ).first()
        assert not_found is None

    def test_delete_operations(self, db_session: Session):
        """Test delete operations"""
        # Create a user
        user = User(username="deleteme", hashed_password="hash123")
        db_session.add(user)
        db_session.commit()
        user_id = user.id
        
        # Delete the user
        db_session.delete(user)
        db_session.commit()
        
        # Verify user is deleted
        deleted_user = db_session.query(User).filter(User.id == user_id).first()
        assert deleted_user is None

    def test_update_operations(self, db_session: Session):
        """Test update operations"""
        # Create a user
        user = User(username="updateme", hashed_password="hash123")
        db_session.add(user)
        db_session.commit()
        
        # Update the user
        user.email = "updated@example.com"
        user.age = 30
        db_session.commit()
        
        # Verify updates
        db_session.refresh(user)
        assert user.email == "updated@example.com"
        assert user.age == 30
