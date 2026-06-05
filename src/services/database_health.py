from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.schema_migrations import CURRENT_SCHEMA_VERSION, schema_status
from src.services.database_maintenance import format_backup_size


MAIN_TABLES = ["jobs", "job_analyses", "schema_migrations"]


@dataclass(frozen=True)
class DatabaseHealthExportResult:
    json_path: Path
    markdown_path: Path
    health: dict[str, Any]


class DatabaseHealthService:
    def __init__(self, project_root: str | Path = ".", database_path: str | Path = "data/jobs.db") -> None:
        self.project_root = Path(project_root)
        db_path = Path(database_path)
        self.database_path = db_path if db_path.is_absolute() else self.project_root / db_path

    def collect(self) -> dict[str, Any]:
        status = schema_status(self.database_path)
        base = {
            "database_path": str(self.database_path),
            "exists": self.database_path.exists(),
            "file_size_bytes": self.database_path.stat().st_size if self.database_path.exists() else 0,
            "file_size": format_backup_size(self.database_path.stat().st_size) if self.database_path.exists() else "0 B",
            "schema_current_version": CURRENT_SCHEMA_VERSION,
            "schema_applied_versions": status.applied_versions,
            "schema_status": status.status,
            "integrity_check": "missing database",
            "page_count": 0,
            "freelist_count": 0,
            "table_count": 0,
            "index_count": 0,
            "table_rows": {},
            "indexes": [],
        }
        if not self.database_path.exists():
            return base

        with closing(sqlite3.connect(self.database_path)) as conn:
            tables = _list_tables(conn)
            indexes = _list_indexes(conn)
            base.update(
                {
                    "integrity_check": _pragma_value(conn, "integrity_check"),
                    "page_count": int(_pragma_value(conn, "page_count") or 0),
                    "freelist_count": int(_pragma_value(conn, "freelist_count") or 0),
                    "table_count": len(tables),
                    "index_count": len(indexes),
                    "table_rows": {table: _count_rows(conn, table) for table in MAIN_TABLES if table in tables},
                    "indexes": indexes,
                }
            )
        return base

    def export(self, reports_dir: str | Path | None = None) -> DatabaseHealthExportResult:
        health = self.collect()
        output_dir = Path(reports_dir) if reports_dir else self.project_root / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = f"db_health_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        json_path = output_dir / f"{base_name}.json"
        markdown_path = output_dir / f"{base_name}.md"

        json_path.write_text(json.dumps(health, ensure_ascii=False, indent=2), encoding="utf-8")
        markdown_path.write_text(render_database_health_markdown(health), encoding="utf-8")
        return DatabaseHealthExportResult(json_path=json_path, markdown_path=markdown_path, health=health)


def render_database_health_markdown(health: dict[str, Any]) -> str:
    lines = [
        "# Database Health",
        "",
        "## Resumo",
        "",
        f"- Banco: `{health['database_path']}`",
        f"- Existe: `{'sim' if health['exists'] else 'nao'}`",
        f"- Tamanho: `{health['file_size']}`",
        f"- Integridade: `{health['integrity_check']}`",
        f"- Schema: `{health['schema_status']}`",
        f"- Versao esperada: `{health['schema_current_version']}`",
        f"- Versoes aplicadas: `{health['schema_applied_versions']}`",
        f"- Page count: `{health['page_count']}`",
        f"- Freelist count: `{health['freelist_count']}`",
        f"- Tabelas: `{health['table_count']}`",
        f"- Indices: `{health['index_count']}`",
        "",
        "## Linhas por tabela",
        "",
        "| Tabela | Linhas |",
        "| --- | ---: |",
    ]
    table_rows = health.get("table_rows") or {}
    if table_rows:
        for table_name, row_count in table_rows.items():
            lines.append(f"| {table_name} | {row_count} |")
    else:
        lines.append("| n/a | 0 |")

    lines.extend(["", "## Indices", "", "| Nome | Tabela | Colunas |", "| --- | --- | --- |"])
    indexes = health.get("indexes") or []
    if indexes:
        for index in indexes:
            columns = ", ".join(index.get("columns") or [])
            lines.append(f"| {index['name']} | {index['table']} | {columns} |")
    else:
        lines.append("| n/a | n/a | n/a |")
    return "\n".join(lines)


def _list_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    return [str(row[0]) for row in rows]


def _list_indexes(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT name, tbl_name
        FROM sqlite_master
        WHERE type='index'
        ORDER BY tbl_name, name
        """
    ).fetchall()
    indexes = []
    for name, table in rows:
        indexes.append({"name": str(name), "table": str(table), "columns": _index_columns(conn, str(name))})
    return indexes


def _index_columns(conn: sqlite3.Connection, index_name: str) -> list[str]:
    rows = conn.execute(f"PRAGMA index_info({index_name})").fetchall()
    return [str(row[2]) for row in rows if row[2] is not None]


def _count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(row[0] or 0)


def _pragma_value(conn: sqlite3.Connection, pragma_name: str) -> Any:
    row = conn.execute(f"PRAGMA {pragma_name}").fetchone()
    return row[0] if row else None
