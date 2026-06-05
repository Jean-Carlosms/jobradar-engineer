import json

from src.config import Settings
from src.main import run_db_health, run_export_db_health
from src.schema_migrations import apply_schema_migrations
from src.services.database_health import DatabaseHealthService, render_database_health_markdown


def test_database_health_returns_integrity_and_schema_status(tmp_path):
    db_path = tmp_path / "jobs.db"
    apply_schema_migrations(db_path)

    health = DatabaseHealthService(tmp_path, db_path).collect()

    assert health["exists"] is True
    assert health["integrity_check"] == "ok"
    assert health["schema_status"] == "atualizado"
    assert health["schema_current_version"] == 2
    assert health["table_count"] >= 3
    assert health["index_count"] >= 10
    assert health["table_rows"]["jobs"] == 0
    assert any(index["name"] == "idx_jobs_match_score" for index in health["indexes"])


def test_database_health_handles_missing_database(tmp_path):
    health = DatabaseHealthService(tmp_path, tmp_path / "missing.db").collect()

    assert health["exists"] is False
    assert health["integrity_check"] == "missing database"
    assert health["schema_status"] == "desatualizado"
    assert health["index_count"] == 0


def test_database_health_export_creates_json_and_markdown(tmp_path):
    db_path = tmp_path / "jobs.db"
    apply_schema_migrations(db_path)

    result = DatabaseHealthService(tmp_path, db_path).export(tmp_path / "reports")

    assert result.json_path.exists()
    assert result.markdown_path.exists()
    raw = json.loads(result.json_path.read_text(encoding="utf-8"))
    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert raw["integrity_check"] == "ok"
    assert "# Database Health" in markdown
    assert "idx_jobs_match_score" in markdown


def test_database_health_markdown_handles_empty_indexes():
    markdown = render_database_health_markdown(
        {
            "database_path": "missing.db",
            "exists": False,
            "file_size": "0 B",
            "integrity_check": "missing database",
            "schema_status": "desatualizado",
            "schema_current_version": 2,
            "schema_applied_versions": [],
            "page_count": 0,
            "freelist_count": 0,
            "table_count": 0,
            "index_count": 0,
            "table_rows": {},
            "indexes": [],
        }
    )

    assert "| n/a | 0 |" in markdown
    assert "| n/a | n/a | n/a |" in markdown


def test_db_health_cli_prints_summary(tmp_path, capsys):
    db_path = tmp_path / "jobs.db"
    apply_schema_migrations(db_path)
    settings = Settings(project_root=tmp_path, database_path=db_path)

    health = run_db_health(settings=settings)

    captured = capsys.readouterr()
    assert health["integrity_check"] == "ok"
    assert "Integridade: ok" in captured.out
    assert "Schema: atualizado" in captured.out
    assert "Indices encontrados" in captured.out


def test_export_db_health_cli_creates_reports(tmp_path, capsys):
    db_path = tmp_path / "jobs.db"
    apply_schema_migrations(db_path)
    settings = Settings(project_root=tmp_path, database_path=db_path)

    result = run_export_db_health(settings=settings)

    captured = capsys.readouterr()
    assert result.json_path.exists()
    assert result.markdown_path.exists()
    assert "Saude JSON" in captured.out
    assert "Schema: atualizado" in captured.out
