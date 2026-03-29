{% raw %}
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_login_page_accessible(client: AsyncClient):
    response = await client.get("/admin/login")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_unauthenticated_redirects(client: AsyncClient):
    """Unauthenticated admin list access redirects to login (not 500)."""
    response = await client.get("/admin/user/list", follow_redirects=False)
    assert response.status_code in (302, 303)


@pytest.mark.asyncio
async def test_admin_login_rejects_non_superuser(client: AsyncClient, test_user):
    response = await client.post(
        "/admin/login",
        data={"username": "test@example.com", "password": "testpassword"},
        follow_redirects=False,
    )
    # Failed login: stays on login page (200) or redirects back to it
    location = response.headers.get("location", "login")
    if response.status_code in (302, 303):
        assert "login" in location


@pytest.mark.asyncio
async def test_admin_login_accepts_superuser(client: AsyncClient, superuser):
    response = await client.post(
        "/admin/login",
        data={"username": "admin@example.com", "password": "adminpassword"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    location = response.headers.get("location", "")
    assert "login" not in location


@pytest.mark.asyncio
async def test_admin_user_list_after_login(client: AsyncClient, superuser):
    """Admin user list must return 200, not 500 (regression: wrong engine type)."""
    await client.post(
        "/admin/login",
        data={"username": "admin@example.com", "password": "adminpassword"},
        follow_redirects=True,
    )
    response = await client.get("/admin/user/list")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_item_list_after_login(client: AsyncClient, superuser):
    """Admin item list must return 200, not 500."""
    await client.post(
        "/admin/login",
        data={"username": "admin@example.com", "password": "adminpassword"},
        follow_redirects=True,
    )
    response = await client.get("/admin/item/list")
    assert response.status_code == 200
{% endraw %}
