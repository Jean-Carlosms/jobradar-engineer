from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_CSV = ROOT / "examples" / "sample_jobs.csv"
SAMPLE_DB = ROOT / "data" / "sample_jobs.db"
REAL_DB = ROOT / "data" / "jobs.db"


def main() -> int:
    if SAMPLE_DB == REAL_DB:
        raise RuntimeError("Refusing to write to the real jobs database.")

    rows = load_rows(SAMPLE_CSV)
    SAMPLE_DB.parent.mkdir(parents=True, exist_ok=True)
    if SAMPLE_DB.exists():
        SAMPLE_DB.unlink()

    with sqlite3.connect(SAMPLE_DB) as connection:
        create_schema(connection)
        insert_rows(connection, rows)

    print(f"Sample database created: {SAMPLE_DB}")
    print(f"Rows inserted: {len(rows)}")
    return 0


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def create_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL DEFAULT '',
            location TEXT NOT NULL DEFAULT '',
            source TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            description_snippet TEXT NOT NULL DEFAULT '',
            published_date TEXT,
            collected_at TEXT NOT NULL,
            match_score REAL NOT NULL DEFAULT 0,
            match_reason TEXT NOT NULL DEFAULT '',
            priority_company BOOLEAN NOT NULL DEFAULT 0,
            query_used TEXT NOT NULL DEFAULT '',
            already_sent BOOLEAN NOT NULL DEFAULT 0
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE job_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL UNIQUE,
            fit_level TEXT NOT NULL,
            fit_score INTEGER NOT NULL DEFAULT 0,
            matched_skills_json TEXT NOT NULL DEFAULT '[]',
            missing_skills_json TEXT NOT NULL DEFAULT '[]',
            strengths_json TEXT NOT NULL DEFAULT '[]',
            risks_json TEXT NOT NULL DEFAULT '[]',
            resume_keywords_json TEXT NOT NULL DEFAULT '[]',
            recruiter_message TEXT NOT NULL DEFAULT '',
            analysis_summary TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(job_id) REFERENCES jobs(id)
        )
        """
    )


def insert_rows(connection: sqlite3.Connection, rows: list[dict[str, str]]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for row in rows:
        cursor = connection.execute(
            """
            INSERT INTO jobs (
                title, company, location, source, url, description_snippet,
                published_date, collected_at, match_score, match_reason,
                priority_company, query_used, already_sent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["title"],
                row["company"],
                row["location"],
                row["source"],
                row["url"],
                row["description_snippet"],
                "ficticio",
                now,
                float(row["match_score"]),
                row["match_reason"],
                _to_bool_int(row["priority_company"]),
                row["query_used"],
                _to_bool_int(row["already_sent"]),
            ),
        )
        job_id = cursor.lastrowid
        matched = _keywords_from_text(row["description_snippet"])
        connection.execute(
            """
            INSERT INTO job_analyses (
                job_id, fit_level, fit_score, matched_skills_json,
                missing_skills_json, strengths_json, risks_json,
                resume_keywords_json, recruiter_message, analysis_summary,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                row["fit_level"],
                int(row["fit_score"]),
                json.dumps(matched, ensure_ascii=False),
                json.dumps(["Validar requisitos especificos da vaga"], ensure_ascii=False),
                json.dumps(["Exemplo ficticio aderente ao perfil do projeto"], ensure_ascii=False),
                json.dumps(["Dados ficticios para portfolio; validar vaga real antes de aplicar"], ensure_ascii=False),
                json.dumps(matched[:8], ensure_ascii=False),
                f"Ola! Tenho interesse na vaga ficticia de {row['title']} e experiencia alinhada ao contexto descrito.",
                row["analysis_summary"],
                now,
                now,
            ),
        )
    connection.commit()


def _to_bool_int(value: str) -> int:
    return 1 if str(value).strip().lower() in {"1", "true", "yes", "sim"} else 0


def _keywords_from_text(text: str) -> list[str]:
    candidates = [
        "Python",
        "Power BI",
        "CLP Siemens",
        "PLC",
        "redes industriais",
        "melhoria de processos",
        "Industria 4.0",
        "dados industriais",
        "dashboards",
        "documentacao tecnica",
    ]
    normalized = text.casefold()
    return [candidate for candidate in candidates if candidate.casefold() in normalized]


if __name__ == "__main__":
    raise SystemExit(main())
