{% raw %}
import structlog
from fastapi import HTTPException, status

from app.repositories.item import ItemRepository
from app.schemas.item import ItemCreate, ItemResponse, ItemUpdate

logger = structlog.get_logger()


class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository

    async def list_items(
        self, owner_id: int, skip: int = 0, limit: int = 100
    ) -> list[ItemResponse]:
        items = await self.repository.get_all(owner_id=owner_id, skip=skip, limit=limit)
        return [ItemResponse.model_validate(item) for item in items]

    async def get_item(self, item_id: int, owner_id: int) -> ItemResponse:
        item = await self.repository.get_by_id(item_id, owner_id=owner_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_id} not found",
            )
        return ItemResponse.model_validate(item)

    async def create_item(self, data: ItemCreate, owner_id: int) -> ItemResponse:
        item = await self.repository.create(data, owner_id=owner_id)
        logger.info("item_created", item_id=item.id, owner_id=owner_id)
        return ItemResponse.model_validate(item)

    async def update_item(
        self, item_id: int, data: ItemUpdate, owner_id: int
    ) -> ItemResponse:
        item = await self.repository.get_by_id(item_id, owner_id=owner_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_id} not found",
            )
        updated = await self.repository.update(item, data)
        logger.info("item_updated", item_id=item.id, owner_id=owner_id)
        return ItemResponse.model_validate(updated)

    async def delete_item(self, item_id: int, owner_id: int) -> None:
        item = await self.repository.get_by_id(item_id, owner_id=owner_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item {item_id} not found",
            )
        await self.repository.delete(item)
        logger.info("item_deleted", item_id=item_id, owner_id=owner_id)
{% endraw %}
