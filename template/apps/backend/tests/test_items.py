{% raw %}
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_items_require_auth(client: AsyncClient):
    response = await client.get("/api/items/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_item(authenticated_client: AsyncClient):
    response = await authenticated_client.post(
        "/api/items/", json={"title": "Test item"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test item"
    assert data["id"] is not None
    assert data["owner_id"] is not None


@pytest.mark.asyncio
async def test_list_items(authenticated_client: AsyncClient):
    await authenticated_client.post("/api/items/", json={"title": "Item 1"})
    await authenticated_client.post("/api/items/", json={"title": "Item 2"})
    response = await authenticated_client.get("/api/items/")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_list_items_empty(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/items/")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_item(authenticated_client: AsyncClient):
    create = await authenticated_client.post("/api/items/", json={"title": "My item"})
    item_id = create.json()["id"]
    response = await authenticated_client.get(f"/api/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "My item"


@pytest.mark.asyncio
async def test_get_item_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/items/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_item(authenticated_client: AsyncClient):
    create = await authenticated_client.post(
        "/api/items/", json={"title": "Original"}
    )
    item_id = create.json()["id"]
    response = await authenticated_client.put(
        f"/api/items/{item_id}", json={"title": "Updated"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_update_item_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.put("/api/items/999", json={"title": "X"})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_item(authenticated_client: AsyncClient):
    create = await authenticated_client.post(
        "/api/items/", json={"title": "To delete"}
    )
    item_id = create.json()["id"]
    response = await authenticated_client.delete(f"/api/items/{item_id}")
    assert response.status_code == 204
    get_response = await authenticated_client.get(f"/api/items/{item_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_item_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.delete("/api/items/999")
    assert response.status_code == 404
{% endraw %}
