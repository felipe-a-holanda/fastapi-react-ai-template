{% raw %}
"""
Domain exceptions.

Services raise these. They carry NO HTTP concepts.
The handler in main.py maps each to an HTTP status code.

To add a new exception:
1. Create a subclass of AppError here
2. Add the mapping in EXCEPTION_STATUS_MAP
3. That's it - the handler does the rest
"""

from fastapi import Request
from fastapi.responses import JSONResponse


# --- Base ---

class AppError(Exception):
    """Base for all domain errors. Never raise this directly."""
    def __init__(self, detail: str):
        self.detail = detail


# --- Concrete errors ---

class NotFoundError(AppError):
    """Entity not found. Maps to 404."""
    pass


class ConflictError(AppError):
    """Duplicate or conflicting state. Maps to 409."""
    pass


class AuthenticationError(AppError):
    """Invalid credentials or missing auth. Maps to 401."""
    pass


class AuthorizationError(AppError):
    """Authenticated but not permitted. Maps to 403."""
    pass


class ValidationError(AppError):
    """Business rule violated (not schema validation). Maps to 422."""
    pass


# --- Mapping: domain error -> HTTP status ---

EXCEPTION_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: 404,
    ConflictError: 409,
    AuthenticationError: 401,
    AuthorizationError: 403,
    ValidationError: 422,
}


# --- Handler (registered in main.py) ---

async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.detail},
    )
{% endraw %}
