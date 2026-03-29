{% raw %}
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_refresh_token, hash_password
from app.models.user import User


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "new@example.com",
            "password": "securepassword",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    response = await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "another"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient, test_user):
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, session: AsyncSession):
    inactive = User(
        email="inactive@example.com",
        hashed_password=hash_password("password"),
        full_name="Inactive",
        is_active=False,
        is_superuser=False,
    )
    session.add(inactive)
    await session.commit()

    response = await client.post(
        "/api/auth/login",
        json={"email": "inactive@example.com", "password": "password"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_me(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    """A garbage cookie value is rejected with 401."""
    client.cookies.set("access_token", "not.a.valid.token")
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_refresh_token_rejected(client: AsyncClient, test_user):
    """A refresh token in the access_token cookie must be rejected."""
    refresh = create_refresh_token(test_user.id)
    client.cookies.set("access_token", refresh)
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(authenticated_client: AsyncClient):
    response = await authenticated_client.post("/api/auth/logout")
    assert response.status_code == 200


# --- get_current_superuser dependency ---


@pytest.mark.asyncio
async def test_superuser_dep_rejects_regular_user(test_user):
    """get_current_superuser raises 403 for non-superuser."""
    from fastapi import HTTPException

    from app.api.deps import get_current_superuser

    with pytest.raises(HTTPException) as exc_info:
        await get_current_superuser(current_user=test_user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_superuser_dep_accepts_superuser(superuser):
    """get_current_superuser passes through a superuser unchanged."""
    from app.api.deps import get_current_superuser

    result = await get_current_superuser(current_user=superuser)
    assert result == superuser
{% endraw %}
