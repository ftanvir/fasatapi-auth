# core/email.py

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings

settings = get_settings()


async def send_otp_email(
    to_email: str,
    full_name: str,
    otp: str,
    subject: str,
) -> None:
    body = f"""
Hi {full_name},

Your OTP is: {otp}

This OTP expires in {settings.EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES} minutes.
If you did not request this, please ignore this email.

Regards,
{settings.APP_NAME}
    """

    message = MIMEMultipart()
    message["From"] = settings.EMAILS_FROM
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )