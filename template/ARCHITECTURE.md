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
