import json
import sqlite3
from datetime import timedelta
from pathlib import Path

import pytest

from src.config import Settings
from src.main import run_db_backup_summary
from src.services.database_maintenance import (
    BACKUP_MANIFEST_COLUMNS,
    DatabaseMaintenanceService,
    calculate_sha256,
    build_backup_cleanup_plan,
    format_backup_size,
    load_backup_manifest_rows,
    utc_now,
    short_sha256,
    summarize_backups,
)


def create_temp_db(path: Path, title: str = "Original") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
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
            VALUES (?, 'mock', 'relevant', 1, 0, 88)
            """,
            (title,),
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
    finally:
        connection.close()


def read_title(path: Path) -> str:
    connection = sqlite3.connect(path)
    try:
        return str(connection.execute("SELECT title FROM jobs WHERE id = 1").fetchone()[0])
    finally:
        connection.close()


def rewrite_manifest_timestamp(manifest_path: Path, timestamp: str) -> None:
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    raw["timestamp"] = timestamp
    manifest_path.write_text(json.dumps(raw), encoding="utf-8")


def test_database_backup_creates_db_and_manifest(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)

    result = service.create_backup(reason="unit test")

    assert result.backup_db.exists()
    assert result.manifest_path.exists()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["reason"] == "unit test"
    assert manifest["file_size_bytes"] == result.backup_db.stat().st_size
    assert manifest["sha256"] == calculate_sha256(result.backup_db)


def test_database_backup_calculates_sha256(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    result = DatabaseMaintenanceService(tmp_path, db_path).create_backup(reason="sha")

    assert result.sha256 == calculate_sha256(result.backup_db)
    assert len(result.sha256) == 64


def test_database_backup_list_backups(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)
    service.create_backup(reason="first")
    service.create_backup(reason="second")

    backups = service.list_backups()

    assert len(backups) == 2
    assert {backup.reason for backup in backups} == {"first", "second"}


def test_database_backup_loads_valid_manifest_rows(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)
    service.create_backup(reason="dashboard")

    rows = load_backup_manifest_rows(tmp_path / "backups")

    assert len(rows) == 1
    assert rows[0]["reason"] == "dashboard"
    assert rows[0]["sha256_short"]


def test_database_backup_ignores_invalid_manifest(tmp_path):
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    (backups_dir / "jobs_backup_invalid.json").write_text("{broken", encoding="utf-8")

    assert load_backup_manifest_rows(backups_dir) == []


def test_database_backup_summarizes_rows(tmp_path):
    rows = [
        {
            "timestamp": "2026-06-05T10:00:00+00:00",
            "backup_db": "older.db",
            "file_size_bytes": 1024,
        },
        {
            "timestamp": "2026-06-05T11:00:00+00:00",
            "backup_db": "newer.db",
            "file_size_bytes": 2048,
        },
    ]

    summary = summarize_backups(rows)

    assert summary["total_backups"] == 2
    assert summary["total_size_bytes"] == 3072
    assert summary["latest_backup"] == "2026-06-05T11:00:00+00:00"
    assert summary["largest_backup"] == "newer.db"


def test_database_backup_formats_size_and_short_sha():
    assert format_backup_size(0) == "0 B"
    assert format_backup_size(1536) == "1.5 KB"
    assert short_sha256("abcdef1234567890") == "abcdef123456"


def test_database_backup_verify_valid_backup(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)
    backup = service.create_backup(reason="verify")

    verification = service.verify_backup(backup.manifest_path)

    assert verification.valid is True
    assert verification.sha256_matches is True
    assert verification.integrity_ok is True


def test_database_restore_requires_confirmation(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)
    backup = service.create_backup(reason="restore")

    with pytest.raises(ValueError, match="--confirm-restore"):
        service.restore_backup(backup.backup_db, confirm_restore=False)


def test_database_restore_with_confirmation_creates_pre_restore_backup(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path, title="Original")
    service = DatabaseMaintenanceService(tmp_path, db_path)
    backup = service.create_backup(reason="restore")

    db_path.unlink()
    create_temp_db(db_path, title="Changed")
    result = service.restore_backup(backup.backup_db, confirm_restore=True)

    assert read_title(db_path) == "Original"
    assert result.pre_restore_backup is not None
    assert result.pre_restore_backup.exists()


def test_database_export_summary_creates_json_and_csv(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)

    result = service.export_summary(tmp_path / "reports")

    assert result.json_path.exists()
    assert result.csv_path.exists()
    assert result.summary["jobs"]["total"] == 1
    assert result.summary["analyses"]["total"] == 1
    assert "jobs.total" in result.csv_path.read_text(encoding="utf-8")


def test_database_backup_summary_cli_prints_totals(tmp_path, capsys):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    settings = Settings(project_root=tmp_path, database_path=db_path)
    DatabaseMaintenanceService(tmp_path, db_path).create_backup(reason="cli")

    summary = run_db_backup_summary(settings=settings)

    captured = capsys.readouterr()
    assert summary["total_backups"] == 1
    assert "Backups: 1" in captured.out
    assert "Tamanho total:" in captured.out


def test_database_backup_dashboard_rows_have_expected_columns(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)
    service.create_backup(reason="columns")

    rows = service.backup_rows()

    assert set(BACKUP_MANIFEST_COLUMNS).issubset(rows[0].keys())


def test_backup_cleanup_plan_marks_old_backups_as_candidates(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)
    old_backup = service.create_backup(reason="old")
    recent_backup = service.create_backup(reason="recent")
    rewrite_manifest_timestamp(old_backup.manifest_path, (utc_now() - timedelta(days=45)).isoformat())
    rewrite_manifest_timestamp(recent_backup.manifest_path, utc_now().isoformat())

    plan = service.plan_backup_cleanup(retention_days=30)

    assert plan["backups_found"] == 2
    assert plan["candidates_count"] == 1
    assert plan["candidates"][0]["reason"] == "mais antigo que 30 dia(s)"


def test_backup_cleanup_never_removes_latest_backup(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)
    older = service.create_backup(reason="older")
    latest = service.create_backup(reason="latest")
    old_timestamp = (utc_now() - timedelta(days=90)).isoformat()
    rewrite_manifest_timestamp(older.manifest_path, old_timestamp)
    rewrite_manifest_timestamp(latest.manifest_path, old_timestamp)

    plan = service.plan_backup_cleanup(retention_days=30)

    protected_paths = {item["manifest_path"] for item in plan["protected"]}
    assert str(latest.manifest_path) in protected_paths


def test_backup_cleanup_dry_run_does_not_delete_files(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)
    old_backup = service.create_backup(reason="old")
    service.create_backup(reason="latest")
    rewrite_manifest_timestamp(old_backup.manifest_path, (utc_now() - timedelta(days=45)).isoformat())

    result = service.cleanup_backups(
        retention_days=30,
        reports_dir=tmp_path / "reports",
        dry_run=True,
        confirm_cleanup=False,
    )

    assert old_backup.backup_db.exists()
    assert old_backup.manifest_path.exists()
    assert result.removed_files == []


def test_backup_cleanup_without_confirmation_does_not_delete_files(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)
    old_backup = service.create_backup(reason="old")
    service.create_backup(reason="latest")
    rewrite_manifest_timestamp(old_backup.manifest_path, (utc_now() - timedelta(days=45)).isoformat())

    result = service.cleanup_backups(
        retention_days=30,
        reports_dir=tmp_path / "reports",
        dry_run=False,
        confirm_cleanup=False,
    )

    assert old_backup.backup_db.exists()
    assert old_backup.manifest_path.exists()
    assert result.dry_run is True


def test_backup_cleanup_with_confirmation_deletes_candidates(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)
    old_backup = service.create_backup(reason="old")
    latest = service.create_backup(reason="latest")
    rewrite_manifest_timestamp(old_backup.manifest_path, (utc_now() - timedelta(days=45)).isoformat())

    result = service.cleanup_backups(
        retention_days=30,
        reports_dir=tmp_path / "reports",
        dry_run=False,
        confirm_cleanup=True,
    )

    assert not old_backup.backup_db.exists()
    assert not old_backup.manifest_path.exists()
    assert latest.backup_db.exists()
    assert latest.manifest_path.exists()
    assert len(result.removed_files) == 2


def test_backup_cleanup_protects_invalid_manifest_by_default(tmp_path):
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir()
    invalid_manifest = backups_dir / "jobs_backup_invalid.json"
    invalid_manifest.write_text("{broken", encoding="utf-8")

    plan = build_backup_cleanup_plan(backups_dir, retention_days=0)

    assert plan["candidates_count"] == 0
    assert plan["protected"][0]["reason"] == "manifesto invalido protegido"


def test_backup_cleanup_generates_markdown_and_csv(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)
    service = DatabaseMaintenanceService(tmp_path, db_path)
    old_backup = service.create_backup(reason="old")
    service.create_backup(reason="latest")
    rewrite_manifest_timestamp(old_backup.manifest_path, (utc_now() - timedelta(days=45)).isoformat())

    result = service.cleanup_backups(
        retention_days=30,
        reports_dir=tmp_path / "reports",
        dry_run=True,
        confirm_cleanup=False,
    )

    assert result.markdown_path.exists()
    assert result.csv_path.exists()
    assert "Backup Cleanup Report" in result.markdown_path.read_text(encoding="utf-8")
    assert "decision" in result.csv_path.read_text(encoding="utf-8")


def test_database_maintenance_vacuum_analyze_temp_db(tmp_path):
    db_path = tmp_path / "data" / "jobs.db"
    create_temp_db(db_path)

    result = DatabaseMaintenanceService(tmp_path, db_path).run_maintenance()

    assert result.integrity_before == "ok"
    assert result.integrity_after == "ok"
    assert result.page_count > 0


def test_gitignore_protects_backups_directory():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "backups/*" in gitignore
    assert "!backups/.gitkeep" in gitignore
