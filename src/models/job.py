from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


@dataclass
class JobListing:
    title: str
    company: str
    location: str
    source: str
    url: str
    description_snippet: str = ""
    published_date: str | None = None
    collected_at: datetime = field(default_factory=utc_now)
    match_score: float = 0.0
    match_reason: str = ""
    priority_company: bool = False
    query_used: str = ""


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("title", "company", "location", name="uq_job_title_company_location"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    company: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    location: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    description_snippet: Mapped[str] = mapped_column(Text, nullable=False, default="")
    published_date: Mapped[str | None] = mapped_column(String(80), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    match_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    priority_company: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    query_used: Mapped[str] = mapped_column(Text, nullable=False, default="")
    already_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    analysis: Mapped["JobAnalysis | None"] = relationship(
        back_populates="job",
        uselist=False,
        lazy="joined",
        cascade="all, delete-orphan",
    )

    @property
    def match_reasons(self) -> str:
        return self.match_reason

    @match_reasons.setter
    def match_reasons(self, value: str) -> None:
        self.match_reason = value


class JobAnalysis(Base):
    __tablename__ = "job_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False, unique=True, index=True)
    fit_level: Mapped[str] = mapped_column(String(20), nullable=False)
    fit_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    matched_skills_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    missing_skills_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    strengths_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    risks_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    resume_keywords_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    recruiter_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    analysis_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)

    job: Mapped[Job] = relationship(back_populates="analysis")
