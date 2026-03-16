from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator

class BaseResponse[DataT](BaseModel):
    """
        Consistent response shape for every endpoint.
        {
            "status": "success" | "error",
            "message": "...",
            "data": { ... } | null
        }
        """
    status: str
    message: str
    data: Optional[DataT] = None

class EmailRequest(BaseModel):
    """Used by endpoints that only need an email — forgot password, resend OTP."""
    email: EmailStr

class UserResponse(BaseModel):
    """
    Safe user representation — never exposes hashed_password.
    Returned after register, and available via /me later.
    """
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}

class RegisterRequest(BaseModel):
    first_name: str = Field(
        min_length=1,
        max_length=50,
    )
    last_name: str = Field(
        min_length=1,
        max_length=50,
    )
    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=64,
    )
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=1,
    )

class TokenData(BaseModel):
    """The data payload nested inside LoginResponse and TokenResponse."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )
    new_password: str = Field(
        min_length=8,
        max_length=64,
    )
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "ResetPasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self



class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(
        min_length=8,
        max_length=64,
    )
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


MessageResponse = BaseResponse[None]
LoginResponse = BaseResponse[TokenData]
TokenResponse = BaseResponse[TokenData]
RegisterResponse = BaseResponse[UserResponse]