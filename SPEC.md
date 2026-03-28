# AI-Agent-Optimized Monorepo — Copier Template Specification

> **Purpose**: This document is a complete specification for generating a Copier template that scaffolds an AI-agent-optimized full-stack monorepo. Paste this into Claude Code and instruct it to generate the template file by file.

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
├── ARCHITECTURE.md
├── AGENTS.md
├── CLAUDE.md
│
├── packages/
│   └── contracts/
│       ├── openapi.yaml           # Source of truth
│       └── package.json
│
├── apps/
│   ├── backend/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   ├── alembic.ini
│   │   ├── alembic/
│   │   │   ├── env.py
│   │   │   └── versions/
│   │   │       └── 001_create_items_table.py
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── exceptions.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   └── item.py         # SQLAlchemy model
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   └── item.py         # Pydantic schemas
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py
│   │   │   │   └── item.py         # DB access layer
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   └── item.py         # Business logic
│   │   │   └── api/
│   │   │       ├── __init__.py
│   │   │       ├── deps.py         # FastAPI dependencies
│   │   │       └── items.py        # Route handlers
│   │   └── tests/
│   │       ├── conftest.py
│   │       └── test_items.py
│   │
│   └── frontend/
│       ├── Dockerfile
│       ├── package.json
│       ├── tsconfig.json
│       ├── next.config.js
│       ├── tailwind.config.ts
│       ├── postcss.config.js
│       ├── components.json          # shadcn/ui config
│       ├── src/
│       │   ├── app/
│       │   │   ├── layout.tsx
│       │   │   ├── page.tsx
│       │   │   └── providers.tsx    # QueryClientProvider
│       │   ├── lib/
│       │   │   ├── api-client.ts    # Generated types + fetch wrapper
│       │   │   └── utils.ts         # cn() helper for shadcn
│       │   ├── features/
│       │   │   └── items/
│       │   │       ├── api.ts       # TanStack Query hooks
│       │   │       ├── schema.ts    # Zod validation (mirrors backend)
│       │   │       ├── ItemList.tsx
│       │   │       └── ItemForm.tsx # RHF + Zod
│       │   └── components/
│       │       └── ui/              # shadcn/ui components (copied in)
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
6. **Strict layering in backend**: Router → Service → Repository. Routers never touch the database. Services never import FastAPI. Repositories never contain business logic
7. **One file = one concern**. No file should mix model definitions, business logic, and route handling

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
      summary: List all items
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

components:
  schemas:
    Item:
      type: object
      required: [id, title, created_at]
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

### 4.2 Backend: SQLAlchemy Model — `apps/backend/app/models/item.py`

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )
```

### 4.3 Backend: Pydantic Schemas — `apps/backend/app/schemas/item.py`

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
    created_at: datetime
    updated_at: datetime | None = None
```

### 4.4 Backend: Repository — `apps/backend/app/repositories/item.py`

```python
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
```

### 4.5 Backend: Service — `apps/backend/app/services/item.py`

```python
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
```

### 4.6 Backend: Dependencies — `apps/backend/app/api/deps.py`

```python
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
```

### 4.7 Backend: Router — `apps/backend/app/api/items.py`

```python
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
```

### 4.8 Backend: Database — `apps/backend/app/database.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
```

### 4.9 Backend: Config — `apps/backend/app/config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/app"
    app_name: str = "{{ project_slug }}"
    debug: bool = True

    model_config = {"env_file": ".env"}


settings = Settings()
```

### 4.10 Backend: Exception Handling — `apps/backend/app/exceptions.py`

```python
from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )
```

### 4.11 Backend: Main — `apps/backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.items import router as items_router
from app.config import settings
from app.exceptions import AppException, app_exception_handler

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.include_router(items_router)
```

### 4.12 Backend: pyproject.toml — `apps/backend/pyproject.toml`

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
    "pydantic-settings>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "httpx>=0.27",
    "ruff>=0.8",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

### 4.13 Backend: Alembic — `apps/backend/alembic/env.py`

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.database import Base
from app.models.item import Item  # noqa: F401 — ensure model is registered

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

### 4.14 Backend: First Migration — `apps/backend/alembic/versions/001_create_items_table.py`

```python
"""create items table

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
        "items",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("items")
```

### 4.15 Backend: Tests — `apps/backend/tests/conftest.py`

```python
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.main import app
from app.api.deps import get_session

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


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
        yield session

    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
```

### 4.16 Backend: Tests — `apps/backend/tests/test_items.py`

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient):
    response = await client.post("/api/items/", json={"title": "Test item"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test item"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_list_items(client: AsyncClient):
    await client.post("/api/items/", json={"title": "Item 1"})
    await client.post("/api/items/", json={"title": "Item 2"})
    response = await client.get("/api/items/")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_item_not_found(client: AsyncClient):
    response = await client.get("/api/items/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_item(client: AsyncClient):
    create = await client.post("/api/items/", json={"title": "Original"})
    item_id = create.json()["id"]
    response = await client.put(
        f"/api/items/{item_id}", json={"title": "Updated"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"


@pytest.mark.asyncio
async def test_delete_item(client: AsyncClient):
    create = await client.post("/api/items/", json={"title": "To delete"})
    item_id = create.json()["id"]
    response = await client.delete(f"/api/items/{item_id}")
    assert response.status_code == 204
    get_response = await client.get(f"/api/items/{item_id}")
    assert get_response.status_code == 404
```

---

### 4.17 Frontend: API Client — `apps/frontend/src/lib/api-client.ts`

```typescript
// This file wraps the generated OpenAPI types with typed fetch functions.
// After running `just generate-client`, the types in packages/client/src/types.ts
// are the source of truth for all API shapes.
//
// IMPORTANT: When adding a new feature, add new functions here following
// the same pattern. Never use raw fetch() in components.

import type { paths } from "../../../../packages/client/src/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Item = paths["/api/items"]["get"]["responses"]["200"]["content"]["application/json"][number];
type ItemCreate = paths["/api/items"]["post"]["requestBody"]["content"]["application/json"];
type ItemUpdate = paths["/api/items/{item_id}"]["put"]["requestBody"]["content"]["application/json"];

export type { Item, ItemCreate, ItemUpdate };

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail ?? `API error: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const itemsApi = {
  list: (skip = 0, limit = 100) =>
    apiFetch<Item[]>(`/api/items/?skip=${skip}&limit=${limit}`),

  get: (id: number) =>
    apiFetch<Item>(`/api/items/${id}`),

  create: (data: ItemCreate) =>
    apiFetch<Item>("/api/items/", { method: "POST", body: JSON.stringify(data) }),

  update: (id: number, data: ItemUpdate) =>
    apiFetch<Item>(`/api/items/${id}`, { method: "PUT", body: JSON.stringify(data) }),

  delete: (id: number) =>
    apiFetch<void>(`/api/items/${id}`, { method: "DELETE" }),
};
```

### 4.18 Frontend: TanStack Query Hooks — `apps/frontend/src/features/items/api.ts`

```typescript
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { itemsApi, type ItemCreate, type ItemUpdate } from "@/lib/api-client";

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
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ITEMS_KEY }),
  });
}

export function useUpdateItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ItemUpdate }) =>
      itemsApi.update(id, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ITEMS_KEY }),
  });
}

export function useDeleteItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => itemsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ITEMS_KEY }),
  });
}
```

### 4.19 Frontend: Zod Schema — `apps/frontend/src/features/items/schema.ts`

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

### 4.20 Frontend: ItemForm Component — `apps/frontend/src/features/items/ItemForm.tsx`

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
      {/* NOTE: Do NOT use <form> tags in artifacts/React.
          Use div + button onClick instead. */}
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

### 4.21 Frontend: ItemList Component — `apps/frontend/src/features/items/ItemList.tsx`

```tsx
"use client";

import { useItems, useDeleteItem, useUpdateItem } from "./api";

export function ItemList() {
  const { data: items, isLoading, error } = useItems();
  const deleteItem = useDeleteItem();
  const updateItem = useUpdateItem();

  if (isLoading) return <div className="py-4 text-gray-500">Loading...</div>;
  if (error) return <div className="py-4 text-red-500">Error: {error.message}</div>;
  if (!items?.length) return <div className="py-4 text-gray-500">No items yet.</div>;

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
            <span className={item.is_completed ? "line-through text-gray-400" : ""}>
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

### 4.22 Frontend: Providers — `apps/frontend/src/app/providers.tsx`

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
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}
```

### 4.23 Frontend: Root Layout — `apps/frontend/src/app/layout.tsx`

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

### 4.24 Frontend: Home Page — `apps/frontend/src/app/page.tsx`

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
    "zod": "^3"
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

## 6. AGENTS.md (Root)

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

2. **Generate client types**: `just generate-client`

3. **Create backend files** (copy from `items` and rename):
   - `app/models/<feature>.py` — SQLAlchemy model
   - `app/schemas/<feature>.py` — Pydantic schemas (Base, Create, Update, Response)
   - `app/repositories/<feature>.py` — DB access (get_all, get_by_id, create, update, delete)
   - `app/services/<feature>.py` — Business logic (calls repository, raises HTTPException)
   - `app/api/<feature>.py` — Router (calls service via Depends)
   - Register router in `app/main.py`

4. **Create migration**: `just db-migrate "add <feature> table"`

5. **Add backend dependency wiring** in `app/api/deps.py`

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
- NEVER import FastAPI in services
- ALWAYS follow the existing patterns in `items/`
- ALWAYS run `just generate-client` after changing `openapi.yaml`
- ALWAYS run `just lint` before committing

## Naming Conventions

- Backend files: `snake_case.py`
- Frontend files: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Database tables: `snake_case` plural (e.g., `items`)
- API routes: `/api/<resource>` plural (e.g., `/api/items`)
- Query keys: `["<resource>"]` matching route name

## File Locations

- Models: `apps/backend/app/models/`
- Schemas: `apps/backend/app/schemas/`
- Repositories: `apps/backend/app/repositories/`
- Services: `apps/backend/app/services/`
- Routers: `apps/backend/app/api/`
- Frontend features: `apps/frontend/src/features/<feature>/`
- Shared UI components: `apps/frontend/src/components/ui/`
```

## 7. CLAUDE.md (Root)

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
- `just reset` — Reset database and reapply migrations

## Architecture Rules

Read AGENTS.md for full rules. Key points:
- OpenAPI spec is the source of truth
- Backend: Router → Service → Repository (strict layers)
- Frontend: Components → Hooks (features/*/api.ts) → API Client (lib/api-client.ts)
- Never use fetch() in components
- Never define duplicate types
- Always follow the `items` reference feature pattern

## When Adding a New Feature

Follow the checklist in AGENTS.md exactly. Copy the `items` feature as template.

## Tech Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2
- Frontend: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Hook Form, Zod
- Infra: PostgreSQL 16 (Docker), pnpm workspaces
- Tools: Ruff (lint/format), pytest, Vitest, pre-commit
```

## 8. ARCHITECTURE.md

```markdown
# Architecture

## System Map

```
┌─────────────────────────────────────────────────┐
│                   Monorepo                       │
│                                                  │
│  packages/                                       │
│    contracts/    ← OpenAPI spec (source of truth)│
│    client/       ← Generated TypeScript types    │
│                                                  │
│  apps/                                           │
│    backend/      ← FastAPI (Python)              │
│    frontend/     ← Next.js (TypeScript)          │
└─────────────────────────────────────────────────┘
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
                                ↑                        ↑
                          Pydantic schemas          SQLAlchemy models
                          (schemas/)                (models/)
```

Each layer has ONE responsibility:
- **Router**: HTTP concerns (status codes, request parsing, response serialization)
- **Service**: Business logic (validation rules, orchestration, exceptions)
- **Repository**: Data access (queries, CRUD operations)

## Frontend Organization

```
src/
  app/           ← Next.js pages and layouts
  lib/           ← Shared utilities (api-client, cn helper)
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

## 9. Instructions for the Code Agent

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
