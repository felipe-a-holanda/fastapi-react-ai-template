{% raw %}
import structlog
from fastapi import HTTPException, status

from app.auth import create_access_token, hash_password, verify_password
from app.repositories.user import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserResponse

logger = structlog.get_logger()


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register(self, data: UserCreate) -> UserResponse:
        existing = await self.user_repository.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        hashed = hash_password(data.password)
        user = await self.user_repository.create(
            email=data.email, hashed_password=hashed, full_name=data.full_name
        )
        logger.info("user_registered", user_id=user.id, email=user.email)
        return UserResponse.model_validate(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )
        access_token = create_access_token(user.id)
        logger.info("user_logged_in", user_id=user.id)
        return TokenResponse(access_token=access_token)

    async def refresh(self, user_id: int) -> TokenResponse:
        user = await self.user_repository.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        access_token = create_access_token(user.id)
        return TokenResponse(access_token=access_token)
{% endraw %}
