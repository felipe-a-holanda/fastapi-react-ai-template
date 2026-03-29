{% raw %}
from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_item_service
from app.models.user import User
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate
from app.services.item import ItemService

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("/", response_model=list[ItemResponse])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    service: ItemService = Depends(get_item_service),
):
    return await service.list_items(owner_id=current_user.id, skip=skip, limit=limit)


@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    data: ItemCreate,
    current_user: User = Depends(get_current_user),
    service: ItemService = Depends(get_item_service),
):
    return await service.create_item(data, owner_id=current_user.id)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    service: ItemService = Depends(get_item_service),
):
    return await service.get_item(item_id, owner_id=current_user.id)


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    data: ItemUpdate,
    current_user: User = Depends(get_current_user),
    service: ItemService = Depends(get_item_service),
):
    return await service.update_item(item_id, data, owner_id=current_user.id)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    service: ItemService = Depends(get_item_service),
):
    await service.delete_item(item_id, owner_id=current_user.id)
{% endraw %}
