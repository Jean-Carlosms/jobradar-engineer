import sqlite3

import pandas as pd

from dashboard import (
    calculate_funnel_metrics,
    calculate_metrics,
    display_column_name,
    filter_jobs,
    load_jobs,
    normalize_jobs_dataframe,
    standardize_display_columns,
    to_display_dataframe,
)


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
                    "review_status": "relevant",
                    "is_favorite": True,
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
                    "review_status": "unreviewed",
                    "is_favorite": False,
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
    assert metrics["reviewed_jobs"] == 1
    assert metrics["relevant_jobs"] == 1
    assert metrics["favorite_jobs"] == 1


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

    assert "Título" in display.columns
    assert "Empresa" in display.columns
    assert "Match Score" in display.columns
    assert "Pré-filtro" in display.columns
    assert "Revisão" in display.columns
    assert "Favorita" in display.columns
    assert "Link" in display.columns
    assert display.iloc[0]["Favorita"] == "sim"


def test_standardize_display_columns_uses_portfolio_labels():
    dataframe = pd.DataFrame(
        [
            {
                "title": "Engenheiro",
                "company": "Empresa",
                "location": "Campinas",
                "source": "mock",
                "match_score": 90,
                "fit_score": 80,
                "prefilter_score": 70,
                "review_status": "relevant",
                "is_favorite": True,
            }
        ]
    )

    display = standardize_display_columns(dataframe)

    assert display_column_name("title") == "Título"
    assert display_column_name("prefilter_score") == "Pré-filtro"
    assert {"Título", "Empresa", "Localidade", "Fonte", "Match Score", "Fit Score", "Pré-filtro", "Revisão", "Favorita"}.issubset(
        set(display.columns)
    )


def test_calculate_funnel_metrics_for_dashboard_dataframe():
    dataframe = make_dashboard_dataframe()
    dataframe.loc[0, "prefilter_score"] = 55
    dataframe.loc[0, "fit_level"] = "alto"
    dataframe.loc[0, "fit_score"] = 82

    funnel = calculate_funnel_metrics(dataframe)

    assert funnel["total_jobs"] == 2
    assert funnel["prefiltered_jobs"] == 1
    assert funnel["matched_jobs"] == 2
    assert funnel["analyzed_jobs"] == 1
    assert funnel["reviewed_jobs"] == 1
    assert funnel["favorite_jobs"] == 1


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
                review_status TEXT,
                review_notes TEXT,
                is_favorite BOOLEAN,
                viewed_at TEXT,
                reviewed_at TEXT,
                already_sent BOOLEAN
            )
            """
        )
        connection.execute(
            """
            INSERT INTO jobs (
                title, company, location, source, url, match_score,
                match_reason, priority_company, query_used, review_status,
                review_notes, is_favorite, viewed_at, reviewed_at, already_sent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                "maybe",
                "Boa vaga.",
                1,
                "2026-05-31T10:00:00",
                "2026-05-31T10:05:00",
                0,
            ),
        )

    dataframe = load_jobs(db_path)

    assert len(dataframe) == 1
    assert dataframe.iloc[0]["title"] == "Automation Engineer"
    assert bool(dataframe.iloc[0]["priority_company"]) is True
    assert dataframe.iloc[0]["review_status"] == "maybe"
    assert bool(dataframe.iloc[0]["is_favorite"]) is True
