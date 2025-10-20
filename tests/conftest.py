"""
Blank Business Builder - Centralized Test Configuration
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

This file provides centralized test fixtures to ensure proper test isolation.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from blank_business_builder.main import app
from blank_business_builder.database import Base, get_db


# Test database setup - in-memory SQLite for isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create engine with StaticPool to maintain single connection
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False  # Set to True for SQL debugging
)

# Create sessionmaker
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the app's database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create database tables once for the entire test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def cleanup_database():
    """
    Clean up database state between tests.

    This fixture runs automatically before each test to ensure:
    1. All tables are cleared
    2. SQLAlchemy session state is reset
    3. No data pollution between tests
    """
    # Run before test
    yield

    # Run after test - clean up all data
    session = TestingSessionLocal()
    try:
        # Get all table names
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()

    # Clear SQLAlchemy identity map to prevent object caching issues
    Session.close_all()


@pytest.fixture(autouse=True)
def reset_app_state():
    """
    Reset application state between tests.

    Clears any cached state in the FastAPI app that might
    cause test interference.
    """
    yield
    # Clear any app-level caches or state here if needed
    pass


@pytest.fixture
def test_client():
    """Provide a test client for making HTTP requests."""
    return client


@pytest.fixture
def db_session():
    """
    Provide a fresh database session for tests that need direct DB access.

    Usage:
        def test_something(db_session):
            user = User(email="test@example.com")
            db_session.add(user)
            db_session.commit()
    """
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    from blank_business_builder.database import User
    from blank_business_builder.auth import AuthService
    from datetime import datetime, timedelta

    user = User(
        email="sample@example.com",
        hashed_password=AuthService.hash_password("testpass123"),
        full_name="Sample User",
        subscription_tier="free",
        license_status="trial",
        trial_expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def pro_user(db_session):
    """Create a pro tier user for testing."""
    from blank_business_builder.database import User
    from blank_business_builder.auth import AuthService
    from datetime import datetime, timedelta

    user = User(
        email="pro@example.com",
        hashed_password=AuthService.hash_password("testpass123"),
        full_name="Pro User",
        subscription_tier="pro",
        license_status="licensed",
        trial_expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(sample_user):
    """Generate an auth token for the sample user."""
    from blank_business_builder.auth import create_access_token
    return create_access_token(data={"sub": sample_user.email})


@pytest.fixture
def pro_auth_token(pro_user):
    """Generate an auth token for the pro user."""
    from blank_business_builder.auth import create_access_token
    return create_access_token(data={"sub": pro_user.email})


# Export commonly used fixtures and utilities
__all__ = [
    'client',
    'test_client',
    'db_session',
    'sample_user',
    'pro_user',
    'auth_token',
    'pro_auth_token',
    'engine',
    'TestingSessionLocal',
]
