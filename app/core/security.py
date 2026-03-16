import hashlib
import random
import string
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# === Password Hashing ===================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(plain_password: str) -> str:
    """Hash a plain text password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ================== OTP =======================

def generate_otp() -> str:
    """Generate a cryptographically random 6-digit OTP."""
    return "".join(random.choices(string.digits, k=6))


# JWT Access Token

def create_access_token(user_id: str) -> str:
    """
    Create a short-lived JWT access token.
    Payload contains user_id, expiry, and token type.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_access_token(token: str) -> str:
    """
    Decode and validate a JWT access token.
    Returns user_id if valid.
    Raises ValueError for any invalid or expired token.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")

        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise ValueError("Token missing subject")

        return user_id

    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e


# ======= Refresh Token ================================================

def generate_refresh_token() -> str:
    """
    Generate a cryptographically secure random refresh token.
    Returns the raw token — send this to the client.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choices(alphabet, k=64))


def hash_refresh_token(raw_token: str) -> str:
    """
    Hash a refresh token using SHA-256 for safe DB storage.
    Never store the raw token in the DB.
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()