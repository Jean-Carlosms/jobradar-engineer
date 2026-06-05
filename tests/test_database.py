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
                prefilter_score=42,
                prefilter_reason="manter e enriquecer: termos tecnicos no titulo.",
            )
        ]
    )

    first_batch = repository.get_unsent_jobs(min_score=50, limit=10)
    repository.mark_jobs_sent([saved[0].id])
    second_batch = repository.get_unsent_jobs(min_score=50, limit=10)

    assert len(first_batch) == 1
    assert first_batch[0].prefilter_score == 42
    assert "termos tecnicos" in first_batch[0].prefilter_reason
    assert second_batch == []


def test_save_jobs_updates_existing_metadata_by_url(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db")
    repository = JobRepository(settings)
    repository.init_db()
    repository.save_jobs(
        [
            JobListing(
                title="Titulo antigo",
                company="Empresa antiga",
                location="Local antigo",
                source="old",
                url="https://example.com/job",
                match_score=10,
            )
        ]
    )

    saved = repository.save_jobs(
        [
            JobListing(
                title="Titulo novo",
                company="Empresa nova",
                location="Sorocaba - SP",
                source="new",
                url="https://example.com/job",
                match_score=20,
            )
        ]
    )

    assert len(saved) == 1
    assert saved[0].title == "Titulo novo"
    assert saved[0].company == "Empresa nova"
    assert saved[0].location == "Sorocaba - SP"


def test_repository_close_disposes_engine(tmp_path, monkeypatch):
    settings = Settings(database_path=tmp_path / "jobs.db")
    repository = JobRepository(settings)
    disposed = False

    def fake_dispose() -> None:
        nonlocal disposed
        disposed = True

    monkeypatch.setattr(repository.engine, "dispose", fake_dispose)

    repository.close()

    assert disposed is True
