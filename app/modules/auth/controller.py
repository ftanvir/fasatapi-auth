import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.auth.service import AuthService
from app.modules.auth.schema import (
    RegisterRequest,
    RegisterResponse, MessageResponse, VerifyOTPRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201, response_model=RegisterResponse)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(AuthService),
) -> RegisterResponse:
    return await service.register(payload)

@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
        payload: VerifyOTPRequest,
        service: AuthService = Depends(AuthService),
) -> MessageResponse:
    return await service.verify_email(payload)