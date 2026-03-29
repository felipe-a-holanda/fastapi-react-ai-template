{% raw %}
"""Direct unit tests for service and repository layers."""
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
from app.models.item import Item
from app.models.user import User
from app.repositories.item import ItemRepository
from app.repositories.user import UserRepository
from app.schemas.item import ItemCreate, ItemUpdate
from app.schemas.user import UserCreate
from app.services.auth import AuthService
from app.services.item import ItemService


# ---------------------------------------------------------------------------
# UserRepository
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_repo_create_and_get_by_email(session: AsyncSession):
    repo = UserRepository(session)
    user = await repo.create(email="repo@test.com", hashed_password=hash_password("pw"))
    assert user.id is not None

    found = await repo.get_by_email("repo@test.com")
    assert found is not None
    assert found.email == "repo@test.com"


@pytest.mark.asyncio
async def test_user_repo_get_by_id(session: AsyncSession):
    repo = UserRepository(session)
    user = await repo.create(email="byid@test.com", hashed_password=hash_password("pw"))

    found = await repo.get_by_id(user.id)
    assert found is not None
    assert found.id == user.id


@pytest.mark.asyncio
async def test_user_repo_get_by_id_missing(session: AsyncSession):
    repo = UserRepository(session)
    assert await repo.get_by_id(99999) is None


@pytest.mark.asyncio
async def test_user_repo_get_by_email_missing(session: AsyncSession):
    repo = UserRepository(session)
    assert await repo.get_by_email("nope@test.com") is None


# ---------------------------------------------------------------------------
# ItemRepository
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_item_repo_create_and_list(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    item = await repo.create(ItemCreate(title="Repo item"), owner_id=test_user.id)
    assert item.id is not None

    items = await repo.get_all(owner_id=test_user.id)
    assert len(items) == 1
    assert items[0].title == "Repo item"


@pytest.mark.asyncio
async def test_item_repo_get_by_id(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    item = await repo.create(ItemCreate(title="Find me"), owner_id=test_user.id)

    found = await repo.get_by_id(item.id, owner_id=test_user.id)
    assert found is not None
    assert found.title == "Find me"


@pytest.mark.asyncio
async def test_item_repo_get_by_id_missing(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    assert await repo.get_by_id(99999, owner_id=test_user.id) is None


@pytest.mark.asyncio
async def test_item_repo_update(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    item = await repo.create(ItemCreate(title="Old title"), owner_id=test_user.id)
    updated = await repo.update(item, ItemUpdate(title="New title"))
    assert updated.title == "New title"


@pytest.mark.asyncio
async def test_item_repo_delete(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    item = await repo.create(ItemCreate(title="Delete me"), owner_id=test_user.id)
    await repo.delete(item)
    assert await repo.get_by_id(item.id, owner_id=test_user.id) is None


# ---------------------------------------------------------------------------
# AuthService
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auth_service_register(session: AsyncSession):
    repo = UserRepository(session)
    service = AuthService(repo)
    result = await service.register(
        UserCreate(email="svc@test.com", password="password123")
    )
    assert result.email == "svc@test.com"


@pytest.mark.asyncio
async def test_auth_service_register_duplicate_raises(session: AsyncSession):
    repo = UserRepository(session)
    service = AuthService(repo)
    await service.register(UserCreate(email="dup@test.com", password="pw"))
    with pytest.raises(HTTPException) as exc_info:
        await service.register(UserCreate(email="dup@test.com", password="pw"))
    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_auth_service_login(session: AsyncSession):
    repo = UserRepository(session)
    service = AuthService(repo)
    await service.register(UserCreate(email="login@test.com", password="secret"))
    token = await service.login("login@test.com", "secret")
    assert token.access_token


@pytest.mark.asyncio
async def test_auth_service_login_wrong_password(session: AsyncSession):
    repo = UserRepository(session)
    service = AuthService(repo)
    await service.register(UserCreate(email="wrong@test.com", password="correct"))
    with pytest.raises(HTTPException) as exc_info:
        await service.login("wrong@test.com", "incorrect")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_service_login_inactive_user(session: AsyncSession):
    repo = UserRepository(session)
    user = User(
        email="inactive2@test.com",
        hashed_password=hash_password("pw"),
        is_active=False,
    )
    session.add(user)
    await session.commit()
    service = AuthService(repo)
    with pytest.raises(HTTPException) as exc_info:
        await service.login("inactive2@test.com", "pw")
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_auth_service_refresh(session: AsyncSession):
    repo = UserRepository(session)
    service = AuthService(repo)
    result = await service.register(UserCreate(email="refresh@test.com", password="pw"))
    token = await service.refresh(result.id)
    assert token.access_token


@pytest.mark.asyncio
async def test_auth_service_refresh_missing_user(session: AsyncSession):
    repo = UserRepository(session)
    service = AuthService(repo)
    with pytest.raises(HTTPException) as exc_info:
        await service.refresh(99999)
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# ItemService
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_item_service_list(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    service = ItemService(repo)
    await repo.create(ItemCreate(title="Svc item"), owner_id=test_user.id)
    items = await service.list_items(owner_id=test_user.id)
    assert len(items) == 1
    assert items[0].title == "Svc item"


@pytest.mark.asyncio
async def test_item_service_create(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    service = ItemService(repo)
    item = await service.create_item(ItemCreate(title="Created"), owner_id=test_user.id)
    assert item.id is not None
    assert item.title == "Created"


@pytest.mark.asyncio
async def test_item_service_get_item(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    service = ItemService(repo)
    created = await service.create_item(ItemCreate(title="Get me"), owner_id=test_user.id)
    found = await service.get_item(created.id, owner_id=test_user.id)
    assert found.title == "Get me"


@pytest.mark.asyncio
async def test_item_service_get_item_not_found(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    service = ItemService(repo)
    with pytest.raises(HTTPException) as exc_info:
        await service.get_item(99999, owner_id=test_user.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_item_service_update(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    service = ItemService(repo)
    created = await service.create_item(ItemCreate(title="Old"), owner_id=test_user.id)
    updated = await service.update_item(
        created.id, ItemUpdate(title="New"), owner_id=test_user.id
    )
    assert updated.title == "New"


@pytest.mark.asyncio
async def test_item_service_update_not_found(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    service = ItemService(repo)
    with pytest.raises(HTTPException) as exc_info:
        await service.update_item(99999, ItemUpdate(title="X"), owner_id=test_user.id)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_item_service_delete(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    service = ItemService(repo)
    created = await service.create_item(ItemCreate(title="Bye"), owner_id=test_user.id)
    await service.delete_item(created.id, owner_id=test_user.id)
    with pytest.raises(HTTPException):
        await service.get_item(created.id, owner_id=test_user.id)


@pytest.mark.asyncio
async def test_item_service_delete_not_found(session: AsyncSession, test_user: User):
    repo = ItemRepository(session)
    service = ItemService(repo)
    with pytest.raises(HTTPException) as exc_info:
        await service.delete_item(99999, owner_id=test_user.id)
    assert exc_info.value.status_code == 404
{% endraw %}
