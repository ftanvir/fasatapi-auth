from http import HTTPStatus


class AppException(Exception):
    """
    Base exception for all custom exceptions.
    Every custom exception must inherit from this.
    """
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred"

    def __init__(self, detail: str = None):
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


# ─── Auth Exceptions ──────────────────────────────────────────────────────────

class InvalidCredentialsException(AppException):
    status_code = HTTPStatus.UNAUTHORIZED
    detail = "Invalid email or password"


class InactiveUserException(AppException):
    status_code = HTTPStatus.FORBIDDEN
    detail = "User account is inactive"


class UserAlreadyExistsException(AppException):
    status_code = HTTPStatus.CONFLICT
    detail = "User with this email already exists"


class UserNotFoundException(AppException):
    status_code = HTTPStatus.NOT_FOUND
    detail = "User not found"

class UserAlreadyVerifiedException(AppException):
    status_code = HTTPStatus.CONFLICT
    detail = "User already verified"

class UserNotVerifiedException(AppException):
    status_code = HTTPStatus.CONFLICT
    detail = "User not verified"


# ─── Token Exceptions ─────────────────────────────────────────────────────────

class TokenExpiredException(AppException):
    status_code = HTTPStatus.UNAUTHORIZED
    detail = "Token has expired"


class InvalidTokenException(AppException):
    status_code = HTTPStatus.UNAUTHORIZED
    detail = "Invalid token"


class RefreshTokenExpiredException(AppException):
    status_code = HTTPStatus.UNAUTHORIZED
    detail = "Refresh token has expired"


# ─── Password Exceptions ──────────────────────────────────────────────────────

class InvalidPasswordException(AppException):
    status_code = HTTPStatus.BAD_REQUEST
    detail = "Current password is incorrect"


class PasswordResetTokenExpiredException(AppException):
    status_code = HTTPStatus.BAD_REQUEST
    detail = "Password reset token has expired"

class PasswordMismatchException(AppException):
    status_code = HTTPStatus.CONFLICT
    detail = "Password mismatch"


# ─── OTP Exception ─────────────────────────────────────────────────────────
class InvalidOTPException(AppException):
    status_code = HTTPStatus.BAD_REQUEST
    detail = "Invalid OTP code"

class OTPExpiredException(AppException):
    status_code = HTTPStatus.BAD_REQUEST
    detail = "OTP code has expired"