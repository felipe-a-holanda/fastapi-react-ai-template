{% raw %}
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient):
    response = await client.post("/api/items/", json={"title": "Test item"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test item"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_list_items(client: AsyncClient):
    await client.post("/api/items/", json={"title": "Item 1"})
    await client.post("/api/items/", json={"title": "Item 2"})
    response = await client.get("/api/items/")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_item_not_found(client: AsyncClient):
    response = await client.get("/api/items/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_item(client: AsyncClient):
    create = await client.post("/api/items/", json={"title": "Original"})
    item_id = create.json()["id"]
    response = await client.put(
        f"/api/items/{item_id}", json={"title": "Updated"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient):
    create = await client.post("/api/items/", json={"title": "To delete"})
    item_id = create.json()["id"]
    response = await client.delete(f"/api/items/{item_id}")
    assert response.status_code == 204
    get_response = await client.get(f"/api/items/{item_id}")
    assert get_response.status_code == 404
{% endraw %}
