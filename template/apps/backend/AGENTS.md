# Backend Agent Instructions

## Layer Rules

### Routers (`app/api/`)
- ONLY handle HTTP concerns: parse request, call service, return response
- NEVER import SQLAlchemy, never access `session` directly
- ALWAYS use `Depends()` to inject the service
- ALWAYS set explicit `status_code` on mutating endpoints (201 for create, 204 for delete)
- ALWAYS use `response_model` on every endpoint

### Services (`app/services/`)
- Contain ALL business logic and validation beyond schema-level validation
- NEVER import FastAPI (no Request, Response, Depends, HTTPException import is the ONE exception)
- NEVER import SQLAlchemy models or session
- Receive and return Pydantic schemas only (input: Create/Update schemas, output: Response schemas)
- Call repository methods, never write queries

### Repositories (`app/repositories/`)
- ONLY handle database access: queries, inserts, updates, deletes
- NEVER raise HTTPException (that's the service's job)
- NEVER contain business logic or conditional branching based on business rules
- Return SQLAlchemy model instances (the service converts to Pydantic)
- Always receive `AsyncSession` via constructor injection

### Models (`app/models/`)
- One file per database table
- Always use `Mapped[]` type annotations (SQLAlchemy 2.0 style)
- Always import and register in `alembic/env.py` after creating a new model

### Schemas (`app/schemas/`)
- One file per feature with: Base, Create, Update, Response classes
- Response schemas MUST have `model_config = ConfigDict(from_attributes=True)`
- Create/Update schemas MUST NOT include `id`, `created_at`, `updated_at`
- Use `str | None` not `Optional[str]`

## Adding a new endpoint to an existing feature

1. Add the path/operation to `packages/contracts/openapi.yaml`
2. Add schema if needed in `app/schemas/<feature>.py`
3. Add repository method in `app/repositories/<feature>.py`
4. Add service method in `app/services/<feature>.py`
5. Add route in `app/api/<feature>.py`
6. Run `just generate-client`

## Adding a new feature (full CRUD)

1. Copy the `items` feature across all layers (model, schema, repository, service, router)
2. Rename every occurrence of `item`/`Item` to your new feature name
3. Register the new router in `app/main.py`
4. Add dependency functions in `app/api/deps.py`
5. Create migration: `just db-migrate "create <feature> table"`
6. Add the OpenAPI paths and schemas to `packages/contracts/openapi.yaml`
7. Run `just generate-client`
8. Write tests in `tests/test_<feature>.py` (copy from `test_items.py`)

## Testing patterns

- Use the `client` fixture from `conftest.py` for integration tests
- Test the happy path AND the 404 case for every endpoint
- Test validation errors (422) for create/update endpoints
- Each test function should be independent — don't rely on execution order

## Error handling

- Repository: return `None` when entity not found (never raise)
- Service: check for `None` from repository, raise `HTTPException(404)` with descriptive message
- Router: let exceptions propagate (FastAPI handles them)
- For custom business errors: use `AppException` from `app/exceptions.py`

## Database conventions

- Table names: plural snake_case (`items`, `user_profiles`)
- Column names: snake_case (`is_completed`, `created_at`)
- Always add `created_at` with `server_default=func.now()`
- Always add `updated_at` with `onupdate=func.now(), nullable=True`
- Always add `index=True` on primary keys and foreign keys
- Use `String(n)` with explicit length, never unbounded `String()`

## Logging

- Use `structlog.get_logger()` in services and repositories
- Log at INFO level for successful operations: `logger.info("item_created", item_id=item.id)`
- Log at WARNING level for expected failures: `logger.warning("item_not_found", item_id=item_id)`
- Log at ERROR level for unexpected failures
- ALWAYS use structured key-value pairs, never f-strings in log messages
- NEVER log in routers — the service layer handles logging
