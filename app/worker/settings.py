from arq.connections import RedisSettings

from app.core.config import get_settings
from app.worker.tasks import (
    send_password_reset_otp_task,
    send_verification_otp_task,
)

settings = get_settings()


class WorkerSettings:
    functions = [
        send_verification_otp_task,
        send_password_reset_otp_task,
    ]

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

    max_tries = 3
    retry_delay = 5
    job_timeout = 30

    async def on_startup(ctx: dict) -> None:
        print("ARQ worker started")

    async def on_shutdown(ctx: dict) -> None:
        print("ARQ worker shutting down")