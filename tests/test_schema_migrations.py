import sqlite3
from contextlib import closing

from src.config import Settings
from src.database import JobRepository
from src.main import run_migrate_schema, run_schema_status
from src.schema_migrations import (
    CURRENT_SCHEMA_VERSION,
    apply_schema_migrations,
    get_applied_migrations,
    schema_status,
)


def table_names(db_path):
    with closing(sqlite3.connect(db_path)) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {row[0] for row in rows}


def column_names(db_path, table_name):
    with closing(sqlite3.connect(db_path)) as conn:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def index_names(db_path):
    with closing(sqlite3.connect(db_path)) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    return {row[0] for row in rows}


def create_legacy_jobs_db(db_path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE
            )
            """
        )
        conn.execute(
            """
            INSERT INTO jobs (title, company, location, source, url)
            VALUES ('Engenheiro de Automacao', 'Siemens', 'Campinas', 'legacy', 'https://example.com/legacy')
            """
        )
        conn.commit()


def test_schema_migration_creates_control_table_and_initial_schema(tmp_path):
    db_path = tmp_path / "jobs.db"

    result = apply_schema_migrations(db_path)

    assert result.applied_now == [1, CURRENT_SCHEMA_VERSION]
    assert result.status == "atualizado"
    assert {"schema_migrations", "jobs", "job_analyses"}.issubset(table_names(db_path))
    with closing(sqlite3.connect(db_path)) as conn:
        migrations = get_applied_migrations(conn)
    assert [migration["version"] for migration in migrations] == [1, CURRENT_SCHEMA_VERSION]
    assert migrations[0]["name"] == "initial_local_schema"


def test_schema_migration_is_idempotent(tmp_path):
    db_path = tmp_path / "jobs.db"

    first = apply_schema_migrations(db_path)
    second = apply_schema_migrations(db_path)

    assert first.applied_now == [1, CURRENT_SCHEMA_VERSION]
    assert second.applied_now == []
    assert second.applied_versions == [1, CURRENT_SCHEMA_VERSION]
    with closing(sqlite3.connect(db_path)) as conn:
        row_count = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    assert row_count == 2


def test_schema_migration_v2_creates_performance_indexes(tmp_path):
    db_path = tmp_path / "jobs.db"

    result = apply_schema_migrations(db_path)

    assert CURRENT_SCHEMA_VERSION == 2
    assert result.applied_versions == [1, 2]
    indexes = index_names(db_path)
    assert {
        "idx_jobs_url",
        "idx_jobs_title",
        "idx_jobs_company",
        "idx_jobs_source",
        "idx_jobs_match_score",
        "idx_jobs_prefilter_score",
        "idx_jobs_review_status",
        "idx_jobs_is_favorite",
        "idx_jobs_already_sent",
        "idx_jobs_collected_at",
        "idx_job_analyses_job_id",
        "idx_schema_migrations_version",
    }.issubset(indexes)


def test_schema_migration_v2_is_idempotent_for_existing_v1_database(tmp_path):
    db_path = tmp_path / "jobs.db"
    apply_schema_migrations(db_path)
    with closing(sqlite3.connect(db_path)) as conn:
        conn.execute("DELETE FROM schema_migrations WHERE version = 2")
        conn.commit()

    result = apply_schema_migrations(db_path)

    assert result.applied_now == [2]
    assert result.applied_versions == [1, 2]
    with closing(sqlite3.connect(db_path)) as conn:
        version_2_count = conn.execute("SELECT COUNT(*) FROM schema_migrations WHERE version = 2").fetchone()[0]
    assert version_2_count == 1


def test_schema_migration_preserves_existing_legacy_data(tmp_path):
    db_path = tmp_path / "jobs.db"
    create_legacy_jobs_db(db_path)

    result = apply_schema_migrations(db_path)

    assert result.status == "atualizado"
    columns = column_names(db_path, "jobs")
    assert {"match_reason", "prefilter_score", "review_status", "is_favorite", "already_sent"}.issubset(columns)
    with closing(sqlite3.connect(db_path)) as conn:
        row = conn.execute("SELECT title, company, url FROM jobs WHERE id = 1").fetchone()
    assert row == ("Engenheiro de Automacao", "Siemens", "https://example.com/legacy")


def test_repository_init_applies_schema_migrations(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db")
    repository = JobRepository(settings)

    repository.init_db()

    status = schema_status(settings.resolved_database_path)
    assert status.status == "atualizado"
    assert status.applied_versions == [1, CURRENT_SCHEMA_VERSION]


def test_schema_status_reports_outdated_database_without_control_table(tmp_path):
    db_path = tmp_path / "jobs.db"
    create_legacy_jobs_db(db_path)

    status = schema_status(db_path)

    assert status.status == "desatualizado"
    assert status.applied_versions == []


def test_schema_status_cli_outputs_expected_fields(tmp_path, capsys):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path)
    apply_schema_migrations(settings.resolved_database_path)

    result = run_schema_status(settings=settings)

    captured = capsys.readouterr()
    assert result.status == "atualizado"
    assert "Versao esperada" in captured.out
    assert "Migracoes aplicadas" in captured.out
    assert "Status: atualizado" in captured.out


def test_migrate_schema_cli_updates_legacy_database(tmp_path, capsys):
    db_path = tmp_path / "jobs.db"
    create_legacy_jobs_db(db_path)
    settings = Settings(database_path=db_path, project_root=tmp_path)

    result = run_migrate_schema(settings=settings)

    captured = capsys.readouterr()
    assert result.applied_now == [1, CURRENT_SCHEMA_VERSION]
    assert result.status == "atualizado"
    assert "Migracoes aplicadas agora" in captured.out
    assert "Status: atualizado" in captured.out


def test_migrate_schema_cli_does_not_reapply_current_database(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path)
    run_migrate_schema(settings=settings)

    result = run_migrate_schema(settings=settings)

    assert result.applied_now == []
    assert result.applied_versions == [1, CURRENT_SCHEMA_VERSION]
