from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from src.database import JobRepository
from src.models.job import Job, utc_now


REVIEW_STATUSES = ["unreviewed", "relevant", "irrelevant", "maybe", "applied", "ignored"]


@dataclass(frozen=True)
class ReviewSummary:
    total_jobs: int
    status_counts: dict[str, int]
    favorite_count: int
    top_relevant_companies: list[tuple[str, int]]
    top_relevant_titles: list[tuple[str, int]]
    top_irrelevance_reasons: list[tuple[str, int]]


@dataclass(frozen=True)
class ReviewExportResult:
    path: Path
    row_count: int


class JobReviewService:
    def __init__(self, repository: JobRepository) -> None:
        self.repository = repository

    def mark_viewed(self, job_id: int) -> Job | None:
        with self.repository.session_factory() as session:
            job = session.get(Job, job_id)
            if job is None:
                return None
            job.viewed_at = utc_now()
            session.commit()
            return job

    def set_favorite(self, job_id: int, is_favorite: bool = True) -> Job | None:
        with self.repository.session_factory() as session:
            job = session.get(Job, job_id)
            if job is None:
                return None
            job.is_favorite = bool(is_favorite)
            job.reviewed_at = utc_now()
            session.commit()
            return job

    def update_review(
        self,
        job_id: int,
        review_status: str,
        review_notes: str | None = None,
        is_favorite: bool | None = None,
        mark_viewed: bool = True,
    ) -> Job | None:
        self._validate_status(review_status)
        with self.repository.session_factory() as session:
            job = session.get(Job, job_id)
            if job is None:
                return None
            job.review_status = review_status
            if review_notes is not None:
                job.review_notes = review_notes
            if is_favorite is not None:
                job.is_favorite = bool(is_favorite)
            now = utc_now()
            job.reviewed_at = now
            if mark_viewed:
                job.viewed_at = now
            session.commit()
            return job

    def save_notes(self, job_id: int, review_notes: str) -> Job | None:
        with self.repository.session_factory() as session:
            job = session.get(Job, job_id)
            if job is None:
                return None
            job.review_notes = review_notes
            job.reviewed_at = utc_now()
            session.commit()
            return job

    def list_by_status(self, review_status: str) -> list[Job]:
        self._validate_status(review_status)
        with self.repository.session_factory() as session:
            statement = select(Job).where(Job.review_status == review_status).order_by(Job.match_score.desc())
            return list(session.scalars(statement).unique().all())

    def summarize_feedback(self) -> ReviewSummary:
        with self.repository.session_factory() as session:
            jobs = list(session.scalars(select(Job)).unique().all())
        status_counts = {status: 0 for status in REVIEW_STATUSES}
        for job in jobs:
            status_counts[job.review_status or "unreviewed"] = status_counts.get(job.review_status or "unreviewed", 0) + 1
        relevant = [job for job in jobs if job.review_status in {"relevant", "applied"}]
        irrelevant = [job for job in jobs if job.review_status in {"irrelevant", "ignored"}]
        return ReviewSummary(
            total_jobs=len(jobs),
            status_counts=status_counts,
            favorite_count=sum(1 for job in jobs if job.is_favorite),
            top_relevant_companies=Counter(job.company or "Nao informado" for job in relevant).most_common(10),
            top_relevant_titles=Counter(job.title or "Nao informado" for job in relevant).most_common(10),
            top_irrelevance_reasons=Counter(
                self._note_reason(job.review_notes) for job in irrelevant if (job.review_notes or "").strip()
            ).most_common(10),
        )

    def export_feedback_csv(self, reports_dir: str | Path = "reports") -> ReviewExportResult:
        reports_path = Path(reports_dir)
        reports_path.mkdir(parents=True, exist_ok=True)
        output_path = reports_path / f"job_review_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with self.repository.session_factory() as session:
            jobs = list(session.scalars(select(Job).order_by(Job.match_score.desc())).unique().all())

        with output_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "title",
                    "company",
                    "location",
                    "url",
                    "prefilter_score",
                    "match_score",
                    "fit_score",
                    "review_status",
                    "is_favorite",
                    "review_notes",
                    "reviewed_at",
                ],
            )
            writer.writeheader()
            for job in jobs:
                analysis = getattr(job, "analysis", None)
                writer.writerow(
                    {
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "url": job.url,
                        "prefilter_score": f"{(job.prefilter_score or 0):.1f}",
                        "match_score": f"{(job.match_score or 0):.1f}",
                        "fit_score": analysis.fit_score if analysis else 0,
                        "review_status": job.review_status,
                        "is_favorite": job.is_favorite,
                        "review_notes": job.review_notes,
                        "reviewed_at": job.reviewed_at.isoformat() if job.reviewed_at else "",
                    }
                )
        return ReviewExportResult(path=output_path, row_count=len(jobs))

    def render_summary(self, summary: ReviewSummary | None = None) -> str:
        summary = summary or self.summarize_feedback()
        lines = [
            "Resumo de feedback humano",
            "=" * 26,
            f"Total de vagas: {summary.total_jobs}",
            f"Favoritas: {summary.favorite_count}",
            "",
            "Por status:",
        ]
        for status in REVIEW_STATUSES:
            lines.append(f"- {status}: {summary.status_counts.get(status, 0)}")
        lines.extend(["", "Top empresas relevantes:"])
        lines.extend(_format_counter_lines(summary.top_relevant_companies))
        lines.extend(["", "Top titulos relevantes:"])
        lines.extend(_format_counter_lines(summary.top_relevant_titles))
        lines.extend(["", "Top motivos de irrelevancia:"])
        lines.extend(_format_counter_lines(summary.top_irrelevance_reasons))
        return "\n".join(lines)

    def _validate_status(self, review_status: str) -> None:
        if review_status not in REVIEW_STATUSES:
            raise ValueError(f"review_status invalido: {review_status}")

    def _note_reason(self, note: str) -> str:
        cleaned = re.sub(r"\s+", " ", note or "").strip()
        if not cleaned:
            return "sem nota"
        return cleaned.split(".", 1)[0][:120]


def _format_counter_lines(items: list[tuple[str, int]]) -> list[str]:
    if not items:
        return ["- nenhum dado"]
    return [f"- {name}: {count}" for name, count in items]
