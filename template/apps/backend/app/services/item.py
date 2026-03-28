{% raw %}
from fastapi import HTTPException, status

from app.repositories.item import ItemRepository
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse


class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository

    async def list_items(self, skip: int = 0, limit: int = 100) -> list[ItemResponse]:
        items = await self.repository.get_all(skip=skip, limit=limit)
        return [ItemResponse.model_validate(item) for item in items]

    async def get_item(self, item_id: int) -> ItemResponse:
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_id} not found",
            )
        return ItemResponse.model_validate(item)

    async def create_item(self, data: ItemCreate) -> ItemResponse:
        item = await self.repository.create(data)
        return ItemResponse.model_validate(item)

    async def update_item(self, item_id: int, data: ItemUpdate) -> ItemResponse:
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_id} not found",
            )
        updated = await self.repository.update(item, data)
        return ItemResponse.model_validate(updated)

    async def delete_item(self, item_id: int) -> None:
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_id} not found",
            )
        await self.repository.delete(item)
{% endraw %}
