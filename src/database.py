from __future__ import annotations

import json

from sqlalchemy import and_, create_engine, or_, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from src.config import Settings
from src.models.job import Base, Job, JobAnalysis, JobListing, utc_now
from src.schema_migrations import apply_schema_migrations
from src.services.job_profile_analyzer import JobProfileAnalysis


class JobRepository:
    def __init__(self, settings: Settings) -> None:
        db_path = settings.resolved_database_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path.as_posix()}", future=True, poolclass=NullPool)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False, future=True)

    def close(self) -> None:
        self.engine.dispose()

    def __enter__(self) -> JobRepository:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def init_db(self) -> None:
        Base.metadata.create_all(self.engine)
        apply_schema_migrations(self.db_path)

    def save_jobs(self, listings: list[JobListing]) -> list[Job]:
        saved: list[Job] = []
        with self.session_factory() as session:
            for listing in listings:
                existing = self._find_existing(session, listing)
                if existing:
                    self._update_existing(existing, listing)
                    saved.append(existing)
                else:
                    job = Job(
                        title=listing.title,
                        company=listing.company,
                        location=listing.location,
                        source=listing.source,
                        url=listing.url,
                        description_snippet=listing.description_snippet,
                        published_date=listing.published_date,
                        collected_at=listing.collected_at,
                        match_score=listing.match_score,
                        match_reason=listing.match_reason,
                        priority_company=listing.priority_company,
                        query_used=listing.query_used,
                        prefilter_score=listing.prefilter_score,
                        prefilter_reason=listing.prefilter_reason,
                        review_status=listing.review_status,
                        review_notes=listing.review_notes,
                        is_favorite=listing.is_favorite,
                        viewed_at=listing.viewed_at,
                        reviewed_at=listing.reviewed_at,
                        already_sent=False,
                    )
                    session.add(job)
                    saved.append(job)
            session.commit()
        return saved

    def get_unsent_jobs(self, min_score: float, limit: int) -> list[Job]:
        with self.session_factory() as session:
            statement = (
                select(Job)
                .where(and_(Job.already_sent.is_(False), Job.match_score >= min_score))
                .order_by(Job.match_score.desc(), Job.collected_at.desc())
                .limit(limit)
            )
            return list(session.scalars(statement).all())

    def get_jobs_for_analysis(
        self,
        min_score: float = 0,
        only_without_analysis: bool = True,
        limit: int | None = None,
    ) -> list[Job]:
        with self.session_factory() as session:
            statement = select(Job).where(Job.match_score >= min_score).order_by(Job.match_score.desc())
            if only_without_analysis:
                statement = statement.where(Job.analysis == None)  # noqa: E711
            if limit is not None:
                statement = statement.limit(limit)
            return list(session.scalars(statement).unique().all())

    def get_job(self, job_id: int) -> Job | None:
        with self.session_factory() as session:
            return session.scalars(select(Job).where(Job.id == job_id)).unique().first()

    def upsert_analysis(self, job_id: int, analysis: JobProfileAnalysis) -> JobAnalysis:
        with self.session_factory() as session:
            existing = session.scalars(select(JobAnalysis).where(JobAnalysis.job_id == job_id)).first()
            if existing is None:
                existing = JobAnalysis(job_id=job_id, fit_level=analysis.fit_level, fit_score=analysis.fit_score)
                session.add(existing)
            self._update_analysis(existing, analysis)
            session.commit()
            return existing

    def analyze_jobs(
        self,
        analyzer,
        min_score: float = 0,
        reanalyze: bool = False,
    ) -> int:
        jobs = self.get_jobs_for_analysis(min_score=min_score, only_without_analysis=not reanalyze)
        for job in jobs:
            self.upsert_analysis(job.id, analyzer.analyze(job))
        return len(jobs)

    def mark_jobs_sent(self, job_ids: list[int]) -> None:
        if not job_ids:
            return
        with self.session_factory() as session:
            jobs = session.scalars(select(Job).where(Job.id.in_(job_ids))).all()
            for job in jobs:
                job.already_sent = True
            session.commit()

    def _find_existing(self, session: Session, listing: JobListing) -> Job | None:
        statement = select(Job).where(
            or_(
                Job.url == listing.url,
                and_(
                    Job.title == listing.title,
                    Job.company == listing.company,
                    Job.location == listing.location,
                ),
            )
        )
        return session.scalars(statement).first()

    def _update_existing(self, job: Job, listing: JobListing) -> None:
        job.title = listing.title
        job.company = listing.company
        job.location = listing.location
        job.source = listing.source
        job.url = listing.url
        job.description_snippet = listing.description_snippet
        job.published_date = listing.published_date
        job.collected_at = listing.collected_at
        job.match_score = listing.match_score
        job.match_reason = listing.match_reason
        job.priority_company = listing.priority_company
        job.query_used = listing.query_used
        job.prefilter_score = listing.prefilter_score
        job.prefilter_reason = listing.prefilter_reason

    def _update_analysis(self, target: JobAnalysis, analysis: JobProfileAnalysis) -> None:
        now = utc_now()
        target.fit_level = analysis.fit_level
        target.fit_score = analysis.fit_score
        target.matched_skills_json = json.dumps(analysis.matched_skills, ensure_ascii=False)
        target.missing_skills_json = json.dumps(analysis.missing_skills, ensure_ascii=False)
        target.strengths_json = json.dumps(analysis.strengths, ensure_ascii=False)
        target.risks_json = json.dumps(analysis.risks, ensure_ascii=False)
        target.resume_keywords_json = json.dumps(analysis.resume_keywords, ensure_ascii=False)
        target.recruiter_message = analysis.recruiter_message
        target.analysis_summary = analysis.analysis_summary
        if target.created_at is None:
            target.created_at = now
        target.updated_at = now
