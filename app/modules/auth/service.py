from datetime import datetime, timezone, timedelta
import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.email import send_otp_email
from app.core.exceptions import UserAlreadyExistsException, UserNotFoundException, UserAlreadyVerifiedException, \
    InvalidTokenException, RefreshTokenExpiredException
from app.core.security import generate_otp, hash_password, generate_refresh_token, create_access_token, hash_refresh_token
from app.db.redis import get_redis
from app.db.session import get_db
from app.modules.auth.model import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schema import RegisterRequest, RegisterResponse, UserResponse, VerifyOTPRequest, MessageResponse, \
    LoginRequest, LoginResponse, TokenData, RefreshTokenRequest, TokenResponse, LogoutRequest

settings = get_settings()


class AuthService:

    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        redis: aioredis.Redis = Depends(get_redis),
    ):
        self.db = db
        self.redis = redis
        self.repo = AuthRepository(db)

    async def register(self, payload: RegisterRequest) -> RegisterResponse:
        # 1. check email uniqueness
        existing_user = await self.repo.get_user_by_email(payload.email)
        if existing_user:
            raise UserAlreadyExistsException()

        # 2. hash password
        hashed_password = hash_password(payload.password)

        # 3. create user
        user = await self.repo.create_user(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            hashed_password=hashed_password,
        )

        # 4. generate OTP
        otp = generate_otp()

        # 5. store OTP in Redis with TTL
        otp_key = f"email_verification:{str(user.id)}"
        await self.redis.set(
            otp_key,
            otp,
            ex=settings.EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES * 60,
        )

        # 6. send OTP via email
        await send_otp_email(
            to_email=user.email,
            full_name=f"{user.first_name} {user.last_name}",
            otp=otp,
            subject="Verify Your Email",
        )

        # 7. return response
        return RegisterResponse(
            status="success",
            message="Registration successful. OTP sent to your email.",
            data=UserResponse.model_validate(user),
        )

    async def verify_email(self, payload: VerifyOTPRequest) -> MessageResponse:

        # 1. find user
        user = await self.repo.get_user_by_email(payload.email)

        if not user:
            raise UserNotFoundException()

        # 2. check if already verified
        if user.is_verified:
            raise UserAlreadyExistsException()

        # 3. get OTP from Redis
        otp_key = f"email_verification:{str(user.id)}"
        stored_otp = await self.redis.get(otp_key)

        # 4. check OTP expired (key missing from Redis)
        if stored_otp is None:
            raise OTPExpiredException()

        # 5. check OTP matches
        if stored_otp != payload.otp:
            raise InvalidOTPException()

        # 6. mark user verified
        await self.repo.update_user_verified(user)

        # 7. delete OTP from Redis
        await self.redis.delete(otp_key)

        return MessageResponse(
            status="success",
            message="Email verified successfully.",
            data=None,
        )

    async def resend_verification_otp(self, email: str) ->MessageResponse:
        # 1. find user
        user = await self.repo.get_user_by_email(email)
        if not user:
            raise UserNotFoundException()

        # 2. check if user already verified
        if user.is_verified:
            raise UserAlreadyVerifiedException()

        # 3. generate fresh otp
        otp = generate_otp()

        # 4. overwrite OTP in Redis with new TTL
        otp_key = f"email_verification:{str(user.id)}"
        await self.redis.set(
            otp_key,
            otp,
            ex=settings.EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES * 60,
        )

        # 5. resend email with new otp
        await send_otp_email(
            to_email=user.email,
            full_name=f"{user.first_name} {user.last_name}",
            otp=otp,
            subject="Verify Your Email",
        )

        return MessageResponse(
            status="success",
            message="Verification OTP resent to your email.",
            data=None,
        )

    async def login(self, payload: LoginRequest) -> LoginResponse:
        # 1. find user by email
        user = await self.repo.get_user_by_email(payload.email)

        if not user:
            raise UserNotFoundException()

        if not user.is_verified:
            raise UnverifiedException()

        access_token = create_access_token(str(user.id))

        raw_refresh_token = generate_refresh_token()

        token_hash = hash_refresh_token(raw_refresh_token)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.repo.create_refresh_token(
            user_id=str(user.id),
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return LoginResponse(
            status="success",
            message="Login successful.",
            data=TokenData(
                access_token=access_token,
                refresh_token=raw_refresh_token,
                token_type="bearer",
            ),
        )

    async def refresh_token(self, payload: RefreshTokenRequest):
        token_hash = hash_refresh_token(payload.refresh_token)
        token = await self.repo.get_refresh_token_by_hash(token_hash)

        if not token:
            raise InvalidTokenException()

        if token.is_revoked:
            raise InvalidTokenException()

        if datetime.now(timezone.utc) > token.expires_at:
            raise RefreshTokenExpiredException()

        new_access_token = create_access_token(str(token.user_id))

        await self.repo.revoke_refresh_token(token)

        new_raw_refresh_token = generate_refresh_token()
        new_token_hash = hash_refresh_token(new_raw_refresh_token)
        new_expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.repo.create_refresh_token(
            user_id=str(token.user_id),
            token_hash=new_token_hash,
            expires_at=new_expires_at,
        )

        return TokenResponse(
            status="success",
            message="Token refreshed successfully.",
            data=TokenData(
                access_token=new_access_token,
                refresh_token=new_raw_refresh_token,
                token_type="bearer",
            ),
        )

    async def logout(self, payload: LogoutRequest, current_user: User) ->MessageResponse:
        token_hash = hash_refresh_token(payload.refresh_token)
        token = await self.repo.get_refresh_token_by_hash(token_hash)

        if not token:
            raise InvalidTokenException()

        if str(token.user_id) != str(current_user.id):
            raise InvalidTokenException()

        await self.repo.revoke_refresh_token(token)

        return MessageResponse(
            status="success",
            message="Logout successful.",
            data=None,
        )

    async def forgot_password(self, email: str) -> MessageResponse:
        user = await self.repo.get_user_by_email(email)

        if user and user.is_verified and user.is_active:
            otp = generate_otp()
            otp_key = f"password_reset:{str(user.id)}"

            await self.redis.set(
                otp_key,
                otp,
                ex=settings.PASSWORD_RESET_OTP_EXPIRE_MINUTES * 60,
            )

            await send_otp_email(
                to_email=user.email,
                full_name=f"{user.first_name} {user.last_name}",
                otp=otp,
                subject="Password Reset OTP",
            )

            return MessageResponse(
                status="success",
                message="If that email exists, a reset OTP was sent.",
                data=None,
            )
