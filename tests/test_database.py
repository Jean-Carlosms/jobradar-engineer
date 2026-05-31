from src.config import Settings
from src.database import JobRepository
from src.models.job import JobListing


def test_already_sent_job_is_not_returned_again(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db")
    repository = JobRepository(settings)
    repository.init_db()
    saved = repository.save_jobs(
        [
            JobListing(
                title="Engenheiro de Automacao",
                company="Siemens",
                location="Campinas",
                source="mock",
                url="https://example.com/job",
                match_score=80,
                match_reason="Alta aderencia por conter Python e CLP.",
                priority_company=True,
                query_used="mock",
            )
        ]
    )

    first_batch = repository.get_unsent_jobs(min_score=50, limit=10)
    repository.mark_jobs_sent([saved[0].id])
    second_batch = repository.get_unsent_jobs(min_score=50, limit=10)

    assert len(first_batch) == 1
    assert second_batch == []
