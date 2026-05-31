from src.config import Settings
from src.database import JobRepository
from src.main import run_analysis_only
from src.models.job import JobListing
from src.profile_summary import ProfileSummary


def test_run_analysis_only_without_subprocess(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db")
    repository = JobRepository(settings)
    repository.init_db()
    saved = repository.save_jobs(
        [
            JobListing(
                title="Automation Engineer",
                company="Siemens",
                location="Campinas",
                source="mock",
                url="https://example.com/automation",
                description_snippet="Python, Power BI e CLP Siemens.",
                match_score=90,
                priority_company=True,
            )
        ]
    )

    count = run_analysis_only(
        settings=settings,
        profile_summary=ProfileSummary(
            core_skills=["Python", "Power BI", "CLP Siemens"],
            tools=["Python"],
            target_companies=["Siemens"],
        ),
        analysis_min_score=50,
        reanalyze=False,
    )

    analyzed_job = repository.get_job(saved[0].id)
    assert count == 1
    assert analyzed_job is not None
    assert analyzed_job.analysis is not None
