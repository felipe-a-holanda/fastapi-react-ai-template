# AI-Agent-Optimized Monorepo — Copier Template Specification v2

> **Purpose**: Complete specification for generating a Copier template that scaffolds an AI-agent-optimized full-stack monorepo. Paste this into Claude Code and instruct it to generate the template file by file.
>
> **v2 changes**: Resolved service/framework coupling, introduced request-scoped transactions, added cross-slice reference pattern, explicit error taxonomy, contract testing, and domain escalation rules.

---

## 1. Meta: Template Engine

- **Engine**: Copier (NOT Cookiecutter)
- **Template variables** (defined in `copier.yml`):
  - `project_name` (str): e.g. "my-saas"
  - `project_slug` (str, derived): kebab-case of project_name
  - `db_name` (str, default: `{{ project_slug }}`)
  - `python_version` (str, default: "3.12")
  - `node_version` (str, default: "20")
  - `author_name` (str)
  - `author_email` (str)
- All files below live under `template/` in the Copier repo
- Use Jinja2 `{{ project_slug }}` where the project name appears in generated files

---

## 2. Target Directory Structure

```
{{ project_slug }}/
├── copier.yml                     # (only in template repo, not in output)
├── pnpm-workspace.yaml
├── package.json
├── justfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI
├── ARCHITECTURE.md
├── AGENTS.md                      # Root agent instructions
├── CLAUDE.md
│
├── packages/
│   ├── contracts/
│   │   ├── openapi.yaml           # Source of truth
│   │   └── package.json
│   └── client/
│       ├── src/
│       │   └── types.ts           # Generated — DO NOT EDIT
│       └── package.json
│
├── apps/
│   ├── backend/
│   │   ├── AGENTS.md              # Backend-specific agent rules
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── alembic.ini
│   │   ├── alembic/
│   │   │   ├── env.py
│   │   │   └── versions/
│   │   │       └── 001_create_tables.py
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── exceptions.py      # Domain exceptions (NOT HTTP)
│   │   │   ├── logging.py         # structlog setup
│   │   │   ├── auth.py            # JWT + password hashing
│   │   │   ├── admin.py           # SQLAdmin panel
│   │   │   ├── seed.py            # Database seeding
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py        # User model
│   │   │   │   └── item.py        # Item model (owner FK)
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py        # User/auth schemas
│   │   │   │   └── item.py        # Item schemas
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py        # User DB access
│   │   │   │   └── item.py        # Item DB access
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py        # Auth business logic
│   │   │   │   └── item.py        # Item business logic
│   │   │   └── api/
│   │   │       ├── __init__.py
│   │   │       ├── deps.py        # FastAPI dependencies + auth
│   │   │       ├── auth.py        # Auth routes
│   │   │       ├── health.py      # Health check route
│   │   │       └── items.py       # Item routes (auth-protected)
│   │   └── tests/
│   │       ├── conftest.py
│   │       ├── test_auth.py
│   │       ├── test_items.py
│   │       └── test_contract.py   # v2: OpenAPI contract validation
│   │
│   └── frontend/
│       ├── AGENTS.md              # Frontend-specific agent rules
│       ├── Dockerfile
│       ├── package.json
│       ├── tsconfig.json
│       ├── next.config.js
│       ├── tailwind.config.ts
│       ├── postcss.config.js
│       ├── components.json        # shadcn/ui config
│       ├── src/
│       │   ├── app/
│       │   │   ├── layout.tsx
│       │   │   ├── page.tsx
│       │   │   └── providers.tsx  # QueryClientProvider
│       │   ├── lib/
│       │   │   ├── api-client.ts  # Generated types + fetch wrapper
│       │   │   ├── store.ts       # Zustand store for UI state
│       │   │   └── utils.ts       # cn() helper for shadcn
│       │   ├── features/
│       │   │   ├── auth/
│       │   │   │   ├── api.ts     # Auth hooks (useCurrentUser, useLogin, etc.)
│       │   │   │   ├── schema.ts  # Zod login/register schemas
│       │   │   │   ├── LoginForm.tsx
│       │   │   │   └── RegisterForm.tsx
│       │   │   └── items/
│       │   │       ├── api.ts     # TanStack Query hooks
│       │   │       ├── schema.ts  # Zod validation (mirrors backend)
│       │   │       ├── ItemList.tsx
│       │   │       └── ItemForm.tsx
│       │   └── components/
│       │       └── ui/            # shadcn/ui components (copied in)
│       └── tests/
│           └── items.test.tsx
```

---

## 3. Design Principles (embed in AGENTS.md and CLAUDE.md)

1. **OpenAPI is the single source of truth** for all API contracts
2. **Contracts flow one direction**: `openapi.yaml → generated types → backend implements → frontend consumes`
3. **Every feature follows the reference pattern** (items). To add a feature, copy `items` across all layers
4. **No fetch() in components**. All data access goes through TanStack Query hooks in `features/*/api.ts`
5. **No ad-hoc types**. All request/response types come from the generated client
6. **Strict layering in backend**: Router → Service → Repository. Routers never touch the database. Services never import FastAPI (they raise domain exceptions). Repositories never contain business logic
7. **One file = one concern**. No file should mix model definitions, business logic, and route handling
8. **Authentication by default**. All data endpoints require auth. JWT tokens live in httpOnly cookies — agents add `credentials: "include"` and the `get_current_user` dependency
9. **User isolation**. All user-scoped data is filtered by `owner_id` at the repository level — agents never return another user's data
10. **Request-scoped transactions**. Repositories never commit. The session dependency commits on success and rolls back on failure. This allows services to compose multiple repository calls atomically
11. **Domain exceptions, not HTTP exceptions**. Services raise `NotFoundError`, `ConflictError`, etc. The exception handler translates them to HTTP status codes. This keeps services framework-agnostic
12. **No domain layer until needed**. Business logic lives in services. Introduce dedicated domain objects only when a service accumulates complex invariants that deserve their own unit tests independent of persistence

---

## 4. Reference Feature: Items (CRUD)

The "items" feature is the canonical example. Every file below must be generated in the template. Agents will copy this pattern for every new feature.

### 4.1 Contract: `packages/contracts/openapi.yaml`

```yaml
openapi: 3.0.3
info:
  title: "{{ project_slug }} API"
  version: "0.1.0"

paths:
  /api/items:
    get:
      operationId: listItems
      summary: List all items for current user
      security:
        - cookieAuth: []
      parameters:
        - name: skip
          in: query
          schema:
            type: integer
            default: 0
        - name: limit
          in: query
          schema:
            type: integer
            default: 100
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/Item"
    post:
      operationId: createItem
      summary: Create an item
      security:
        - cookieAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ItemCreate"
      responses:
        "201":
          description: Created
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Item"
        "422":
          description: Validation error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/HTTPValidationError"

  /api/items/{item_id}:
    get:
      operationId: getItem
      summary: Get an item by ID
      security:
        - cookieAuth: []
      parameters:
        - name: item_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Item"
        "404":
          description: Not found
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ErrorResponse"
    put:
      operationId: updateItem
      summary: Update an item
      security:
        - cookieAuth: []
      parameters:
        - name: item_id
          in: path
          required: true
          schema:
            type: integer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/ItemUpdate"
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Item"
        "404":
          description: Not found
    delete:
      operationId: deleteItem
      summary: Delete an item
      security:
        - cookieAuth: []
      parameters:
        - name: item_id
          in: path
          required: true
          schema:
            type: integer
      responses:
        "204":
          description: Deleted
        "404":
          description: Not found

  /api/auth/register:
    post:
      operationId: register
      summary: Register a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/UserCreate"
      responses:
        "201":
          description: Created
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
        "409":
          description: Email already registered

  /api/auth/login:
    post:
      operationId: login
      summary: Login and receive JWT cookie
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/LoginRequest"
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
        "401":
          description: Invalid credentials

  /api/auth/me:
    get:
      operationId: getCurrentUser
      summary: Get current authenticated user
      security:
        - cookieAuth: []
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
        "401":
          description: Not authenticated

  /api/auth/logout:
    post:
      operationId: logout
      summary: Clear auth cookie
      responses:
        "204":
          description: Logged out

  /api/health:
    get:
      operationId: healthCheck
      summary: Health check
      responses:
        "200":
          description: OK
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "ok"

components:
  securitySchemes:
    cookieAuth:
      type: apiKey
      in: cookie
      name: access_token

  schemas:
    Item:
      type: object
      required: [id, title, is_completed, owner_id, created_at]
      properties:
        id:
          type: integer
        title:
          type: string
          maxLength: 255
        description:
          type: string
          nullable: true
        is_completed:
          type: boolean
          default: false
        owner_id:
          type: integer
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time
          nullable: true

    ItemCreate:
      type: object
      required: [title]
      properties:
        title:
          type: string
          maxLength: 255
        description:
          type: string
          nullable: true

    ItemUpdate:
      type: object
      properties:
        title:
          type: string
          maxLength: 255
        description:
          type: string
          nullable: true
        is_completed:
          type: boolean

    User:
      type: object
      required: [id, email, is_active, created_at]
      properties:
        id:
          type: integer
        email:
          type: string
          format: email
        full_name:
          type: string
          nullable: true
        is_active:
          type: boolean
        created_at:
          type: string
          format: date-time

    UserCreate:
      type: object
      required: [email, password]
      properties:
        email:
          type: string
          format: email
        password:
          type: string
          minLength: 8
        full_name:
          type: string
          nullable: true

    LoginRequest:
      type: object
      required: [email, password]
      properties:
        email:
          type: string
          format: email
        password:
          type: string

    ErrorResponse:
      type: object
      required: [detail]
      properties:
        detail:
          type: string

    HTTPValidationError:
      type: object
      properties:
        detail:
          type: array
          items:
            type: object
            properties:
              loc:
                type: array
                items:
                  oneOf:
                    - type: string
                    - type: integer
              msg:
                type: string
              type:
                type: string
```

### 4.2 Backend: Domain Exceptions — `apps/backend/app/exceptions.py`

> **v2 CHANGE**: Exceptions are now domain-level, not HTTP-level. Services raise these. The exception handler in `main.py` maps them to HTTP status codes. This is the **single place** where domain errors become HTTP responses.

```python
"""
Domain exceptions.

Services raise these. They carry NO HTTP concepts.
The handler in main.py maps each to an HTTP status code.

To add a new exception:
1. Create a subclass of AppError here
2. Add the mapping in EXCEPTION_STATUS_MAP
3. That's it — the handler does the rest
"""

from fastapi import Request
from fastapi.responses import JSONResponse


# --- Base ---

class AppError(Exception):
    """Base for all domain errors. Never raise this directly."""
    def __init__(self, detail: str):
        self.detail = detail


# --- Concrete errors ---

class NotFoundError(AppError):
    """Entity not found. Maps to 404."""
    pass


class ConflictError(AppError):
    """Duplicate or conflicting state. Maps to 409."""
    pass


class AuthenticationError(AppError):
    """Invalid credentials or missing auth. Maps to 401."""
    pass


class AuthorizationError(AppError):
    """Authenticated but not permitted. Maps to 403."""
    pass


class ValidationError(AppError):
    """Business rule violated (not schema validation). Maps to 422."""
    pass


# --- Mapping: domain error → HTTP status ---

EXCEPTION_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: 404,
    ConflictError: 409,
    AuthenticationError: 401,
    AuthorizationError: 403,
    ValidationError: 422,
}


# --- Handler (registered in main.py) ---

async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.detail},
    )
```

### 4.3 Backend: SQLAlchemy Model — `apps/backend/app/models/item.py`

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
```

### 4.4 Backend: Pydantic Schemas — `apps/backend/app/schemas/item.py`

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    is_completed: bool | None = None


class ItemResponse(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_completed: bool
    owner_id: int
    created_at: datetime
    updated_at: datetime | None = None
```

### 4.5 Backend: Repository — `apps/backend/app/repositories/item.py`

> **v2 CHANGE**: Repositories NEVER call `session.commit()`. They use `session.flush()` when they need the DB to assign an ID. Commit/rollback happens in the session dependency (see deps.py). This allows services to compose multiple repo calls in a single transaction.

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


class ItemRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self, owner_id: int, skip: int = 0, limit: int = 100
    ) -> list[Item]:
        result = await self.session.execute(
            select(Item)
            .where(Item.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, item_id: int, owner_id: int) -> Item | None:
        result = await self.session.execute(
            select(Item).where(Item.id == item_id, Item.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: ItemCreate, owner_id: int) -> Item:
        item = Item(**data.model_dump(), owner_id=owner_id)
        self.session.add(item)
        await self.session.flush()  # assigns item.id without committing
        return item

    async def update(self, item: Item, data: ItemUpdate) -> Item:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(item, field, value)
        await self.session.flush()
        return item

    async def delete(self, item: Item) -> None:
        await self.session.delete(item)
        await self.session.flush()
```

### 4.6 Backend: Service — `apps/backend/app/services/item.py`

> **v2 CHANGE**: Services raise domain exceptions (`NotFoundError`), NOT `HTTPException`. They have zero FastAPI imports. This makes services testable without HTTP and reusable outside of web context.

```python
from app.exceptions import NotFoundError
from app.repositories.item import ItemRepository
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse


class ItemService:
    def __init__(self, repository: ItemRepository):
        self.repository = repository

    async def list_items(
        self, owner_id: int, skip: int = 0, limit: int = 100
    ) -> list[ItemResponse]:
        items = await self.repository.get_all(
            owner_id=owner_id, skip=skip, limit=limit
        )
        return [ItemResponse.model_validate(item) for item in items]

    async def get_item(self, item_id: int, owner_id: int) -> ItemResponse:
        item = await self.repository.get_by_id(item_id, owner_id=owner_id)
        if not item:
            raise NotFoundError(f"Item {item_id} not found")
        return ItemResponse.model_validate(item)

    async def create_item(
        self, data: ItemCreate, owner_id: int
    ) -> ItemResponse:
        item = await self.repository.create(data, owner_id=owner_id)
        return ItemResponse.model_validate(item)

    async def update_item(
        self, item_id: int, data: ItemUpdate, owner_id: int
    ) -> ItemResponse:
        item = await self.repository.get_by_id(item_id, owner_id=owner_id)
        if not item:
            raise NotFoundError(f"Item {item_id} not found")
        updated = await self.repository.update(item, data)
        return ItemResponse.model_validate(updated)

    async def delete_item(self, item_id: int, owner_id: int) -> None:
        item = await self.repository.get_by_id(item_id, owner_id=owner_id)
        if not item:
            raise NotFoundError(f"Item {item_id} not found")
        await self.repository.delete(item)
```

### 4.7 Backend: Dependencies — `apps/backend/app/api/deps.py`

> **v2 CHANGE**: The session dependency now owns the transaction boundary — commit on success, rollback on exception. This replaces per-repository commits and enables atomic multi-repo operations within a single request. Cross-slice wiring is also demonstrated here.

```python
from typing import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.auth import decode_access_token
from app.exceptions import AuthenticationError
from app.models.user import User
from app.repositories.item import ItemRepository
from app.repositories.user import UserRepository
from app.services.item import ItemService
from app.services.auth import AuthService


# --- Session (transaction boundary) ---

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# --- Auth ---

async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise AuthenticationError("Not authenticated")
    payload = decode_access_token(token)
    if not payload:
        raise AuthenticationError("Invalid or expired token")
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(payload["sub"])
    if not user or not user.is_active:
        raise AuthenticationError("User not found or inactive")
    return user


# --- Items ---

def get_item_repository(
    session: AsyncSession = Depends(get_session),
) -> ItemRepository:
    return ItemRepository(session)


def get_item_service(
    repository: ItemRepository = Depends(get_item_repository),
) -> ItemService:
    return ItemService(repository)


# --- Auth service ---

def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> AuthService:
    return AuthService(user_repo)


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
```

### 4.8 Backend: Router — `apps/backend/app/api/items.py`

> **v2 CHANGE**: Routers are the thinnest possible layer. They receive the service and current user via Depends, delegate, and return. No try/except — the global exception handler catches domain errors.

```python
from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, get_item_service
from app.models.user import User
from app.schemas.item import ItemCreate, ItemUpdate, ItemResponse
from app.services.item import ItemService

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("/", response_model=list[ItemResponse])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user),
):
    return await service.list_items(
        owner_id=current_user.id, skip=skip, limit=limit
    )


@router.post(
    "/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED
)
async def create_item(
    data: ItemCreate,
    service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user),
):
    return await service.create_item(data, owner_id=current_user.id)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user),
):
    return await service.get_item(item_id, owner_id=current_user.id)


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    data: ItemUpdate,
    service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user),
):
    return await service.update_item(
        item_id, data, owner_id=current_user.id
    )


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    service: ItemService = Depends(get_item_service),
    current_user: User = Depends(get_current_user),
):
    await service.delete_item(item_id, owner_id=current_user.id)
```

### 4.9 Backend: Database — `apps/backend/app/database.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass
```

### 4.10 Backend: Config — `apps/backend/app/config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/app"
    app_name: str = "{{ project_slug }}"
    debug: bool = True

    # Auth
    secret_key: str = "CHANGE-ME-IN-PRODUCTION"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # Admin
    admin_email: str = "admin@example.com"
    admin_password: str = "admin"

    model_config = {"env_file": ".env"}


settings = Settings()
```

### 4.11 Backend: Structured Logging — `apps/backend/app/logging.py`

```python
import logging
import sys

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )
```

### 4.12 Backend: Main — `apps/backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin import setup_admin
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.items import router as items_router
from app.config import settings
from app.exceptions import AppError, app_exception_handler
from app.logging import setup_logging

setup_logging()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the domain exception handler
app.add_exception_handler(AppError, app_exception_handler)

# Routers
app.include_router(auth_router)
app.include_router(items_router)
app.include_router(health_router)

# Admin panel (available at /admin)
setup_admin(app)
```

### 4.13 Backend: pyproject.toml — `apps/backend/pyproject.toml`

```toml
[project]
name = "{{ project_slug }}-backend"
version = "0.1.0"
requires-python = ">={{ python_version }}"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.30",
    "alembic>=1.14",
    "pydantic>=2.0",
    "pydantic[email]>=2.0",
    "pydantic-settings>=2.0",
    "structlog>=24.0",
    "passlib[bcrypt]>=1.7",
    "python-jose[cryptography]>=3.3",
    "python-multipart>=0.0.9",
    "sqladmin>=0.19",
    "itsdangerous>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
    "ruff>=0.8",
    "aiosqlite>=0.20",
    "schemathesis>=3.0",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### 4.14 Backend: Alembic — `apps/backend/alembic/env.py`

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base
from app.models.user import User  # noqa: F401
from app.models.item import Item  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.database_url)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

### 4.15 Backend: First Migration — `apps/backend/alembic/versions/001_create_tables.py`

```python
"""create users and items tables

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_superuser", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), default=False),
        sa.Column(
            "owner_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            index=True,
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("items")
    op.drop_table("users")
```

### 4.16 Backend: Tests — `apps/backend/tests/conftest.py`

```python
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.main import app
from app.api.deps import get_session

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(session):
    async def override_get_session():
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
```

### 4.17 Backend: Tests — `apps/backend/tests/test_items.py`

```python
import pytest
from httpx import AsyncClient


# Helper to create an authenticated user and return cookies
async def auth_cookies(client: AsyncClient) -> dict:
    await client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    return dict(response.cookies)


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient):
    cookies = await auth_cookies(client)
    response = await client.post(
        "/api/items/", json={"title": "Test item"}, cookies=cookies
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test item"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_list_items(client: AsyncClient):
    cookies = await auth_cookies(client)
    await client.post("/api/items/", json={"title": "Item 1"}, cookies=cookies)
    await client.post("/api/items/", json={"title": "Item 2"}, cookies=cookies)
    response = await client.get("/api/items/", cookies=cookies)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_item_not_found(client: AsyncClient):
    cookies = await auth_cookies(client)
    response = await client.get("/api/items/999", cookies=cookies)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_item(client: AsyncClient):
    cookies = await auth_cookies(client)
    create = await client.post(
        "/api/items/", json={"title": "Original"}, cookies=cookies
    )
    item_id = create.json()["id"]
    response = await client.put(
        f"/api/items/{item_id}", json={"title": "Updated"}, cookies=cookies
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient):
    cookies = await auth_cookies(client)
    create = await client.post(
        "/api/items/", json={"title": "To delete"}, cookies=cookies
    )
    item_id = create.json()["id"]
    response = await client.delete(f"/api/items/{item_id}", cookies=cookies)
    assert response.status_code == 204
    get_response = await client.get(f"/api/items/{item_id}", cookies=cookies)
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_user_isolation(client: AsyncClient):
    """Items created by user A must not be visible to user B."""
    # User A
    await client.post(
        "/api/auth/register",
        json={"email": "a@test.com", "password": "testpass123"},
    )
    resp_a = await client.post(
        "/api/auth/login",
        json={"email": "a@test.com", "password": "testpass123"},
    )
    cookies_a = dict(resp_a.cookies)
    await client.post(
        "/api/items/", json={"title": "A's item"}, cookies=cookies_a
    )

    # User B
    await client.post(
        "/api/auth/register",
        json={"email": "b@test.com", "password": "testpass123"},
    )
    resp_b = await client.post(
        "/api/auth/login",
        json={"email": "b@test.com", "password": "testpass123"},
    )
    cookies_b = dict(resp_b.cookies)

    response = await client.get("/api/items/", cookies=cookies_b)
    assert response.status_code == 200
    assert len(response.json()) == 0
```

### 4.18 Backend: Contract Tests — `apps/backend/tests/test_contract.py`

> **v2 NEW**: Validates that the running backend conforms to `openapi.yaml`. Catches schema drift that type generation alone cannot detect (e.g., a field present in the spec but missing from the Pydantic response model).

```python
"""
Contract tests: validate backend responses against openapi.yaml.

This ensures the OpenAPI spec (source of truth) and the actual API
stay in sync. Catches drift that type generation alone misses.
"""
import pytest
from httpx import AsyncClient

import yaml
from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parents[3] / "packages" / "contracts" / "openapi.yaml"


@pytest.fixture(scope="module")
def openapi_spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text())


def get_schema_fields(spec: dict, schema_name: str) -> set[str]:
    """Extract field names from an OpenAPI schema component."""
    schema = spec["components"]["schemas"][schema_name]
    return set(schema.get("properties", {}).keys())


@pytest.mark.asyncio
async def test_item_response_matches_spec(client: AsyncClient, openapi_spec: dict):
    """Verify that a created item contains all fields from the Item schema."""
    cookies = await _auth(client)
    response = await client.post(
        "/api/items/", json={"title": "Contract test"}, cookies=cookies
    )
    assert response.status_code == 201

    expected_fields = get_schema_fields(openapi_spec, "Item")
    actual_fields = set(response.json().keys())

    missing = expected_fields - actual_fields
    assert not missing, f"Fields in OpenAPI spec but missing from response: {missing}"


@pytest.mark.asyncio
async def test_user_response_matches_spec(client: AsyncClient, openapi_spec: dict):
    """Verify that /auth/me returns all fields from the User schema."""
    cookies = await _auth(client)
    response = await client.get("/api/auth/me", cookies=cookies)
    assert response.status_code == 200

    expected_fields = get_schema_fields(openapi_spec, "User")
    actual_fields = set(response.json().keys())

    missing = expected_fields - actual_fields
    assert not missing, f"Fields in OpenAPI spec but missing from response: {missing}"


async def _auth(client: AsyncClient) -> dict:
    await client.post(
        "/api/auth/register",
        json={"email": "contract@test.com", "password": "testpass123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "contract@test.com", "password": "testpass123"},
    )
    return dict(resp.cookies)
```

---

### 4.19 Frontend: API Client — `apps/frontend/src/lib/api-client.ts`

```typescript
// This file wraps the generated OpenAPI types with typed fetch functions.
// After running `just generate-client`, the types in packages/client/src/types.ts
// are the source of truth for all API shapes.
//
// IMPORTANT: When adding a new feature, add new functions here following
// the same pattern. Never use raw fetch() in components.

import type { paths } from "../../../../packages/client/src/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Item =
  paths["/api/items"]["get"]["responses"]["200"]["content"]["application/json"][number];
type ItemCreate =
  paths["/api/items"]["post"]["requestBody"]["content"]["application/json"];
type ItemUpdate =
  paths["/api/items/{item_id}"]["put"]["requestBody"]["content"]["application/json"];

export type { Item, ItemCreate, ItemUpdate };

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res
      .json()
      .catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? `API error: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const itemsApi = {
  list: (skip = 0, limit = 100) =>
    apiFetch<Item[]>(`/api/items/?skip=${skip}&limit=${limit}`),

  get: (id: number) => apiFetch<Item>(`/api/items/${id}`),

  create: (data: ItemCreate) =>
    apiFetch<Item>("/api/items/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (id: number, data: ItemUpdate) =>
    apiFetch<Item>(`/api/items/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: number) =>
    apiFetch<void>(`/api/items/${id}`, { method: "DELETE" }),
};
```

### 4.20 Frontend: TanStack Query Hooks — `apps/frontend/src/features/items/api.ts`

```typescript
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  itemsApi,
  type ItemCreate,
  type ItemUpdate,
} from "@/lib/api-client";

const ITEMS_KEY = ["items"] as const;

export function useItems() {
  return useQuery({
    queryKey: ITEMS_KEY,
    queryFn: () => itemsApi.list(),
  });
}

export function useItem(id: number) {
  return useQuery({
    queryKey: [...ITEMS_KEY, id],
    queryFn: () => itemsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ItemCreate) => itemsApi.create(data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ITEMS_KEY }),
  });
}

export function useUpdateItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ItemUpdate }) =>
      itemsApi.update(id, data),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ITEMS_KEY }),
  });
}

export function useDeleteItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => itemsApi.delete(id),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ITEMS_KEY }),
  });
}
```

### 4.21 Frontend: Zod Schema — `apps/frontend/src/features/items/schema.ts`

```typescript
import { z } from "zod";

export const itemCreateSchema = z.object({
  title: z.string().min(1, "Title is required").max(255),
  description: z.string().nullable().optional(),
});

export const itemUpdateSchema = z.object({
  title: z.string().min(1).max(255).optional(),
  description: z.string().nullable().optional(),
  is_completed: z.boolean().optional(),
});

export type ItemCreateForm = z.infer<typeof itemCreateSchema>;
export type ItemUpdateForm = z.infer<typeof itemUpdateSchema>;
```

### 4.22 Frontend: ItemForm Component — `apps/frontend/src/features/items/ItemForm.tsx`

```tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { itemCreateSchema, type ItemCreateForm } from "./schema";
import { useCreateItem } from "./api";

export function ItemForm() {
  const createItem = useCreateItem();

  const form = useForm<ItemCreateForm>({
    resolver: zodResolver(itemCreateSchema),
    defaultValues: { title: "", description: "" },
  });

  const onSubmit = (data: ItemCreateForm) => {
    createItem.mutate(data, {
      onSuccess: () => form.reset(),
    });
  };

  return (
    <div className="space-y-4 rounded-lg border p-4">
      <h2 className="text-lg font-semibold">New Item</h2>
      <div className="space-y-3">
        <div>
          <input
            {...form.register("title")}
            placeholder="Item title"
            className="w-full rounded border px-3 py-2"
          />
          {form.formState.errors.title && (
            <p className="mt-1 text-sm text-red-500">
              {form.formState.errors.title.message}
            </p>
          )}
        </div>
        <div>
          <textarea
            {...form.register("description")}
            placeholder="Description (optional)"
            className="w-full rounded border px-3 py-2"
            rows={3}
          />
        </div>
        <button
          type="button"
          onClick={form.handleSubmit(onSubmit)}
          disabled={createItem.isPending}
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {createItem.isPending ? "Creating..." : "Create Item"}
        </button>
      </div>
    </div>
  );
}
```

### 4.23 Frontend: ItemList Component — `apps/frontend/src/features/items/ItemList.tsx`

```tsx
"use client";

import { useItems, useDeleteItem, useUpdateItem } from "./api";

export function ItemList() {
  const { data: items, isLoading, error } = useItems();
  const deleteItem = useDeleteItem();
  const updateItem = useUpdateItem();

  if (isLoading)
    return <div className="py-4 text-gray-500">Loading...</div>;
  if (error)
    return (
      <div className="py-4 text-red-500">Error: {error.message}</div>
    );
  if (!items?.length)
    return <div className="py-4 text-gray-500">No items yet.</div>;

  return (
    <ul className="space-y-2">
      {items.map((item) => (
        <li
          key={item.id}
          className="flex items-center justify-between rounded border p-3"
        >
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={item.is_completed}
              onChange={() =>
                updateItem.mutate({
                  id: item.id,
                  data: { is_completed: !item.is_completed },
                })
              }
              className="h-4 w-4"
            />
            <span
              className={
                item.is_completed ? "line-through text-gray-400" : ""
              }
            >
              {item.title}
            </span>
          </div>
          <button
            type="button"
            onClick={() => deleteItem.mutate(item.id)}
            className="text-sm text-red-500 hover:text-red-700"
          >
            Delete
          </button>
        </li>
      ))}
    </ul>
  );
}
```

### 4.24 Frontend: Zustand Store — `apps/frontend/src/lib/store.ts`

```typescript
import { create } from "zustand";

interface AppState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () =>
    set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
}));
```

### 4.25 Frontend: Providers — `apps/frontend/src/app/providers.tsx`

```tsx
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
```

### 4.26 Frontend: Root Layout — `apps/frontend/src/app/layout.tsx`

```tsx
import type { Metadata } from "next";
import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "{{ project_name }}",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

### 4.27 Frontend: Home Page — `apps/frontend/src/app/page.tsx`

```tsx
import { ItemList } from "@/features/items/ItemList";
import { ItemForm } from "@/features/items/ItemForm";

export default function Home() {
  return (
    <main className="mx-auto max-w-2xl p-8">
      <h1 className="mb-8 text-2xl font-bold">{{ project_name }}</h1>
      <ItemForm />
      <div className="mt-8">
        <ItemList />
      </div>
    </main>
  );
}
```

---

## 5. Infrastructure & Config Files

### 5.1 `justfile` (root)

```makefile
set shell := ["bash", "-cu"]

# Development
dev:
    docker compose up -d db
    cd apps/backend && uvicorn app.main:app --reload --port 8000 &
    cd apps/frontend && pnpm dev

# Build
build:
    cd apps/backend && echo "Backend: no build step"
    cd apps/frontend && pnpm build

# Lint
lint:
    cd apps/backend && ruff check . && ruff format --check .
    cd apps/frontend && pnpm lint

# Format
format:
    cd apps/backend && ruff format .
    cd apps/frontend && pnpm lint --fix

# Test
test:
    cd apps/backend && pytest
    cd apps/frontend && pnpm test

# Generate OpenAPI client types
generate-client:
    cd packages/client && pnpm generate

# Database
db-migrate message:
    cd apps/backend && alembic revision --autogenerate -m "{{message}}"

db-upgrade:
    cd apps/backend && alembic upgrade head

db-downgrade:
    cd apps/backend && alembic downgrade -1

# Seed database with admin user and sample data
seed:
    cd apps/backend && python -m app.seed

# Reset everything
reset:
    docker compose down -v
    docker compose up -d db
    sleep 2
    just db-upgrade
```

### 5.2 `docker-compose.yml`

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

> **Note**: Backend and frontend run locally during development (via `just dev`), NOT in containers. Docker is only for infrastructure (database). This avoids volume mount issues, hot-reload complexity, and keeps the development loop fast.

### 5.3 `.env.example`

```env
DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/app
NEXT_PUBLIC_API_URL=http://localhost:8000
SECRET_KEY=CHANGE-ME-IN-PRODUCTION
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin
```

### 5.4 `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
        files: ^apps/backend/
      - id: ruff-format
        files: ^apps/backend/

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
```

### 5.5 `packages/client/package.json`

```json
{
  "name": "{{ project_slug }}-client",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "generate": "openapi-typescript ../contracts/openapi.yaml -o ./src/types.ts"
  },
  "devDependencies": {
    "openapi-typescript": "^7.0.0",
    "typescript": "^5.0.0"
  }
}
```

### 5.6 Frontend `package.json` — `apps/frontend/package.json`

```json
{
  "name": "{{ project_slug }}-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "lint": "next lint",
    "test": "vitest"
  },
  "dependencies": {
    "next": "^14",
    "react": "^18",
    "react-dom": "^18",
    "@tanstack/react-query": "^5",
    "react-hook-form": "^7",
    "@hookform/resolvers": "^3",
    "zod": "^3",
    "zustand": "^4",
    "clsx": "^2",
    "tailwind-merge": "^2"
  },
  "devDependencies": {
    "typescript": "^5",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "tailwindcss": "^3",
    "postcss": "^8",
    "autoprefixer": "^10",
    "vitest": "^2",
    "@testing-library/react": "^16",
    "@vitejs/plugin-react": "^4"
  }
}
```

---

## 6. Per-App Agent Instructions

### 6.1 `apps/backend/AGENTS.md`

Contains backend-specific layer rules (Router, Service, Repository, Model, Schema), testing patterns, error handling conventions, database conventions, and structured logging guidelines.

Key rules:

- **Import boundaries (STRICT)**:
  - Routers: may import from `schemas`, `services`, `api.deps`. NEVER import `models`, `repositories`, or SQLAlchemy
  - Services: may import from `schemas`, `repositories`, `exceptions`. NEVER import `fastapi`, `sqlalchemy`, or `api.*`
  - Repositories: may import from `models`, `schemas`, SQLAlchemy. NEVER import `services`, `api.*`, or `exceptions`
- **Error handling**: Services raise domain exceptions from `app.exceptions`. Repositories return `None` on not-found, never raise. Routers never catch exceptions (the global handler does)
- **Transactions**: Repositories never call `commit()`. The session dependency in `deps.py` owns the transaction boundary
- **structlog usage**: `logger.info("event_name", key=value)`, never f-strings in logs
- **Database conventions**: plural snake_case tables, `String(n)` with explicit length, always `timezone=True` on DateTime
- **Authentication**: JWT in httpOnly cookies, `get_current_user` dependency, `owner_id` filtering at repository level
- **Admin panel**: SQLAdmin at `/admin`, superuser-only, ModelView registration pattern
- **Seeding**: `just seed` is idempotent, extend `app/seed.py` for new features

### 6.2 `apps/frontend/AGENTS.md`

Contains frontend-specific rules for data fetching, types, components, forms, styling, Zustand usage, and authentication.

Key rules:

- Zustand: only for client-side UI state, never server data. Always use selector pattern
- Components in `components/ui/` never import from `features/` or `lib/api-client.ts`
- File naming conventions: PascalCase for components, camelCase for hooks/utilities
- Authentication: `useCurrentUser` hook, protected page pattern, never store tokens in localStorage

---

## 7. AGENTS.md (Root)

```markdown
# Agent Instructions

This project is an AI-agent-optimized monorepo. Follow these rules strictly.

## Architecture

- Monorepo: pnpm workspaces
- Backend: FastAPI + SQLAlchemy 2.0 (async) + Alembic
- Frontend: Next.js + TypeScript + Tailwind + shadcn/ui
- Contracts: OpenAPI (source of truth)
- Data fetching: TanStack Query (no raw fetch in components)
- Forms: React Hook Form + Zod
- State: Zustand (when global state is needed)

## Adding a New Feature — Checklist

Follow this exact order. Do NOT skip steps.

1. **Define the contract** in `packages/contracts/openapi.yaml`
   - Add paths and schemas
   - Follow the existing `items` pattern exactly
   - Include `security: [cookieAuth: []]` on all protected endpoints

2. **Generate client types**: `just generate-client`

3. **Create backend files** (copy from `items` and rename):
   - `app/models/<feature>.py` — SQLAlchemy model (include `owner_id` FK if user-scoped)
   - `app/schemas/<feature>.py` — Pydantic schemas (Base, Create, Update, Response)
   - `app/repositories/<feature>.py` — DB access (get_all, get_by_id, create, update, delete). NEVER call `session.commit()` — use `session.flush()` only
   - `app/services/<feature>.py` — Business logic (calls repository, raises domain exceptions from `app.exceptions`). NEVER import FastAPI
   - `app/api/<feature>.py` — Router (calls service via Depends, injects `current_user`)
   - Add dependency functions to `app/api/deps.py`
   - Register router in `app/main.py`

4. **Create migration**: `just db-migrate "add <feature> table"`

5. **Add contract test** in `tests/test_contract.py` — verify response fields match OpenAPI spec

6. **Create frontend files** (copy from `features/items/` and rename):
   - `src/features/<feature>/api.ts` — TanStack Query hooks
   - `src/features/<feature>/schema.ts` — Zod validation
   - `src/features/<feature>/<Feature>List.tsx` — List component
   - `src/features/<feature>/<Feature>Form.tsx` — Form component (RHF + Zod)

7. **Write tests**: Backend in `tests/test_<feature>.py`, frontend in `tests/<feature>.test.tsx`

## Rules

- NEVER use `fetch()` directly in React components
- NEVER define types manually that exist in the generated client
- NEVER put database logic in routers or services
- NEVER put business logic in repositories
- NEVER import FastAPI in services (raise domain exceptions instead)
- NEVER call `session.commit()` in repositories (use `flush()`)
- ALWAYS follow the existing patterns in `items/`
- ALWAYS run `just generate-client` after changing `openapi.yaml`
- ALWAYS run `just lint` before committing

## Error Handling

Services raise domain exceptions from `app/exceptions.py`:
- `NotFoundError` → 404
- `ConflictError` → 409
- `AuthenticationError` → 401
- `AuthorizationError` → 403
- `ValidationError` → 422

Routers do NOT catch exceptions. The global handler in `main.py` does the translation.

To add a new domain error: add the class in `exceptions.py` and add the mapping in `EXCEPTION_STATUS_MAP`.

## Cross-Slice Dependencies

When service A needs service B:
1. Wire it in `app/api/deps.py` — inject B as a dependency of A
2. Service A receives B via constructor, never imports B's repository
3. If it's not wired in `deps.py`, the dependency doesn't exist

## When to Introduce Domain Objects

Keep business logic in services until ANY of these triggers:
- A service method exceeds ~50 lines of conditional logic
- The same invariant is checked in 3+ places
- You need to unit-test business rules without touching persistence

Then: create `app/domain/<feature>.py` with pure Python classes (no SQLAlchemy, no Pydantic). The service instantiates domain objects, calls their methods, then persists via repository.

## Naming Conventions

- Backend files: `snake_case.py`
- Frontend files: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Database tables: `snake_case` plural (e.g., `items`)
- API routes: `/api/<resource>` plural (e.g., `/api/items`)
- Query keys: `["<resource>"]` matching route name
- Domain exceptions: `<Noun>Error` (e.g., `NotFoundError`, `ConflictError`)

## File Locations

- Models: `apps/backend/app/models/`
- Schemas: `apps/backend/app/schemas/`
- Repositories: `apps/backend/app/repositories/`
- Services: `apps/backend/app/services/`
- Routers: `apps/backend/app/api/`
- Dependencies: `apps/backend/app/api/deps.py` (single file)
- Domain exceptions: `apps/backend/app/exceptions.py` (single file)
- Frontend features: `apps/frontend/src/features/<feature>/`
- Shared UI components: `apps/frontend/src/components/ui/`
```

## 8. CLAUDE.md (Root)

```markdown
# CLAUDE.md

This file provides context for Claude Code when working in this repository.

## Project Overview

AI-agent-optimized full-stack monorepo with contracts-first architecture.

## Key Commands

- `just dev` — Start database + backend + frontend
- `just test` — Run all tests
- `just lint` — Lint all code
- `just format` — Format all code
- `just generate-client` — Regenerate TypeScript types from OpenAPI spec
- `just db-migrate "message"` — Create a new Alembic migration
- `just db-upgrade` — Apply pending migrations
- `just seed` — Seed database with admin user and sample data
- `just reset` — Reset database and reapply migrations

## Architecture Rules

Read AGENTS.md for full rules. Key points:
- OpenAPI spec is the source of truth
- Backend: Router → Service → Repository (strict layers)
- Services raise domain exceptions (NotFoundError, ConflictError, etc.) — NEVER HTTPException
- Repositories NEVER call session.commit() — the session dependency handles transactions
- Auth: JWT tokens in httpOnly cookies, `get_current_user` dependency for protected endpoints
- Frontend: Components → Hooks (features/*/api.ts) → API Client (lib/api-client.ts)
- Never use fetch() in components
- Never define duplicate types
- Always follow the `items` reference feature pattern
- Admin panel at `/admin` (superuser only, via SQLAdmin)

## When Adding a New Feature

Follow the checklist in AGENTS.md exactly. Copy the `items` feature as template.

## Error Handling Quick Reference

| Domain Exception     | HTTP Status | When to use                          |
|---------------------|-------------|--------------------------------------|
| NotFoundError       | 404         | Entity not found                     |
| ConflictError       | 409         | Duplicate email, conflicting state   |
| AuthenticationError | 401         | Bad credentials, missing token       |
| AuthorizationError  | 403         | Authenticated but not permitted      |
| ValidationError     | 422         | Business rule violated               |

Add new exceptions in `app/exceptions.py` + mapping in `EXCEPTION_STATUS_MAP`.

## Tech Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, structlog
- Auth: passlib (bcrypt), python-jose (JWT), httpOnly cookies
- Admin: SQLAdmin at `/admin`
- Frontend: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Hook Form, Zod, Zustand
- Infra: PostgreSQL 16 (Docker), pnpm workspaces, GitHub Actions CI
- Tools: Ruff (lint/format), pytest, Vitest, pre-commit
```

## 9. ARCHITECTURE.md

```markdown
# Architecture

## System Map

```
┌──────────────────────────────────────────────────────┐
│                      Monorepo                         │
│                                                       │
│  packages/                                            │
│    contracts/    ← OpenAPI spec (source of truth)     │
│    client/       ← Generated TypeScript types         │
│                                                       │
│  apps/                                                │
│    backend/      ← FastAPI (Python)                   │
│    frontend/     ← Next.js (TypeScript)               │
└──────────────────────────────────────────────────────┘
```

## Data Flow

```
openapi.yaml
    ↓ (just generate-client)
packages/client/src/types.ts
    ↓ (imported by)
apps/frontend/src/lib/api-client.ts
    ↓ (used by)
apps/frontend/src/features/*/api.ts  ← TanStack Query hooks
    ↓ (used by)
apps/frontend/src/features/*/Component.tsx
```

## Backend Layers

```
Request → Router (api/) → Service (services/) → Repository (repositories/) → Database
               │                  │                       │
          Depends(auth)    Domain exceptions          flush() only
          HTTP codes       from exceptions.py        (no commit)
               │                  │                       │
          schemas/           app.exceptions           models/
       (Pydantic)         (NotFoundError, etc.)    (SQLAlchemy)
```

Each layer has ONE responsibility:
- **Router**: HTTP concerns (status codes, request parsing, response serialization). Injects auth
- **Service**: Business logic (validation rules, orchestration). Raises domain exceptions. Zero framework imports
- **Repository**: Data access (queries, CRUD). Uses flush(), never commit(). Returns None on not-found

## Transaction Boundary

```
get_session() dependency:
  session = new AsyncSession
  try:
      yield session        ← router/service/repo all use this session
      await session.commit()   ← success: commit everything
  except:
      await session.rollback() ← failure: rollback everything
      raise
```

This means a service can call multiple repositories and all operations are atomic.

## Error Flow

```
Repository returns None
    ↓
Service raises NotFoundError("Item 42 not found")
    ↓
Global handler in main.py catches AppError
    ↓
EXCEPTION_STATUS_MAP[NotFoundError] → 404
    ↓
JSONResponse(status_code=404, content={"detail": "Item 42 not found"})
```

## Cross-Slice Dependencies

```
deps.py:

def get_notification_service(
    notification_repo = Depends(get_notification_repository),
    user_service = Depends(get_user_service),        ← cross-slice
) -> NotificationService:
    return NotificationService(notification_repo, user_service)
```

Rule: if it's not wired in deps.py, the dependency doesn't exist.

## Frontend Organization

```
src/
  app/           ← Next.js pages and layouts
  lib/           ← Shared utilities (api-client, store, cn helper)
  features/      ← Feature modules (self-contained)
    items/
      api.ts     ← TanStack Query hooks (data layer)
      schema.ts  ← Zod validation (form validation)
      ItemList.tsx
      ItemForm.tsx
  components/
    ui/          ← shadcn/ui primitives (buttons, inputs, etc.)
```
```

---

## 10. GitHub Actions CI — `.github/workflows/ci.yml`

Three jobs run on push/PR to `main`:

- **backend**: Lint (Ruff), test (pytest — including contract tests) against a PostgreSQL 16 service container
- **frontend**: Lint, test (Vitest), build
- **contracts**: Regenerate TypeScript types and fail if uncommitted changes exist (catches spec/type drift)

---

## 11. Instructions for the Code Agent

When you receive this document in Claude Code, execute the following:

1. **Create the Copier template repository** with the directory structure from Section 2
2. **Create `copier.yml`** with the variables from Section 1
3. **Generate every file** listed in Sections 4-8, using the exact code provided
4. **For files not explicitly listed** (e.g., `__init__.py`, `alembic.ini`, `tailwind.config.ts`, `postcss.config.js`, `next.config.js`, `tsconfig.json`, `.gitignore`, `components.json`), generate standard minimal versions following the conventions established
5. **Ensure all Jinja2 template variables** (`{{ project_slug }}`, `{{ project_name }}`, etc.) are properly escaped for Copier
6. **Test**: After generating, run `copier copy ./template ./test-output` with test values and verify the structure is complete

### Copier-specific notes:
- Copier uses Jinja2 but with `copier.yml` for variable definitions
- Template files go inside a subdirectory (often the root, configured via `_subdirectory` in copier.yml)
- Variables in filenames use `{{ project_slug }}` syntax
- Ensure `.gitignore`, `__pycache__/`, `node_modules/` are properly templated

---

## Appendix A: v2 Changelog — What Changed and Why

This section documents every structural change from v1 to v2, with rationale. It exists so agents and reviewers can understand the *why* behind each decision.

### A.1 Domain Exceptions Replace HTTPException in Services

**v1**: Services imported `HTTPException` from FastAPI and raised it directly.
**v2**: Services raise `NotFoundError`, `ConflictError`, etc. from `app/exceptions.py`. A global handler maps them to HTTP status codes.

**Why**: v1 violated its own design principle #6 ("Services never import FastAPI"). The contradiction meant an agent reading the rules would produce different code than an agent reading the reference implementation. v2 eliminates the contradiction. Services are now framework-agnostic and testable without HTTP.

### A.2 Request-Scoped Transactions (No Commit in Repositories)

**v1**: Each repository method called `session.commit()` individually.
**v2**: Repositories use `session.flush()`. The `get_session()` dependency commits on success, rolls back on failure.

**Why**: v1 prevented atomic multi-repository operations. If a service needed to create an item AND update a counter in the same request, a failure after the first commit would leave the database in an inconsistent state. v2 makes the entire request a single transaction by default. This is critical for any feature beyond trivial CRUD.

### A.3 Contract Testing

**v1**: CI checked that generated types matched the OpenAPI spec, but nothing verified the backend actually returned the right fields.
**v2**: `test_contract.py` validates actual API responses against `openapi.yaml` schema definitions.

**Why**: The OpenAPI spec is only "source of truth" if it's enforced at runtime. Without contract tests, a developer (or agent) can add a field to the spec, forget to add it to the Pydantic response model, and the CI passes. v2 closes this gap.

### A.4 Cross-Slice Wiring Pattern Documented

**v1**: No example of service-to-service dependencies.
**v2**: `deps.py` includes a commented cross-slice example and the rule "if it's not wired in deps.py, the dependency doesn't exist."

**Why**: The first time an agent needs to create a feature that depends on another feature's service, it needs a pattern to follow. Without one, agents invent ad-hoc imports between service files — which violates the layering rules.

### A.5 Domain Object Escalation Criteria

**v1**: No guidance on when to introduce domain objects vs keeping logic in services.
**v2**: AGENTS.md defines three concrete triggers for introducing `app/domain/<feature>.py`.

**Why**: Both extremes are harmful — premature domain modeling adds complexity to simple CRUD, while keeping complex invariants in services makes them untestable. v2 gives agents a mechanical decision rule.

### A.6 User Isolation Test

**v1**: Tests did not verify that user A's items are invisible to user B.
**v2**: `test_user_isolation` explicitly verifies cross-user data leakage.

**Why**: Principle #9 ("User isolation") was stated but not tested. An agent could implement the pattern incorrectly (e.g., forgetting `owner_id` filter in a query) and all tests would pass. v2 makes the security guarantee testable.

### A.7 Complete OpenAPI Spec with Auth Endpoints

**v1**: OpenAPI spec only covered items endpoints.
**v2**: Full spec including auth (register, login, logout, me), security schemes, and all schema definitions.

**Why**: Agents need the complete contract to generate client types correctly. A partial spec forces manual type definitions on the frontend — violating principle #5.
