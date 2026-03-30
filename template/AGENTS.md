# Agent Instructions

This project is an AI-agent-optimized monorepo. Follow these rules strictly.

## FORGE Protocol (for multi-task features)

For features that span multiple files or require planning, use the **FORGE protocol**:
1. Create a change directory: `forge/changes/{change-id}/`
2. Write `spec.md` (requirements), `tasks.md` (atomic tasks), `decisions.md`, `state.json`
3. Present to human for review, then execute one task at a time
4. See `forge/FORGE.md` for the full protocol and `forge/CLAUDE.md` for the operating manual
5. Run with `just forge` (autonomous) or `just forge-status` (dry-run)

For quick single-file fixes, follow the checklist below directly.

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
