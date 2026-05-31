import sqlite3

import pandas as pd

from dashboard import calculate_metrics, filter_jobs, load_jobs, normalize_jobs_dataframe, to_display_dataframe


def make_dashboard_dataframe() -> pd.DataFrame:
    return normalize_jobs_dataframe(
        pd.DataFrame(
            [
                {
                    "title": "Engenheiro de Automacao",
                    "company": "Siemens",
                    "location": "Campinas",
                    "source": "mock",
                    "url": "https://example.com/1",
                    "match_score": 88,
                    "match_reason": "Alta aderencia por conter Python e CLP.",
                    "priority_company": True,
                    "query_used": "mock",
                    "already_sent": True,
                },
                {
                    "title": "Analista de Projetos",
                    "company": "ACME",
                    "location": "Sorocaba",
                    "source": "search",
                    "url": "https://example.com/2",
                    "match_score": 42,
                    "match_reason": "Aderencia media por conter planejamento.",
                    "priority_company": False,
                    "query_used": "site:infojobs.com.br",
                    "already_sent": False,
                },
            ]
        )
    )


def test_calculate_metrics_for_dashboard_dataframe():
    metrics = calculate_metrics(make_dashboard_dataframe())

    assert metrics["total_jobs"] == 2
    assert metrics["sent_jobs"] == 1
    assert metrics["unsent_jobs"] == 1
    assert metrics["max_score"] == 88
    assert metrics["priority_companies"] == 1


def test_filter_jobs_applies_score_status_priority_and_text():
    dataframe = make_dashboard_dataframe()

    filtered = filter_jobs(
        dataframe,
        min_score=50,
        sent_status="Enviadas",
        priority_only=True,
        text_search="python",
    )

    assert len(filtered) == 1
    assert filtered.iloc[0]["company"] == "Siemens"


def test_to_display_dataframe_uses_expected_columns():
    display = to_display_dataframe(make_dashboard_dataframe())

    assert "motivo de aderencia" in display.columns
    assert "link" in display.columns
    assert display.iloc[0]["empresa prioritaria"] == "sim"


def test_load_jobs_reads_sqlite_database(tmp_path):
    db_path = tmp_path / "jobs.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE jobs (
                id INTEGER PRIMARY KEY,
                title TEXT,
                company TEXT,
                location TEXT,
                source TEXT,
                url TEXT,
                match_score REAL,
                match_reason TEXT,
                priority_company BOOLEAN,
                query_used TEXT,
                already_sent BOOLEAN
            )
            """
        )
        connection.execute(
            """
            INSERT INTO jobs (
                title, company, location, source, url, match_score,
                match_reason, priority_company, query_used, already_sent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "Automation Engineer",
                "Siemens",
                "Campinas",
                "mock",
                "https://example.com/job",
                90,
                "Alta aderencia por conter PLC.",
                1,
                "mock",
                0,
            ),
        )

    dataframe = load_jobs(db_path)

    assert len(dataframe) == 1
    assert dataframe.iloc[0]["title"] == "Automation Engineer"
    assert bool(dataframe.iloc[0]["priority_company"]) is True
