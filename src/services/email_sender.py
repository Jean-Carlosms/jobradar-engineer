from __future__ import annotations

import logging
import smtplib
import ssl
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
        if not self._has_smtp_credentials():
            logger.error(
                "Credenciais SMTP ausentes. Configure SMTP_USERNAME e SMTP_PASSWORD no .env antes de usar --send-email."
            )
            return False

        try:
            with self._open_smtp_connection() as smtp:
                if self.settings.smtp_use_tls and not self.settings.smtp_use_ssl:
                    smtp.starttls()
                if self.settings.smtp_username:
                    smtp.login(self.settings.smtp_username, self.settings.smtp_password)
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException, ssl.SSLError):
            logger.exception("Falha ao enviar e-mail. Nenhuma vaga sera marcada como enviada.")
            return False

        logger.info("E-mail enviado para %s com %s vaga(s).", self.settings.email_to, len(selected_jobs))
        return True

    def _has_smtp_credentials(self) -> bool:
        return bool(self.settings.smtp_username and self.settings.smtp_password)

    def _open_smtp_connection(self) -> smtplib.SMTP:
        if self.settings.smtp_use_ssl:
            return smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port)
        return smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port)

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
            prefilter_score = getattr(job, "prefilter_score", 0.0) or 0.0
            lines.extend(
                [
                    f"{index}. {job.title}",
                    f"   Empresa: {job.company or 'Nao informado'}",
                    f"   Local: {job.location or 'Nao informado'}",
                    f"   Fonte: {job.source}",
                    f"   Score: {job.match_score:.1f}",
                    f"   Pre-filtro: {prefilter_score:.1f}",
                    f"   Empresa prioritaria: {priority_marker}",
                    f"   Motivo: {job.match_reason or 'Score calculado por palavras-chave do perfil.'}",
                ]
            )
            prefilter_reason = getattr(job, "prefilter_reason", "")
            if prefilter_reason:
                lines.append(f"   Motivo pre-filtro: {prefilter_reason[:180]}")
            lines.append(f"   Link: {job.url}")
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
