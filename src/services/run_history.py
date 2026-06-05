from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


RUN_HISTORY_COLUMNS = [
    "run_id",
    "started_at",
    "mode",
    "source",
    "unique_jobs",
    "email_eligible",
    "email_sent",
    "duration_seconds",
    "errors_count",
    "report_path",
]

OPERATIONAL_ALERT_COLUMNS = [
    "started_at",
    "mode",
    "source",
    "operational_alert_type",
    "operational_alert_sent",
    "operational_alert_reason",
    "email_eligible",
    "unique_jobs",
    "report_path",
]

ALERT_TYPES = ["failure", "no_jobs", "no_email_eligible", "success_summary"]


@dataclass(frozen=True)
class RunHistoryEntry:
    run_id: str
    started_at: str
    finished_at: str
    duration_seconds: float
    mode: str
    source: str
    sources_executed: list[str] = field(default_factory=list)
    jobs_collected_by_source: dict[str, int] = field(default_factory=dict)
    unique_jobs: int = 0
    email_eligible: int = 0
    email_sent: bool = False
    email_skip_reason: str = ""
    operational_alert_type: str = ""
    operational_alert_should_send: bool = False
    operational_alert_sent: bool = False
    operational_alert_reason: str = ""
    source_errors: dict[str, str] = field(default_factory=dict)
    generated_reports: list[str] = field(default_factory=list)
    report_path: str = ""
    json_path: str = ""

    @property
    def errors_count(self) -> int:
        return sum(1 for error in self.source_errors.values() if str(error).strip())


class RunHistoryService:
    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root)
        self.runs_dir = self.project_root / "runs"

    def load(self) -> list[RunHistoryEntry]:
        entries = []
        for path in self.runs_dir.glob("run_report_*.json"):
            entry = self._load_entry(path)
            if entry is not None:
                entries.append(entry)
        return sorted(entries, key=_entry_sort_key, reverse=True)

    def rows(self, entries: list[RunHistoryEntry] | None = None) -> list[dict[str, Any]]:
        selected_entries = self.load() if entries is None else entries
        return [entry_to_row(entry) for entry in selected_entries]

    def alert_rows(self, entries: list[RunHistoryEntry] | None = None) -> list[dict[str, Any]]:
        selected_entries = self.load() if entries is None else entries
        return [entry_to_alert_row(entry) for entry in selected_entries if entry.operational_alert_type]

    def summary(self, entries: list[RunHistoryEntry] | None = None) -> dict[str, Any]:
        selected_entries = self.load() if entries is None else entries
        source_counts = Counter(entry.source for entry in selected_entries if entry.source)
        total_duration = sum(entry.duration_seconds for entry in selected_entries)
        alert_metrics = calculate_alert_metrics(selected_entries)
        summary = {
            "total_runs": len(selected_entries),
            "latest_run": selected_entries[0].started_at if selected_entries else "",
            "total_unique_jobs": sum(entry.unique_jobs for entry in selected_entries),
            "total_email_eligible": sum(entry.email_eligible for entry in selected_entries),
            "total_emails_sent": sum(1 for entry in selected_entries if entry.email_sent),
            "runs_with_errors": sum(1 for entry in selected_entries if entry.errors_count > 0),
            "average_duration_seconds": round(total_duration / len(selected_entries), 3)
            if selected_entries
            else 0.0,
            "most_used_source": source_counts.most_common(1)[0][0] if source_counts else "",
        }
        summary.update(alert_metrics)
        return summary

    def _load_entry(self, path: Path) -> RunHistoryEntry | None:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(raw, dict):
            return None
        return normalize_run_entry(raw, path)


def normalize_run_entry(raw: dict[str, Any], json_path: str | Path) -> RunHistoryEntry:
    path = Path(json_path)
    source_errors = _clean_string_dict(raw.get("source_errors"))
    return RunHistoryEntry(
        run_id=str(raw.get("run_id") or path.stem.replace("run_report_", "")),
        started_at=str(raw.get("started_at") or ""),
        finished_at=str(raw.get("finished_at") or ""),
        duration_seconds=_to_float(raw.get("duration_seconds")),
        mode=str(raw.get("mode") or ""),
        source=str(raw.get("source") or ""),
        sources_executed=_to_string_list(raw.get("sources_executed")),
        jobs_collected_by_source=_clean_int_dict(raw.get("jobs_collected_by_source")),
        unique_jobs=_to_int(raw.get("unique_jobs")),
        email_eligible=_to_int(raw.get("email_eligible_jobs", raw.get("email_eligible"))),
        email_sent=_to_bool(raw.get("email_sent")),
        email_skip_reason=str(raw.get("email_skip_reason") or ""),
        operational_alert_type=str(raw.get("operational_alert_type") or ""),
        operational_alert_should_send=_to_bool(raw.get("operational_alert_should_send")),
        operational_alert_sent=_to_bool(raw.get("operational_alert_sent")),
        operational_alert_reason=str(raw.get("operational_alert_reason") or ""),
        source_errors=source_errors,
        generated_reports=_to_string_list(raw.get("generated_reports")),
        report_path=str(path.with_suffix(".md")),
        json_path=str(path),
    )


def entry_to_row(entry: RunHistoryEntry) -> dict[str, Any]:
    row = {
        "run_id": entry.run_id,
        "started_at": entry.started_at,
        "mode": entry.mode,
        "source": entry.source,
        "unique_jobs": entry.unique_jobs,
        "email_eligible": entry.email_eligible,
        "email_sent": entry.email_sent,
        "duration_seconds": entry.duration_seconds,
        "errors_count": entry.errors_count,
        "report_path": entry.report_path,
    }
    return {column: row[column] for column in RUN_HISTORY_COLUMNS}


def entry_to_alert_row(entry: RunHistoryEntry) -> dict[str, Any]:
    row = {
        "started_at": entry.started_at,
        "mode": entry.mode,
        "source": entry.source,
        "operational_alert_type": entry.operational_alert_type,
        "operational_alert_sent": entry.operational_alert_sent,
        "operational_alert_reason": entry.operational_alert_reason,
        "email_eligible": entry.email_eligible,
        "unique_jobs": entry.unique_jobs,
        "report_path": entry.report_path,
    }
    return {column: row[column] for column in OPERATIONAL_ALERT_COLUMNS}


def calculate_alert_metrics(entries: list[RunHistoryEntry]) -> dict[str, Any]:
    alert_entries = [entry for entry in entries if entry.operational_alert_type]
    alerts_by_type = Counter(entry.operational_alert_type for entry in alert_entries)
    latest_alert = alert_entries[0] if alert_entries else None
    metrics = {
        "total_alerts": len(alert_entries),
        "operational_alerts_sent": sum(1 for entry in alert_entries if entry.operational_alert_sent),
        "alerts_by_type": {alert_type: alerts_by_type.get(alert_type, 0) for alert_type in ALERT_TYPES},
        "runs_without_alert": len(entries) - len(alert_entries),
        "latest_alert": latest_alert.started_at if latest_alert else "",
        "latest_alert_type": latest_alert.operational_alert_type if latest_alert else "",
        "alert_failures": alerts_by_type.get("failure", 0),
        "alert_no_jobs": alerts_by_type.get("no_jobs", 0),
        "alert_no_email_eligible": alerts_by_type.get("no_email_eligible", 0),
        "alert_success_summary": alerts_by_type.get("success_summary", 0),
    }
    return metrics


def format_run_history_summary(summary: dict[str, Any]) -> str:
    if not summary.get("total_runs"):
        return "Nenhum historico de execucao encontrado em runs/."
    return (
        f"Execucoes: {summary['total_runs']} | "
        f"ultima: {summary['latest_run']} | "
        f"emails_enviados: {summary['total_emails_sent']} | "
        f"duracao_media: {summary['average_duration_seconds']:.3f}s | "
        f"com_erro: {summary['runs_with_errors']} | "
        f"alertas: {summary['total_alerts']} | "
        f"alertas_enviados: {summary['operational_alerts_sent']} | "
        f"ultimo_alerta: {summary['latest_alert_type'] or 'n/a'} | "
        f"failures: {summary['alert_failures']}"
    )


def format_operational_alerts_summary(summary: dict[str, Any]) -> str:
    if not summary.get("total_runs"):
        return "Nenhum historico de execucao encontrado em runs/."
    by_type = summary.get("alerts_by_type", {})
    type_text = ", ".join(f"{alert_type}={by_type.get(alert_type, 0)}" for alert_type in ALERT_TYPES)
    return (
        f"Alertas: {summary['total_alerts']} | "
        f"enviados: {summary['operational_alerts_sent']} | "
        f"por_tipo: {type_text} | "
        f"ultimo: {summary['latest_alert_type'] or 'n/a'} em {summary['latest_alert'] or 'n/a'} | "
        f"failures: {summary['alert_failures']}"
    )


def _entry_sort_key(entry: RunHistoryEntry) -> tuple[float, str]:
    parsed = _parse_datetime(entry.started_at)
    if parsed is None:
        parsed = _parse_datetime(entry.run_id.replace("_", ""))
    return ((parsed.timestamp() if parsed else 0.0), entry.json_path)


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _to_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "sim", "sent"}
    return bool(value)


def _to_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _clean_string_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items() if str(key).strip()}


def _clean_int_dict(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {str(key): _to_int(item) for key, item in value.items() if str(key).strip()}
