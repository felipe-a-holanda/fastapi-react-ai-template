# Agent Instructions

This project is an AI-agent-optimized monorepo. Follow these rules strictly.

## FORGE Protocol (for multi-task features)

For features that span multiple files or require planning, use the **FORGE protocol**:

```bash
# 1. Create a new change
just forge-new add-notifications --description "Email notifications for item comments"

# 2. Fill out spec.md and tasks.md (or ask agent to help)

# 3. Update state.json phase to "EXECUTE" when ready

# 4. Run autonomous execution
just forge                    # Run until done
just forge --max-iterations 5 # Limit to 5 tasks
just forge-status             # Dry-run preview
```

See `forge/FORGE.md` for the full protocol and `forge/AGENTS.md` for the operating manual.

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
   - `app/repositories/<feature>.py` — DB access (get_all, get_by_id, create, update, delete). NEVER call `session.commit()` — use `session.flush()` only
   - `app/services/<feature>.py` — Business logic (calls repository, raises domain exceptions from `app.exceptions`). NEVER import FastAPI
   - `app/api/<feature>.py` — Router (calls service via Depends)
   - Register router in `app/main.py`

4. **Create migration**: `just db-migrate "add <feature> table"`

5. **Add backend dependency wiring** in `app/api/deps.py` and **add contract test** in `tests/test_contract.py`

6. **Create frontend files** (copy from `features/items/` and rename):
   - `src/features/<feature>/api.ts` — TanStack Query hooks
   - `src/features/<feature>/schema.ts` — Zod validation
   - `src/features/<feature>/<Feature>List.tsx` — List component
   - `src/features/<feature>/<Feature>Form.tsx` — Form component (RHF + Zod)

7. **Write tests**: Backend in `tests/test_<feature>.py`, frontend in `tests/<feature>.test.tsx`

## Rules

- NEVER use `fetch()` directly in React components
- NEVER define types manually that exist in the generated client
  - **Exception**: `features/auth/api.ts` defines `User`, `LoginData`, `RegisterData` inline — auth is a bootstrap module needed before `just generate-client` can run. Do not remove these; do not replicate this pattern elsewhere.
- NEVER put database logic in routers or services
- NEVER put business logic in repositories
- NEVER import FastAPI in services (raise domain exceptions instead)
- NEVER call `session.commit()` in repositories (use `flush()`)
- ALWAYS follow the existing patterns in `items/`
- ALWAYS run `just generate-client` after changing `openapi.yaml`
- ALWAYS run `just lint` before committing

## Error Handling

Services raise domain exceptions from `app/exceptions.py`:
- `NotFoundError` -> 404
- `ConflictError` -> 409
- `AuthenticationError` -> 401
- `AuthorizationError` -> 403
- `ValidationError` -> 422

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

## File Locations

- Models: `apps/backend/app/models/`
- Schemas: `apps/backend/app/schemas/`
- Repositories: `apps/backend/app/repositories/`
- Services: `apps/backend/app/services/`
- Routers: `apps/backend/app/api/`
- Frontend features: `apps/frontend/src/features/<feature>/`
- Shared UI components: `apps/frontend/src/components/ui/`
