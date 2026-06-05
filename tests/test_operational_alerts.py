import json
import smtplib
from dataclasses import replace

from src.config import Settings
from src.main import run_once, run_test_operational_alert
from src.profile import ProfileConfig
from src.services.email_sender import EmailSender
from src.services.operational_alerts import OperationalAlertService
from src.services.run_reporter import RunReport


def make_report(
    unique_jobs: int = 3,
    email_eligible_jobs: int = 1,
    source_errors: dict[str, str] | None = None,
) -> RunReport:
    return RunReport(
        run_id="test-run",
        started_at="2026-06-04T10:00:00+00:00",
        finished_at="2026-06-04T10:00:01+00:00",
        duration_seconds=1.0,
        mode="dry-run",
        source="mock",
        sources_executed=["mock"],
        jobs_collected_by_source={"mock": unique_jobs},
        unique_jobs=unique_jobs,
        email_eligible_jobs=email_eligible_jobs,
        source_errors=source_errors or {},
    )


def alert_settings(tmp_path, **overrides) -> Settings:
    settings = Settings(
        project_root=tmp_path,
        database_path=tmp_path / "jobs.db",
        email_dry_run=True,
        operational_alerts_enabled=True,
    )
    return replace(settings, **overrides)


def test_operational_alert_failure_when_source_has_error(tmp_path):
    alert = OperationalAlertService(alert_settings(tmp_path)).build_alert(
        make_report(source_errors={"mock": "falha simulada"})
    )

    assert alert.alert_type == "failure"
    assert alert.should_send is True
    assert "falha operacional" in alert.subject


def test_operational_alert_no_jobs_when_unique_jobs_is_zero(tmp_path):
    alert = OperationalAlertService(alert_settings(tmp_path)).build_alert(make_report(unique_jobs=0))

    assert alert.alert_type == "no_jobs"
    assert alert.should_send is True
    assert "nenhuma vaga" in alert.subject


def test_operational_alert_no_email_eligible_respects_specific_setting(tmp_path):
    settings = alert_settings(tmp_path, operational_alerts_on_no_email_eligible=True)
    alert = OperationalAlertService(settings).build_alert(make_report(unique_jobs=3, email_eligible_jobs=0))

    assert alert.alert_type == "no_email_eligible"
    assert alert.should_send is True
    assert "nenhuma vaga passou" in alert.body_text


def test_operational_alert_success_summary_when_enabled(tmp_path):
    settings = alert_settings(tmp_path, operational_daily_summary=True)
    alert = OperationalAlertService(settings).build_alert(make_report(unique_jobs=3, email_eligible_jobs=2))

    assert alert.alert_type == "success_summary"
    assert alert.should_send is True
    assert "resumo operacional" in alert.subject


def test_operational_alert_should_send_respects_global_config(tmp_path):
    settings = alert_settings(tmp_path, operational_alerts_enabled=False)
    alert = OperationalAlertService(settings).build_alert(
        make_report(source_errors={"mock": "falha simulada"})
    )

    assert alert.alert_type == "failure"
    assert alert.should_send is False
    assert alert.reason == "Alertas operacionais desativados."


def test_operational_alert_dry_run_does_not_open_smtp(monkeypatch, tmp_path):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("SMTP should not be opened during dry-run")

    monkeypatch.setattr(smtplib, "SMTP", fail_if_called)
    settings = alert_settings(tmp_path, email_dry_run=True)

    assert EmailSender(settings).send_operational_alert("Teste", "Corpo") is True


def test_test_operational_alert_cli_helper_works_in_dry_run(tmp_path, capsys):
    settings = alert_settings(tmp_path, email_dry_run=True)

    assert run_test_operational_alert(settings=settings) is True

    captured = capsys.readouterr()
    assert "Alerta operacional de teste" in captured.out
    assert "JobRadar Engineer - alerta operacional" in captured.out
    assert "Resultado: enviado/dry-run" in captured.out


def test_run_report_registers_operational_alert_status(tmp_path):
    settings = alert_settings(
        tmp_path,
        email_dry_run=True,
        operational_alerts_on_no_email_eligible=True,
    )

    run_once(
        settings=settings,
        profile=ProfileConfig(),
        source="mock",
        min_score=999,
        email_dry_run=True,
        run_report=True,
        operational_alerts=True,
    )

    json_path = next((tmp_path / "runs").glob("run_report_*.json"))
    raw = json.loads(json_path.read_text(encoding="utf-8"))
    assert raw["operational_alert_type"] == "no_email_eligible"
    assert raw["operational_alert_should_send"] is True
    assert raw["operational_alert_sent"] is True
