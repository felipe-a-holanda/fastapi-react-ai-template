{% raw %}
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.items import router as items_router
from app.config import settings
from app.exceptions import AppException, app_exception_handler

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.include_router(items_router)
{% endraw %}
