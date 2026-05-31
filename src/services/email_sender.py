from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Iterable, Sequence

from src.config import Settings
from src.models.job import Job

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_message(
        self,
        jobs: Sequence[Job],
        min_score: float | None = None,
        limit: int | None = None,
    ) -> EmailMessage:
        selected_jobs = self.select_jobs(jobs, min_score=min_score, limit=limit)
        message = EmailMessage()
        message["Subject"] = f"JobRadar Engineer: {len(selected_jobs)} vaga(s) recomendada(s)"
        message["From"] = self.settings.email_from
        message["To"] = self.settings.email_to
        message.set_content(self.render_body(selected_jobs))
        return message

    def send_jobs(
        self,
        jobs: Sequence[Job],
        min_score: float | None = None,
        limit: int | None = None,
    ) -> bool:
        selected_jobs = self.select_jobs(jobs, min_score=min_score, limit=limit)
        if not selected_jobs:
            logger.info("Nenhuma vaga elegivel para envio.")
            return False

        message = self.build_message(selected_jobs, min_score=0, limit=len(selected_jobs))

        if self.settings.email_dry_run:
            logger.info("EMAIL_DRY_RUN ativo. E-mail gerado, mas nao enviado:\n%s", message.get_content())
            return True

        if self.settings.smtp_use_tls:
            smtp: smtplib.SMTP = smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port)
        else:
            smtp = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port)

        with smtp:
            if self.settings.smtp_username:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)
        logger.info("E-mail enviado para %s com %s vaga(s).", self.settings.email_to, len(selected_jobs))
        return True

    def select_jobs(
        self,
        jobs: Sequence[Job],
        min_score: float | None = None,
        limit: int | None = None,
    ) -> list[Job]:
        effective_min_score = min_score if min_score is not None else self.settings.min_score_to_email
        effective_limit = limit if limit is not None else self.settings.max_email_jobs
        effective_min_score = effective_min_score if effective_min_score is not None else 0
        effective_limit = effective_limit if effective_limit is not None else len(jobs)

        return sorted(
            [job for job in jobs if job.match_score >= effective_min_score],
            key=lambda job: job.match_score,
            reverse=True,
        )[:effective_limit]

    def render_body(self, jobs: Iterable[Job]) -> str:
        lines = [
            "JobRadar Engineer - vagas recomendadas",
            "=" * 41,
            "",
        ]
        for index, job in enumerate(jobs, start=1):
            priority_marker = "sim" if job.priority_company else "nao"
            analysis = getattr(job, "analysis", None)
            lines.extend(
                [
                    f"{index}. {job.title}",
                    f"   Empresa: {job.company or 'Nao informado'}",
                    f"   Local: {job.location or 'Nao informado'}",
                    f"   Fonte: {job.source}",
                    f"   Score: {job.match_score:.1f}",
                    f"   Empresa prioritaria: {priority_marker}",
                    f"   Motivo: {job.match_reason or 'Score calculado por palavras-chave do perfil.'}",
                    f"   Link: {job.url}",
                ]
            )
            if analysis:
                lines.extend(
                    [
                        f"   Fit level: {analysis.fit_level}",
                        f"   Fit score: {analysis.fit_score}/100",
                        f"   Analise: {analysis.analysis_summary}",
                        f"   Mensagem sugerida: {analysis.recruiter_message}",
                    ]
                )
            lines.append("")
        return "\n".join(lines)

    def _render_body(self, jobs: Iterable[Job]) -> str:
        return self.render_body(jobs)
