# add-auth — JWT Cookie Authentication System

## Goal

Add a complete authentication system using JWT tokens in httpOnly cookies, following the architecture defined in SPEC.md. Users can register, log in, and access protected resources. The `get_current_user` FastAPI dependency protects endpoints. All user-scoped data is isolated by `owner_id`.

## Non-Goals

- OAuth / social login (future change)
- Role-based access control / permissions (future change)
- Password reset flow (future change)
- Email verification (future change)
- Rate limiting on auth endpoints (separate change)

## Requirements

1. Users can register with email + password via `POST /api/auth/register`
2. Passwords are hashed with bcrypt via passlib
3. Users can log in with email + password via `POST /api/auth/login`
4. Access tokens are JWTs signed with HS256, expire in 30 minutes (configurable via `app/config.py`)
5. Refresh tokens are JWTs, expire in 7 days (configurable via `app/config.py`)
6. Tokens are set as httpOnly cookies (not returned in response body)
7. `get_current_user` FastAPI dependency extracts and validates JWT from cookies
8. Protected endpoints return 401 when token is missing/invalid/expired
9. All items endpoints filter by `owner_id` (user isolation at repository level)
10. Auth operations logged via structlog with event names and user context
11. Frontend uses `credentials: "include"` for all API calls (already in `api-client.ts`)
12. `useCurrentUser` TanStack Query hook for frontend auth state
13. Login and register forms using React Hook Form + Zod

## Constraints

- JWT secret loaded from `SECRET_KEY` environment variable via `app/config.py` (Pydantic Settings)
- Token payloads contain only: `sub` (user email), `exp` — no PII beyond email
- Password validation: minimum 8 characters
- Auth follows the layered architecture: Router → Service → Repository
- Auth module uses `app/auth.py` for JWT + password utilities (already specified in SPEC.md)
- All database operations use the existing repository pattern (see `items` reference)
- Backend auth routes in `app/api/auth.py`, service in `app/services/auth.py`, etc.
- Frontend auth feature in `src/features/auth/`

## Edge Cases

- Registration with an already-existing email → 409 Conflict with `{"detail": "Email already registered"}`
- Login with wrong password → 401 (same error shape as wrong email, no enumeration)
- Expired access token → 401 with `{"detail": "Token expired"}`
- Missing cookie → 401 with `{"detail": "Not authenticated"}`
- Malformed JWT → 401 with `{"detail": "Invalid token"}`

## Inputs / Outputs

### POST /api/auth/register
```
Request:  { "email": string, "password": string, "full_name": string | null }
Success:  201 { "id": int, "email": string, "full_name": string | null, "created_at": string }
Conflict: 409 { "detail": "Email already registered" }
```

### POST /api/auth/login
```
Request:  { "email": string, "password": string }
Success:  200 { "access_token": string, "token_type": "bearer" }
          + Set-Cookie: access_token=<jwt>; HttpOnly; Path=/; SameSite=Lax
          + Set-Cookie: refresh_token=<jwt>; HttpOnly; Path=/api/auth; SameSite=Lax
Failure:  401 { "detail": "Invalid credentials" }
```

### POST /api/auth/refresh
```
Cookies:  refresh_token (httpOnly)
Success:  200 { "access_token": string, "token_type": "bearer" }
          + Set-Cookie: access_token=<new jwt>; HttpOnly
Failure:  401 { "detail": "Invalid refresh token" }
```

### POST /api/auth/logout
```
Cookies:  access_token (httpOnly)
Success:  200 { "detail": "Logged out" }
          + Set-Cookie: access_token=; HttpOnly; Max-Age=0
          + Set-Cookie: refresh_token=; HttpOnly; Max-Age=0
```

### GET /api/auth/me
```
Cookies:  access_token (httpOnly)
Success:  200 { "id": int, "email": string, "full_name": string | null, "is_active": bool }
Failure:  401 { "detail": "Not authenticated" }
```

### get_current_user dependency
```python
# In app/api/deps.py
async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)) -> User:
    # Decode JWT, fetch user from DB, return User model
    # Raises HTTPException(401) on failure
```

## Open Questions

(none — all resolved during planning, follows SPEC.md architecture)
