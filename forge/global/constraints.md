# Global Constraints

> These rules apply to ALL changes. The agent must respect them at all times.

## Technology Stack

### Backend
- Runtime: Python 3.12+
- Framework: FastAPI
- ORM: SQLAlchemy 2.0 (async)
- Migrations: Alembic
- Schemas: Pydantic v2
- Config: Pydantic Settings (env-driven)
- Logging: structlog (key-value, never f-strings in logs)
- Auth: passlib (bcrypt) + python-jose (JWT) + httpOnly cookies
- Admin: SQLAdmin at `/admin`
- Linting/Formatting: Ruff
- Testing: pytest + pytest-asyncio + httpx

### Frontend
- Runtime: Node.js 20+
- Framework: Next.js 14 (TypeScript, strict mode)
- Styling: Tailwind CSS
- Components: shadcn/ui (lives inside repo, not black-box)
- Data fetching: TanStack Query (no raw fetch in components)
- Forms: React Hook Form + Zod
- Global state: Zustand (UI state only, never server data)
- Testing: Vitest + Testing Library

### Infrastructure
- Database: PostgreSQL 16 (Docker Compose)
- Package manager: pnpm (workspaces)
- Task runner: Justfile
- Contracts: OpenAPI 3.0 (`packages/contracts/openapi.yaml`)
- Client types: Generated via openapi-typescript
- CI: GitHub Actions
- Git hooks: pre-commit (Ruff + trailing whitespace)

## Architectural Rules

### Contracts-First
- OpenAPI spec is the **single source of truth** for all API contracts
- Contracts flow one direction: `openapi.yaml → generated types → backend implements → frontend consumes`
- Never define types manually that exist in the generated client
- Always run `just generate-client` after changing `openapi.yaml`

### Backend Layering (strict)
- **Router** (api/): HTTP concerns only — status codes, request parsing, response serialization
- **Service** (services/): Business logic, orchestration, raises HTTPException
- **Repository** (repositories/): Database access only — SQLAlchemy queries, returns None on not-found
- Routers NEVER touch the database or import SQLAlchemy
- Services NEVER import FastAPI (except HTTPException)
- Repositories NEVER contain business logic or raise HTTP exceptions
- All environment variables accessed through `app/config.py` (Pydantic Settings)

### Frontend Rules
- No `fetch()` in components — all data access through TanStack Query hooks in `features/*/api.ts`
- No ad-hoc types — all request/response types from generated client
- No `any` types — use `unknown` + type narrowing
- Zustand for client-side UI state only, never for server data
- Components in `components/ui/` never import from `features/` or `lib/api-client.ts`

### Feature Structure
- Every feature follows the `items` reference pattern exactly
- Backend: model → schema → repository → service → router → deps.py wiring
- Frontend: api.ts (TanStack Query hooks) → schema.ts (Zod) → Components
- One file = one concern

### Authentication
- JWT tokens in httpOnly cookies (never localStorage)
- `get_current_user` dependency for protected endpoints
- User isolation: all user-scoped data filtered by `owner_id` at repository level
- `credentials: "include"` on all frontend fetch calls

## Performance
- No N+1 query patterns
- Async database operations only (asyncpg)
- No synchronous I/O in request handlers

## Security
- No secrets in code — use environment variables via `app/config.py`
- All user input validated at the boundary (Pydantic schemas on backend, Zod on frontend)
- SQL queries through SQLAlchemy ORM only (parameterized by default)
- Authentication tokens must have expiration
- Password hashing: bcrypt with minimum cost factor

## Naming Conventions
- Backend files: `snake_case.py`
- Frontend files: `PascalCase.tsx` for components, `camelCase.ts` for utilities
- Database tables: `snake_case` plural (e.g., `items`)
- API routes: `/api/<resource>` plural (e.g., `/api/items`)
- Query keys: `["<resource>"]` matching route name
- structlog events: `snake_case` (e.g., `item_created`, `user_login_failed`)

## Dependencies
- Prefer established libraries (active maintenance, wide adoption)
- Backend deps pinned in `pyproject.toml` with minimum versions
- Frontend deps in `package.json` with caret ranges
- No native dependencies unless absolutely necessary
