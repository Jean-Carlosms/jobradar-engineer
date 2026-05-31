from src.config import Settings
from src.database import JobRepository
from src.models.job import JobListing
from src.profile_summary import ProfileSummary
from src.services.job_profile_analyzer import JobProfileAnalyzer


def test_upsert_analysis_creates_and_updates_database_row(tmp_path):
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
                description_snippet="Python, CLP Siemens e Power BI.",
                match_score=85,
                priority_company=True,
            )
        ]
    )
    analyzer = JobProfileAnalyzer(
        ProfileSummary(
            core_skills=["Python", "CLP Siemens", "Power BI", "robotica"],
            tools=["Python"],
            target_companies=["Siemens"],
        )
    )

    first = repository.upsert_analysis(saved[0].id, analyzer.analyze(saved[0]))
    second = repository.upsert_analysis(saved[0].id, analyzer.analyze(saved[0]))
    jobs_for_analysis = repository.get_jobs_for_analysis(min_score=50, only_without_analysis=True)
    analyzed_job = repository.get_job(saved[0].id)

    assert first.id == second.id
    assert jobs_for_analysis == []
    assert analyzed_job is not None
    assert analyzed_job.analysis is not None
    assert analyzed_job.analysis.fit_score > 0
