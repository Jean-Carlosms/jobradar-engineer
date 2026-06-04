from __future__ import annotations

import argparse
import logging
from dataclasses import replace
from pathlib import Path

from src.config import Settings, load_settings
from src.database import JobRepository
from src.profile import ProfileConfig, load_profile
from src.profile_summary import ProfileSummary, load_profile_summary
from src.services.deduplicator import deduplicate_jobs
from src.services.email_sender import EmailSender
from src.services.job_profile_analyzer import JobProfileAnalyzer
from src.services.job_review_service import JobReviewService
from src.services.matcher import JobMatcher
from src.services.prefilter_audit import find_latest_prefilter_csv, generate_prefilter_audit
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
) -> int:
    settings = settings or load_settings()
    if email_dry_run is not None:
        settings = replace(settings, email_dry_run=email_dry_run)
    profile = profile or load_profile(settings.resolved_profile_path)
    setup_logging(logging.DEBUG if debug_search else logging.INFO)

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
        try:
            logger.info("Buscando vagas em %s.", job_source.name)
            collected.extend(job_source.fetch(search_terms, locations))
        except Exception:
            logger.exception("Erro ao buscar vagas em %s. A execucao continuara.", job_source.name)

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
    if sent and not settings.email_dry_run:
        repository.mark_jobs_sent([job.id for job in jobs_to_send])

    logger.info(
        "Execucao finalizada: %s coletadas, %s unicas, %s elegiveis para e-mail.",
        len(collected),
        len(unique_jobs),
        len(jobs_to_send),
    )
    if audit_prefilter:
        run_prefilter_audit_only(settings=settings, audit_input=audit_input)
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
    args = parser.parse_args()

    settings = load_settings()
    profile = load_profile(settings.resolved_profile_path)
    profile_summary = load_profile_summary(settings.resolved_profile_summary_path)
    email_dry_run = None
    if args.dry_run:
        email_dry_run = True
    if args.send_email:
        email_dry_run = False

    if args.review_summary:
        run_review_summary(settings=settings)
    elif args.export_review_feedback:
        run_export_review_feedback(settings=settings)
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
        )


if __name__ == "__main__":
    main()
