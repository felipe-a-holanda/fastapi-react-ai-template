{% raw -%}
from fastapi import APIRouter, Depends, Response

from app.api.deps import get_auth_service, get_current_user
from app.config import settings
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_token_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserCreate,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    user = await service.register(data)
    tokens = await service.login(data.email, data.password)
    _set_token_cookie(response, tokens.access_token)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserLogin,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    tokens = await service.login(data.email, data.password)
    _set_token_cookie(response, tokens.access_token)
    return tokens


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"detail": "Logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
):
    tokens = await service.refresh(current_user.id)
    _set_token_cookie(response, tokens.access_token)
    return tokens


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
{% endraw %}
