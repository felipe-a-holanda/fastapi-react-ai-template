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
               │                  │                       │
          Depends(auth)    Domain exceptions          flush() only
          HTTP codes       from exceptions.py        (no commit)
               │                  │                       │
          schemas/           app.exceptions           models/
       (Pydantic)         (NotFoundError, etc.)    (SQLAlchemy)
```

Each layer has ONE responsibility:
- **Router**: HTTP concerns (status codes, request parsing, response serialization)
- **Service**: Business logic (validation rules, orchestration, domain exceptions)
- **Repository**: Data access (queries, CRUD operations, flush only)

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
