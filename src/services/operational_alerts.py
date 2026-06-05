from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.services.run_reporter import RunReport


class OperationalAlertSettings(Protocol):
    operational_alerts_enabled: bool
    operational_alerts_on_failure: bool
    operational_alerts_on_no_jobs: bool
    operational_alerts_on_no_email_eligible: bool
    operational_daily_summary: bool


@dataclass(frozen=True)
class OperationalAlert:
    alert_type: str
    subject: str
    body_text: str
    should_send: bool
    reason: str


class OperationalAlertService:
    def __init__(self, settings: OperationalAlertSettings) -> None:
        self.settings = settings

    def build_alert(self, report: RunReport, force_enabled: bool = False) -> OperationalAlert:
        alert_type = self._alert_type(report)
        enabled = force_enabled or self.settings.operational_alerts_enabled
        should_send = force_enabled or (enabled and self._type_enabled(alert_type))
        subject = self._subject(report, alert_type)
        body = self._body(report, alert_type)
        reason = "habilitado" if should_send else self._skip_reason(alert_type, enabled)
        return OperationalAlert(
            alert_type=alert_type,
            subject=subject,
            body_text=body,
            should_send=should_send,
            reason=reason,
        )

    def _alert_type(self, report: RunReport) -> str:
        if any(str(error).strip() for error in report.source_errors.values()):
            return "failure"
        if report.unique_jobs == 0:
            return "no_jobs"
        if report.email_eligible_jobs == 0:
            return "no_email_eligible"
        return "success_summary"

    def _type_enabled(self, alert_type: str) -> bool:
        return {
            "failure": self.settings.operational_alerts_on_failure,
            "no_jobs": self.settings.operational_alerts_on_no_jobs,
            "no_email_eligible": self.settings.operational_alerts_on_no_email_eligible,
            "success_summary": self.settings.operational_daily_summary,
        }.get(alert_type, False)

    def _skip_reason(self, alert_type: str, enabled: bool) -> str:
        if not enabled:
            return "Alertas operacionais desativados."
        if alert_type == "success_summary":
            return "Resumo operacional diario desativado."
        return f"Alerta operacional do tipo {alert_type} desativado."

    def _subject(self, report: RunReport, alert_type: str) -> str:
        labels = {
            "failure": "falha operacional",
            "no_jobs": "nenhuma vaga coletada",
            "no_email_eligible": "sem vagas elegiveis",
            "success_summary": "resumo operacional",
        }
        return f"JobRadar Engineer: {labels.get(alert_type, alert_type)} ({report.source})"

    def _body(self, report: RunReport, alert_type: str) -> str:
        lines = [
            "JobRadar Engineer - alerta operacional",
            "=" * 40,
            "",
            f"Tipo: {alert_type}",
            f"Run ID: {report.run_id}",
            f"Inicio: {report.started_at}",
            f"Fim: {report.finished_at or 'em andamento'}",
            f"Duracao: {report.duration_seconds:.3f}s",
            f"Modo: {report.mode}",
            f"Source selecionada: {report.source}",
            "",
            "Totais",
            f"- Vagas unicas: {report.unique_jobs}",
            f"- Vagas elegiveis para e-mail: {report.email_eligible_jobs}",
            f"- E-mail de vagas enviado: {'sim' if report.email_sent else 'nao'}",
            f"- Motivo de nao envio: {report.email_skip_reason or 'n/a'}",
            "",
            "Fontes",
        ]
        if report.sources_executed:
            for source_name in report.sources_executed:
                collected = report.jobs_collected_by_source.get(source_name, 0)
                error = report.source_errors.get(source_name, "")
                suffix = f" | erro: {error}" if error else ""
                lines.append(f"- {source_name}: {collected} vaga(s){suffix}")
        else:
            lines.append("- nenhuma fonte registrada")

        if alert_type == "success_summary":
            lines.extend(["", "Resumo: execucao concluida sem alertas criticos."])
        elif alert_type == "no_email_eligible":
            lines.extend(["", "Resumo: houve coleta, mas nenhuma vaga passou nos criterios de envio."])
        elif alert_type == "no_jobs":
            lines.extend(["", "Resumo: nenhuma vaga unica foi coletada nesta execucao."])
        else:
            lines.extend(["", "Resumo: uma ou mais fontes registraram erro durante a execucao."])
        return "\n".join(lines)
