import csv

from src.config import Settings
from src import main as main_module
from src.database import JobRepository
from src.main import run_feedback_insights
from src.models.job import JobListing
from src.profile import ProfileConfig
from src.profile_summary import ProfileSummary
from src.services.feedback_insights import FeedbackInsightsService
from src.services.job_review_service import JobReviewService


def make_repository(tmp_path) -> JobRepository:
    repository = JobRepository(Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path))
    repository.init_db()
    return repository


def seed_reviewed_job(
    repository: JobRepository,
    title: str,
    company: str,
    status: str,
    score: float,
    url_slug: str,
    description: str = "",
    location: str = "Campinas",
    favorite: bool = False,
):
    job = repository.save_jobs(
        [
            JobListing(
                title=title,
                company=company,
                location=location,
                source="mock",
                url=f"https://example.com/{url_slug}",
                description_snippet=description,
                match_score=score,
            )
        ]
    )[0]
    JobReviewService(repository).update_review(job.id, status, is_favorite=favorite)
    return repository.get_job(job.id)


def insight_candidates(result, insight_type: str) -> list[str]:
    return [insight.candidate for insight in result.insights if insight.insight_type == insight_type]


def test_feedback_insights_with_few_reviews_warns_low_confidence(tmp_path):
    repository = make_repository(tmp_path)
    seed_reviewed_job(repository, "Engenheiro Python", "Siemens", "relevant", 80, "python")

    result = FeedbackInsightsService(repository).generate(tmp_path / "reports", min_reviewed=5)

    assert result.low_confidence is True
    assert "Aviso de baixa confianca" in result.markdown_path.read_text(encoding="utf-8")


def test_feedback_insights_suggests_positive_terms_from_relevant_jobs(tmp_path):
    repository = make_repository(tmp_path)
    seed_reviewed_job(
        repository,
        "Engenheiro de Automacao Python",
        "Siemens",
        "relevant",
        82,
        "positive-1",
        "CLP Siemens e Power BI industrial.",
    )

    result = FeedbackInsightsService(repository).generate(tmp_path / "reports", min_reviewed=1)

    assert "python" in insight_candidates(result, "positive_term_candidate")
    assert "automacao" in insight_candidates(result, "positive_term_candidate")


def test_feedback_insights_suggests_negative_terms_from_irrelevant_jobs(tmp_path):
    repository = make_repository(tmp_path)
    seed_reviewed_job(
        repository,
        "Vendedor Comercial",
        "Loja Exemplo",
        "irrelevant",
        72,
        "negative-1",
        "Vendas externas e prospeccao comercial.",
    )

    result = FeedbackInsightsService(repository).generate(tmp_path / "reports", min_reviewed=1)

    assert "vendedor" in insight_candidates(result, "negative_term_candidate")
    assert "vendas" in insight_candidates(result, "negative_term_candidate")


def test_feedback_insights_prioritizes_company_with_high_relevant_ratio(tmp_path):
    repository = make_repository(tmp_path)
    seed_reviewed_job(repository, "Automation Engineer", "Siemens", "relevant", 88, "siemens-1")
    seed_reviewed_job(repository, "Engenheiro de Automacao", "Siemens", "relevant", 84, "siemens-2")
    seed_reviewed_job(repository, "Vendedor", "Loja", "irrelevant", 10, "loja")

    result = FeedbackInsightsService(repository).generate(tmp_path / "reports", min_reviewed=1)

    assert "Siemens" in insight_candidates(result, "priority_company_candidate")


def test_feedback_insights_detects_false_positive(tmp_path):
    repository = make_repository(tmp_path)
    seed_reviewed_job(repository, "Vendedor Tecnico", "Comercial", "irrelevant", 92, "false-positive")

    result = FeedbackInsightsService(repository).generate(tmp_path / "reports", min_reviewed=1)

    assert "Vendedor Tecnico" in insight_candidates(result, "false_positive")


def test_feedback_insights_detects_false_negative(tmp_path):
    repository = make_repository(tmp_path)
    seed_reviewed_job(repository, "Projetista de Automacao", "Facens", "relevant", 25, "false-negative")

    result = FeedbackInsightsService(repository).generate(tmp_path / "reports", min_reviewed=1)

    assert "Projetista de Automacao" in insight_candidates(result, "false_negative")


def test_feedback_insights_generates_markdown(tmp_path):
    repository = make_repository(tmp_path)
    seed_reviewed_job(repository, "Engenheiro Python", "Siemens", "relevant", 80, "markdown")

    result = FeedbackInsightsService(repository).generate(tmp_path / "reports", min_reviewed=1)
    markdown = result.markdown_path.read_text(encoding="utf-8")

    assert result.markdown_path.exists()
    assert "Resumo executivo" in markdown
    assert "Termos candidatos a positivos" in markdown
    assert "Recomendacoes para profile_keywords.yaml" in markdown
    assert "nao altera `profile_keywords.yaml` automaticamente" in markdown


def test_feedback_insights_generates_csv(tmp_path):
    repository = make_repository(tmp_path)
    seed_reviewed_job(repository, "Engenheiro Python", "Siemens", "relevant", 80, "csv")

    result = FeedbackInsightsService(repository).generate(tmp_path / "reports", min_reviewed=1)

    assert result.csv_path.exists()
    with result.csv_path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert {"insight_type", "candidate", "count", "evidence", "recommendation", "confidence"}.issubset(
        rows[0].keys()
    )
    assert any(row["candidate"] == "python" for row in rows)


def test_run_feedback_insights_cli_helper_creates_reports(tmp_path, capsys):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path)
    repository = JobRepository(settings)
    repository.init_db()
    seed_reviewed_job(repository, "Engenheiro Python", "Siemens", "relevant", 80, "cli")

    result = run_feedback_insights(settings=settings, min_reviewed=1)

    captured = capsys.readouterr()
    assert result.markdown_path.exists()
    assert result.csv_path.exists()
    assert "Insights de feedback gerados" in captured.out


def test_feedback_insights_cli_argument_creates_reports(tmp_path, monkeypatch, capsys):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path)
    repository = JobRepository(settings)
    repository.init_db()
    seed_reviewed_job(repository, "Engenheiro Python", "Siemens", "relevant", 80, "cli-argument")
    monkeypatch.setattr(main_module, "load_settings", lambda: settings)
    monkeypatch.setattr(main_module, "load_profile", lambda path: ProfileConfig())
    monkeypatch.setattr(main_module, "load_profile_summary", lambda path: ProfileSummary())
    monkeypatch.setattr(
        "sys.argv",
        ["python -m src.main", "--feedback-insights", "--feedback-insights-min-reviewed", "1"],
    )

    main_module.main()

    captured = capsys.readouterr()
    assert "Insights de feedback gerados" in captured.out
    assert list((tmp_path / "reports").glob("feedback_insights_*.md"))
    assert list((tmp_path / "reports").glob("feedback_insights_*.csv"))
