import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import uuid
from typing import AsyncGenerator, Generator

from main import app
from api.v1.core.database import get_db, Base
from api.v1.models.user import User
from api.v1.models.project import Project
from api.v1.core.auth import get_password_hash, create_access_token

# Test database URL - using SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
)

TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def shutdown_db_engine():
    yield
    await test_engine.dispose()


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Clean up - drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(test_db) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

    # Clean up
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_inactive_user(test_db: AsyncSession) -> User:
    """Create an inactive test user."""
    user = User(
        id=uuid.uuid4(),
        email="inactive@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=False,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_project(test_db: AsyncSession, test_user: User) -> Project:
    """Create a test project."""
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        description="A test project",
        owner_user_id=test_user.id,
    )
    test_db.add(project)
    await test_db.commit()
    await test_db.refresh(project)
    return project


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create an authentication token for test user."""
    return create_access_token(
        data={"sub": str(test_user.id), "email": test_user.email}
    )


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Create authentication headers."""
    return {"Authorization": f"Bearer {auth_token}"}


# Test data fixtures
@pytest.fixture
def valid_user_data():
    """Valid user registration data."""
    return {"email": "newuser@example.com", "password": "securepassword123"}


@pytest.fixture
def valid_login_data():
    """Valid login data."""
    return {"email": "test@example.com", "password": "testpassword"}


@pytest.fixture
def valid_project_data():
    """Valid project creation data."""
    return {"name": "New Project", "description": "A new project for testing"}
