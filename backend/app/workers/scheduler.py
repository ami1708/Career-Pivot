from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.services.auto_apply import auto_apply_available_jobs
from app.services.discovery import run_discovery


def create_scheduler() -> BackgroundScheduler:
    settings = get_settings()
    scheduler = BackgroundScheduler(timezone=settings.scheduler_timezone)
    scheduler.add_job(
        _scheduled_discovery,
        trigger="cron",
        hour=settings.daily_discovery_hour,
        minute=settings.daily_discovery_minute,
        id="daily_job_discovery",
        replace_existing=True,
    )
    return scheduler


def _scheduled_discovery() -> None:
    settings = get_settings()
    db: Session = SessionLocal()
    try:
        run_discovery(db)
        if settings.daily_auto_apply_enabled:
            auto_apply_available_jobs(db, limit=settings.daily_auto_apply_limit)
    finally:
        db.close()
