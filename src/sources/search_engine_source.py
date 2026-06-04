from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

from src.models.job import JobListing
from src.sources.base import JobSource

logger = logging.getLogger(__name__)


DEFAULT_SEARCH_SITES = [
    "gupy.io/jobs",
    "linkedin.com/jobs",
    "indeed.com",
    "infojobs.com.br",
    "glassdoor.com.br",
    "catho.com.br",
    "vagas.com.br",
]

ACCEPTED_URL_PATTERNS = [
    "gupy.io/jobs",
    "linkedin.com/jobs",
    "indeed.com",
    "infojobs.com.br",
    "glassdoor.com.br",
    "catho.com.br",
    "vagas.com.br",
]

FALLBACK_QUERIES = [
    ('"Engenheiro de Automacao" Sorocaba vaga', "Sorocaba"),
    ('"Analista de Projetos" Sorocaba vaga', "Sorocaba"),
    ('"Manufacturing Engineer" Sorocaba', "Sorocaba"),
    ('"Automation Engineer" Campinas', "Campinas"),
    ('"Engenheiro de Projetos" Campinas', "Campinas"),
    ("site:gupy.io/jobs automacao Sorocaba", "Sorocaba"),
    ("site:linkedin.com/jobs engenharia automacao Sorocaba", "Sorocaba"),
]

DUCKDUCKGO_URL = "https://html.duckduckgo.com/html/"


@dataclass(frozen=True)
class ExtractedLink:
    title: str
    url: str
    snippet: str
    selector: str


class SearchEngineSource(JobSource):
    name = "BuscaPublica"

    def __init__(
        self,
        settings,
        site_filter: str | None = None,
        source_name: str | None = None,
        search_sites: list[str] | None = None,
        debug_search: bool = False,
    ) -> None:
        super().__init__(settings)
        if site_filter:
            self.search_sites = [site_filter]
        else:
            self.search_sites = search_sites or DEFAULT_SEARCH_SITES
        self.debug_search = debug_search
        self.debug_dir = self.settings.project_root / "logs" / "search_debug"
        if source_name:
            self.name = source_name

    def fetch(self, keywords: list[str], locations: list[str]) -> list[JobListing]:
        if not self.settings.enable_web_search:
            logger.info("Busca publica desativada por ENABLE_WEB_SEARCH=false.")
            return []

        jobs: list[JobListing] = []
        for index, (query, location) in enumerate(self.build_queries(keywords, locations), start=1):
            try:
                jobs.extend(self._search_duckduckgo(query, location, index))
            except requests.RequestException as exc:
                logger.warning("Falha na busca publica para '%s': %s", query, exc)
            except Exception:
                logger.exception("Erro inesperado ao processar busca publica para '%s'.", query)
            self.polite_pause()
        return jobs

    def build_queries(self, titles: list[str], locations: list[str]) -> list[tuple[str, str]]:
        queries: list[tuple[str, str]] = []
        queries.extend(FALLBACK_QUERIES)

        for site in self.search_sites:
            for title in titles:
                for location in locations:
                    queries.append((self._build_query(site, title, location), location))

        deduplicated: list[tuple[str, str]] = []
        seen: set[str] = set()
        for query, location in queries:
            key = query.lower()
            if key not in seen:
                deduplicated.append((query, location))
                seen.add(key)
            if len(deduplicated) >= self.settings.max_search_queries:
                break
        return deduplicated

    def _build_query(self, site: str, title: str, location: str) -> str:
        return f'site:{site} "{title}" "{location}"'

    def _search_duckduckgo(self, query: str, location: str, query_index: int = 0) -> list[JobListing]:
        logger.info("BuscaPublica query: %s", query)
        response = requests.get(
            DUCKDUCKGO_URL,
            params={"q": query},
            headers={"User-Agent": "jobradar-engineer/0.8 (+local personal job search)"},
            timeout=self.settings.request_timeout_seconds,
        )
        logger.info(
            "BuscaPublica HTTP: url=%s status=%s html_bytes=%s",
            response.url,
            response.status_code,
            len(response.text or ""),
        )
        response.raise_for_status()

        challenge_detected = self.detect_search_challenge(response.text)
        if challenge_detected:
            logger.warning(
                "BuscaPublica recebeu pagina de desafio/captcha ou bloqueio do buscador para a query: %s",
                query,
            )

        raw_links = self.extract_links(response.text)
        filtered_links = self.filter_links(raw_links)
        jobs = self.links_to_jobs(filtered_links, query=query, location=location)

        logger.info(
            "BuscaPublica resultado: raw_links=%s filtered_links=%s jobs=%s challenge_detected=%s",
            len(raw_links),
            len(filtered_links),
            len(jobs),
            challenge_detected,
        )

        if self.debug_search:
            self._write_debug_files(
                query_index=query_index,
                query=query,
                response_url=response.url,
                html=response.text,
                raw_links=raw_links,
                filtered_links=filtered_links,
                jobs=jobs,
                challenge_detected=challenge_detected,
            )

        return jobs

    def extract_links(self, html: str) -> list[ExtractedLink]:
        soup = BeautifulSoup(html or "", "html.parser")
        candidates: list[tuple[str, Tag]] = []
        selectors = [
            ("a.result__a", "a.result__a"),
            ("a[data-testid]", "a[data-testid]"),
            ("a[class*=result]", "a[class*=result]"),
            ("a[href]", "a[href]"),
        ]

        seen_nodes: set[int] = set()
        for label, selector in selectors:
            for link in soup.select(selector):
                if not isinstance(link, Tag):
                    continue
                node_id = id(link)
                if node_id in seen_nodes:
                    continue
                seen_nodes.add(node_id)
                candidates.append((label, link))

        extracted: list[ExtractedLink] = []
        seen_urls: set[str] = set()
        for selector, link in candidates:
            raw_href = str(link.get("href") or "")
            cleaned_url = self.clean_result_url(raw_href)
            title = unescape(link.get_text(" ", strip=True))
            snippet = self._extract_snippet(link, fallback=title)

            if not raw_href:
                self._debug_discard("link sem href", title, raw_href)
                continue
            if not cleaned_url:
                self._debug_discard("url vazia apos limpeza", title, raw_href)
                continue
            if cleaned_url in seen_urls:
                self._debug_discard("url duplicada", title, cleaned_url)
                continue
            if not title:
                title = cleaned_url

            seen_urls.add(cleaned_url)
            extracted.append(
                ExtractedLink(
                    title=title[:300],
                    url=cleaned_url,
                    snippet=snippet[:1000],
                    selector=selector,
                )
            )
        return extracted

    def filter_links(self, links: list[ExtractedLink]) -> list[ExtractedLink]:
        filtered: list[ExtractedLink] = []
        for link in links:
            if self.is_accepted_url(link.url):
                filtered.append(link)
            else:
                self._debug_discard("dominio fora da lista permitida", link.title, link.url)
        return filtered

    def links_to_jobs(self, links: list[ExtractedLink], query: str, location: str) -> list[JobListing]:
        jobs: list[JobListing] = []
        for link in links:
            snippet = link.snippet or query
            jobs.append(
                JobListing(
                    title=link.title or "Vaga sem titulo",
                    company=self._guess_company(link.url),
                    location=location or "Nao identificado",
                    source=self.name,
                    url=link.url,
                    description_snippet=snippet,
                    published_date=None,
                    query_used=query,
                )
            )
        return jobs

    def clean_result_url(self, raw_url: str) -> str:
        if not raw_url:
            return ""
        raw_url = unescape(raw_url).strip()
        if raw_url.startswith("//"):
            raw_url = "https:" + raw_url
        if raw_url.startswith(("#", "javascript:", "mailto:")):
            return ""

        parsed = urlparse(raw_url)
        if parsed.netloc.endswith("duckduckgo.com") or raw_url.startswith("/l/"):
            query = parse_qs(parsed.query)
            target = query.get("uddg", [""])[0] or query.get("u", [""])[0]
            raw_url = unquote(target) if target else raw_url

        parsed = urlparse(raw_url)
        if not parsed.scheme and parsed.netloc:
            raw_url = "https:" + raw_url
        elif not parsed.scheme and raw_url.startswith("www."):
            raw_url = "https://" + raw_url
        elif parsed.scheme not in {"http", "https"}:
            return ""

        return raw_url.strip()

    def is_accepted_url(self, url: str) -> bool:
        normalized_url = (url or "").lower()
        return any(pattern in normalized_url for pattern in ACCEPTED_URL_PATTERNS)

    def detect_search_challenge(self, html: str) -> bool:
        normalized = (html or "").lower()
        challenge_markers = [
            "anomaly-modal",
            "unfortunately, bots use duckduckgo too",
            "complete the following challenge",
            "captcha",
            "confirm this search was made by a human",
        ]
        return any(marker in normalized for marker in challenge_markers)

    def _guess_company(self, url: str) -> str:
        host = urlparse(url).netloc.replace("www.", "")
        if not host:
            return "Nao identificado"
        if "gupy.io" in host:
            return "Gupy"
        return host.split(".")[0].title() or "Nao identificado"

    def _extract_snippet(self, link: Tag, fallback: str) -> str:
        parent = link.find_parent(class_=re.compile("result"))
        if parent:
            snippet_node = parent.select_one(".result__snippet")
            if snippet_node:
                return unescape(snippet_node.get_text(" ", strip=True))
            parent_text = parent.get_text(" ", strip=True)
            if parent_text:
                return unescape(parent_text)
        return fallback

    def _write_debug_files(
        self,
        query_index: int,
        query: str,
        response_url: str,
        html: str,
        raw_links: list[ExtractedLink],
        filtered_links: list[ExtractedLink],
        jobs: list[JobListing],
        challenge_detected: bool,
    ) -> None:
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        prefix = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{query_index:03d}"
        safe_html = self._sanitize_html(html)[:200_000]
        (self.debug_dir / f"{prefix}_sample.html").write_text(safe_html, encoding="utf-8")

        lines = [
            f"query={query}",
            f"response_url={response_url}",
            f"raw_links={len(raw_links)}",
            f"filtered_links={len(filtered_links)}",
            f"jobs={len(jobs)}",
            f"challenge_detected={challenge_detected}",
            "",
            "RAW LINKS",
        ]
        lines.extend(f"- [{link.selector}] {link.title} -> {link.url}" for link in raw_links)
        lines.append("")
        lines.append("FILTERED LINKS")
        lines.extend(f"- {link.title} -> {link.url}" for link in filtered_links)
        lines.append("")
        lines.append("JOBS")
        lines.extend(f"- {job.title} | {job.company} | {job.location} | {job.url}" for job in jobs)
        (self.debug_dir / f"{prefix}_links.txt").write_text("\n".join(lines), encoding="utf-8")

    def _sanitize_html(self, html: str) -> str:
        sanitized = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email-redacted]", html or "")
        return re.sub(r"(?i)(token|password|senha|api_key)=([^&\"'>\\s]+)", r"\1=[redacted]", sanitized)

    def _debug_discard(self, reason: str, title: str, url: str) -> None:
        if self.debug_search:
            logger.info("BuscaPublica descarte: motivo=%s titulo=%s url=%s", reason, title[:120], url[:300])
