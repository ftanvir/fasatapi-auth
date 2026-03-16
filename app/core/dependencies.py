from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import InvalidTokenException
from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.auth.model import User
from app.modules.auth.repository import AuthRepository
from sqlalchemy.ext.asyncio import AsyncSession

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials

    try:
        user_id = decode_access_token(token)
    except ValueError:
        raise InvalidTokenException()

    repo = AuthRepository(db)
    user = await repo.get_user_by_id(user_id)

    if not user:
        raise InvalidTokenException()

    return user