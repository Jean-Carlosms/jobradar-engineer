import json
from pathlib import Path

from src.config import Settings
from src.main import run_latest_run_report, run_once
from src.profile import ProfileConfig
from src.services.run_reporter import RunReporter


def test_run_reporter_creates_markdown_and_json(tmp_path):
    reporter = RunReporter(tmp_path, mode="dry-run", source="mock", run_id="test-run")
    reporter.record_source("GupySimulada", collected=3, duration_seconds=0.1)
    reporter.record_totals(unique_jobs=2, email_eligible_jobs=1, prefilter_kept_jobs=2)
    reporter.record_email(sent=True)

    result = reporter.finish(tmp_path / "runs")

    assert result.markdown_path.exists()
    assert result.json_path.exists()
    markdown = result.markdown_path.read_text(encoding="utf-8")
    raw = json.loads(result.json_path.read_text(encoding="utf-8"))
    assert "JobRadar Run Report" in markdown
    assert raw["run_id"] == "test-run"
    assert raw["jobs_collected_by_source"]["GupySimulada"] == 3


def test_run_reporter_sanitizes_sensitive_values(tmp_path):
    reporter = RunReporter(tmp_path, mode="production", source="mock", run_id="secret-run")
    reporter.record_source_error("Fonte", "SMTP_PASSWORD=abc123 user@example.com .env")

    result = reporter.finish(tmp_path / "runs")
    markdown = result.markdown_path.read_text(encoding="utf-8")
    raw_text = result.json_path.read_text(encoding="utf-8")

    assert "abc123" not in markdown
    assert "user@example.com" not in markdown
    assert ".env" not in markdown
    assert "abc123" not in raw_text
    assert "user@example.com" not in raw_text


def test_run_once_with_run_report_generates_report(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path, email_dry_run=True)

    count = run_once(
        settings=settings,
        profile=ProfileConfig(),
        source="mock",
        min_score=0,
        email_dry_run=True,
        run_report=True,
    )

    reports = list((tmp_path / "runs").glob("run_report_*.md"))
    assert count == 3
    assert reports
    assert reports[0].with_suffix(".json").exists()


def test_run_once_without_run_report_does_not_generate_report(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path, email_dry_run=True)

    run_once(
        settings=settings,
        profile=ProfileConfig(),
        source="mock",
        min_score=0,
        email_dry_run=True,
        run_report=False,
    )

    assert not list((tmp_path / "runs").glob("run_report_*.md"))


def test_latest_run_report_prints_summary(tmp_path, capsys):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path, email_dry_run=True)
    run_once(
        settings=settings,
        profile=ProfileConfig(),
        source="mock",
        min_score=0,
        email_dry_run=True,
        run_report=True,
    )

    latest = run_latest_run_report(settings=settings)

    captured = capsys.readouterr()
    assert latest is not None
    assert "Relatorio mais recente" in captured.out
    assert "email_eligible=3" in captured.out


def test_gitignore_protects_runs_directory():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "runs/*" in gitignore
    assert "!runs/.gitkeep" in gitignore
