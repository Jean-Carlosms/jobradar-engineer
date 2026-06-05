import json

from src.config import Settings
from src.main import run_history_summary, run_operational_alerts_summary
from src.services.run_history import OPERATIONAL_ALERT_COLUMNS, RUN_HISTORY_COLUMNS, RunHistoryService


def write_run_report(
    runs_dir,
    name: str,
    started_at: str,
    source: str = "mock",
    unique_jobs: int = 0,
    email_eligible_jobs: int = 0,
    email_sent: bool = False,
    duration_seconds: float = 0.0,
    source_errors: dict[str, str] | None = None,
    operational_alert_type: str = "",
    operational_alert_should_send: bool = False,
    operational_alert_sent: bool = False,
    operational_alert_reason: str = "",
):
    payload = {
        "run_id": name,
        "started_at": started_at,
        "finished_at": started_at,
        "duration_seconds": duration_seconds,
        "mode": "dry-run",
        "source": source,
        "sources_executed": [source],
        "jobs_collected_by_source": {source: unique_jobs},
        "unique_jobs": unique_jobs,
        "email_eligible_jobs": email_eligible_jobs,
        "email_sent": email_sent,
        "source_errors": source_errors or {},
        "generated_reports": ["reports/demo.md"],
        "operational_alert_type": operational_alert_type,
        "operational_alert_should_send": operational_alert_should_send,
        "operational_alert_sent": operational_alert_sent,
        "operational_alert_reason": operational_alert_reason,
    }
    path = runs_dir / f"run_report_{name}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_run_history_loads_multiple_valid_jsons(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    write_run_report(runs_dir, "old", "2026-06-04T10:00:00+00:00", unique_jobs=2)
    write_run_report(runs_dir, "new", "2026-06-04T11:00:00+00:00", unique_jobs=3)

    entries = RunHistoryService(tmp_path).load()

    assert len(entries) == 2
    assert {entry.run_id for entry in entries} == {"old", "new"}


def test_run_history_ignores_invalid_json(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    write_run_report(runs_dir, "valid", "2026-06-04T10:00:00+00:00")
    (runs_dir / "run_report_broken.json").write_text("{broken", encoding="utf-8")

    entries = RunHistoryService(tmp_path).load()

    assert len(entries) == 1
    assert entries[0].run_id == "valid"


def test_run_history_sorts_newest_first(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    write_run_report(runs_dir, "older", "2026-06-04T09:00:00+00:00")
    write_run_report(runs_dir, "newer", "2026-06-04T12:00:00+00:00")

    entries = RunHistoryService(tmp_path).load()

    assert [entry.run_id for entry in entries] == ["newer", "older"]


def test_run_history_summary_calculates_totals(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    write_run_report(
        runs_dir,
        "one",
        "2026-06-04T10:00:00+00:00",
        source="mock",
        unique_jobs=4,
        email_eligible_jobs=2,
        email_sent=True,
        duration_seconds=2,
    )
    write_run_report(
        runs_dir,
        "two",
        "2026-06-04T11:00:00+00:00",
        source="mock",
        unique_jobs=6,
        email_eligible_jobs=3,
        duration_seconds=4,
        source_errors={"mock": "falha simulada"},
        operational_alert_type="failure",
        operational_alert_should_send=True,
        operational_alert_sent=True,
        operational_alert_reason="enviado ou dry-run",
    )

    service = RunHistoryService(tmp_path)
    summary = service.summary(service.load())

    assert summary["total_runs"] == 2
    assert summary["latest_run"] == "2026-06-04T11:00:00+00:00"
    assert summary["total_unique_jobs"] == 10
    assert summary["total_email_eligible"] == 5
    assert summary["total_emails_sent"] == 1
    assert summary["runs_with_errors"] == 1
    assert summary["average_duration_seconds"] == 3
    assert summary["most_used_source"] == "mock"
    assert summary["total_alerts"] == 1
    assert summary["operational_alerts_sent"] == 1
    assert summary["alerts_by_type"]["failure"] == 1
    assert summary["runs_without_alert"] == 1
    assert summary["latest_alert_type"] == "failure"
    assert summary["alert_failures"] == 1


def test_run_history_rows_have_expected_columns(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    write_run_report(runs_dir, "row", "2026-06-04T10:00:00+00:00", email_eligible_jobs=1)

    rows = RunHistoryService(tmp_path).rows()

    assert list(rows[0].keys()) == RUN_HISTORY_COLUMNS
    assert rows[0]["email_eligible"] == 1
    assert rows[0]["report_path"].endswith(".md")


def test_run_history_extracts_operational_alert_fields(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    write_run_report(
        runs_dir,
        "alert",
        "2026-06-04T10:00:00+00:00",
        operational_alert_type="no_email_eligible",
        operational_alert_should_send=True,
        operational_alert_sent=True,
        operational_alert_reason="enviado ou dry-run",
    )

    entry = RunHistoryService(tmp_path).load()[0]

    assert entry.operational_alert_type == "no_email_eligible"
    assert entry.operational_alert_should_send is True
    assert entry.operational_alert_sent is True
    assert entry.operational_alert_reason == "enviado ou dry-run"


def test_run_history_alert_rows_ignore_runs_without_alert(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    write_run_report(runs_dir, "plain", "2026-06-04T10:00:00+00:00")
    write_run_report(
        runs_dir,
        "alert",
        "2026-06-04T11:00:00+00:00",
        operational_alert_type="no_jobs",
        operational_alert_reason="desativado",
    )

    rows = RunHistoryService(tmp_path).alert_rows()

    assert len(rows) == 1
    assert list(rows[0].keys()) == OPERATIONAL_ALERT_COLUMNS
    assert rows[0]["operational_alert_type"] == "no_jobs"


def test_run_history_summary_counts_alerts_by_type(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    write_run_report(runs_dir, "failure", "2026-06-04T10:00:00+00:00", operational_alert_type="failure")
    write_run_report(runs_dir, "no_jobs", "2026-06-04T11:00:00+00:00", operational_alert_type="no_jobs")
    write_run_report(
        runs_dir,
        "no_email",
        "2026-06-04T12:00:00+00:00",
        operational_alert_type="no_email_eligible",
    )
    write_run_report(
        runs_dir,
        "success",
        "2026-06-04T13:00:00+00:00",
        operational_alert_type="success_summary",
    )

    summary = RunHistoryService(tmp_path).summary()

    assert summary["total_alerts"] == 4
    assert summary["alert_failures"] == 1
    assert summary["alert_no_jobs"] == 1
    assert summary["alert_no_email_eligible"] == 1
    assert summary["alert_success_summary"] == 1


def test_run_history_summary_cli_prints_summary(tmp_path, capsys):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    write_run_report(runs_dir, "cli", "2026-06-04T10:00:00+00:00", email_sent=True, duration_seconds=5)
    settings = Settings(project_root=tmp_path, database_path=tmp_path / "jobs.db")

    summary = run_history_summary(settings=settings)

    captured = capsys.readouterr()
    assert summary["total_runs"] == 1
    assert "Execucoes: 1" in captured.out
    assert "emails_enviados: 1" in captured.out
    assert "alertas: 0" in captured.out


def test_run_history_summary_cli_includes_alerts(tmp_path, capsys):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    write_run_report(
        runs_dir,
        "cli-alert",
        "2026-06-04T10:00:00+00:00",
        operational_alert_type="failure",
        operational_alert_sent=True,
    )
    settings = Settings(project_root=tmp_path, database_path=tmp_path / "jobs.db")

    summary = run_history_summary(settings=settings)

    captured = capsys.readouterr()
    assert summary["total_alerts"] == 1
    assert "alertas: 1" in captured.out
    assert "ultimo_alerta: failure" in captured.out


def test_operational_alerts_summary_cli_prints_alert_totals(tmp_path, capsys):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    write_run_report(
        runs_dir,
        "summary-alert",
        "2026-06-04T10:00:00+00:00",
        operational_alert_type="failure",
        operational_alert_sent=True,
    )
    settings = Settings(project_root=tmp_path, database_path=tmp_path / "jobs.db")

    summary = run_operational_alerts_summary(settings=settings)

    captured = capsys.readouterr()
    assert summary["total_alerts"] == 1
    assert "Alertas: 1" in captured.out
    assert "failure=1" in captured.out
