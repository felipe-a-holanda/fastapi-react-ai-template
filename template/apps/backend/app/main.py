{% raw -%}
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.admin import setup_admin
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.items import router as items_router
from app.config import settings
from app.exceptions import AppError, app_exception_handler
from app.logging import setup_logging

setup_logging()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_exception_handler)

# Routers
app.include_router(auth_router)
app.include_router(items_router)
app.include_router(health_router)

# Admin panel (available at /admin)
setup_admin(app)
{% endraw %}
