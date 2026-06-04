import csv

from sqlalchemy import inspect

from src.config import Settings
from src.database import JobRepository
from src.models.job import JobListing
from src.services.job_review_service import JobReviewService


def make_repository(tmp_path) -> JobRepository:
    repository = JobRepository(Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path))
    repository.init_db()
    return repository


def seed_job(repository: JobRepository):
    return repository.save_jobs(
        [
            JobListing(
                title="Engenheiro de Automacao",
                company="Siemens",
                location="Campinas",
                source="mock",
                url="https://example.com/automation",
                match_score=90,
                prefilter_score=60,
            )
        ]
    )[0]


def test_review_columns_are_migrated(tmp_path):
    repository = make_repository(tmp_path)
    columns = {column["name"] for column in inspect(repository.engine).get_columns("jobs")}

    assert {"review_status", "review_notes", "is_favorite", "viewed_at", "reviewed_at"}.issubset(columns)


def test_review_service_marks_job_as_relevant(tmp_path):
    repository = make_repository(tmp_path)
    job = seed_job(repository)

    updated = JobReviewService(repository).update_review(job.id, "relevant")

    assert updated is not None
    fetched = repository.get_job(job.id)
    assert fetched.review_status == "relevant"
    assert fetched.reviewed_at is not None
    assert fetched.viewed_at is not None


def test_review_service_marks_favorite(tmp_path):
    repository = make_repository(tmp_path)
    job = seed_job(repository)

    JobReviewService(repository).set_favorite(job.id, True)

    assert repository.get_job(job.id).is_favorite is True


def test_review_service_saves_notes(tmp_path):
    repository = make_repository(tmp_path)
    job = seed_job(repository)

    JobReviewService(repository).save_notes(job.id, "Boa vaga para automacao.")

    assert repository.get_job(job.id).review_notes == "Boa vaga para automacao."


def test_review_service_summary_by_status(tmp_path):
    repository = make_repository(tmp_path)
    job = seed_job(repository)
    service = JobReviewService(repository)
    service.update_review(job.id, "relevant", review_notes="Muito aderente.")
    second = repository.save_jobs(
        [
            JobListing(
                title="Vendedor",
                company="Loja",
                location="Sao Paulo",
                source="mock",
                url="https://example.com/sales",
                match_score=0,
            )
        ]
    )[0]
    service.update_review(second.id, "irrelevant", review_notes="Vaga comercial.")

    summary = service.summarize_feedback()

    assert summary.total_jobs == 2
    assert summary.status_counts["relevant"] == 1
    assert summary.status_counts["irrelevant"] == 1
    assert summary.top_relevant_companies[0] == ("Siemens", 1)
    assert summary.top_irrelevance_reasons[0][0] == "Vaga comercial"


def test_review_service_exports_feedback_csv(tmp_path):
    repository = make_repository(tmp_path)
    job = seed_job(repository)
    service = JobReviewService(repository)
    service.update_review(job.id, "maybe", review_notes="Revisar requisitos.", is_favorite=True)

    result = service.export_feedback_csv(tmp_path / "reports")

    assert result.path.exists()
    assert result.row_count == 1
    with result.path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows[0]["title"] == "Engenheiro de Automacao"
    assert rows[0]["review_status"] == "maybe"
    assert rows[0]["is_favorite"] == "True"
