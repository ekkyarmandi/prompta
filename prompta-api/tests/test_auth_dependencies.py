import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from auth.dependencies import (
    get_current_user_from_token,
    get_current_user_from_api_key,
    get_current_user,
    get_current_user_flexible,
)


@pytest.mark.asyncio
async def test_get_current_user_from_token_success():
    """Test successful user retrieval from token"""
    # Create mock objects
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.is_active = True
    mock_credentials = MagicMock()
    mock_credentials.credentials = "valid_token"

    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Test the function
    with patch("auth.dependencies.verify_token") as mock_verify_token:
        mock_verify_token.return_value = MagicMock(username="testuser")
        user = await get_current_user_from_token(mock_credentials, mock_db)
        assert user == mock_user
        mock_verify_token.assert_called_once_with("valid_token")


@pytest.mark.asyncio
async def test_get_current_user_from_token_invalid_token():
    """Test handling of invalid token"""
    # Create mock objects
    mock_db = MagicMock()
    mock_credentials = MagicMock()
    mock_credentials.credentials = "invalid_token"

    # Test the function
    with patch("auth.dependencies.verify_token", return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token(mock_credentials, mock_db)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_from_token_user_not_found():
    """Test handling of token with valid format but non-existent user"""
    # Create mock objects
    mock_db = MagicMock()
    mock_credentials = MagicMock()
    mock_credentials.credentials = "valid_token_wrong_user"

    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Test the function
    with patch("auth.dependencies.verify_token") as mock_verify_token:
        mock_verify_token.return_value = MagicMock(username="nonexistent_user")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token(mock_credentials, mock_db)

        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_from_token_inactive_user():
    """Test handling of token for inactive user"""
    # Create mock objects
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.is_active = False
    mock_credentials = MagicMock()
    mock_credentials.credentials = "valid_token"

    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Test the function
    with patch("auth.dependencies.verify_token") as mock_verify_token:
        mock_verify_token.return_value = MagicMock(username="inactive_user")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_token(mock_credentials, mock_db)

        assert exc_info.value.status_code == 400
        assert "Inactive user" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_from_api_key_success():
    """Test successful user retrieval from API key"""
    # Create mock objects
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.is_active = True

    # Test the function
    with patch("auth.dependencies.verify_api_key", return_value=mock_user):
        user = await get_current_user_from_api_key("valid_api_key", mock_db)
        assert user == mock_user


@pytest.mark.asyncio
async def test_get_current_user_from_api_key_missing_key():
    """Test handling of missing API key"""
    # Create mock objects
    mock_db = MagicMock()

    # Test the function
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_from_api_key("", mock_db)

    assert exc_info.value.status_code == 401
    assert "API key required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_from_api_key_invalid_key():
    """Test handling of invalid API key"""
    # Create mock objects
    mock_db = MagicMock()

    # Test the function
    with patch("auth.dependencies.verify_api_key", return_value=None):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_api_key("invalid_api_key", mock_db)

        assert exc_info.value.status_code == 401
        assert "Invalid API key" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_from_api_key_inactive_user():
    """Test handling of API key for inactive user"""
    # Create mock objects
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.is_active = False

    # Test the function
    with patch("auth.dependencies.verify_api_key", return_value=mock_user):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_api_key("valid_api_key", mock_db)

        assert exc_info.value.status_code == 400
        assert "Inactive user" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_token_first():
    """Test that token authentication is tried first"""
    # Create mock objects
    mock_token_user = MagicMock()
    mock_api_key_user = MagicMock()

    # Test the function
    user = await get_current_user(mock_token_user, mock_api_key_user)
    assert user == mock_token_user


@pytest.mark.asyncio
async def test_get_current_user_api_key_fallback():
    """Test fallback to API key authentication when token fails"""
    # Create mock objects
    mock_token_user = None
    mock_api_key_user = MagicMock()

    # Test the function
    user = await get_current_user(mock_token_user, mock_api_key_user)
    assert user == mock_api_key_user


@pytest.mark.asyncio
async def test_get_current_user_both_fail():
    """Test handling when both authentication methods fail"""
    # Create mock objects
    mock_token_user = None
    mock_api_key_user = None

    # Test the function
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(mock_token_user, mock_api_key_user)

    assert exc_info.value.status_code == 401
    assert "Authentication required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_current_user_flexible_token_success():
    """Test flexible authentication with valid token"""
    # Create mock objects
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.is_active = True
    mock_credentials = MagicMock()
    mock_credentials.credentials = "valid_token"

    # Setup mocks
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Test the function
    with patch("auth.dependencies.verify_token") as mock_verify_token:
        mock_verify_token.return_value = MagicMock(username="testuser")
        user = await get_current_user_flexible(mock_db, mock_credentials, None)
        assert user == mock_user


@pytest.mark.asyncio
async def test_get_current_user_flexible_api_key_fallback():
    """Test flexible authentication fallback to API key"""
    # Create mock objects
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.is_active = True

    # Setup mocks for token failure
    with patch("auth.dependencies.verify_token", return_value=None):
        # Setup mocks for API key success
        with patch("auth.dependencies.verify_api_key", return_value=mock_user):
            user = await get_current_user_flexible(
                mock_db, MagicMock(), "valid_api_key"
            )
            assert user == mock_user


@pytest.mark.asyncio
async def test_get_current_user_flexible_both_fail():
    """Test flexible authentication when both methods fail"""
    # Create mock objects
    mock_db = MagicMock()

    # Setup mocks for both failures
    with patch("auth.dependencies.verify_token", return_value=None):
        with patch("auth.dependencies.verify_api_key", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_flexible(mock_db, MagicMock(), "invalid_api_key")

            assert exc_info.value.status_code == 401
            assert "Could not validate credentials" in exc_info.value.detail
