import sqlite3
from contextlib import closing

from src.config import Settings
from src.database import JobRepository
from src.main import (
    build_sources,
    evaluate_operational_alert,
    run_analysis_only,
    run_auto_backup_before_run,
    run_backup_db,
    run_cleanup_db_backups,
    run_db_backup_summary,
    run_db_maintenance,
    run_export_db_summary,
    run_export_review_feedback,
    run_latest_run_report,
    run_list_db_backups,
    run_once,
    run_prefilter_audit_only,
    run_review_summary,
    run_verify_db_backup,
)
from src.services.run_reporter import RunReporter
from src.sources.gupy_source import GupyPublicSource, MockGupySource
from src.sources.search_engine_source import SearchEngineSource
from src.models.job import JobListing
from src.profile_summary import ProfileSummary


def create_maintenance_db(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            """
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                source TEXT,
                review_status TEXT,
                is_favorite INTEGER,
                already_sent INTEGER,
                match_score REAL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO jobs (
                title, source, review_status, is_favorite, already_sent, match_score
            )
            VALUES ('Automation Engineer', 'mock', 'relevant', 1, 0, 88)
            """
        )
        connection.execute(
            """
            CREATE TABLE job_analyses (
                id INTEGER PRIMARY KEY,
                job_id INTEGER,
                fit_score INTEGER
            )
            """
        )
        connection.execute("INSERT INTO job_analyses (job_id, fit_score) VALUES (1, 80)")
        connection.commit()


def test_run_analysis_only_without_subprocess(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db")
    repository = JobRepository(settings)
    repository.init_db()
    saved = repository.save_jobs(
        [
            JobListing(
                title="Automation Engineer",
                company="Siemens",
                location="Campinas",
                source="mock",
                url="https://example.com/automation",
                description_snippet="Python, Power BI e CLP Siemens.",
                match_score=90,
                priority_company=True,
            )
        ]
    )

    count = run_analysis_only(
        settings=settings,
        profile_summary=ProfileSummary(
            core_skills=["Python", "Power BI", "CLP Siemens"],
            tools=["Python"],
            target_companies=["Siemens"],
        ),
        analysis_min_score=50,
        reanalyze=False,
    )

    analyzed_job = repository.get_job(saved[0].id)
    assert count == 1
    assert analyzed_job is not None
    assert analyzed_job.analysis is not None


def test_run_once_dry_run_does_not_mark_jobs_as_sent(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db", email_dry_run=True)

    count = run_once(
        settings=settings,
        source="mock",
        min_score=0,
        email_dry_run=True,
        analyze=False,
    )

    repository = JobRepository(settings)
    unsent_jobs = repository.get_unsent_jobs(min_score=0, limit=10)

    assert count == 3
    assert len(unsent_jobs) == 3
    assert all(job.already_sent is False for job in unsent_jobs)


def test_build_sources_passes_debug_search_to_search_source(tmp_path):
    settings = Settings(project_root=tmp_path)

    sources = build_sources(settings, "search", debug_search=True)

    assert len(sources) == 1
    assert isinstance(sources[0], SearchEngineSource)
    assert sources[0].debug_search is True


def test_build_sources_supports_gupy_source(tmp_path):
    settings = Settings(project_root=tmp_path)

    sources = build_sources(settings, "gupy", debug_search=True)

    assert len(sources) == 1
    assert isinstance(sources[0], GupyPublicSource)
    assert sources[0].debug_search is True


def test_build_sources_all_excludes_mock_by_default_and_can_include_it(tmp_path):
    settings = Settings(project_root=tmp_path)

    default_sources = build_sources(settings, "all")
    with_mock_sources = build_sources(settings, "all", include_mock_in_all=True)

    assert [type(source) for source in default_sources] == [GupyPublicSource, SearchEngineSource]
    assert any(isinstance(source, MockGupySource) for source in with_mock_sources)


def test_run_review_summary_outputs_statuses(tmp_path, capsys):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path)
    repository = JobRepository(settings)
    repository.init_db()
    repository.save_jobs(
        [
            JobListing(
                title="Automation Engineer",
                company="Siemens",
                location="Campinas",
                source="mock",
                url="https://example.com/review-summary",
                match_score=90,
            )
        ]
    )

    summary = run_review_summary(settings=settings)

    captured = capsys.readouterr()
    assert "Total de vagas: 1" in summary
    assert "unreviewed: 1" in captured.out


def test_run_export_review_feedback_creates_report(tmp_path, capsys):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path)
    repository = JobRepository(settings)
    repository.init_db()
    repository.save_jobs(
        [
            JobListing(
                title="Automation Engineer",
                company="Siemens",
                location="Campinas",
                source="mock",
                url="https://example.com/review-export",
                match_score=90,
            )
        ]
    )

    result = run_export_review_feedback(settings=settings)

    captured = capsys.readouterr()
    assert result.path.exists()
    assert result.row_count == 1
    assert "Feedback exportado" in captured.out


def test_latest_run_report_without_reports_returns_none(tmp_path, capsys):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path)

    latest = run_latest_run_report(settings=settings)

    captured = capsys.readouterr()
    assert latest is None
    assert "Nenhum relatorio de execucao" in captured.out


def test_prefilter_audit_without_csv_returns_none(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path)

    assert run_prefilter_audit_only(settings=settings) is None


def test_auto_backup_before_run_skips_missing_database(tmp_path):
    settings = Settings(
        database_path=tmp_path / "data" / "jobs.db",
        project_root=tmp_path,
        auto_backup_before_run=True,
    )
    reporter = RunReporter(tmp_path, mode="dry-run", source="mock")

    result = run_auto_backup_before_run(settings, reporter=reporter)

    assert result is None
    assert reporter.report.generated_reports == []


def test_auto_backup_before_run_records_generated_paths(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_maintenance_db(db_path)
    settings = Settings(database_path=db_path, project_root=tmp_path, auto_backup_before_run=True)
    reporter = RunReporter(tmp_path, mode="dry-run", source="mock")

    result = run_auto_backup_before_run(settings, reporter=reporter)

    assert result is not None
    assert result.backup_db.exists()
    assert str(result.backup_db) in reporter.report.generated_reports
    assert str(result.manifest_path) in reporter.report.generated_reports


def test_database_maintenance_cli_wrappers_cover_backup_lifecycle(tmp_path, capsys):
    db_path = tmp_path / "data" / "jobs.db"
    create_maintenance_db(db_path)
    settings = Settings(database_path=db_path, project_root=tmp_path)

    backup = run_backup_db(settings=settings, reason="coverage lifecycle")
    backups = run_list_db_backups(settings=settings)
    verification = run_verify_db_backup(settings=settings, backup_path=backup.manifest_path)
    maintenance = run_db_maintenance(settings=settings)
    export = run_export_db_summary(settings=settings)
    summary = run_db_backup_summary(settings=settings)
    cleanup = run_cleanup_db_backups(settings=settings, dry_run=True, confirm_cleanup=False)

    captured = capsys.readouterr()
    assert backup.backup_db.exists()
    assert len(backups) == 1
    assert verification.valid is True
    assert maintenance.integrity_after == "ok"
    assert export.json_path.exists()
    assert summary["total_backups"] == 1
    assert cleanup.dry_run is True
    assert "Backup criado" in captured.out
    assert "Backups encontrados" in captured.out


def test_evaluate_operational_alert_records_disabled_alert(tmp_path):
    settings = Settings(
        database_path=tmp_path / "jobs.db",
        project_root=tmp_path,
        email_dry_run=True,
        operational_alerts_enabled=False,
    )
    reporter = RunReporter(tmp_path, mode="dry-run", source="mock")
    reporter.record_source_error("mock", "falha simulada")

    sent = evaluate_operational_alert(settings, reporter, operational_alerts=False)

    assert sent is False
    assert reporter.report.operational_alert_type == "failure"
    assert reporter.report.operational_alert_should_send is False
    assert reporter.report.operational_alert_sent is False
    assert reporter.report.operational_alert_reason == "Alertas operacionais desativados."


def test_evaluate_operational_alert_records_failed_send(monkeypatch, tmp_path):
    settings = Settings(
        database_path=tmp_path / "jobs.db",
        project_root=tmp_path,
        email_dry_run=False,
        operational_alerts_enabled=True,
        operational_alerts_on_no_jobs=True,
    )
    reporter = RunReporter(tmp_path, mode="production", source="mock")
    reporter.record_totals(unique_jobs=0, email_eligible_jobs=0)
    monkeypatch.setattr("src.main.EmailSender.send_operational_alert", lambda self, subject, body: False)

    sent = evaluate_operational_alert(settings, reporter, operational_alerts=True)

    assert sent is False
    assert reporter.report.operational_alert_type == "no_jobs"
    assert reporter.report.operational_alert_should_send is True
    assert reporter.report.operational_alert_sent is False
    assert reporter.report.operational_alert_reason == "habilitado"
