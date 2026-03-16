import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.auth.service import AuthService
from app.modules.auth.schema import (
    RegisterRequest,
    RegisterResponse, MessageResponse, VerifyOTPRequest, ResendOTPRequest, LoginResponse, LoginRequest,
    RefreshTokenRequest, TokenResponse,
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

@router.post("/resend-verification-otp", response_model=MessageResponse)
async def resend_verification_otp(
        payload: ResendOTPRequest,
        service: AuthService = Depends(AuthService),
):
    return await service.resend_verification_otp(payload.email)

@router.post("/login", response_model=LoginResponse)
async def login(
        payload: LoginRequest,
        service: AuthService = Depends(AuthService),
) -> LoginResponse:
    return await service.login(payload)

@router.post("/refresh-token", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(AuthService),
) -> TokenResponse:
    return await service.refresh_token(payload)