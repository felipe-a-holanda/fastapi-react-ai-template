{% raw %}
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.auth import verify_password
from app.config import settings
from app.database import async_session_maker
from app.models.item import Item
from app.models.user import User


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")

        async with async_session_maker() as session:
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

        if not user or not user.is_superuser:
            return False
        if not verify_password(password, user.hashed_password):
            return False
        request.session.update({"user_id": user.id})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return "user_id" in request.session


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.email,
        User.full_name,
        User.is_active,
        User.is_superuser,
        User.created_at,
    ]
    column_searchable_list = [User.email, User.full_name]
    column_sortable_list = [User.id, User.email, User.created_at]
    can_create = True
    can_edit = True
    can_delete = True
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"

    # Hide password from list, show in form
    form_excluded_columns = [User.items]
    column_details_exclude_list = [User.hashed_password]


class ItemAdmin(ModelView, model=Item):
    column_list = [Item.id, Item.title, Item.is_completed, Item.owner_id, Item.created_at]
    column_searchable_list = [Item.title]
    column_sortable_list = [Item.id, Item.title, Item.created_at]
    can_create = True
    can_edit = True
    can_delete = True
    name = "Item"
    name_plural = "Items"
    icon = "fa-solid fa-box"


def setup_admin(app) -> Admin:
    authentication_backend = AdminAuth(secret_key=settings.secret_key)
    admin = Admin(
        app,
        async_session_maker,
        authentication_backend=authentication_backend,
        title=f"{settings.app_name} Admin",
    )
    admin.add_view(UserAdmin)
    admin.add_view(ItemAdmin)
    return admin
{% endraw %}
