from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CURRENT_SCHEMA_VERSION = 2
INITIAL_MIGRATION_NAME = "initial_local_schema"
INDEX_MIGRATION_NAME = "performance_indexes"


@dataclass(frozen=True)
class SchemaMigrationResult:
    db_path: Path
    current_version: int
    applied_versions: list[int]
    applied_now: list[int]

    @property
    def is_current(self) -> bool:
        return self.latest_applied_version >= self.current_version

    @property
    def latest_applied_version(self) -> int:
        return max(self.applied_versions, default=0)

    @property
    def status(self) -> str:
        return "atualizado" if self.is_current else "desatualizado"


def get_applied_migrations(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    _ensure_migration_table(conn)
    rows = conn.execute(
        """
        SELECT id, version, name, applied_at
        FROM schema_migrations
        ORDER BY version ASC, id ASC
        """
    ).fetchall()
    return [
        {
            "id": row[0],
            "version": row[1],
            "name": row[2],
            "applied_at": row[3],
        }
        for row in rows
    ]


def apply_schema_migrations(db_path: str | Path) -> SchemaMigrationResult:
    resolved_path = Path(db_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(resolved_path)) as conn:
        _ensure_migration_table(conn)
        applied_before = _applied_versions(conn)
        applied_now: list[int] = []

        if 1 not in applied_before:
            _apply_initial_schema(conn)
            _record_migration(conn, 1, INITIAL_MIGRATION_NAME)
            applied_now.append(1)
        else:
            _apply_initial_schema(conn)

        applied_after_initial = _applied_versions(conn)
        if 2 not in applied_after_initial:
            _apply_performance_indexes(conn)
            _record_migration(conn, 2, INDEX_MIGRATION_NAME)
            applied_now.append(2)
        else:
            _apply_performance_indexes(conn)

        conn.commit()
        applied_after = _applied_versions(conn)

    return SchemaMigrationResult(
        db_path=resolved_path,
        current_version=CURRENT_SCHEMA_VERSION,
        applied_versions=applied_after,
        applied_now=applied_now,
    )


def schema_status(db_path: str | Path) -> SchemaMigrationResult:
    resolved_path = Path(db_path)
    if not resolved_path.exists():
        return SchemaMigrationResult(
            db_path=resolved_path,
            current_version=CURRENT_SCHEMA_VERSION,
            applied_versions=[],
            applied_now=[],
        )

    with closing(sqlite3.connect(resolved_path)) as conn:
        applied = _applied_versions(conn) if _table_exists(conn, "schema_migrations") else []
    return SchemaMigrationResult(
        db_path=resolved_path,
        current_version=CURRENT_SCHEMA_VERSION,
        applied_versions=applied,
        applied_now=[],
    )


def _ensure_migration_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version INTEGER NOT NULL UNIQUE,
            name TEXT NOT NULL,
            applied_at TEXT NOT NULL
        )
        """
    )


def _apply_initial_schema(conn: sqlite3.Connection) -> None:
    _ensure_jobs_table(conn)
    _ensure_job_analyses_table(conn)
    _ensure_jobs_columns(conn)
    _ensure_job_analyses_columns(conn)
    _copy_legacy_match_reasons(conn)


def _apply_performance_indexes(conn: sqlite3.Connection) -> None:
    _create_index_if_columns_exist(conn, "idx_jobs_url", "jobs", ["url"], unique=True)
    _create_index_if_columns_exist(conn, "idx_jobs_title", "jobs", ["title"])
    _create_index_if_columns_exist(conn, "idx_jobs_company", "jobs", ["company"])
    _create_index_if_columns_exist(conn, "idx_jobs_source", "jobs", ["source"])
    _create_index_if_columns_exist(conn, "idx_jobs_match_score", "jobs", ["match_score"])
    _create_index_if_columns_exist(conn, "idx_jobs_prefilter_score", "jobs", ["prefilter_score"])
    _create_index_if_columns_exist(conn, "idx_jobs_review_status", "jobs", ["review_status"])
    _create_index_if_columns_exist(conn, "idx_jobs_is_favorite", "jobs", ["is_favorite"])
    _create_index_if_columns_exist(conn, "idx_jobs_already_sent", "jobs", ["already_sent"])
    _create_index_if_columns_exist(conn, "idx_jobs_collected_at", "jobs", ["collected_at"])
    _create_index_if_columns_exist(conn, "idx_jobs_created_at", "jobs", ["created_at"])
    _create_index_if_columns_exist(conn, "idx_job_analyses_job_id", "job_analyses", ["job_id"], unique=True)
    _create_index_if_columns_exist(conn, "idx_schema_migrations_version", "schema_migrations", ["version"], unique=True)


def _ensure_jobs_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(300) NOT NULL,
            company VARCHAR(200) NOT NULL DEFAULT '',
            location VARCHAR(200) NOT NULL DEFAULT '',
            source VARCHAR(80) NOT NULL,
            url VARCHAR(1000) NOT NULL UNIQUE,
            description_snippet TEXT NOT NULL DEFAULT '',
            published_date VARCHAR(80),
            collected_at DATETIME NOT NULL,
            match_score FLOAT NOT NULL DEFAULT 0,
            match_reason TEXT NOT NULL DEFAULT '',
            priority_company BOOLEAN NOT NULL DEFAULT 0,
            query_used TEXT NOT NULL DEFAULT '',
            prefilter_score FLOAT NOT NULL DEFAULT 0,
            prefilter_reason TEXT NOT NULL DEFAULT '',
            review_status VARCHAR(30) NOT NULL DEFAULT 'unreviewed',
            review_notes TEXT NOT NULL DEFAULT '',
            is_favorite BOOLEAN NOT NULL DEFAULT 0,
            viewed_at DATETIME,
            reviewed_at DATETIME,
            already_sent BOOLEAN NOT NULL DEFAULT 0,
            UNIQUE (title, company, location)
        )
        """
    )


def _ensure_job_analyses_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL UNIQUE,
            fit_level VARCHAR(20) NOT NULL,
            fit_score INTEGER NOT NULL DEFAULT 0,
            matched_skills_json TEXT NOT NULL DEFAULT '[]',
            missing_skills_json TEXT NOT NULL DEFAULT '[]',
            strengths_json TEXT NOT NULL DEFAULT '[]',
            risks_json TEXT NOT NULL DEFAULT '[]',
            resume_keywords_json TEXT NOT NULL DEFAULT '[]',
            recruiter_message TEXT NOT NULL DEFAULT '',
            analysis_summary TEXT NOT NULL DEFAULT '',
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY(job_id) REFERENCES jobs (id)
        )
        """
    )
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_job_analyses_job_id ON job_analyses (job_id)")


def _ensure_jobs_columns(conn: sqlite3.Connection) -> None:
    columns = _column_names(conn, "jobs")
    migrations = {
        "company": "ALTER TABLE jobs ADD COLUMN company VARCHAR(200) NOT NULL DEFAULT ''",
        "location": "ALTER TABLE jobs ADD COLUMN location VARCHAR(200) NOT NULL DEFAULT ''",
        "description_snippet": "ALTER TABLE jobs ADD COLUMN description_snippet TEXT NOT NULL DEFAULT ''",
        "published_date": "ALTER TABLE jobs ADD COLUMN published_date VARCHAR(80)",
        "collected_at": "ALTER TABLE jobs ADD COLUMN collected_at DATETIME",
        "match_score": "ALTER TABLE jobs ADD COLUMN match_score FLOAT NOT NULL DEFAULT 0",
        "match_reason": "ALTER TABLE jobs ADD COLUMN match_reason TEXT NOT NULL DEFAULT ''",
        "priority_company": "ALTER TABLE jobs ADD COLUMN priority_company BOOLEAN NOT NULL DEFAULT 0",
        "query_used": "ALTER TABLE jobs ADD COLUMN query_used TEXT NOT NULL DEFAULT ''",
        "prefilter_score": "ALTER TABLE jobs ADD COLUMN prefilter_score FLOAT NOT NULL DEFAULT 0",
        "prefilter_reason": "ALTER TABLE jobs ADD COLUMN prefilter_reason TEXT NOT NULL DEFAULT ''",
        "review_status": "ALTER TABLE jobs ADD COLUMN review_status VARCHAR(30) NOT NULL DEFAULT 'unreviewed'",
        "review_notes": "ALTER TABLE jobs ADD COLUMN review_notes TEXT NOT NULL DEFAULT ''",
        "is_favorite": "ALTER TABLE jobs ADD COLUMN is_favorite BOOLEAN NOT NULL DEFAULT 0",
        "viewed_at": "ALTER TABLE jobs ADD COLUMN viewed_at DATETIME",
        "reviewed_at": "ALTER TABLE jobs ADD COLUMN reviewed_at DATETIME",
        "already_sent": "ALTER TABLE jobs ADD COLUMN already_sent BOOLEAN NOT NULL DEFAULT 0",
    }
    for column_name, statement in migrations.items():
        if column_name not in columns:
            conn.execute(statement)


def _ensure_job_analyses_columns(conn: sqlite3.Connection) -> None:
    columns = _column_names(conn, "job_analyses")
    migrations = {
        "fit_level": "ALTER TABLE job_analyses ADD COLUMN fit_level VARCHAR(20) NOT NULL DEFAULT ''",
        "fit_score": "ALTER TABLE job_analyses ADD COLUMN fit_score INTEGER NOT NULL DEFAULT 0",
        "matched_skills_json": "ALTER TABLE job_analyses ADD COLUMN matched_skills_json TEXT NOT NULL DEFAULT '[]'",
        "missing_skills_json": "ALTER TABLE job_analyses ADD COLUMN missing_skills_json TEXT NOT NULL DEFAULT '[]'",
        "strengths_json": "ALTER TABLE job_analyses ADD COLUMN strengths_json TEXT NOT NULL DEFAULT '[]'",
        "risks_json": "ALTER TABLE job_analyses ADD COLUMN risks_json TEXT NOT NULL DEFAULT '[]'",
        "resume_keywords_json": "ALTER TABLE job_analyses ADD COLUMN resume_keywords_json TEXT NOT NULL DEFAULT '[]'",
        "recruiter_message": "ALTER TABLE job_analyses ADD COLUMN recruiter_message TEXT NOT NULL DEFAULT ''",
        "analysis_summary": "ALTER TABLE job_analyses ADD COLUMN analysis_summary TEXT NOT NULL DEFAULT ''",
        "created_at": "ALTER TABLE job_analyses ADD COLUMN created_at DATETIME",
        "updated_at": "ALTER TABLE job_analyses ADD COLUMN updated_at DATETIME",
    }
    for column_name, statement in migrations.items():
        if column_name not in columns:
            conn.execute(statement)


def _copy_legacy_match_reasons(conn: sqlite3.Connection) -> None:
    columns = _column_names(conn, "jobs")
    if "match_reasons" in columns and "match_reason" in columns:
        conn.execute("UPDATE jobs SET match_reason = match_reasons WHERE match_reason = ''")


def _record_migration(conn: sqlite3.Connection, version: int, name: str) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO schema_migrations (version, name, applied_at)
        VALUES (?, ?, ?)
        """,
        (version, name, datetime.now(timezone.utc).isoformat()),
    )


def _applied_versions(conn: sqlite3.Connection) -> list[int]:
    if not _table_exists(conn, "schema_migrations"):
        return []
    rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version ASC").fetchall()
    return [int(row[0]) for row in rows]


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _column_names(conn: sqlite3.Connection, table_name: str) -> set[str]:
    if not _table_exists(conn, table_name):
        return set()
    return {str(row[1]) for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()}


def _create_index_if_columns_exist(
    conn: sqlite3.Connection,
    index_name: str,
    table_name: str,
    columns: list[str],
    unique: bool = False,
) -> None:
    available_columns = _column_names(conn, table_name)
    if not available_columns or not set(columns).issubset(available_columns):
        return
    unique_sql = "UNIQUE " if unique else ""
    quoted_columns = ", ".join(columns)
    conn.execute(f"CREATE {unique_sql}INDEX IF NOT EXISTS {index_name} ON {table_name} ({quoted_columns})")
