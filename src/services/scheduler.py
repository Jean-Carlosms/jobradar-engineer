from __future__ import annotations

import logging
from collections.abc import Callable

from apscheduler.schedulers.blocking import BlockingScheduler

from src.config import Settings

logger = logging.getLogger(__name__)


def run_daily(job: Callable[[], None], settings: Settings) -> None:
    scheduler = BlockingScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(job, "cron", hour=settings.scheduler_hour, minute=settings.scheduler_minute)
    logger.info("Agendador iniciado para %02d:%02d.", settings.scheduler_hour, settings.scheduler_minute)
    scheduler.start()
