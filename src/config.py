from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_SEARCH_TERMS = [
    "Engenheiro Mecatronico",
    "Engenheiro de Automacao",
    "Engenheiro de Projetos",
    "Analista de Projetos",
    "Manufacturing Engineer",
    "Automation Engineer",
    "Technical Support Engineer",
    "Engenheiro de Processos",
    "Engenheiro de Dados Industriais",
    "Robotica PLC Python industrial Power BI Industria 4.0",
]

DEFAULT_LOCATIONS = [
    "Sorocaba",
    "Campinas",
    "Piracicaba",
    "Sao Paulo",
    "Remoto",
    "Hibrido",
]


def _split_env_list(value: str | None, fallback: list[str]) -> list[str]:
    if not value:
        return fallback
    return [item.strip() for item in value.split(",") if item.strip()]


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "sim"}


@dataclass(frozen=True)
class Settings:
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[1])
    database_path: Path = field(default_factory=lambda: Path(os.getenv("DATABASE_PATH", "data/jobs.db")))
    profile_path: Path = field(default_factory=lambda: Path(os.getenv("PROFILE_PATH", "config/profile_keywords.yaml")))
    profile_summary_path: Path = field(
        default_factory=lambda: Path(os.getenv("PROFILE_SUMMARY_PATH", "config/profile_summary.yaml"))
    )
    search_terms: list[str] = field(
        default_factory=lambda: _split_env_list(os.getenv("SEARCH_TERMS"), DEFAULT_SEARCH_TERMS)
    )
    locations: list[str] = field(default_factory=lambda: _split_env_list(os.getenv("LOCATIONS"), DEFAULT_LOCATIONS))
    min_score_to_email: float | None = field(
        default_factory=lambda: float(os.getenv("MIN_SCORE_TO_EMAIL")) if os.getenv("MIN_SCORE_TO_EMAIL") else None
    )
    max_email_jobs: int | None = field(
        default_factory=lambda: int(os.getenv("MAX_EMAIL_JOBS")) if os.getenv("MAX_EMAIL_JOBS") else None
    )
    request_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15")))
    rate_limit_seconds: float = field(default_factory=lambda: float(os.getenv("RATE_LIMIT_SECONDS", "1.5")))
    max_search_queries: int = field(default_factory=lambda: int(os.getenv("MAX_SEARCH_QUERIES", "20")))
    enable_web_search: bool = field(default_factory=lambda: _bool_env("ENABLE_WEB_SEARCH", True))

    email_dry_run: bool = field(default_factory=lambda: _bool_env("EMAIL_DRY_RUN", True))
    smtp_host: str = field(default_factory=lambda: os.getenv("SMTP_HOST", "localhost"))
    smtp_port: int = field(default_factory=lambda: int(os.getenv("SMTP_PORT", "1025")))
    smtp_username: str = field(default_factory=lambda: os.getenv("SMTP_USERNAME", ""))
    smtp_password: str = field(default_factory=lambda: os.getenv("SMTP_PASSWORD", ""))
    smtp_use_tls: bool = field(default_factory=lambda: _bool_env("SMTP_USE_TLS", False))
    email_from: str = field(default_factory=lambda: os.getenv("EMAIL_FROM", "jobradar@example.com"))
    email_to: str = field(default_factory=lambda: os.getenv("EMAIL_TO", "you@example.com"))

    scheduler_hour: int = field(default_factory=lambda: int(os.getenv("SCHEDULER_HOUR", "8")))
    scheduler_minute: int = field(default_factory=lambda: int(os.getenv("SCHEDULER_MINUTE", "0")))

    @property
    def resolved_database_path(self) -> Path:
        if self.database_path.is_absolute():
            return self.database_path
        return self.project_root / self.database_path

    @property
    def resolved_profile_path(self) -> Path:
        if self.profile_path.is_absolute():
            return self.profile_path
        return self.project_root / self.profile_path

    @property
    def resolved_profile_summary_path(self) -> Path:
        if self.profile_summary_path.is_absolute():
            return self.profile_summary_path
        return self.project_root / self.profile_summary_path


def load_settings(env_file: str | Path | None = None) -> Settings:
    load_dotenv(dotenv_path=env_file)
    return Settings()
