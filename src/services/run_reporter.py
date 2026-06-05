from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


SENSITIVE_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    re.compile(r"(?i)(password|senha|token|api[_-]?key|smtp_password)\s*[:=]\s*[^,\s]+"),
    re.compile(r"(?i)\.env"),
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp_for_path(moment: datetime | None = None) -> str:
    return (moment or utc_now()).strftime("%Y%m%d_%H%M%S")


@dataclass
class SourceRunMetric:
    name: str
    collected: int = 0
    duration_seconds: float = 0.0
    error: str = ""


@dataclass
class RunReport:
    run_id: str
    started_at: str
    finished_at: str = ""
    duration_seconds: float = 0.0
    mode: str = "dry-run"
    source: str = "all"
    sources_executed: list[str] = field(default_factory=list)
    jobs_collected_by_source: dict[str, int] = field(default_factory=dict)
    unique_jobs: int = 0
    prefilter_discarded_jobs: int = 0
    prefilter_kept_jobs: int = 0
    enriched_jobs: int = 0
    email_eligible_jobs: int = 0
    email_sent: bool = False
    email_skip_reason: str = ""
    operational_alert_type: str = ""
    operational_alert_should_send: bool = False
    operational_alert_sent: bool = False
    operational_alert_reason: str = ""
    source_errors: dict[str, str] = field(default_factory=dict)
    generated_reports: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RunReportResult:
    markdown_path: Path
    json_path: Path
    report: RunReport


class RunReporter:
    def __init__(
        self,
        project_root: str | Path = ".",
        mode: str = "dry-run",
        source: str = "all",
        run_id: str | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        self.started_at = utc_now()
        self.report = RunReport(
            run_id=run_id or self.started_at.strftime("%Y%m%d_%H%M%S"),
            started_at=self.started_at.isoformat(),
            mode=mode,
            source=source,
        )

    def record_source(self, name: str, collected: int, duration_seconds: float = 0.0) -> None:
        if name not in self.report.sources_executed:
            self.report.sources_executed.append(name)
        self.report.jobs_collected_by_source[name] = self.report.jobs_collected_by_source.get(name, 0) + collected

    def record_source_error(self, name: str, error: str) -> None:
        if name not in self.report.sources_executed:
            self.report.sources_executed.append(name)
        self.report.source_errors[name] = self._sanitize(error)

    def record_totals(
        self,
        unique_jobs: int,
        email_eligible_jobs: int,
        prefilter_discarded_jobs: int = 0,
        prefilter_kept_jobs: int = 0,
        enriched_jobs: int = 0,
    ) -> None:
        self.report.unique_jobs = unique_jobs
        self.report.email_eligible_jobs = email_eligible_jobs
        self.report.prefilter_discarded_jobs = prefilter_discarded_jobs
        self.report.prefilter_kept_jobs = prefilter_kept_jobs
        self.report.enriched_jobs = enriched_jobs

    def record_email(self, sent: bool, skip_reason: str = "") -> None:
        self.report.email_sent = sent
        self.report.email_skip_reason = self._sanitize(skip_reason)

    def record_operational_alert(
        self,
        alert_type: str,
        should_send: bool,
        sent: bool,
        reason: str = "",
    ) -> None:
        self.report.operational_alert_type = self._sanitize(alert_type)
        self.report.operational_alert_should_send = should_send
        self.report.operational_alert_sent = sent
        self.report.operational_alert_reason = self._sanitize(reason)

    def add_generated_report(self, path: str | Path | None) -> None:
        if path is None:
            return
        sanitized = self._sanitize(str(path))
        if sanitized not in self.report.generated_reports:
            self.report.generated_reports.append(sanitized)

    def finish(self, reports_dir: str | Path | None = None) -> RunReportResult:
        finished_at = utc_now()
        self.report.finished_at = finished_at.isoformat()
        self.report.duration_seconds = round((finished_at - self.started_at).total_seconds(), 3)
        output_dir = Path(reports_dir) if reports_dir else self.project_root / "runs"
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = f"run_report_{timestamp_for_path(finished_at)}"
        json_path = output_dir / f"{base_name}.json"
        markdown_path = output_dir / f"{base_name}.md"
        json_path.write_text(json.dumps(self._safe_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        markdown_path.write_text(self.render_markdown(), encoding="utf-8")
        return RunReportResult(markdown_path=markdown_path, json_path=json_path, report=self.report)

    def render_markdown(self) -> str:
        lines = [
            "# JobRadar Run Report",
            "",
            "## Resumo",
            "",
            f"- Run ID: `{self._sanitize(self.report.run_id)}`",
            f"- Inicio: `{self.report.started_at}`",
            f"- Fim: `{self.report.finished_at}`",
            f"- Duracao: `{self.report.duration_seconds:.3f}s`",
            f"- Modo: `{self.report.mode}`",
            f"- Source selecionada: `{self.report.source}`",
            "",
            "## Fontes",
            "",
            "| Fonte | Vagas coletadas | Erro |",
            "| --- | ---: | --- |",
        ]
        for source_name in self.report.sources_executed:
            lines.append(
                f"| {self._escape_md(source_name)} | "
                f"{self.report.jobs_collected_by_source.get(source_name, 0)} | "
                f"{self._escape_md(self.report.source_errors.get(source_name, ''))} |"
            )
        if not self.report.sources_executed:
            lines.append("| nenhuma | 0 | |")

        lines.extend(
            [
                "",
                "## Totais",
                "",
                f"- Vagas unicas: {self.report.unique_jobs}",
                f"- Vagas descartadas pelo pre-filtro: {self.report.prefilter_discarded_jobs}",
                f"- Vagas mantidas pelo pre-filtro: {self.report.prefilter_kept_jobs}",
                f"- Vagas enriquecidas: {self.report.enriched_jobs}",
                f"- Vagas elegiveis para e-mail: {self.report.email_eligible_jobs}",
                "",
                "## E-mail",
                "",
                f"- Enviado: {'sim' if self.report.email_sent else 'nao'}",
                f"- Motivo de nao envio: {self.report.email_skip_reason or 'n/a'}",
                "",
                "## Alerta operacional",
                "",
                f"- Tipo: {self.report.operational_alert_type or 'n/a'}",
                f"- Envio habilitado: {'sim' if self.report.operational_alert_should_send else 'nao'}",
                f"- Enviado: {'sim' if self.report.operational_alert_sent else 'nao'}",
                f"- Motivo/status: {self.report.operational_alert_reason or 'n/a'}",
                "",
                "## Relatorios e debug",
                "",
            ]
        )
        if self.report.generated_reports:
            lines.extend(f"- `{self._sanitize(path)}`" for path in self.report.generated_reports)
        else:
            lines.append("- nenhum")
        lines.extend(["", "## Segurança", "", "- Credenciais, tokens, e-mails e arquivos de ambiente sao sanitizados neste relatorio."])
        return "\n".join(lines)

    def summary_text(self) -> str:
        return (
            f"{self.report.run_id} | mode={self.report.mode} | source={self.report.source} | "
            f"unique={self.report.unique_jobs} | email_eligible={self.report.email_eligible_jobs} | "
            f"email_sent={'sim' if self.report.email_sent else 'nao'}"
        )

    def _safe_dict(self) -> dict:
        return self._sanitize_value(asdict(self.report))

    def _sanitize_value(self, value):
        if isinstance(value, dict):
            return {self._sanitize(str(key)): self._sanitize_value(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._sanitize_value(item) for item in value]
        if isinstance(value, str):
            return self._sanitize(value)
        return value

    def _sanitize(self, value: str) -> str:
        sanitized = str(value or "")
        for pattern in SENSITIVE_PATTERNS:
            sanitized = pattern.sub("[redacted]", sanitized)
        return sanitized

    def _escape_md(self, value: str) -> str:
        return self._sanitize(value).replace("|", "\\|").replace("\n", " ").strip()


def find_latest_run_report(project_root: str | Path = ".") -> Path | None:
    runs_dir = Path(project_root) / "runs"
    candidates = sorted(runs_dir.glob("run_report_*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def load_run_report_summary(markdown_path: str | Path) -> str:
    path = Path(markdown_path)
    json_path = path.with_suffix(".json")
    if json_path.exists():
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        return (
            f"{raw.get('run_id', '')} | mode={raw.get('mode', '')} | source={raw.get('source', '')} | "
            f"unique={raw.get('unique_jobs', 0)} | email_eligible={raw.get('email_eligible_jobs', 0)} | "
            f"email_sent={'sim' if raw.get('email_sent') else 'nao'}"
        )
    return path.read_text(encoding="utf-8").splitlines()[0] if path.exists() else ""
