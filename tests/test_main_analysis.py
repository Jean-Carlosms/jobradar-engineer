from src.config import Settings
from src.database import JobRepository
from src.main import build_sources, run_analysis_only, run_export_review_feedback, run_once, run_review_summary
from src.sources.gupy_source import GupyPublicSource, MockGupySource
from src.sources.search_engine_source import SearchEngineSource
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


def test_run_once_dry_run_does_not_mark_jobs_as_sent(tmp_path):
    settings = Settings(database_path=tmp_path / "jobs.db", email_dry_run=True)

    count = run_once(
        settings=settings,
        source="mock",
        min_score=0,
        email_dry_run=True,
        analyze=False,
    )

    repository = JobRepository(settings)
    unsent_jobs = repository.get_unsent_jobs(min_score=0, limit=10)

    assert count == 3
    assert len(unsent_jobs) == 3
    assert all(job.already_sent is False for job in unsent_jobs)


def test_build_sources_passes_debug_search_to_search_source(tmp_path):
    settings = Settings(project_root=tmp_path)

    sources = build_sources(settings, "search", debug_search=True)

    assert len(sources) == 1
    assert isinstance(sources[0], SearchEngineSource)
    assert sources[0].debug_search is True


def test_build_sources_supports_gupy_source(tmp_path):
    settings = Settings(project_root=tmp_path)

    sources = build_sources(settings, "gupy", debug_search=True)

    assert len(sources) == 1
    assert isinstance(sources[0], GupyPublicSource)
    assert sources[0].debug_search is True


def test_build_sources_all_excludes_mock_by_default_and_can_include_it(tmp_path):
    settings = Settings(project_root=tmp_path)

    default_sources = build_sources(settings, "all")
    with_mock_sources = build_sources(settings, "all", include_mock_in_all=True)

    assert [type(source) for source in default_sources] == [GupyPublicSource, SearchEngineSource]
    assert any(isinstance(source, MockGupySource) for source in with_mock_sources)


def test_run_review_summary_outputs_statuses(tmp_path, capsys):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path)
    repository = JobRepository(settings)
    repository.init_db()
    repository.save_jobs(
        [
            JobListing(
                title="Automation Engineer",
                company="Siemens",
                location="Campinas",
                source="mock",
                url="https://example.com/review-summary",
                match_score=90,
            )
        ]
    )

    summary = run_review_summary(settings=settings)

    captured = capsys.readouterr()
    assert "Total de vagas: 1" in summary
    assert "unreviewed: 1" in captured.out


def test_run_export_review_feedback_creates_report(tmp_path, capsys):
    settings = Settings(database_path=tmp_path / "jobs.db", project_root=tmp_path)
    repository = JobRepository(settings)
    repository.init_db()
    repository.save_jobs(
        [
            JobListing(
                title="Automation Engineer",
                company="Siemens",
                location="Campinas",
                source="mock",
                url="https://example.com/review-export",
                match_score=90,
            )
        ]
    )

    result = run_export_review_feedback(settings=settings)

    captured = capsys.readouterr()
    assert result.path.exists()
    assert result.row_count == 1
    assert "Feedback exportado" in captured.out
