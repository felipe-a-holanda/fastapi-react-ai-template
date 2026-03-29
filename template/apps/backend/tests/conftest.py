{% raw %}
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import get_session
from app.auth import hash_password
from app.config import settings
from app.database import Base, engine as app_engine
from app.main import app
from app.models.user import User

# NullPool ensures each checkout gets a fresh connection, avoiding asyncpg
# "another operation is in progress" errors when fixtures share the event loop.
test_engine = create_async_engine(settings.database_url, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Dispose the app's engine pool so the next test gets fresh connections
    # in its own event loop (avoids "Future attached to a different loop").
    await app_engine.dispose()


@pytest.fixture
async def session():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(session):
    async def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(session) -> User:
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def superuser(session) -> User:
    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpassword"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture
async def authenticated_client(client, test_user):
    """Client with auth cookie set."""
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    return client
{% endraw %}
