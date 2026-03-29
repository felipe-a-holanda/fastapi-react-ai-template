{% raw %}
"""
Direct function-call tests for route handlers.

httpx's ASGITransport runs the ASGI app in a way that coverage.py cannot trace
after await points in coroutines. These tests call route handlers and dependency
functions directly so coverage is captured accurately.
"""
import pytest
from fastapi import HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.health import health_check
from app.auth import create_access_token, hash_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserLogin
from app.services.auth import AuthService


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_check_direct(session: AsyncSession):
    result = await health_check(session=session)
    assert result["status"] == "ok"
    assert result["database"] == "ok"
    assert "app" in result


# ---------------------------------------------------------------------------
# Auth router — register & login success paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_route_direct(session: AsyncSession):
    from app.api.auth import register

    repo = UserRepository(session)
    service = AuthService(repo)
    response = Response()
    data = UserCreate(email="direct_reg@test.com", password="pw123")
    user = await register(data=data, response=response, service=service)
    assert user.email == "direct_reg@test.com"
    # Cookie should have been set
    assert "access_token" in response.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_login_route_direct(session: AsyncSession):
    from app.api.auth import login

    repo = UserRepository(session)
    service = AuthService(repo)
    # Register user first
    await service.register(UserCreate(email="direct_login@test.com", password="pw123"))

    response = Response()
    data = UserLogin(email="direct_login@test.com", password="pw123")
    token_resp = await login(data=data, response=response, service=service)
    assert token_resp.access_token
    assert "access_token" in response.headers.get("set-cookie", "")


# ---------------------------------------------------------------------------
# get_current_user — user not found and inactive paths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_current_user_unknown_user(session: AsyncSession):
    """Token is valid but the user no longer exists → 401."""
    token = create_access_token(user_id=99999)
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(session=session, access_token=token)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_inactive_user(session: AsyncSession):
    """Token is valid but the user is deactivated → 401."""
    inactive = User(
        email="inactive_dep@test.com",
        hashed_password=hash_password("pw"),
        is_active=False,
    )
    session.add(inactive)
    await session.commit()
    await session.refresh(inactive)

    token = create_access_token(user_id=inactive.id)
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(session=session, access_token=token)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_success(session: AsyncSession, test_user):
    """Happy path: valid token + active user returns the user."""
    token = create_access_token(user_id=test_user.id)
    user = await get_current_user(session=session, access_token=token)
    assert user.id == test_user.id


# ---------------------------------------------------------------------------
# get_session — real implementation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_session_yields_async_session():
    """The real get_session generator should yield an AsyncSession."""
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.api.deps import get_session

    async for session in get_session():
        assert isinstance(session, AsyncSession)
        break


# ---------------------------------------------------------------------------
# Health endpoint — error path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_check_db_error():
    """When the DB execute raises, the endpoint reports degraded status."""
    from unittest.mock import AsyncMock

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=Exception("DB unreachable"))
    result = await health_check(session=mock_session)
    assert result["status"] == "degraded"
    assert result["database"] == "error"


# ---------------------------------------------------------------------------
# AdminAuth — direct login (covers post-await line inside async with)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_auth_login_direct(superuser):
    """Call AdminAuth.login directly to cover the async-with session block."""
    from unittest.mock import AsyncMock, MagicMock

    from app.admin import AdminAuth
    from app.config import settings

    auth = AdminAuth(secret_key=settings.secret_key)

    mock_form = {"username": "admin@example.com", "password": "adminpassword"}
    mock_request = MagicMock()
    mock_request.form = AsyncMock(return_value=mock_form)
    mock_request.session = {}

    result = await auth.login(mock_request)
    assert result is True
    assert mock_request.session["user_id"] == superuser.id
{% endraw %}
