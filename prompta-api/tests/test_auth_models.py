import pytest
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from auth.models import User, APIKey
from app.database import Base


@pytest.fixture(scope="function")
def setup_database():
    """Set up a test database for model testing"""
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:")

    # Create tables
    Base.metadata.create_all(engine)

    # Create session
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    # Clean up
    session.close()
    Base.metadata.drop_all(engine)


def test_user_model(setup_database):
    """Test User model attributes and relationships"""
    # Create a user with minimal attributes
    user = User(
        username="testuser", email="test@example.com", password_hash="hashed_password"
    )

    # Add to database to ensure defaults are set
    session = setup_database
    session.add(user)
    session.commit()
    session.refresh(user)

    # Test basic attributes
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.password_hash == "hashed_password"
    assert user.is_active is True  # Default value

    # Test ID is a valid UUID
    assert user.id is not None
    try:
        UUID(user.id)
        is_valid_uuid = True
    except ValueError:
        is_valid_uuid = False
    assert is_valid_uuid is True

    # Test timestamps
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)

    # Test relationships
    assert hasattr(user, "api_keys")
    assert hasattr(user, "prompts")
    assert hasattr(user, "projects")

    # Test __repr__
    assert repr(user) == f"<User(username='testuser', email='test@example.com')>"


def test_api_key_model(setup_database):
    """Test APIKey model attributes and relationships"""
    # Create a user for the relationship
    user = User(
        username="testuser", email="test@example.com", password_hash="hashed_password"
    )

    session = setup_database
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create an API key
    expires_at = datetime.utcnow() + timedelta(days=30)
    api_key = APIKey(
        key_hash="hashed_api_key",
        name="Test API Key",
        user_id=user.id,
        expires_at=expires_at,
    )

    session.add(api_key)
    session.commit()
    session.refresh(api_key)

    # Test basic attributes
    assert api_key.key_hash == "hashed_api_key"
    assert api_key.name == "Test API Key"
    assert api_key.user_id == user.id
    assert api_key.expires_at == expires_at
    assert api_key.is_active is True  # Default value
    assert api_key.last_used_at is None  # Default value

    # Test ID is a valid UUID
    assert api_key.id is not None
    try:
        UUID(api_key.id)
        is_valid_uuid = True
    except ValueError:
        is_valid_uuid = False
    assert is_valid_uuid is True

    # Test timestamps
    assert isinstance(api_key.created_at, datetime)

    # Test relationship with user
    assert hasattr(api_key, "user")
    assert api_key.user == user

    # Test __repr__
    assert repr(api_key) == f"<APIKey(name='Test API Key', user_id='{user.id}')>"


def test_user_and_api_key_relationship(setup_database):
    """Test relationship between User and APIKey models"""
    session = setup_database

    # Create a user
    user = User(
        username="testuser", email="test@example.com", password_hash="hashed_password"
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    # Create API keys for the user
    api_key1 = APIKey(key_hash="hashed_api_key_1", name="Test API Key 1", user=user)

    api_key2 = APIKey(key_hash="hashed_api_key_2", name="Test API Key 2", user=user)

    session.add(api_key1)
    session.add(api_key2)
    session.commit()
    session.refresh(user)

    # Test that the keys are properly associated with the user
    assert api_key1.user == user
    assert api_key2.user == user

    # Test that the user has the keys in its api_keys relationship
    assert len(user.api_keys) == 2
    assert any(k.name == "Test API Key 1" for k in user.api_keys)
    assert any(k.name == "Test API Key 2" for k in user.api_keys)
