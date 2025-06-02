import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
import time

from app.main import app
from app.config import settings


@pytest.fixture
def client():
    """TestClient fixture for app testing"""
    return TestClient(app)


def test_app_creation():
    """Test that the app was created with the correct settings"""
    assert app.title == settings.app_name
    assert app.version == settings.app_version

    # Check CORS settings
    cors_middleware = next(
        m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"
    )
    assert cors_middleware is not None


def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["app_name"] == settings.app_name
    assert data["version"] == settings.app_version


def test_root_endpoint(client):
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()

    assert "Welcome to Prompta API" in data["message"]
    assert data["version"] == settings.app_version


def test_not_found_handler(client):
    """Test the 404 exception handler"""
    response = client.get("/non-existent-path")
    assert response.status_code == 404
    data = response.json()

    assert data["detail"] == "Resource not found"


def test_request_timing_middleware(client):
    """Test that the request timing middleware adds X-Process-Time header"""
    # Directly test the middleware function
    with patch("time.time") as mock_time:
        # Mock time.time to return increasing values
        mock_time.side_effect = [100.0, 100.5]

        # We need enough side_effect values for all time.time() calls
        mock_time.side_effect = [100.0, 100.5, 101.0, 101.5, 102.0, 102.5]

        response = client.get("/health")
        assert response.status_code == 200

        # Check that X-Process-Time header was added
        assert "X-Process-Time" in response.headers
        assert float(response.headers["X-Process-Time"]) > 0


@pytest.mark.asyncio
async def test_startup_event():
    """Test the startup event"""
    # Create a AsyncMock for create_tables
    with patch("app.main.create_tables") as mock_create_tables:
        # Get the startup event handler (it's an async function)
        startup_handler = None
        for handler in app.router.on_startup:
            if handler.__name__ == "startup_event":
                startup_handler = handler
                break

        assert startup_handler is not None

        # Call the handler
        await startup_handler()

        # Verify create_tables was called
        mock_create_tables.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_event():
    """Test the shutdown event"""
    # Get the shutdown event handler (it's an async function)
    shutdown_handler = None
    for handler in app.router.on_shutdown:
        if handler.__name__ == "shutdown_event":
            shutdown_handler = handler
            break

    assert shutdown_handler is not None

    # Call the handler - should not raise any exceptions
    await shutdown_handler()
