from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.model import RefreshToken, User


class AuthRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        first_name: str,
        last_name: str,
        email: str,
        hashed_password: str,
    ) -> User:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=hashed_password,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user