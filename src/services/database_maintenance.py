from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from contextlib import closing


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp_for_path(moment: datetime | None = None) -> str:
    return (moment or utc_now()).strftime("%Y%m%d_%H%M%S")


@dataclass(frozen=True)
class BackupResult:
    backup_db: Path
    manifest_path: Path
    sha256: str
    file_size_bytes: int
    reason: str


@dataclass(frozen=True)
class BackupInfo:
    manifest_path: Path
    backup_db: Path
    timestamp: str
    file_size_bytes: int
    sha256: str
    reason: str


@dataclass(frozen=True)
class BackupVerificationResult:
    backup_db: Path
    manifest_path: Path | None
    valid: bool
    sha256_matches: bool
    integrity_ok: bool
    message: str


@dataclass(frozen=True)
class RestoreResult:
    restored_db: Path
    backup_used: Path
    pre_restore_backup: Path | None


@dataclass(frozen=True)
class DatabaseSummaryExportResult:
    json_path: Path
    csv_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class DatabaseMaintenanceResult:
    database_path: Path
    integrity_before: str
    integrity_after: str
    page_count: int
    freelist_count: int


@dataclass(frozen=True)
class BackupCleanupResult:
    markdown_path: Path
    csv_path: Path
    plan: dict[str, Any]
    removed_files: list[Path]
    dry_run: bool
    confirmed: bool


BACKUP_MANIFEST_COLUMNS = [
    "timestamp",
    "reason",
    "backup_db",
    "file_size_bytes",
    "file_size",
    "sha256_short",
    "verification_status",
]


class DatabaseMaintenanceService:
    def __init__(
        self,
        project_root: str | Path = ".",
        database_path: str | Path = "data/jobs.db",
        backups_dir: str | Path | None = None,
    ) -> None:
        self.project_root = Path(project_root)
        db_path = Path(database_path)
        self.database_path = db_path if db_path.is_absolute() else self.project_root / db_path
        self.backups_dir = Path(backups_dir) if backups_dir else self.project_root / "backups"

    def create_backup(self, reason: str = "manual") -> BackupResult:
        if not self.database_path.exists():
            raise FileNotFoundError(f"Banco local nao encontrado: {self.database_path}")
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        base_path = self._next_backup_base()
        backup_db = base_path.with_suffix(".db")
        manifest_path = base_path.with_suffix(".json")

        with closing(sqlite3.connect(self.database_path)) as source, closing(sqlite3.connect(backup_db)) as target:
            source.backup(target)

        sha256 = calculate_sha256(backup_db)
        file_size = backup_db.stat().st_size
        manifest = {
            "timestamp": utc_now().isoformat(),
            "source_db": str(self.database_path),
            "backup_db": str(backup_db),
            "file_size_bytes": file_size,
            "sha256": sha256,
            "reason": _safe_text(reason),
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return BackupResult(
            backup_db=backup_db,
            manifest_path=manifest_path,
            sha256=sha256,
            file_size_bytes=file_size,
            reason=_safe_text(reason),
        )

    def list_backups(self) -> list[BackupInfo]:
        return load_backup_infos(self.backups_dir)

    def backup_rows(self, verify: bool = False) -> list[dict[str, Any]]:
        return load_backup_manifest_rows(self.backups_dir, verify=verify)

    def backup_summary(self) -> dict[str, Any]:
        return summarize_backups(self.backup_rows())

    def plan_backup_cleanup(self, retention_days: int, protect_invalid: bool = True) -> dict[str, Any]:
        return build_backup_cleanup_plan(self.backups_dir, retention_days, protect_invalid=protect_invalid)

    def cleanup_backups(
        self,
        retention_days: int,
        reports_dir: str | Path | None = None,
        dry_run: bool = True,
        confirm_cleanup: bool = False,
        protect_invalid: bool = True,
    ) -> BackupCleanupResult:
        plan = self.plan_backup_cleanup(retention_days, protect_invalid=protect_invalid)
        should_delete = confirm_cleanup and not dry_run
        removed_files = []
        if should_delete:
            for candidate in plan["candidates"]:
                for path_key in ["backup_db", "manifest_path"]:
                    path_text = candidate.get(path_key)
                    if not path_text:
                        continue
                    path = Path(path_text)
                    if path.exists():
                        path.unlink()
                        removed_files.append(path)
        output_dir = Path(reports_dir) if reports_dir else self.project_root / "reports"
        markdown_path, csv_path = write_backup_cleanup_report(
            plan,
            output_dir,
            dry_run=dry_run or not confirm_cleanup,
            confirmed=confirm_cleanup,
            removed_files=removed_files,
        )
        return BackupCleanupResult(
            markdown_path=markdown_path,
            csv_path=csv_path,
            plan=plan,
            removed_files=removed_files,
            dry_run=dry_run or not confirm_cleanup,
            confirmed=confirm_cleanup,
        )

    def verify_backup(self, backup_path: str | Path) -> BackupVerificationResult:
        manifest_path, backup_db, manifest = self._resolve_backup(backup_path)
        if not backup_db.exists():
            return BackupVerificationResult(backup_db, manifest_path, False, False, False, "Backup DB nao encontrado.")

        current_sha = calculate_sha256(backup_db)
        expected_sha = str(manifest.get("sha256") or "") if manifest else ""
        sha_matches = not expected_sha or current_sha == expected_sha
        integrity_message = sqlite_integrity_check(backup_db)
        integrity_ok = integrity_message == "ok"
        valid = sha_matches and integrity_ok
        message = "Backup valido." if valid else f"sha_ok={sha_matches}; integrity={integrity_message}"
        return BackupVerificationResult(backup_db, manifest_path, valid, sha_matches, integrity_ok, message)

    def restore_backup(self, backup_path: str | Path, confirm_restore: bool = False) -> RestoreResult:
        if not confirm_restore:
            raise ValueError("Restore bloqueado. Use --confirm-restore para confirmar explicitamente.")
        verification = self.verify_backup(backup_path)
        if not verification.valid:
            raise ValueError(f"Backup invalido: {verification.message}")

        pre_restore = None
        if self.database_path.exists():
            pre_restore = self.create_backup(reason="automatic pre-restore backup").backup_db
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(verification.backup_db, self.database_path)
        return RestoreResult(
            restored_db=self.database_path,
            backup_used=verification.backup_db,
            pre_restore_backup=pre_restore,
        )

    def export_summary(self, output_dir: str | Path | None = None) -> DatabaseSummaryExportResult:
        if not self.database_path.exists():
            raise FileNotFoundError(f"Banco local nao encontrado: {self.database_path}")
        target_dir = Path(output_dir) if output_dir else self.project_root / "reports"
        target_dir.mkdir(parents=True, exist_ok=True)
        base_name = f"db_summary_{timestamp_for_path()}"
        json_path = target_dir / f"{base_name}.json"
        csv_path = target_dir / f"{base_name}.csv"
        summary = self._build_summary()
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        with csv_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["metric", "value"])
            writer.writeheader()
            for key, value in flatten_summary(summary).items():
                writer.writerow({"metric": key, "value": value})
        return DatabaseSummaryExportResult(json_path=json_path, csv_path=csv_path, summary=summary)

    def run_maintenance(self) -> DatabaseMaintenanceResult:
        if not self.database_path.exists():
            raise FileNotFoundError(f"Banco local nao encontrado: {self.database_path}")
        with closing(sqlite3.connect(self.database_path)) as connection:
            with connection:
                integrity_before = connection.execute("PRAGMA integrity_check").fetchone()[0]
                connection.execute("VACUUM")
                connection.execute("ANALYZE")
                integrity_after = connection.execute("PRAGMA integrity_check").fetchone()[0]
                page_count = connection.execute("PRAGMA page_count").fetchone()[0]
                freelist_count = connection.execute("PRAGMA freelist_count").fetchone()[0]
        return DatabaseMaintenanceResult(
            database_path=self.database_path,
            integrity_before=str(integrity_before),
            integrity_after=str(integrity_after),
            page_count=_to_int(page_count),
            freelist_count=_to_int(freelist_count),
        )

    def _build_summary(self) -> dict[str, Any]:
        with closing(sqlite3.connect(self.database_path)) as connection:
            connection.row_factory = sqlite3.Row
            tables = _table_names(connection)
            jobs_exists = "jobs" in tables
            analyses_exists = "job_analyses" in tables
            summary = {
                "timestamp": utc_now().isoformat(),
                "database_path": str(self.database_path),
                "file_size_bytes": self.database_path.stat().st_size,
                "sha256": calculate_sha256(self.database_path),
                "tables": {table: _count_rows(connection, table) for table in tables},
                "jobs": {},
            }
            if jobs_exists:
                summary["jobs"] = {
                    "total": _count_rows(connection, "jobs"),
                    "already_sent": _count_where(connection, "jobs", "already_sent = 1"),
                    "favorites": _count_where(connection, "jobs", "is_favorite = 1"),
                    "review_status": _group_counts(connection, "jobs", "review_status"),
                    "sources": _group_counts(connection, "jobs", "source"),
                    "max_match_score": _scalar(connection, "SELECT MAX(match_score) FROM jobs") or 0,
                }
            if analyses_exists:
                summary["analyses"] = {"total": _count_rows(connection, "job_analyses")}
        return summary

    def _next_backup_base(self) -> Path:
        base = self.backups_dir / f"jobs_backup_{timestamp_for_path()}"
        if not base.with_suffix(".db").exists() and not base.with_suffix(".json").exists():
            return base
        for index in range(1, 1000):
            candidate = self.backups_dir / f"{base.name}_{index:03d}"
            if not candidate.with_suffix(".db").exists() and not candidate.with_suffix(".json").exists():
                return candidate
        raise RuntimeError("Nao foi possivel gerar nome unico para backup.")

    def _resolve_backup(self, backup_path: str | Path) -> tuple[Path | None, Path, dict[str, Any]]:
        path = Path(backup_path)
        if not path.is_absolute():
            path = self.project_root / path
        if path.suffix.lower() == ".json":
            raw = json.loads(path.read_text(encoding="utf-8"))
            backup_db = Path(str(raw.get("backup_db") or path.with_suffix(".db")))
            return path, backup_db, raw
        manifest_path = path.with_suffix(".json")
        manifest = {}
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return manifest_path if manifest_path.exists() else None, path, manifest


def calculate_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_backup_infos(backups_dir: str | Path) -> list[BackupInfo]:
    infos = []
    for manifest_path in sorted(Path(backups_dir).glob("jobs_backup_*.json"), reverse=True):
        raw = _read_manifest(manifest_path)
        if raw is None:
            continue
        backup_db = Path(str(raw.get("backup_db") or manifest_path.with_suffix(".db")))
        infos.append(
            BackupInfo(
                manifest_path=manifest_path,
                backup_db=backup_db,
                timestamp=str(raw.get("timestamp") or ""),
                file_size_bytes=_to_int(raw.get("file_size_bytes")),
                sha256=str(raw.get("sha256") or ""),
                reason=str(raw.get("reason") or ""),
            )
        )
    return infos


def load_backup_manifest_rows(backups_dir: str | Path, verify: bool = False) -> list[dict[str, Any]]:
    rows = []
    for backup in load_backup_infos(backups_dir):
        verification_status = "nao verificado"
        if verify:
            verification_status = _verify_backup_info(backup)
        rows.append(
            {
                "timestamp": backup.timestamp,
                "reason": backup.reason,
                "backup_db": str(backup.backup_db),
                "file_size_bytes": backup.file_size_bytes,
                "file_size": format_backup_size(backup.file_size_bytes),
                "sha256_short": short_sha256(backup.sha256),
                "verification_status": verification_status,
                "manifest_path": str(backup.manifest_path),
            }
        )
    return rows


def summarize_backups(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "total_backups": 0,
            "total_size_bytes": 0,
            "total_size": format_backup_size(0),
            "latest_backup": "",
            "largest_backup": "",
            "largest_backup_size_bytes": 0,
            "largest_backup_size": format_backup_size(0),
        }
    total_size = sum(_to_int(row.get("file_size_bytes")) for row in rows)
    sorted_by_timestamp = sorted(rows, key=lambda row: str(row.get("timestamp") or ""), reverse=True)
    largest = max(rows, key=lambda row: _to_int(row.get("file_size_bytes")))
    return {
        "total_backups": len(rows),
        "total_size_bytes": total_size,
        "total_size": format_backup_size(total_size),
        "latest_backup": str(sorted_by_timestamp[0].get("timestamp") or ""),
        "largest_backup": str(largest.get("backup_db") or ""),
        "largest_backup_size_bytes": _to_int(largest.get("file_size_bytes")),
        "largest_backup_size": format_backup_size(_to_int(largest.get("file_size_bytes"))),
    }


def format_backup_size(size_bytes: int) -> str:
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} GB"


def short_sha256(value: str, length: int = 12) -> str:
    digest = str(value or "")
    return digest[:length] if digest else ""


def build_backup_cleanup_plan(
    backups_dir: str | Path,
    retention_days: int,
    protect_invalid: bool = True,
    now: datetime | None = None,
) -> dict[str, Any]:
    current_time = now or utc_now()
    manifests = sorted(Path(backups_dir).glob("jobs_backup_*.json"), reverse=True)
    valid_rows = load_backup_manifest_rows(backups_dir)
    latest_valid_manifest = valid_rows[0]["manifest_path"] if valid_rows else ""
    items = []

    for manifest_path in manifests:
        raw = _read_manifest(manifest_path)
        if raw is None:
            items.append(
                _cleanup_item(
                    manifest_path=manifest_path,
                    backup_db=manifest_path.with_suffix(".db"),
                    timestamp="",
                    age_days=None,
                    file_size_bytes=0,
                    decision="protected",
                    reason="manifesto invalido protegido",
                    valid_manifest=False,
                )
            )
            continue

        timestamp = str(raw.get("timestamp") or "")
        age_days = _age_days(timestamp, current_time)
        backup_db = Path(str(raw.get("backup_db") or manifest_path.with_suffix(".db")))
        file_size_bytes = _to_int(raw.get("file_size_bytes"))
        is_latest = str(manifest_path) == latest_valid_manifest
        if is_latest:
            decision = "protected"
            reason = "backup mais recente protegido"
        elif age_days is None:
            decision = "protected"
            reason = "timestamp invalido protegido"
        elif age_days > retention_days:
            decision = "remove"
            reason = f"mais antigo que {retention_days} dia(s)"
        else:
            decision = "protected"
            reason = f"dentro da retencao de {retention_days} dia(s)"

        items.append(
            _cleanup_item(
                manifest_path=manifest_path,
                backup_db=backup_db,
                timestamp=timestamp,
                age_days=age_days,
                file_size_bytes=file_size_bytes,
                decision=decision,
                reason=reason,
                valid_manifest=True,
            )
        )

    if not protect_invalid:
        for item in items:
            if not item["valid_manifest"] and item["decision"] == "protected":
                item["decision"] = "remove"
                item["reason"] = "manifesto invalido com remocao autorizada"

    candidates = [item for item in items if item["decision"] == "remove"]
    protected = [item for item in items if item["decision"] != "remove"]
    return {
        "generated_at": current_time.isoformat(),
        "retention_days": retention_days,
        "backups_found": len(items),
        "candidates_count": len(candidates),
        "protected_count": len(protected),
        "recoverable_size_bytes": sum(_to_int(item.get("file_size_bytes")) for item in candidates),
        "recoverable_size": format_backup_size(sum(_to_int(item.get("file_size_bytes")) for item in candidates)),
        "candidates": candidates,
        "protected": protected,
        "items": items,
    }


def write_backup_cleanup_report(
    plan: dict[str, Any],
    reports_dir: str | Path,
    dry_run: bool,
    confirmed: bool,
    removed_files: list[Path] | None = None,
) -> tuple[Path, Path]:
    output_dir = Path(reports_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"backup_cleanup_{timestamp_for_path()}"
    markdown_path = output_dir / f"{base_name}.md"
    csv_path = output_dir / f"{base_name}.csv"
    removed = [str(path) for path in (removed_files or [])]
    markdown_path.write_text(
        render_backup_cleanup_markdown(plan, dry_run=dry_run, confirmed=confirmed, removed_files=removed),
        encoding="utf-8",
    )
    with csv_path.open("w", encoding="utf-8", newline="") as file:
        fieldnames = [
            "decision",
            "reason",
            "timestamp",
            "age_days",
            "file_size_bytes",
            "file_size",
            "backup_db",
            "manifest_path",
            "valid_manifest",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for item in plan["items"]:
            writer.writerow({field: item.get(field, "") for field in fieldnames})
    return markdown_path, csv_path


def render_backup_cleanup_markdown(
    plan: dict[str, Any],
    dry_run: bool,
    confirmed: bool,
    removed_files: list[str],
) -> str:
    lines = [
        "# Backup Cleanup Report",
        "",
        "## Resumo",
        "",
        f"- Gerado em: `{plan['generated_at']}`",
        f"- Retencao: {plan['retention_days']} dia(s)",
        f"- Modo: {'dry-run' if dry_run else 'execucao real'}",
        f"- Confirmado: {'sim' if confirmed else 'nao'}",
        f"- Backups encontrados: {plan['backups_found']}",
        f"- Candidatos a remocao: {plan['candidates_count']}",
        f"- Protegidos: {plan['protected_count']}",
        f"- Espaco recuperavel estimado: {plan['recoverable_size']}",
        "",
        "## Itens",
        "",
        "| Decisao | Motivo | Idade | Tamanho | Backup |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for item in plan["items"]:
        lines.append(
            "| "
            f"{item['decision']} | "
            f"{item['reason']} | "
            f"{item['age_days'] if item['age_days'] is not None else 'n/a'} | "
            f"{item['file_size']} | "
            f"`{item['backup_db']}` |"
        )
    lines.extend(["", "## Arquivos removidos", ""])
    if removed_files:
        lines.extend(f"- `{path}`" for path in removed_files)
    else:
        lines.append("- nenhum")
    return "\n".join(lines)


def sqlite_integrity_check(path: str | Path) -> str:
    try:
        with closing(sqlite3.connect(path)) as connection:
            return str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    except sqlite3.Error as exc:
        return str(exc)


def flatten_summary(summary: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flattened = {}
    for key, value in summary.items():
        label = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flattened.update(flatten_summary(value, label))
        else:
            flattened[label] = value
    return flattened


def _table_names(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name").fetchall()
    return [str(row[0]) for row in rows]


def _count_rows(connection: sqlite3.Connection, table_name: str) -> int:
    return _to_int(connection.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0])


def _count_where(connection: sqlite3.Connection, table_name: str, where_clause: str) -> int:
    return _to_int(connection.execute(f'SELECT COUNT(*) FROM "{table_name}" WHERE {where_clause}').fetchone()[0])


def _group_counts(connection: sqlite3.Connection, table_name: str, column_name: str) -> dict[str, int]:
    rows = connection.execute(
        f'SELECT COALESCE("{column_name}", "") AS label, COUNT(*) AS total '
        f'FROM "{table_name}" GROUP BY "{column_name}" ORDER BY total DESC'
    ).fetchall()
    return {str(row[0] or "n/a"): _to_int(row[1]) for row in rows}


def _scalar(connection: sqlite3.Connection, statement: str) -> Any:
    row = connection.execute(statement).fetchone()
    return row[0] if row else None


def _to_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_text(value: str) -> str:
    return str(value or "").replace("\n", " ").replace("\r", " ").strip()[:300]


def _read_manifest(manifest_path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _verify_backup_info(backup: BackupInfo) -> str:
    if not backup.backup_db.exists():
        return "arquivo ausente"
    sha_matches = not backup.sha256 or calculate_sha256(backup.backup_db) == backup.sha256
    integrity_ok = sqlite_integrity_check(backup.backup_db) == "ok"
    if sha_matches and integrity_ok:
        return "valido"
    if not sha_matches:
        return "sha divergente"
    return "integridade falhou"


def _cleanup_item(
    manifest_path: Path,
    backup_db: Path,
    timestamp: str,
    age_days: int | None,
    file_size_bytes: int,
    decision: str,
    reason: str,
    valid_manifest: bool,
) -> dict[str, Any]:
    return {
        "manifest_path": str(manifest_path),
        "backup_db": str(backup_db),
        "timestamp": timestamp,
        "age_days": age_days,
        "file_size_bytes": file_size_bytes,
        "file_size": format_backup_size(file_size_bytes),
        "decision": decision,
        "reason": reason,
        "valid_manifest": valid_manifest,
    }


def _age_days(timestamp: str, now: datetime) -> int | None:
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max((now - parsed).days, 0)
