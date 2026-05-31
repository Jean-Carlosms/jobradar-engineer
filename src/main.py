from __future__ import annotations

import argparse
import logging
from dataclasses import replace

from src.config import Settings, load_settings
from src.database import JobRepository
from src.profile import ProfileConfig, load_profile
from src.profile_summary import ProfileSummary, load_profile_summary
from src.services.deduplicator import deduplicate_jobs
from src.services.email_sender import EmailSender
from src.services.job_profile_analyzer import JobProfileAnalyzer
from src.services.matcher import JobMatcher
from src.services.scheduler import run_daily
from src.sources.gupy_source import GupySource
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
) -> int:
    settings = settings or load_settings()
    if email_dry_run is not None:
        settings = replace(settings, email_dry_run=email_dry_run)
    profile = profile or load_profile(settings.resolved_profile_path)
    setup_logging()

    repository = JobRepository(settings)
    repository.init_db()

    sources = build_sources(settings, source)
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
    if sent:
        repository.mark_jobs_sent([job.id for job in jobs_to_send])

    logger.info(
        "Execucao finalizada: %s coletadas, %s unicas, %s elegiveis para e-mail.",
        len(collected),
        len(unique_jobs),
        len(jobs_to_send),
    )
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


def build_sources(settings: Settings, source: str):
    if source == "mock":
        return [GupySource(settings)]
    if source == "search":
        return [SearchEngineSource(settings)]
    return [GupySource(settings), SearchEngineSource(settings)]


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
        choices=["mock", "search", "all"],
        default="all",
        help="Seleciona fonte simulada, busca publica ou ambas.",
    )
    parser.add_argument("--min-score", type=float, default=None, help="Score minimo para envio nesta execucao.")
    parser.add_argument("--analyze", action="store_true", help="Gera analises vaga x perfil apos coletar vagas.")
    parser.add_argument("--analyze-only", action="store_true", help="Analisa vagas ja salvas, sem coletar nem enviar e-mail.")
    parser.add_argument("--reanalyze", action="store_true", help="Atualiza analises existentes alem de criar novas.")
    parser.add_argument("--analysis-min-score", type=float, default=0, help="Score minimo para gerar analise.")
    args = parser.parse_args()

    settings = load_settings()
    profile = load_profile(settings.resolved_profile_path)
    profile_summary = load_profile_summary(settings.resolved_profile_summary_path)
    email_dry_run = None
    if args.dry_run:
        email_dry_run = True
    if args.send_email:
        email_dry_run = False

    if args.analyze_only or (args.reanalyze and not args.analyze and not args.schedule):
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
        )


if __name__ == "__main__":
    main()
