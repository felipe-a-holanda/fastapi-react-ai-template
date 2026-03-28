{% raw %}
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


class ItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Item]:
        result = await self.session.execute(
            select(Item).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, item_id: int) -> Item | None:
        result = await self.session.execute(
            select(Item).where(Item.id == item_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: ItemCreate) -> Item:
        item = Item(**data.model_dump())
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def update(self, item: Item, data: ItemUpdate) -> Item:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, item: Item) -> None:
        await self.session.delete(item)
        await self.session.commit()
{% endraw %}
