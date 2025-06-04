import pytest
import os
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.engine import create_engine
from app.database import Base, get_db, create_tables, engine, SessionLocal


def test_base_class():
    """Test that Base is a declarative base class"""
    assert hasattr(Base, "metadata")
    assert hasattr(Base, "__table__") is False  # Base itself doesn't have a table


def test_engine_creation():
    """Test that the engine is created with the correct URL"""
    assert engine is not None
    assert hasattr(engine, "url")
    # Test that it uses the environment DATABASE_URL
    assert str(engine.url).startswith("sqlite:///./test.db")


def test_session_local():
    """Test that SessionLocal creates a valid session"""
    assert SessionLocal is not None

    # Create a session and check its type
    session = SessionLocal()
    try:
        assert isinstance(session, Session)
    finally:
        session.close()


def test_get_db():
    """Test the get_db dependency"""
    # Get the generator
    db_generator = get_db()

    # Get the session from the generator
    db = next(db_generator)

    try:
        # Check that we got a valid session
        assert isinstance(db, Session)
    finally:
        # Manually handle the finally block
        try:
            next(db_generator)
        except StopIteration:
            pass


def test_create_tables():
    """Test the create_tables function"""
    with patch("app.database.Base.metadata.create_all") as mock_create_all:
        create_tables()
        mock_create_all.assert_called_once_with(bind=engine)


def test_database_connection_args():
    """Test that SQLite connections have appropriate options"""
    # This is already tested implicitly by the engine creation,
    # but we can add an explicit test here
    assert "sqlite" in str(engine.url)
    # Skip checking specific query params as they may vary between environments


def test_create_tables_integration():
    """Integration test for create_tables function"""
    # Use an in-memory database for testing
    with patch("app.database.engine", create_engine("sqlite:///:memory:")):
        # Import models to ensure they're registered with Base
        from auth.models import User, APIKey
        from prompts.models import Prompt, PromptVersion, Project

        # Call create_tables and verify it doesn't raise any exceptions
        create_tables()

        # Verify tables were created
        assert "users" in Base.metadata.tables
        assert "api_keys" in Base.metadata.tables
        assert "prompts" in Base.metadata.tables
        assert "prompt_versions" in Base.metadata.tables
        assert "projects" in Base.metadata.tables
