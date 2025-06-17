import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from jose import jwt
import secrets

from auth.security import (
    verify_password,
    get_password_hash,
    authenticate_user,
    create_access_token,
    verify_token,
    generate_api_key,
    hash_api_key,
    verify_api_key,
    create_api_key,
)
from auth.models import User, APIKey
from auth.schemas import TokenData
from app.config import settings


def test_password_hashing():
    """Test password hashing and verification"""
    password = "test_password123"
    hashed = get_password_hash(password)

    # Verify the hash is different from the original password
    assert hashed != password

    # Verify the password against the hash
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False


def test_authenticate_user():
    """Test user authentication with username or email"""
    # Create a mock user
    mock_user = MagicMock()
    mock_user.username = "testuser"
    mock_user.email = "test@example.com"
    mock_user.password_hash = get_password_hash("testpassword")

    # Create a mock database session
    mock_db = MagicMock()

    # Test successful authentication with username
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    with patch("auth.security.verify_password", return_value=True):
        result = authenticate_user(mock_db, "testuser", "testpassword")
        assert result == mock_user

    # Test successful authentication with email
    # First call returns None (username not found), second call returns user (email found)
    mock_db.query.return_value.filter.return_value.first.side_effect = [None, mock_user]
    with patch("auth.security.verify_password", return_value=True):
        result = authenticate_user(mock_db, "test@example.com", "testpassword")
        assert result == mock_user

    # Test failed authentication (wrong password)
    mock_db.query.return_value.filter.return_value.first.side_effect = None
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    with patch("auth.security.verify_password", return_value=False):
        result = authenticate_user(mock_db, "testuser", "wrongpassword")
        assert result is False

    # Test user not found (neither username nor email exists)
    mock_db.query.return_value.filter.return_value.first.side_effect = [None, None]
    result = authenticate_user(mock_db, "nonexistentuser", "testpassword")
    assert result is False


def test_create_access_token():
    """Test JWT token creation"""
    data = {"sub": "testuser"}

    # Test with default expiration
    token = create_access_token(data)
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

    assert payload["sub"] == "testuser"
    assert "exp" in payload

    # Test with custom expiration
    expires_delta = timedelta(minutes=15)
    token = create_access_token(data, expires_delta=expires_delta)
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

    assert payload["sub"] == "testuser"
    assert "exp" in payload


def test_verify_token():
    """Test JWT token verification"""
    # Create a valid token
    token = create_access_token({"sub": "testuser"})

    # Test verification of valid token
    token_data = verify_token(token)
    assert isinstance(token_data, TokenData)
    assert token_data.username == "testuser"

    # Test invalid token
    assert verify_token("invalid-token") is None

    # Test malformed token (missing sub claim)
    with patch("auth.security.jwt.decode") as mock_decode:
        mock_decode.return_value = {}  # Token with no 'sub' claim
        assert verify_token("token-without-sub") is None


def test_generate_api_key():
    """Test API key generation"""
    # Patch secrets.token_urlsafe to return a predictable value
    with patch("auth.security.secrets.token_urlsafe", return_value="test_token"):
        api_key = generate_api_key()
        assert api_key == "prompta_test_token"

    # Test that generated keys are different each time
    key1 = generate_api_key()
    key2 = generate_api_key()
    assert key1 != key2
    assert key1.startswith("prompta_")
    assert key2.startswith("prompta_")


def test_hash_api_key():
    """Test API key hashing"""
    api_key = "prompta_test_key"
    hash1 = hash_api_key(api_key)
    hash2 = hash_api_key(api_key)

    # Same input should produce same hash
    assert hash1 == hash2

    # Different input should produce different hash
    assert hash_api_key("prompta_different_key") != hash1

    # Hash should be a hexadecimal string of length 64 (SHA-256)
    assert len(hash1) == 64
    assert all(c in "0123456789abcdef" for c in hash1)


def test_verify_api_key():
    """Test API key verification"""
    # Create mock objects
    mock_db = MagicMock()
    mock_api_key = MagicMock()
    mock_user = MagicMock()

    # Setup the mock API key
    mock_api_key.is_active = True
    mock_api_key.expires_at = None
    mock_api_key.user = mock_user

    # Setup database query mock
    mock_db.query.return_value.filter.return_value.first.return_value = mock_api_key

    # Test successful verification
    with patch("auth.security.hash_api_key", return_value="test_hash"):
        result = verify_api_key(mock_db, "test_api_key")
        assert result == mock_user
        assert mock_api_key.last_used_at is not None

    # Test expired key
    mock_api_key.expires_at = datetime.utcnow() - timedelta(days=1)
    result = verify_api_key(mock_db, "test_api_key")
    assert result is None

    # Test key not found
    mock_db.query.return_value.filter.return_value.first.return_value = None
    result = verify_api_key(mock_db, "nonexistent_key")
    assert result is None


def test_create_api_key_in_db():
    """Test creating an API key in the database"""
    # Create mock objects
    mock_db = MagicMock()
    mock_api_key = MagicMock()

    # Setup database session mock
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    # Test creating API key with default expiration
    with patch("auth.security.generate_api_key", return_value="test_api_key"):
        with patch("auth.security.hash_api_key", return_value="test_hash"):
            with patch("auth.security.APIKey", return_value=mock_api_key):
                db_api_key, api_key = create_api_key(mock_db, "user123", "Test Key")

                assert db_api_key == mock_api_key
                assert api_key == "test_api_key"

                mock_db.add.assert_called_once_with(mock_api_key)
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once_with(mock_api_key)

    # Test creating API key with custom expiration
    expires_at = datetime.utcnow() + timedelta(days=30)
    with patch("auth.security.generate_api_key", return_value="test_api_key"):
        with patch("auth.security.hash_api_key", return_value="test_hash"):
            with patch("auth.security.APIKey", return_value=mock_api_key):
                db_api_key, api_key = create_api_key(
                    mock_db, "user123", "Test Key", expires_at=expires_at
                )

                assert db_api_key == mock_api_key
                assert api_key == "test_api_key"
