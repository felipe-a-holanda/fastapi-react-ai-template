{% raw %}
from fastapi import APIRouter, Depends, status

from app.api.deps import get_item_service
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from app.services.item import ItemService

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("/", response_model=list[ItemResponse])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    service: ItemService = Depends(get_item_service),
):
    return await service.list_items(skip=skip, limit=limit)


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    data: ItemCreate,
    service: ItemService = Depends(get_item_service),
):
    return await service.create_item(data)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    service: ItemService = Depends(get_item_service),
):
    return await service.get_item(item_id)


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    data: ItemUpdate,
    service: ItemService = Depends(get_item_service),
):
    return await service.update_item(item_id, data)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    service: ItemService = Depends(get_item_service),
):
    await service.delete_item(item_id)
{% endraw %}
