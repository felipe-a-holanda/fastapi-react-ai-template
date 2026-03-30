# System Architecture

> The agent reads this to understand the system structure before working on any change.

## Overview

AI-agent-optimized full-stack monorepo with contracts-first architecture. The system scaffolds CRUD-heavy web applications where AI coding agents are the primary developers. Every architectural decision minimizes ambiguity and maximizes agent reliability.

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

## Backend Module Map

```
apps/backend/
  app/
    main.py                ← FastAPI app, middleware, router registration
    config.py              ← Pydantic Settings (env-driven)
    database.py            ← SQLAlchemy async engine + session maker
    exceptions.py          ← AppException + handler
    logging.py             ← structlog setup
    auth.py                ← JWT + password hashing
    admin.py               ← SQLAdmin panel setup
    seed.py                ← Database seeding (idempotent)
    models/                ← SQLAlchemy ORM models
    schemas/               ← Pydantic request/response schemas
    repositories/          ← Database access layer (queries only)
    services/              ← Business logic layer
    api/                   ← Routers (HTTP concerns only)
      deps.py              ← FastAPI Depends wiring
  tests/                   ← pytest + pytest-asyncio tests
  alembic/                 ← Database migrations
```

## Frontend Module Map

```
apps/frontend/
  src/
    app/                   ← Next.js pages and layouts
      layout.tsx           ← Root layout + Providers
      page.tsx             ← Home page
      providers.tsx        ← QueryClientProvider
    lib/
      api-client.ts        ← Typed fetch wrapper (uses generated types)
      store.ts             ← Zustand store (UI state only)
      utils.ts             ← cn() helper for shadcn
    features/              ← Feature modules (self-contained)
      auth/                ← Auth hooks, schemas, LoginForm, RegisterForm
      items/               ← Items hooks, schemas, ItemList, ItemForm
    components/
      ui/                  ← shadcn/ui primitives
  tests/                   ← Vitest + Testing Library tests
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
- **Service**: Business logic (validation rules, orchestration, raises HTTPException)
- **Repository**: Data access (SQLAlchemy queries, CRUD operations, returns None on not-found)

## Key Patterns

- **Contracts-first**: OpenAPI → generated types → backend implements → frontend consumes
- **Repository pattern**: all database access through repository classes
- **Service layer**: business logic lives here, never in routers or repositories
- **FastAPI Depends**: explicit dependency injection (session → repository → service)
- **Reference feature**: `items` is the canonical CRUD example — copy it for new features
- **Feature-based frontend**: all code for a feature lives in `src/features/<name>/`
- **Cookie-based JWT auth**: httpOnly cookies, `get_current_user` dependency, owner_id filtering

## External Dependencies

| Service      | Purpose           | Env Variable        |
|-------------|-------------------|---------------------|
| PostgreSQL  | Primary database  | DATABASE_URL        |

## Key Commands

| Command                        | Purpose                                    |
|-------------------------------|--------------------------------------------|
| `just dev`                    | Start database + backend + frontend         |
| `just test`                   | Run all tests (backend pytest + frontend Vitest) |
| `just lint`                   | Lint all code (Ruff + Next.js lint)         |
| `just generate-client`        | Regenerate TypeScript types from OpenAPI    |
| `just db-migrate "message"`   | Create a new Alembic migration              |
| `just db-upgrade`             | Apply pending migrations                    |
| `just seed`                   | Seed database with admin user + sample data |
| `just reset`                  | Reset database and reapply migrations       |
