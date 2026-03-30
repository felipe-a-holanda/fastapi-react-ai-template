# Tasks — add-auth

## Metadata
- total: 11
- completed: 0
- blocked: 0

## Task List

### task-01: Add auth paths and schemas to OpenAPI contract
- status: [ ]
- touches: packages/contracts/openapi.yaml
- depends: none
- verify: just generate-client
- notes:

Add auth endpoints to `openapi.yaml`: POST /api/auth/register, POST /api/auth/login, POST /api/auth/refresh, POST /api/auth/logout, GET /api/auth/me. Add User, UserCreate, UserResponse, LoginRequest, TokenResponse schemas. Follow the existing `items` pattern for schema naming. Run `just generate-client` to verify types generate correctly.

---

### task-02: Create User model and update migration
- status: [ ]
- touches: apps/backend/app/models/user.py, apps/backend/app/models/__init__.py, apps/backend/alembic/versions/001_create_tables.py
- depends: none
- verify: just db-upgrade
- notes:

The User model already exists in the migration (001_create_tables.py creates the `users` table). Create `app/models/user.py` with the SQLAlchemy model matching the existing migration: id, email, hashed_password, full_name, is_active, is_superuser, created_at, updated_at. Import it in `app/models/__init__.py`. Verify migration still applies cleanly.

---

### task-03: Create auth Pydantic schemas
- status: [ ]
- touches: apps/backend/app/schemas/user.py, apps/backend/app/schemas/__init__.py
- depends: none
- verify: cd apps/backend && .venv/bin/python -c "from app.schemas.user import UserCreate, UserResponse, LoginRequest, TokenResponse"
- notes:

Create `app/schemas/user.py` with Pydantic v2 schemas: UserBase (email), UserCreate (email + password + full_name), UserResponse (id, email, full_name, is_active, created_at — with `model_config = ConfigDict(from_attributes=True)`), LoginRequest (email + password), TokenResponse (access_token, token_type). Follow the pattern in `app/schemas/item.py`.

---

### task-04: Implement auth utilities (JWT + password hashing)
- status: [ ]
- touches: apps/backend/app/auth.py
- depends: none
- verify: cd apps/backend && .venv/bin/python -c "from app.auth import create_access_token, verify_password, get_password_hash"
- notes:

Implement `app/auth.py` with: `get_password_hash(password)` using passlib bcrypt, `verify_password(plain, hashed)`, `create_access_token(data, expires_delta)` using python-jose HS256 with SECRET_KEY from config, `create_refresh_token(data)` with 7-day expiry. All config values from `app/config.py` (secret_key, access_token_expire_minutes, refresh_token_expire_days, algorithm).

---

### task-05: Implement user repository
- status: [ ]
- touches: apps/backend/app/repositories/user.py, apps/backend/app/repositories/__init__.py
- depends: task-02
- verify: cd apps/backend && .venv/bin/pytest tests/test_auth.py -v -k "repository" --no-header 2>/dev/null || echo "tests not yet written, import check only" && .venv/bin/python -c "from app.repositories.user import UserRepository"
- notes:

Implement `UserRepository` following the pattern in `app/repositories/item.py`: `get_by_id(user_id)`, `get_by_email(email)`, `create(data: UserCreate, hashed_password: str)`. Repository returns None on not-found, never raises HTTP exceptions.

---

### task-06: Implement auth service
- status: [ ]
- touches: apps/backend/app/services/auth.py, apps/backend/app/services/__init__.py
- depends: task-04, task-05
- verify: cd apps/backend && .venv/bin/python -c "from app.services.auth import AuthService"
- notes:

Implement `AuthService` following the pattern in `app/services/item.py`: `register(data: UserCreate)` — check email uniqueness, hash password, create user, return UserResponse. `authenticate(email, password)` — find user, verify password, return User or raise 401. `get_current_user_from_token(token)` — decode JWT, fetch user, return User or raise 401. Service raises HTTPException for errors. Uses structlog: `logger.info("user_registered", user_id=user.id)`, `logger.warning("login_failed", email=email)`.

---

### task-07: Implement get_current_user dependency and auth deps wiring
- status: [ ]
- touches: apps/backend/app/api/deps.py
- depends: task-05, task-06
- verify: cd apps/backend && .venv/bin/python -c "from app.api.deps import get_current_user, get_auth_service"
- notes:

Add to `app/api/deps.py`: `get_user_repository(session)`, `get_auth_service(repository)` following existing Depends pattern. Add `get_current_user` dependency that extracts JWT from httpOnly cookie (or Authorization header as fallback), decodes it, fetches user from DB. Returns User model. Raises HTTPException(401) on failure.

---

### task-08: Implement auth router
- status: [ ]
- touches: apps/backend/app/api/auth.py, apps/backend/app/main.py
- depends: task-06, task-07
- verify: cd apps/backend && .venv/bin/pytest tests/test_auth.py -v --no-header 2>/dev/null || echo "tests not yet written, import check only" && .venv/bin/python -c "from app.api.auth import router"
- notes:

Implement `app/api/auth.py` with router (prefix="/api/auth", tags=["auth"]). Endpoints: POST /register (returns 201 + UserResponse), POST /login (sets httpOnly cookies, returns TokenResponse), POST /refresh (reads refresh cookie, sets new cookies), POST /logout (clears cookies), GET /me (protected, returns UserResponse). Register router in `app/main.py`. Follow the pattern in `app/api/items.py`.

---

### task-09: Add owner_id to items and protect items endpoints
- status: [ ]
- touches: apps/backend/app/models/item.py, apps/backend/app/repositories/item.py, apps/backend/app/api/items.py, apps/backend/app/api/deps.py
- depends: task-07
- verify: cd apps/backend && .venv/bin/pytest tests/test_items.py -v
- notes:

Add `owner_id` foreign key to Item model (already in migration). Update `ItemRepository` to filter by `owner_id` in all queries. Update items router to require `get_current_user` dependency and pass `current_user.id` to service/repository. Update tests to account for auth requirement.

---

### task-10: Write backend auth tests
- status: [ ]
- touches: apps/backend/tests/test_auth.py, apps/backend/tests/conftest.py
- depends: task-08
- verify: cd apps/backend && .venv/bin/pytest tests/test_auth.py -v
- notes:

Write comprehensive pytest tests: register success, register duplicate email (409), login success (check cookies set), login wrong password (401), login wrong email (401), /me with valid token, /me without token (401), refresh with valid cookie, logout clears cookies. Update `conftest.py` if needed for auth test helpers.

---

### task-11: Create frontend auth feature (hooks, forms, schemas)
- status: [ ]
- touches: apps/frontend/src/features/auth/, apps/frontend/src/lib/api-client.ts
- depends: task-01, task-08
- verify: cd apps/frontend && pnpm test --run
- notes:

Create `src/features/auth/` following the `items` pattern: `api.ts` with `useCurrentUser`, `useLogin`, `useRegister`, `useLogout` TanStack Query hooks. `schema.ts` with Zod schemas for login and register forms. `LoginForm.tsx` and `RegisterForm.tsx` using React Hook Form + Zod (following `ItemForm.tsx` pattern). Add auth API functions to `lib/api-client.ts`. All fetch calls use `credentials: "include"`.
