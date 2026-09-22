from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.errors import AuthenticationError, VeyraException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.auth import Token, UserLogin, UserRegister, UserResponse


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, data: UserRegister) -> UserResponse:
        existing = await self.user_repo.get_by_email(data.email)
        if existing:
            raise VeyraException(
                code="USER_ALREADY_EXISTS",
                message="An account with this email address already exists.",
            )

        user = User(
            email=data.email.lower().strip(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role="admin",
            is_active=True,
        )
        created = await self.user_repo.create(user)
        return UserResponse.model_validate(created)

    async def login(self, data: UserLogin) -> Token:
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationError("User account is inactive.")

        access_token = create_access_token(subject=user.id)
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        return await self.user_repo.get(user_id)
