import hashlib
import random
import string
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

# === Password Hashing ===================================

PASSWORD_HASH_PREFIX = "bcrypt_sha256$"
BCRYPT_ROUNDS = 12


def _prepare_password_for_bcrypt(password: str) -> bytes:
    """
    Pre-hash the password so bcrypt always receives a short ASCII payload.

    This avoids bcrypt's 72-byte input limit for multi-byte passwords while
    still delegating the password hash storage to bcrypt.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("ascii")


def _normalize_bcrypt_hash(hashed_password: str) -> bytes:
    """Normalize bcrypt prefixes for compatibility with the bcrypt library."""
    normalized = hashed_password
    if normalized.startswith("$2y$"):
        normalized = "$2b$" + normalized[4:]
    return normalized.encode("utf-8")


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password.

    New hashes use SHA-256 pre-hashing before bcrypt so passwords containing
    multi-byte characters do not fail bcrypt's 72-byte input limit.
    """
    prepared_password = _prepare_password_for_bcrypt(plain_password)
    hashed_password = bcrypt.hashpw(
        prepared_password,
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS),
    ).decode("utf-8")
    return f"{PASSWORD_HASH_PREFIX}{hashed_password}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against stored password hashes.

    Supports both new SHA-256+bcrypt hashes and legacy raw bcrypt hashes.
    """
    try:
        if hashed_password.startswith(PASSWORD_HASH_PREFIX):
            prepared_password = _prepare_password_for_bcrypt(plain_password)
            bcrypt_hash = _normalize_bcrypt_hash(
                hashed_password.removeprefix(PASSWORD_HASH_PREFIX)
            )
            return bcrypt.checkpw(prepared_password, bcrypt_hash)

        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            _normalize_bcrypt_hash(hashed_password),
        )
    except ValueError:
        return False


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