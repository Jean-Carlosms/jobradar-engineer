from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from pathlib import Path
from time import perf_counter

from src.config import Settings, load_settings
from src.database import JobRepository
from src.profile import ProfileConfig, load_profile
from src.profile_summary import ProfileSummary, load_profile_summary
from src.schema_migrations import CURRENT_SCHEMA_VERSION, apply_schema_migrations, schema_status
from src.services.database_health import DatabaseHealthService
from src.services.database_maintenance import DatabaseMaintenanceService
from src.services.deduplicator import deduplicate_jobs
from src.services.email_sender import EmailSender
from src.services.feedback_insights import FeedbackInsightsService
from src.services.job_profile_analyzer import JobProfileAnalyzer
from src.services.job_review_service import JobReviewService
from src.services.matcher import JobMatcher
from src.services.operational_alerts import OperationalAlertService
from src.services.prefilter_audit import find_latest_prefilter_csv, generate_prefilter_audit
from src.services.run_history import RunHistoryService, format_operational_alerts_summary, format_run_history_summary
from src.services.run_reporter import RunReporter, find_latest_run_report, load_run_report_summary
from src.services.scheduler import run_daily
from src.sources.gupy_source import GupyPublicSource, MockGupySource
from src.sources.search_engine_source import SearchEngineSource
from src.utils.logger import setup_logging

logger = logging.getLogger(__name__)


def run_once(
    settings: Settings | None = None,
    profile: ProfileConfig | None = None,
    source: str = "all",
    min_score: float | None = None,
    email_dry_run: bool | None = None,
    analyze: bool = False,
    analysis_min_score: float = 0,
    reanalyze: bool = False,
    profile_summary: ProfileSummary | None = None,
    debug_search: bool = False,
    include_mock_in_all: bool = False,
    audit_prefilter: bool = False,
    audit_input: str | None = None,
    run_report: bool = False,
    operational_alerts: bool | None = None,
) -> int:
    settings = settings or load_settings()
    if email_dry_run is not None:
        settings = replace(settings, email_dry_run=email_dry_run)
    profile = profile or load_profile(settings.resolved_profile_path)
    setup_logging(logging.DEBUG if debug_search else logging.INFO)
    reporter = RunReporter(
        settings.project_root,
        mode="dry-run" if settings.email_dry_run else "production",
        source=source,
    ) if run_report else None
    auto_backup = run_auto_backup_before_run(settings, reporter=reporter)
    if auto_backup:
        logger.info("Backup automatico antes da execucao: %s", auto_backup.backup_db)

    repository = JobRepository(settings)
    repository.init_db()

    sources = build_sources(
        settings,
        source,
        profile=profile,
        debug_search=debug_search,
        include_mock_in_all=include_mock_in_all,
    )
    matcher = JobMatcher(profile)
    search_terms = profile.desired_titles or settings.search_terms
    locations = profile.desired_locations or settings.locations

    collected = []
    for job_source in sources:
        source_started = perf_counter()
        try:
            logger.info("Buscando vagas em %s.", job_source.name)
            source_jobs = job_source.fetch(search_terms, locations)
            collected.extend(source_jobs)
            if reporter:
                reporter.record_source(
                    job_source.name,
                    collected=len(source_jobs),
                    duration_seconds=perf_counter() - source_started,
                )
        except Exception as exc:
            logger.exception("Erro ao buscar vagas em %s. A execucao continuara.", job_source.name)
            if reporter:
                reporter.record_source_error(job_source.name, str(exc))

    scored = [matcher.score_listing(job) for job in collected]
    unique_jobs = deduplicate_jobs(scored)
    repository.save_jobs(unique_jobs)

    if analyze:
        profile_summary = profile_summary or load_profile_summary(settings.resolved_profile_summary_path)
        analyzer = JobProfileAnalyzer(profile_summary)
        analyzed_count = repository.analyze_jobs(
            analyzer,
            min_score=analysis_min_score,
            reanalyze=reanalyze,
        )
        logger.info("Analises geradas ou atualizadas: %s.", analyzed_count)

    effective_min_score = resolve_min_score(settings, profile, min_score)
    effective_limit = resolve_email_limit(settings, profile)
    jobs_to_send = repository.get_unsent_jobs(min_score=effective_min_score, limit=effective_limit)

    sender = EmailSender(settings)
    sent = sender.send_jobs(jobs_to_send, min_score=effective_min_score, limit=effective_limit)
    if reporter:
        if sent:
            reporter.record_email(sent=True)
        elif not jobs_to_send:
            reporter.record_email(sent=False, skip_reason="Nenhuma vaga elegivel para e-mail.")
        else:
            reporter.record_email(sent=False, skip_reason="Envio nao confirmado pelo EmailSender.")
    if sent and not settings.email_dry_run:
        repository.mark_jobs_sent([job.id for job in jobs_to_send])

    logger.info(
        "Execucao finalizada: %s coletadas, %s unicas, %s elegiveis para e-mail.",
        len(collected),
        len(unique_jobs),
        len(jobs_to_send),
    )
    if audit_prefilter:
        audit_result = run_prefilter_audit_only(settings=settings, audit_input=audit_input)
        if reporter and audit_result:
            reporter.add_generated_report(audit_result.markdown_path)
            reporter.add_generated_report(audit_result.csv_path)
    if reporter:
        reporter.record_totals(
            unique_jobs=len(unique_jobs),
            email_eligible_jobs=len(jobs_to_send),
            prefilter_discarded_jobs=max(len(scored) - len(unique_jobs), 0),
            prefilter_kept_jobs=len(unique_jobs),
            enriched_jobs=sum(1 for job in unique_jobs if (job.description_snippet or "")),
        )
        evaluate_operational_alert(settings, reporter, operational_alerts=operational_alerts)
        result = reporter.finish(settings.project_root / "runs")
        logger.info("Relatorio de execucao gerado: markdown=%s json=%s", result.markdown_path, result.json_path)
    return len(jobs_to_send)


def run_analysis_only(
    settings: Settings | None = None,
    profile_summary: ProfileSummary | None = None,
    analysis_min_score: float = 0,
    reanalyze: bool = False,
) -> int:
    settings = settings or load_settings()
    setup_logging()
    profile_summary = profile_summary or load_profile_summary(settings.resolved_profile_summary_path)

    repository = JobRepository(settings)
    repository.init_db()
    analyzer = JobProfileAnalyzer(profile_summary)
    analyzed_count = repository.analyze_jobs(
        analyzer,
        min_score=analysis_min_score,
        reanalyze=reanalyze,
    )
    logger.info("Analises geradas ou atualizadas: %s.", analyzed_count)
    return analyzed_count


def run_prefilter_audit_only(
    settings: Settings | None = None,
    audit_input: str | None = None,
):
    settings = settings or load_settings()
    setup_logging()
    input_path = Path(audit_input) if audit_input else find_latest_prefilter_csv(settings.project_root)
    if input_path is None:
        logger.warning("Nenhum CSV de pre-filtro encontrado em logs/gupy_debug.")
        return None
    if not input_path.is_absolute():
        input_path = settings.project_root / input_path
    result = generate_prefilter_audit(input_path, reports_dir=settings.project_root / "reports")
    logger.info(
        "Auditoria do pre-filtro gerada: markdown=%s csv=%s total=%s mantidas=%s descartadas=%s enriquecimento=%s",
        result.markdown_path,
        result.csv_path,
        result.total,
        result.kept,
        result.discarded,
        result.enrich,
    )
    return result


def run_review_summary(settings: Settings | None = None) -> str:
    settings = settings or load_settings()
    setup_logging()
    repository = JobRepository(settings)
    repository.init_db()
    service = JobReviewService(repository)
    summary_text = service.render_summary()
    print(summary_text)
    logger.info("Resumo de feedback gerado.")
    return summary_text


def run_export_review_feedback(settings: Settings | None = None):
    settings = settings or load_settings()
    setup_logging()
    repository = JobRepository(settings)
    repository.init_db()
    service = JobReviewService(repository)
    result = service.export_feedback_csv(settings.project_root / "reports")
    logger.info("Feedback exportado: arquivo=%s linhas=%s", result.path, result.row_count)
    print(f"Feedback exportado: {result.path} ({result.row_count} linha(s))")
    return result


def run_feedback_insights(settings: Settings | None = None, min_reviewed: int = 5):
    settings = settings or load_settings()
    setup_logging()
    repository = JobRepository(settings)
    repository.init_db()
    service = FeedbackInsightsService(repository)
    result = service.generate(settings.project_root / "reports", min_reviewed=min_reviewed)
    logger.info(
        "Insights de feedback gerados: markdown=%s csv=%s revisadas=%s baixa_confianca=%s",
        result.markdown_path,
        result.csv_path,
        result.reviewed_count,
        result.low_confidence,
    )
    print(
        "Insights de feedback gerados: "
        f"{result.markdown_path} e {result.csv_path} "
        f"({result.reviewed_count} vaga(s) revisada(s))"
    )
    if result.low_confidence:
        print("Aviso: baixa confianca por poucas vagas revisadas.")
    return result


def run_latest_run_report(settings: Settings | None = None) -> Path | None:
    settings = settings or load_settings()
    latest = find_latest_run_report(settings.project_root)
    if latest is None:
        print("Nenhum relatorio de execucao encontrado em runs/.")
        return None
    summary = load_run_report_summary(latest)
    print(f"Relatorio mais recente: {latest}")
    print(f"Resumo: {summary}")
    return latest


def run_history_summary(settings: Settings | None = None) -> dict:
    settings = settings or load_settings()
    service = RunHistoryService(settings.project_root)
    entries = service.load()
    summary = service.summary(entries)
    print(format_run_history_summary(summary))
    return summary


def run_operational_alerts_summary(settings: Settings | None = None) -> dict:
    settings = settings or load_settings()
    service = RunHistoryService(settings.project_root)
    entries = service.load()
    summary = service.summary(entries)
    print(format_operational_alerts_summary(summary))
    return summary


def run_auto_backup_before_run(settings: Settings, reporter: RunReporter | None = None):
    if not settings.auto_backup_before_run:
        return None
    if not settings.resolved_database_path.exists():
        logger.info("AUTO_BACKUP_BEFORE_RUN ativo, mas banco ainda nao existe. Backup ignorado.")
        return None
    result = DatabaseMaintenanceService(settings.project_root, settings.resolved_database_path).create_backup(
        reason="automatic before run"
    )
    if reporter:
        reporter.add_generated_report(result.backup_db)
        reporter.add_generated_report(result.manifest_path)
    return result


def run_backup_db(settings: Settings | None = None, reason: str = "manual"):
    settings = settings or load_settings()
    setup_logging()
    result = DatabaseMaintenanceService(settings.project_root, settings.resolved_database_path).create_backup(reason)
    logger.info("Backup criado: db=%s manifest=%s", result.backup_db, result.manifest_path)
    print(f"Backup criado: {result.backup_db}")
    print(f"Manifesto: {result.manifest_path}")
    print(f"SHA256: {result.sha256}")
    return result


def run_list_db_backups(settings: Settings | None = None):
    settings = settings or load_settings()
    service = DatabaseMaintenanceService(settings.project_root, settings.resolved_database_path)
    backups = service.list_backups()
    if not backups:
        print("Nenhum backup encontrado em backups/.")
        return backups
    for backup in backups:
        print(
            f"{backup.timestamp} | {backup.backup_db} | "
            f"{backup.file_size_bytes} bytes | reason={backup.reason}"
        )
    return backups


def run_verify_db_backup(settings: Settings | None = None, backup_path: str | Path = ""):
    settings = settings or load_settings()
    result = DatabaseMaintenanceService(settings.project_root, settings.resolved_database_path).verify_backup(backup_path)
    print(f"Backup: {result.backup_db}")
    print(f"Valido: {'sim' if result.valid else 'nao'}")
    print(f"SHA confere: {'sim' if result.sha256_matches else 'nao'}")
    print(f"Integridade SQLite: {'ok' if result.integrity_ok else 'falha'}")
    print(f"Mensagem: {result.message}")
    return result


def run_restore_db_backup(settings: Settings | None = None, backup_path: str | Path = "", confirm_restore: bool = False):
    settings = settings or load_settings()
    setup_logging()
    result = DatabaseMaintenanceService(settings.project_root, settings.resolved_database_path).restore_backup(
        backup_path,
        confirm_restore=confirm_restore,
    )
    logger.warning("Restore executado: backup=%s destino=%s", result.backup_used, result.restored_db)
    print(f"Banco restaurado: {result.restored_db}")
    print(f"Backup usado: {result.backup_used}")
    if result.pre_restore_backup:
        print(f"Backup automatico pre-restore: {result.pre_restore_backup}")
    return result


def run_db_maintenance(settings: Settings | None = None):
    settings = settings or load_settings()
    setup_logging()
    result = DatabaseMaintenanceService(settings.project_root, settings.resolved_database_path).run_maintenance()
    logger.info("Manutencao SQLite concluida: %s", result.database_path)
    print(f"Banco: {result.database_path}")
    print(f"Integridade antes: {result.integrity_before}")
    print(f"Integridade depois: {result.integrity_after}")
    print(f"Paginas: {result.page_count}")
    print(f"Freelist: {result.freelist_count}")
    return result


def run_export_db_summary(settings: Settings | None = None):
    settings = settings or load_settings()
    setup_logging()
    result = DatabaseMaintenanceService(settings.project_root, settings.resolved_database_path).export_summary(
        settings.project_root / "reports"
    )
    logger.info("Resumo do banco exportado: json=%s csv=%s", result.json_path, result.csv_path)
    print(f"Resumo JSON: {result.json_path}")
    print(f"Resumo CSV: {result.csv_path}")
    return result


def run_db_backup_summary(settings: Settings | None = None) -> dict:
    settings = settings or load_settings()
    summary = DatabaseMaintenanceService(settings.project_root, settings.resolved_database_path).backup_summary()
    print(f"Backups: {summary['total_backups']}")
    print(f"Tamanho total: {summary['total_size']}")
    print(f"Backup mais recente: {summary['latest_backup'] or 'n/a'}")
    print(
        "Maior backup: "
        f"{summary['largest_backup'] or 'n/a'} "
        f"({summary['largest_backup_size']})"
    )
    return summary


def run_cleanup_db_backups(
    settings: Settings | None = None,
    dry_run: bool | None = None,
    confirm_cleanup: bool = False,
):
    settings = settings or load_settings()
    setup_logging()
    effective_dry_run = True if dry_run is True or not confirm_cleanup else False
    result = DatabaseMaintenanceService(settings.project_root, settings.resolved_database_path).cleanup_backups(
        retention_days=settings.backup_retention_days,
        reports_dir=settings.project_root / "reports",
        dry_run=effective_dry_run,
        confirm_cleanup=confirm_cleanup,
    )
    print(f"Backups encontrados: {result.plan['backups_found']}")
    print(f"Candidatos a remocao: {result.plan['candidates_count']}")
    print(f"Protegidos: {result.plan['protected_count']}")
    print(f"Espaco recuperavel estimado: {result.plan['recoverable_size']}")
    print(f"Modo: {'dry-run' if result.dry_run else 'execucao real'}")
    print(f"Arquivos removidos: {len(result.removed_files)}")
    print(f"Relatorio Markdown: {result.markdown_path}")
    print(f"Relatorio CSV: {result.csv_path}")
    return result


def run_schema_status(settings: Settings | None = None):
    settings = settings or load_settings()
    result = schema_status(settings.resolved_database_path)
    print(f"Banco: {result.db_path}")
    print(f"Versao esperada: {CURRENT_SCHEMA_VERSION}")
    print(f"Migracoes aplicadas: {result.applied_versions or []}")
    print(f"Status: {result.status}")
    return result


def run_migrate_schema(settings: Settings | None = None):
    settings = settings or load_settings()
    setup_logging()
    result = apply_schema_migrations(settings.resolved_database_path)
    logger.info(
        "Migracao de schema concluida: banco=%s status=%s aplicadas_agora=%s",
        result.db_path,
        result.status,
        result.applied_now,
    )
    print(f"Banco: {result.db_path}")
    print(f"Versao esperada: {CURRENT_SCHEMA_VERSION}")
    print(f"Migracoes aplicadas agora: {result.applied_now or []}")
    print(f"Migracoes aplicadas: {result.applied_versions or []}")
    print(f"Status: {result.status}")
    return result


def run_db_health(settings: Settings | None = None) -> dict:
    settings = settings or load_settings()
    health = DatabaseHealthService(settings.project_root, settings.resolved_database_path).collect()
    print(f"Banco: {health['database_path']}")
    print(f"Tamanho: {health['file_size']}")
    print(f"Integridade: {health['integrity_check']}")
    print(f"Schema: {health['schema_status']} (versao esperada {health['schema_current_version']})")
    print(f"Tabelas: {health['table_count']}")
    print(f"Indices: {health['index_count']}")
    print(f"Freelist: {health['freelist_count']}")
    print("Linhas por tabela:")
    for table_name, row_count in health["table_rows"].items():
        print(f"- {table_name}: {row_count}")
    print("Indices encontrados:")
    for index in health["indexes"]:
        columns = ", ".join(index.get("columns") or [])
        print(f"- {index['name']} ({index['table']}): {columns}")
    return health


def run_export_db_health(settings: Settings | None = None):
    settings = settings or load_settings()
    result = DatabaseHealthService(settings.project_root, settings.resolved_database_path).export(
        settings.project_root / "reports"
    )
    print(f"Saude JSON: {result.json_path}")
    print(f"Saude Markdown: {result.markdown_path}")
    print(f"Integridade: {result.health['integrity_check']}")
    print(f"Schema: {result.health['schema_status']}")
    return result


def evaluate_operational_alert(
    settings: Settings,
    reporter: RunReporter,
    operational_alerts: bool | None = None,
) -> bool:
    if operational_alerts is True:
        alert_settings = replace(settings, operational_alerts_enabled=True)
    elif operational_alerts is False:
        alert_settings = replace(settings, operational_alerts_enabled=False)
    else:
        alert_settings = settings

    alert = OperationalAlertService(alert_settings).build_alert(reporter.report, force_enabled=operational_alerts is True)
    sent = False
    if alert.should_send:
        sent = EmailSender(alert_settings).send_operational_alert(alert.subject, alert.body_text)
        if sent:
            logger.info("Alerta operacional processado: tipo=%s status=enviado_ou_dry_run.", alert.alert_type)
        else:
            logger.warning("Alerta operacional nao enviado: tipo=%s.", alert.alert_type)
    else:
        logger.info("Alerta operacional nao enviado: tipo=%s motivo=%s", alert.alert_type, alert.reason)
    reporter.record_operational_alert(
        alert_type=alert.alert_type,
        should_send=alert.should_send,
        sent=sent,
        reason=alert.reason if not sent else "enviado ou dry-run",
    )
    return sent


def run_test_operational_alert(settings: Settings | None = None) -> bool:
    settings = replace(settings or load_settings(), email_dry_run=True)
    reporter = RunReporter(settings.project_root, mode="dry-run", source="mock", run_id="test-operational-alert")
    reporter.record_source_error("GupySimulada", "Falha ficticia para validar template de alerta.")
    reporter.record_totals(unique_jobs=0, email_eligible_jobs=0)
    alert = OperationalAlertService(replace(settings, operational_alerts_enabled=True)).build_alert(reporter.report)
    print(f"Alerta operacional de teste: {alert.subject}")
    print(alert.body_text)
    sent = EmailSender(settings).send_operational_alert(alert.subject, alert.body_text)
    print(f"Resultado: {'enviado/dry-run' if sent else 'nao enviado'}")
    return sent


def build_sources(
    settings: Settings,
    source: str,
    profile: ProfileConfig | None = None,
    debug_search: bool = False,
    include_mock_in_all: bool = False,
):
    if source == "mock":
        return [MockGupySource(settings)]
    if source == "gupy":
        return [GupyPublicSource(settings, profile=profile, debug_search=debug_search)]
    if source == "search":
        return [SearchEngineSource(settings, debug_search=debug_search)]
    sources = [
        GupyPublicSource(settings, profile=profile, debug_search=debug_search),
        SearchEngineSource(settings, debug_search=debug_search),
    ]
    if include_mock_in_all:
        sources.append(MockGupySource(settings))
    return sources


def resolve_min_score(settings: Settings, profile: ProfileConfig, cli_min_score: float | None = None) -> float:
    if cli_min_score is not None:
        return cli_min_score
    if settings.min_score_to_email is not None:
        return settings.min_score_to_email
    return profile.min_score_to_email


def resolve_email_limit(settings: Settings, profile: ProfileConfig) -> int:
    if settings.max_email_jobs is not None:
        return settings.max_email_jobs
    return profile.max_email_jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="JobRadar Engineer")
    parser.add_argument("--schedule", action="store_true", help="Executa diariamente via APScheduler.")
    email_mode = parser.add_mutually_exclusive_group()
    email_mode.add_argument("--dry-run", action="store_true", help="Gera o e-mail sem enviar via SMTP.")
    email_mode.add_argument("--send-email", action="store_true", help="Envia via SMTP usando as credenciais do .env.")
    parser.add_argument(
        "--source",
        choices=["mock", "gupy", "search", "all"],
        default="all",
        help="Seleciona fonte mock, Gupy publica, busca publica ou combinacao.",
    )
    parser.add_argument("--include-mock-in-all", action="store_true", help="Inclui fonte mock quando --source all for usado.")
    parser.add_argument("--min-score", type=float, default=None, help="Score minimo para envio nesta execucao.")
    parser.add_argument("--analyze", action="store_true", help="Gera analises vaga x perfil apos coletar vagas.")
    parser.add_argument("--analyze-only", action="store_true", help="Analisa vagas ja salvas, sem coletar nem enviar e-mail.")
    parser.add_argument("--reanalyze", action="store_true", help="Atualiza analises existentes alem de criar novas.")
    parser.add_argument("--analysis-min-score", type=float, default=0, help="Score minimo para gerar analise.")
    parser.add_argument("--debug-search", action="store_true", help="Ativa logs e arquivos de diagnostico da BuscaPublica.")
    parser.add_argument("--audit-prefilter", action="store_true", help="Gera relatorio de auditoria apos a coleta Gupy.")
    parser.add_argument("--audit-prefilter-only", action="store_true", help="Gera auditoria a partir de CSV existente.")
    parser.add_argument("--audit-input", default=None, help="CSV de pre-filtro especifico para auditar.")
    parser.add_argument("--review-summary", action="store_true", help="Mostra resumo do feedback humano salvo no banco.")
    parser.add_argument("--export-review-feedback", action="store_true", help="Exporta feedback humano para CSV em reports/.")
    parser.add_argument("--feedback-insights", action="store_true", help="Gera insights assistivos a partir do feedback humano.")
    parser.add_argument(
        "--feedback-insights-min-reviewed",
        type=int,
        default=5,
        help="Minimo de vagas revisadas para reduzir o aviso de baixa confianca.",
    )
    report_mode = parser.add_mutually_exclusive_group()
    report_mode.add_argument("--run-report", action="store_true", help="Gera relatorio local da execucao em runs/.")
    report_mode.add_argument("--no-run-report", action="store_true", help="Nao gera relatorio local da execucao.")
    operational_mode = parser.add_mutually_exclusive_group()
    operational_mode.add_argument("--send-operational-alerts", action="store_true", help="Habilita alertas operacionais.")
    operational_mode.add_argument("--no-operational-alerts", action="store_true", help="Desabilita alertas operacionais.")
    parser.add_argument("--latest-run-report", action="store_true", help="Mostra o relatorio de execucao mais recente.")
    parser.add_argument("--run-history-summary", action="store_true", help="Mostra resumo do historico em runs/.")
    parser.add_argument("--operational-alerts-summary", action="store_true", help="Mostra resumo dos alertas em runs/.")
    parser.add_argument("--test-operational-alert", action="store_true", help="Gera alerta operacional ficticio.")
    parser.add_argument("--backup-db", action="store_true", help="Cria backup do banco SQLite local em backups/.")
    parser.add_argument("--backup-reason", default="manual", help="Motivo registrado no manifesto do backup.")
    parser.add_argument("--list-db-backups", action="store_true", help="Lista backups disponiveis em backups/.")
    parser.add_argument("--verify-db-backup", default=None, help="Verifica integridade de um backup .db ou manifesto .json.")
    parser.add_argument("--restore-db-backup", default=None, help="Restaura backup .db ou manifesto .json para data/jobs.db.")
    parser.add_argument("--confirm-restore", action="store_true", help="Confirma explicitamente a restauracao do banco.")
    parser.add_argument("--db-maintenance", action="store_true", help="Executa VACUUM e ANALYZE no banco local.")
    parser.add_argument("--export-db-summary", action="store_true", help="Exporta resumo do banco para reports/.")
    parser.add_argument("--db-backup-summary", action="store_true", help="Mostra resumo dos backups em backups/.")
    parser.add_argument("--cleanup-db-backups", action="store_true", help="Planeja ou executa limpeza de backups antigos.")
    parser.add_argument("--cleanup-db-backups-dry-run", action="store_true", help="Mostra plano de limpeza sem apagar backups.")
    parser.add_argument("--confirm-cleanup-backups", action="store_true", help="Confirma remocao de backups candidatos.")
    parser.add_argument("--schema-status", action="store_true", help="Mostra status das migracoes do schema SQLite.")
    parser.add_argument("--migrate-schema", action="store_true", help="Aplica migracoes pendentes do schema SQLite.")
    parser.add_argument("--db-health", action="store_true", help="Mostra resumo de saude do banco SQLite.")
    parser.add_argument("--export-db-health", action="store_true", help="Exporta saude do banco para reports/.")
    args = parser.parse_args()

    settings = load_settings()
    email_dry_run = None
    if args.dry_run:
        email_dry_run = True
    if args.send_email:
        email_dry_run = False
    if email_dry_run is not None:
        settings = replace(settings, email_dry_run=email_dry_run)

    if args.backup_db:
        run_backup_db(settings=settings, reason=args.backup_reason)
        return
    if args.list_db_backups:
        run_list_db_backups(settings=settings)
        return
    if args.verify_db_backup:
        run_verify_db_backup(settings=settings, backup_path=args.verify_db_backup)
        return
    if args.restore_db_backup:
        run_restore_db_backup(
            settings=settings,
            backup_path=args.restore_db_backup,
            confirm_restore=args.confirm_restore,
        )
        return
    if args.db_maintenance:
        run_db_maintenance(settings=settings)
        return
    if args.export_db_summary:
        run_export_db_summary(settings=settings)
        return
    if args.db_backup_summary:
        run_db_backup_summary(settings=settings)
        return
    if args.cleanup_db_backups or args.cleanup_db_backups_dry_run:
        run_cleanup_db_backups(
            settings=settings,
            dry_run=True if args.cleanup_db_backups_dry_run else None,
            confirm_cleanup=args.confirm_cleanup_backups,
        )
        return
    if args.schema_status:
        run_schema_status(settings=settings)
        return
    if args.migrate_schema:
        run_migrate_schema(settings=settings)
        return
    if args.db_health:
        run_db_health(settings=settings)
        return
    if args.export_db_health:
        run_export_db_health(settings=settings)
        return

    profile = load_profile(settings.resolved_profile_path)
    profile_summary = load_profile_summary(settings.resolved_profile_summary_path)

    operational_alerts = None
    if args.send_operational_alerts:
        operational_alerts = True
    if args.no_operational_alerts:
        operational_alerts = False

    if args.review_summary:
        run_review_summary(settings=settings)
    elif args.latest_run_report:
        run_latest_run_report(settings=settings)
    elif args.run_history_summary:
        run_history_summary(settings=settings)
    elif args.operational_alerts_summary:
        run_operational_alerts_summary(settings=settings)
    elif args.test_operational_alert:
        run_test_operational_alert(settings=settings)
    elif args.export_review_feedback:
        run_export_review_feedback(settings=settings)
    elif args.feedback_insights:
        run_feedback_insights(settings=settings, min_reviewed=args.feedback_insights_min_reviewed)
    elif args.audit_prefilter_only:
        run_prefilter_audit_only(settings=settings, audit_input=args.audit_input)
    elif args.analyze_only or (args.reanalyze and not args.analyze and not args.schedule):
        run_analysis_only(
            settings=settings,
            profile_summary=profile_summary,
            analysis_min_score=args.analysis_min_score,
            reanalyze=args.reanalyze,
        )
    elif args.schedule:
        setup_logging()
        run_daily(
            lambda: run_once(
                settings=settings,
                profile=profile,
                source=args.source,
                min_score=args.min_score,
                email_dry_run=email_dry_run,
                analyze=args.analyze,
                analysis_min_score=args.analysis_min_score,
                reanalyze=args.reanalyze,
                profile_summary=profile_summary,
                debug_search=args.debug_search,
                include_mock_in_all=args.include_mock_in_all,
                audit_prefilter=args.audit_prefilter,
                audit_input=args.audit_input,
                run_report=args.run_report and not args.no_run_report,
                operational_alerts=operational_alerts,
            ),
            settings,
        )
    else:
        run_once(
            settings=settings,
            profile=profile,
            source=args.source,
            min_score=args.min_score,
            email_dry_run=email_dry_run,
            analyze=args.analyze,
            analysis_min_score=args.analysis_min_score,
            reanalyze=args.reanalyze,
            profile_summary=profile_summary,
            debug_search=args.debug_search,
            include_mock_in_all=args.include_mock_in_all,
            audit_prefilter=args.audit_prefilter,
            audit_input=args.audit_input,
            run_report=args.run_report and not args.no_run_report,
            operational_alerts=operational_alerts,
        )


if __name__ == "__main__":
    main()
