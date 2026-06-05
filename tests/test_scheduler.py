from src.config import Settings
from src.services import scheduler as scheduler_module
from src.services.scheduler import run_daily


def test_run_daily_registers_cron_job_and_starts(monkeypatch, tmp_path):
    calls = {}

    class FakeScheduler:
        def __init__(self, timezone):
            calls["timezone"] = timezone

        def add_job(self, job, trigger, hour, minute):
            calls["job"] = job
            calls["trigger"] = trigger
            calls["hour"] = hour
            calls["minute"] = minute

        def start(self):
            calls["started"] = True

    monkeypatch.setattr(scheduler_module, "BlockingScheduler", FakeScheduler)
    settings = Settings(project_root=tmp_path, scheduler_hour=7, scheduler_minute=45)

    def job():
        calls["executed"] = True

    run_daily(job, settings)

    assert calls == {
        "timezone": "America/Sao_Paulo",
        "job": job,
        "trigger": "cron",
        "hour": 7,
        "minute": 45,
        "started": True,
    }
