{% raw %}
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.repositories.item import ItemRepository
from app.services.item import ItemService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


def get_item_repository(
    session: AsyncSession = Depends(get_session),
) -> ItemRepository:
    return ItemRepository(session)


def get_item_service(
    repository: ItemRepository = Depends(get_item_repository),
) -> ItemService:
    return ItemService(repository)
{% endraw %}
