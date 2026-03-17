from app.core.email import send_otp_email


async def send_verification_otp_task(
    ctx: dict,
    to_email: str,
    full_name: str,
    otp: str,
) -> None:
    """
    ARQ task — sends email verification OTP.
    ctx is ARQ's worker context, always first argument.
    Retried automatically on failure.
    """
    await send_otp_email(
        to_email=to_email,
        full_name=full_name,
        otp=otp,
        subject="Verify Your Email",
    )


async def send_password_reset_otp_task(
    ctx: dict,
    to_email: str,
    full_name: str,
    otp: str,
) -> None:
    """
    ARQ task — sends password reset OTP.
    ctx is ARQ's worker context, always first argument.
    Retried automatically on failure.
    """
    await send_otp_email(
        to_email=to_email,
        full_name=full_name,
        otp=otp,
        subject="Password Reset OTP",
    )