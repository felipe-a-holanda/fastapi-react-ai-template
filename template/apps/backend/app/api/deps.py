{% raw -%}
from collections.abc import AsyncGenerator

from fastapi import Cookie, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import decode_token
from app.database import async_session_maker
from app.exceptions import AuthenticationError, AuthorizationError
from app.models.user import User
from app.repositories.item import ItemRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.item import ItemService


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# --- Auth dependencies ---


def get_user_repository(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return UserRepository(session)


def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)


async def get_current_user(
    session: AsyncSession = Depends(get_session),
    access_token: str | None = Cookie(default=None),
) -> User:
    if not access_token:
        raise AuthenticationError("Not authenticated")
    payload = decode_token(access_token)
    if not payload or payload.get("type") != "access":
        raise AuthenticationError("Invalid or expired token")
    user_id = int(payload["sub"])
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_superuser:
        raise AuthorizationError("Not enough permissions")
    return current_user


# --- Item dependencies (now require auth) ---


def get_item_repository(session: AsyncSession = Depends(get_session)) -> ItemRepository:
    return ItemRepository(session)


def get_item_service(
    repository: ItemRepository = Depends(get_item_repository),
) -> ItemService:
    return ItemService(repository)


# ------------------------------------------------------------------
# CROSS-SLICE WIRING PATTERN
# ------------------------------------------------------------------
# When a service needs another service (e.g. NotificationService needs
# UserService), wire it HERE — never import across service files.
#
# Example:
#
# def get_notification_service(
#     notification_repo: NotificationRepository = Depends(get_notification_repository),
#     user_service: UserService = Depends(get_user_service),
# ) -> NotificationService:
#     return NotificationService(notification_repo, user_service)
#
# The rule: if it's not wired in deps.py, the dependency doesn't exist.
# ------------------------------------------------------------------
{% endraw %}
