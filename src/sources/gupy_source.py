from __future__ import annotations

import json
import logging
import re
import time
import csv
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.gupy_companies import GupyCompany, load_gupy_companies
from src.models.job import JobListing
from src.profile import ProfileConfig
from src.sources.base import JobSource
from src.services.job_prefilter import JobPrefilter, JobPrefilterResult
from src.utils.text_cleaner import compact_key

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GupyExtractedJob:
    title: str
    company: str
    location: str
    url: str
    description_snippet: str
    query_used: str
    published_date: str | None = None
    company_category: str = ""
    company_priority: bool = False


@dataclass
class GupyCompanyRunStatus:
    name: str
    slug: str
    base_url: str
    category: str
    priority: bool
    configured_status: str
    notes: str
    status_http: int | str = ""
    jobs_found: int = 0
    jobs_created: int = 0
    error: str = ""

    @classmethod
    def from_company(cls, company: GupyCompany) -> "GupyCompanyRunStatus":
        return cls(
            name=company.name,
            slug=company.slug,
            base_url=company.base_url,
            category=company.category,
            priority=company.priority,
            configured_status=company.status,
            notes=company.notes,
        )


@dataclass(frozen=True)
class GupyJobDetail:
    title: str = ""
    company: str = ""
    location: str = ""
    work_mode: str = ""
    description: str = ""
    responsibilities: str = ""
    requirements: str = ""
    benefits: str = ""
    published_date: str | None = None
    job_id: str = ""

    @property
    def aggregated_text(self) -> str:
        parts = [
            self.description,
            self.responsibilities,
            self.requirements,
            self.benefits,
            self.work_mode,
        ]
        return " ".join(part.strip() for part in parts if part and part.strip())


class GupyJobDetailParser:
    def parse(self, html: str, fallback_url: str = "") -> GupyJobDetail:
        soup = BeautifulSoup(html or "", "html.parser")
        json_detail = self._parse_json_detail(soup)
        html_detail = self._parse_html_detail(soup, fallback_url=fallback_url)

        return GupyJobDetail(
            title=json_detail.title or html_detail.title,
            company=json_detail.company or html_detail.company,
            location=json_detail.location or html_detail.location,
            work_mode=json_detail.work_mode or html_detail.work_mode,
            description=json_detail.description or html_detail.description,
            responsibilities=json_detail.responsibilities or html_detail.responsibilities,
            requirements=json_detail.requirements or html_detail.requirements,
            benefits=json_detail.benefits or html_detail.benefits,
            published_date=json_detail.published_date or html_detail.published_date,
            job_id=json_detail.job_id or html_detail.job_id,
        )

    def _parse_html_detail(self, soup: BeautifulSoup, fallback_url: str) -> GupyJobDetail:
        page_text = self._clean_text(soup.get_text(" ", strip=True))
        title_node = soup.select_one("h1") or soup.select_one("[data-testid*=job-title]")
        title = self._clean_text(title_node.get_text(" ", strip=True)) if title_node else ""
        title = title or self._title_from_url(fallback_url)

        return GupyJobDetail(
            title=title,
            location=self._extract_location(page_text),
            work_mode=self._extract_work_mode(page_text),
            description=self._section_text(soup, ["descricao", "descrição", "sobre a vaga", "job description"]) or page_text,
            responsibilities=self._section_text(soup, ["responsabilidades", "atividades", "como sera", "como será"]),
            requirements=self._section_text(soup, ["requisitos", "qualificacoes", "qualificações"]),
            benefits=self._section_text(soup, ["beneficios", "benefícios"]),
            published_date=self._extract_date(page_text),
            job_id=self._extract_job_id(fallback_url, page_text),
        )

    def _parse_json_detail(self, soup: BeautifulSoup) -> GupyJobDetail:
        for script in soup.find_all("script"):
            text = script.string or script.get_text("", strip=False)
            for payload in self._json_payloads_from_script(text):
                detail = self._detail_from_payload(payload)
                if detail.title or detail.description or detail.requirements:
                    return detail
        return GupyJobDetail()

    def _detail_from_payload(self, payload: object) -> GupyJobDetail:
        for item in self._walk_json(payload):
            if not isinstance(item, dict):
                continue
            title = self._first_value(item, ["title", "name", "jobTitle", "role"])
            description = self._first_value(item, ["description", "summary", "jobDescription"])
            requirements = self._first_value(item, ["requirements", "prerequisites", "qualifications"])
            responsibilities = self._first_value(item, ["responsibilities", "activities", "tasks"])
            benefits = self._first_value(item, ["benefits"])
            if not any([title, description, requirements, responsibilities, benefits]):
                continue
            return GupyJobDetail(
                title=self._clean_text(title),
                company=self._clean_text(self._first_value(item, ["company", "companyName"])),
                location=self._format_location(self._first_value(item, ["location", "workplace", "address"])),
                work_mode=self._clean_text(self._first_value(item, ["workplaceType", "workModel", "workMode"])),
                description=self._clean_text(description),
                responsibilities=self._clean_text(responsibilities),
                requirements=self._clean_text(requirements),
                benefits=self._clean_text(benefits),
                published_date=self._clean_text(self._first_value(item, ["publishedDate", "published_at", "createdAt"])),
                job_id=self._clean_text(self._first_value(item, ["id", "jobId", "code"])),
            )
        return GupyJobDetail()

    def _section_text(self, soup: BeautifulSoup, labels: list[str]) -> str:
        normalized_labels = [self._normalize(label) for label in labels]
        for node in soup.find_all(["section", "article", "div"]):
            text = self._clean_text(node.get_text(" ", strip=True))
            normalized_text = self._normalize(text[:120])
            if any(label in normalized_text for label in normalized_labels) and len(text) > 20:
                return text
        return ""

    def _json_payloads_from_script(self, text: str) -> list[object]:
        payloads: list[object] = []
        text = (text or "").strip()
        if not text:
            return payloads
        candidates = [text]
        candidates.extend(match.group(1) for match in re.finditer(r"({.*?})", text, flags=re.DOTALL))
        for candidate in candidates:
            try:
                payloads.append(json.loads(candidate))
            except json.JSONDecodeError:
                continue
        return payloads

    def _walk_json(self, payload: object):
        if isinstance(payload, dict):
            yield payload
            for value in payload.values():
                yield from self._walk_json(value)
        elif isinstance(payload, list):
            for item in payload:
                yield from self._walk_json(item)

    def _first_value(self, item: dict, keys: list[str]) -> object | None:
        for key in keys:
            value = item.get(key)
            if value not in (None, ""):
                return value
        return None

    def _format_location(self, value: object) -> str:
        if not value:
            return ""
        if isinstance(value, str):
            return self._clean_text(value)
        if isinstance(value, dict):
            address = value.get("address") if isinstance(value.get("address"), dict) else value
            city = address.get("city") if isinstance(address, dict) else None
            state = (address.get("stateShortName") or address.get("state")) if isinstance(address, dict) else None
            workplace_type = value.get("workplaceType") or value.get("type")
            parts = [str(part) for part in [city, state, workplace_type] if part]
            return " - ".join(parts)
        return self._clean_text(value)

    def _extract_location(self, text: str) -> str:
        match = re.search(r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÀ-ÿ ]+)\s*-\s*(SP|RJ|MG|PR|SC|RS|BA|PE|CE|GO|DF)", text)
        return match.group(0) if match else ""

    def _extract_work_mode(self, text: str) -> str:
        lowered = text.lower()
        for mode in ["remoto", "híbrido", "hibrido", "presencial", "on-site", "remote", "hybrid"]:
            if mode in lowered:
                return mode
        return ""

    def _extract_date(self, text: str) -> str | None:
        match = re.search(r"\b\d{2}/\d{2}/\d{4}\b|\b\d{4}-\d{2}-\d{2}\b", text)
        return match.group(0) if match else None

    def _extract_job_id(self, fallback_url: str, text: str) -> str:
        url_match = re.search(r"/jobs/(\d+)", fallback_url or "")
        if url_match:
            return url_match.group(1)
        text_match = re.search(r"\bjobId[\"': ]+(\d+)\b", text)
        return text_match.group(1) if text_match else ""

    def _title_from_url(self, url: str) -> str:
        path = urlparse(url or "").path.rstrip("/").split("/")[-1]
        return path.replace("-", " ").replace("_", " ").title() if path else ""

    def _clean_text(self, value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, dict):
            value = " ".join(str(item) for item in value.values() if isinstance(item, str))
        return re.sub(r"\s+", " ", unescape(str(value))).strip()

    def _normalize(self, value: str) -> str:
        replacements = str.maketrans("áàâãéêíóôõúüç", "aaaaeeiooouuc")
        return value.lower().translate(replacements)


class MockGupySource(JobSource):
    name = "GupySimulada"

    def fetch(self, keywords: list[str], locations: list[str]) -> list[JobListing]:
        return [
            JobListing(
                title="Engenheiro de Automacao Industrial",
                company="Empresa Industrial Exemplo",
                location="Campinas - Hibrido",
                source=self.name,
                url="https://jobs.example.com/gupy/engenheiro-automacao-industrial",
                description_snippet=(
                    "Atuacao com CLP Siemens, redes industriais, melhoria de processos, "
                    "Python para automacao e dashboards em Power BI."
                ),
                published_date="recente",
                query_used="mock:gupy:Engenheiro de Automacao:Campinas",
            ),
            JobListing(
                title="Manufacturing Engineer",
                company="Siemens",
                location="Sorocaba",
                source=self.name,
                url="https://jobs.example.com/gupy/manufacturing-engineer-sorocaba",
                description_snippet=(
                    "Projetos de manufatura, Industria 4.0, analise de dados, PLC Rockwell "
                    "e suporte tecnico para linhas automatizadas."
                ),
                published_date="recente",
                query_used="mock:gupy:Manufacturing Engineer:Sorocaba",
            ),
            JobListing(
                title="Vendedor Tecnico",
                company="Comercial Exemplo",
                location="Sao Paulo",
                source=self.name,
                url="https://jobs.example.com/gupy/vendedor-tecnico",
                description_snippet="Vaga comercial pura para vendas externas e prospeccao.",
                published_date="recente",
                query_used="mock:gupy:Vendedor Tecnico:Sao Paulo",
            ),
        ]


class GupyPublicSource(JobSource):
    name = "GupyPublic"

    def __init__(
        self,
        settings,
        companies: list[GupyCompany] | None = None,
        profile: ProfileConfig | None = None,
        debug_search: bool = False,
    ) -> None:
        super().__init__(settings)
        self.companies = companies
        self.profile = profile or ProfileConfig(desired_locations=list(settings.locations))
        self.prefilter = JobPrefilter(self.profile)
        self.debug_search = debug_search
        self.debug_dir = self.settings.project_root / "logs" / "gupy_debug"
        self.detail_parser = GupyJobDetailParser()
        self.company_statuses: list[GupyCompanyRunStatus] = []

    def fetch(self, keywords: list[str], locations: list[str]) -> list[JobListing]:
        companies = self.companies or load_gupy_companies(self.settings.resolved_gupy_companies_path)
        collected: list[GupyExtractedJob] = []
        self.company_statuses = []

        for company in companies:
            status = GupyCompanyRunStatus.from_company(company)
            try:
                company_jobs = self._fetch_company(company, status)
                status.jobs_created = len(company_jobs)
                logger.info(
                    "GupyPublic empresa=%s categoria=%s prioridade=%s status_config=%s notas=%s vagas_criadas=%s",
                    company.name,
                    company.category,
                    company.priority,
                    company.status,
                    company.notes,
                    len(company_jobs),
                )
                collected.extend(company_jobs)
            except requests.RequestException as exc:
                status.error = status.error or str(exc)
                logger.warning(
                    "GupyPublic falha HTTP empresa=%s categoria=%s prioridade=%s status_config=%s notas=%s erro=%s",
                    company.name,
                    company.category,
                    company.priority,
                    company.status,
                    company.notes,
                    exc,
                )
            except Exception:
                status.error = status.error or "unexpected error"
                logger.exception(
                    "GupyPublic erro inesperado empresa=%s categoria=%s prioridade=%s status_config=%s notas=%s",
                    company.name,
                    company.category,
                    company.priority,
                    company.status,
                    company.notes,
                )
            finally:
                self.company_statuses.append(status)
            self.polite_pause()

        if self.debug_search:
            self._write_company_status_report(self.company_statuses)

        raw_count = len(collected)
        metadata_by_url = {
            self._canonical_job_key(job.url): {
                "category": job.company_category,
                "priority": job.company_priority,
            }
            for job in collected
        }
        deduplicated = self._deduplicate_jobs(
            [
                JobListing(
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    source=self.name,
                    url=job.url,
                    description_snippet=job.description_snippet,
                    published_date=job.published_date,
                    query_used=job.query_used,
                    prefilter_score=0,
                    prefilter_reason="",
                )
                for job in collected
            ]
        )
        kept_jobs, enrich_candidates, prefilter_results = self._apply_prefilter(deduplicated, metadata_by_url)
        if self.debug_search:
            self._write_prefilter_debug_file(prefilter_results)
        discarded_count = len(deduplicated) - len(kept_jobs)
        logger.info(
            "GupyPublic pre-filtro resumo: bruto=%s unicas=%s descartadas=%s mantidas=%s selecionadas_enriquecimento=%s motivos_descartes=%s",
            raw_count,
            len(deduplicated),
            discarded_count,
            len(kept_jobs),
            len(enrich_candidates),
            self._discard_reason_summary(prefilter_results),
        )
        if self.settings.gupy_enrich_details:
            self.enrich_job_details(enrich_candidates)
            return kept_jobs
        logger.info("GupyPublic enriquecimento de detalhes desativado.")
        return kept_jobs

    def _fetch_company(
        self,
        company: GupyCompany,
        status: GupyCompanyRunStatus | None = None,
    ) -> list[GupyExtractedJob]:
        company_jobs: list[GupyExtractedJob] = []
        debug_entries: list[str] = []

        for page_url in self._company_urls(company):
            response = self._get(page_url)
            html = response.text or ""
            if status is not None:
                status.status_http = response.status_code
            logger.info(
                "GupyPublic empresa=%s categoria=%s prioridade=%s status_config=%s url=%s status=%s html_bytes=%s notas=%s",
                company.name,
                company.category,
                company.priority,
                company.status,
                response.url,
                response.status_code,
                len(html),
                company.notes,
            )
            try:
                response.raise_for_status()
            except requests.RequestException as exc:
                if status is not None:
                    status.error = str(exc)
                raise

            link_jobs = self.parse_html_links(html, company=company, page_url=response.url)
            json_jobs = self.parse_embedded_json(html, company=company, page_url=response.url)
            page_jobs = link_jobs + json_jobs
            company_jobs.extend(page_jobs)
            if status is not None:
                status.jobs_found += len(page_jobs)
            debug_entries.extend(f"{job.title} -> {job.url}" for job in page_jobs)
            logger.info(
                "GupyPublic empresa=%s categoria=%s prioridade=%s links_jobs=%s json_jobs=%s page_jobs=%s",
                company.name,
                company.category,
                company.priority,
                len(link_jobs),
                len(json_jobs),
                len(page_jobs),
            )

            if self.debug_search:
                self._write_debug_files(company, response.url, html, debug_entries)
            self.polite_pause()

        return company_jobs

    def _company_urls(self, company: GupyCompany) -> list[str]:
        return [company.base_url, urljoin(company.base_url + "/", "jobs")]

    def _get(self, url: str) -> requests.Response:
        return requests.get(
            url,
            headers={"User-Agent": "jobradar-engineer/0.9 (+public Gupy job board check)"},
            timeout=self.settings.request_timeout_seconds,
        )

    def enrich_job_details(self, jobs: list[JobListing]) -> list[JobListing]:
        limit = max(self.settings.gupy_max_detail_pages, 0)
        if limit <= 0:
            logger.info("GupyPublic detalhe: limite zero, enriquecimento ignorado.")
            return jobs

        opened = 0
        enriched = 0
        failed = 0
        for job in jobs[:limit]:
            opened += 1
            try:
                response = self._get(job.url)
                html = response.text or ""
                logger.info(
                    "GupyPublic detalhe url=%s status=%s html_bytes=%s",
                    response.url,
                    response.status_code,
                    len(html),
                )
                response.raise_for_status()
                detail = self.detail_parser.parse(html, fallback_url=response.url)
                if self._apply_detail(job, detail):
                    enriched += 1
                if self.debug_search:
                    self._write_detail_debug_file(job, response.url, html, detail)
            except requests.RequestException as exc:
                failed += 1
                logger.warning("GupyPublic detalhe falhou url=%s erro=%s", job.url, exc)
            except Exception:
                failed += 1
                logger.exception("GupyPublic detalhe erro inesperado url=%s", job.url)
            if self.settings.gupy_detail_request_delay_seconds > 0:
                time.sleep(self.settings.gupy_detail_request_delay_seconds)

        logger.info(
            "GupyPublic detalhe resumo: abertas=%s enriquecidas=%s falhas=%s limite=%s",
            opened,
            enriched,
            failed,
            limit,
        )
        return jobs

    def _apply_detail(self, job: JobListing, detail: GupyJobDetail) -> bool:
        changed = False
        if detail.title and detail.title != job.title:
            job.title = detail.title[:300]
            changed = True
        if detail.company and job.company in {"", "Nao identificado"} and detail.company != job.company:
            job.company = detail.company[:200]
            changed = True
        if detail.location and detail.location != job.location:
            job.location = detail.location[:200]
            changed = True
        if detail.published_date and detail.published_date != job.published_date:
            job.published_date = detail.published_date
            changed = True

        aggregated = detail.aggregated_text
        if detail.job_id:
            aggregated = f"ID da vaga: {detail.job_id}. {aggregated}"
        if aggregated and len(aggregated) > len(job.description_snippet or ""):
            job.description_snippet = aggregated[:2000]
            changed = True
        return changed

    def parse_html_links(self, html: str, company: GupyCompany, page_url: str) -> list[GupyExtractedJob]:
        soup = BeautifulSoup(html or "", "html.parser")
        jobs: list[GupyExtractedJob] = []
        seen_urls: set[str] = set()

        for link in soup.select("a[href]"):
            raw_href = str(link.get("href") or "")
            url = self.normalize_url(raw_href, company.base_url)
            if not self.is_job_url(url):
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)

            title = unescape(link.get_text(" ", strip=True)) or self._title_from_url(url)
            snippet = self._snippet_from_node(link) or title
            jobs.append(
                GupyExtractedJob(
                    title=title[:300],
                    company=company.name,
                    location=self.extract_location(snippet),
                    url=url,
                    description_snippet=snippet[:1000],
                    query_used=f"gupy:{company.slug}:{page_url}",
                    company_category=company.category,
                    company_priority=company.priority,
                )
            )
        return jobs

    def parse_embedded_json(self, html: str, company: GupyCompany, page_url: str) -> list[GupyExtractedJob]:
        soup = BeautifulSoup(html or "", "html.parser")
        jobs: list[GupyExtractedJob] = []
        for script in soup.find_all("script"):
            text = script.string or script.get_text("", strip=False)
            for payload in self._json_payloads_from_script(text):
                jobs.extend(self._jobs_from_json_payload(payload, company, page_url))
        return self._deduplicate_extracted(jobs)

    def _json_payloads_from_script(self, text: str) -> list[object]:
        payloads: list[object] = []
        text = (text or "").strip()
        if not text:
            return payloads

        candidates = [text]
        candidates.extend(match.group(1) for match in re.finditer(r"({.*?})", text, flags=re.DOTALL))
        for candidate in candidates:
            try:
                payloads.append(json.loads(candidate))
            except json.JSONDecodeError:
                continue
        return payloads

    def _jobs_from_json_payload(self, payload: object, company: GupyCompany, page_url: str) -> list[GupyExtractedJob]:
        jobs: list[GupyExtractedJob] = []
        for item in self._walk_json(payload):
            if not isinstance(item, dict):
                continue
            title = self._first_value(item, ["title", "name", "jobTitle", "role"])
            raw_url = self._first_value(item, ["url", "jobUrl", "publicUrl", "careerPageUrl"])
            path_or_id = self._first_value(item, ["id", "jobId", "code"])
            url = self.normalize_url(str(raw_url or ""), company.base_url)
            if not url and path_or_id and title:
                url = urljoin(company.base_url + "/", f"jobs/{path_or_id}")
            if not title or not self.is_job_url(url):
                continue
            location = self._format_location(
                self._first_value(item, ["location", "city", "workplace", "addressCity"])
            )
            description = self._format_text_value(
                self._first_value(item, ["description", "summary", "department", "workplace"]),
                fallback=str(title),
            )
            published_date = self._first_value(item, ["publishedDate", "published_at", "createdAt"])
            jobs.append(
                GupyExtractedJob(
                    title=str(title)[:300],
                    company=company.name,
                    location=location[:200],
                    url=url,
                    description_snippet=description[:1000],
                    query_used=f"gupy-json:{company.slug}:{page_url}",
                    published_date=str(published_date) if published_date else None,
                    company_category=company.category,
                    company_priority=company.priority,
                )
            )
        return jobs

    def _apply_prefilter(
        self,
        jobs: list[JobListing],
        metadata_by_url: dict[str, dict[str, object]],
    ) -> tuple[list[JobListing], list[JobListing], list[tuple[JobListing, JobPrefilterResult]]]:
        evaluated: list[tuple[JobListing, JobPrefilterResult]] = []
        for job in jobs:
            metadata = metadata_by_url.get(self._canonical_job_key(job.url), {})
            result = self.prefilter.evaluate(
                job,
                company_category=str(metadata.get("category", "")),
                company_priority=bool(metadata.get("priority", False)),
            )
            job.prefilter_score = result.prefilter_score
            job.prefilter_reason = result.prefilter_reason
            evaluated.append((job, result))

        evaluated.sort(key=lambda item: item[1].prefilter_score, reverse=True)
        kept = [job for job, result in evaluated if result.should_keep]
        enrich_candidates = [job for job, result in evaluated if result.should_keep and result.should_enrich]
        return kept, enrich_candidates, evaluated

    def _discard_reason_summary(self, evaluated: list[tuple[JobListing, JobPrefilterResult]]) -> str:
        counts: dict[str, int] = {}
        for _, result in evaluated:
            if result.should_keep:
                continue
            if result.strong_negative_matches:
                key = "negativo forte"
            elif result.weak_negative_matches:
                key = "negativo fraco"
            else:
                key = "sem sinais tecnicos"
            counts[key] = counts.get(key, 0) + 1
        if not counts:
            return "nenhum descarte"
        return ", ".join(f"{reason}={count}" for reason, count in sorted(counts.items()))

    def _walk_json(self, payload: object):
        if isinstance(payload, dict):
            yield payload
            for value in payload.values():
                yield from self._walk_json(value)
        elif isinstance(payload, list):
            for item in payload:
                yield from self._walk_json(item)

    def _first_value(self, item: dict, keys: list[str]) -> object | None:
        for key in keys:
            value = item.get(key)
            if value not in (None, ""):
                return value
        return None

    def _format_location(self, value: object) -> str:
        if not value:
            return "Nao identificado"
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            address = value.get("address") if isinstance(value.get("address"), dict) else value
            city = address.get("city") if isinstance(address, dict) else None
            state = (address.get("stateShortName") or address.get("state")) if isinstance(address, dict) else None
            workplace_type = value.get("workplaceType") or value.get("type")
            parts = [str(part) for part in [city, state, workplace_type] if part]
            return " - ".join(parts) if parts else "Nao identificado"
        return str(value)

    def _format_text_value(self, value: object, fallback: str) -> str:
        if not value:
            return fallback
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            values = [str(item) for item in value.values() if isinstance(item, str) and item.strip()]
            return " ".join(values) if values else fallback
        return str(value)

    def normalize_url(self, raw_url: str, base_url: str) -> str:
        raw_url = unescape(str(raw_url or "")).strip()
        if not raw_url or raw_url.startswith(("#", "javascript:", "mailto:")):
            return ""
        if raw_url.startswith("//"):
            raw_url = "https:" + raw_url
        return urljoin(base_url.rstrip("/") + "/", raw_url)

    def is_job_url(self, url: str) -> bool:
        parsed = urlparse(url or "")
        normalized = (parsed.netloc + parsed.path).lower()
        return "gupy.io" in parsed.netloc.lower() and "/jobs/" in normalized

    def extract_location(self, text: str) -> str:
        text = text or ""
        known_locations = ["Sorocaba", "Campinas", "Piracicaba", "Sao Paulo", "São Paulo", "Remoto", "Hibrido", "Híbrido"]
        for location in known_locations:
            if location.lower() in text.lower():
                return location
        return "Nao identificado"

    def _snippet_from_node(self, link) -> str:
        parent = link.find_parent(["li", "article", "div"])
        if parent:
            return unescape(parent.get_text(" ", strip=True))
        return unescape(link.get_text(" ", strip=True))

    def _title_from_url(self, url: str) -> str:
        path = urlparse(url).path.rstrip("/").split("/")[-1]
        return path.replace("-", " ").replace("_", " ").title() if path else "Vaga Gupy"

    def _deduplicate_jobs(self, jobs: list[JobListing]) -> list[JobListing]:
        by_url: dict[str, JobListing] = {}
        by_identity: dict[str, JobListing] = {}
        for job in jobs:
            url_key = self._canonical_job_key(job.url)
            identity_key = compact_key(job.title, job.company, job.location)
            if url_key in by_url or identity_key in by_identity:
                continue
            by_url[url_key] = job
            by_identity[identity_key] = job
        return list(by_url.values())

    def _deduplicate_extracted(self, jobs: list[GupyExtractedJob]) -> list[GupyExtractedJob]:
        by_url: dict[str, GupyExtractedJob] = {}
        for job in jobs:
            by_url.setdefault(self._canonical_job_key(job.url), job)
        return list(by_url.values())

    def _canonical_job_key(self, url: str) -> str:
        parsed = urlparse(url or "")
        return f"{parsed.netloc.lower()}{parsed.path.rstrip('/').lower()}"

    def _write_debug_files(self, company: GupyCompany, page_url: str, html: str, links: list[str]) -> None:
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        prefix = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{company.slug}"
        safe_html = self._sanitize_html(html)[:200_000]
        (self.debug_dir / f"{prefix}_sample.html").write_text(safe_html, encoding="utf-8")
        lines = [f"company={company.name}", f"url={page_url}", f"links={len(links)}", "", *links]
        (self.debug_dir / f"{prefix}_links.txt").write_text("\n".join(lines), encoding="utf-8")

    def _write_detail_debug_file(
        self,
        job: JobListing,
        detail_url: str,
        html: str,
        detail: GupyJobDetail,
    ) -> None:
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        job_id = detail.job_id or re.sub(r"\W+", "_", job.title.lower())[:40]
        prefix = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_detail_{job_id}"
        safe_html = self._sanitize_html(html)[:200_000]
        (self.debug_dir / f"{prefix}_sample.html").write_text(safe_html, encoding="utf-8")
        lines = [
            f"title={detail.title or job.title}",
            f"url={detail_url}",
            f"location={detail.location or job.location}",
            f"work_mode={detail.work_mode}",
            f"published_date={detail.published_date or ''}",
            f"job_id={detail.job_id}",
            f"aggregated_chars={len(detail.aggregated_text)}",
        ]
        (self.debug_dir / f"{prefix}_detail.txt").write_text("\n".join(lines), encoding="utf-8")

    def _write_company_status_report(self, statuses: list[GupyCompanyRunStatus]) -> Path:
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        path = self.debug_dir / f"companies_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "name",
                    "slug",
                    "base_url",
                    "category",
                    "priority",
                    "status_http",
                    "jobs_found",
                    "jobs_created",
                    "error",
                ],
            )
            writer.writeheader()
            for status in statuses:
                writer.writerow(
                    {
                        "name": status.name,
                        "slug": status.slug,
                        "base_url": status.base_url,
                        "category": status.category,
                        "priority": status.priority,
                        "status_http": status.status_http,
                        "jobs_found": status.jobs_found,
                        "jobs_created": status.jobs_created,
                        "error": status.error,
                    }
                )
        logger.info("GupyPublic relatorio de status salvo em %s", path)
        return path

    def _write_prefilter_debug_file(
        self,
        evaluated: list[tuple[JobListing, JobPrefilterResult]],
    ) -> Path:
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        path = self.debug_dir / f"prefilter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "title",
                    "company",
                    "location",
                    "url",
                    "prefilter_score",
                    "prefilter_reason",
                    "should_keep",
                    "should_enrich",
                ],
            )
            writer.writeheader()
            for job, result in evaluated:
                writer.writerow(
                    {
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "url": job.url,
                        "prefilter_score": f"{result.prefilter_score:.1f}",
                        "prefilter_reason": result.prefilter_reason,
                        "should_keep": result.should_keep,
                        "should_enrich": result.should_enrich,
                    }
                )
        logger.info("GupyPublic relatorio de pre-filtro salvo em %s", path)
        return path

    def _sanitize_html(self, html: str) -> str:
        sanitized = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email-redacted]", html or "")
        return re.sub(r"(?i)(token|password|senha|api_key)=([^&\"'>\\s]+)", r"\1=[redacted]", sanitized)


GupySource = MockGupySource
