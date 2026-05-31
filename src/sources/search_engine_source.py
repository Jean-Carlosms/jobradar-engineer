from __future__ import annotations

import logging
from html import unescape
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from src.models.job import JobListing
from src.sources.base import JobSource

logger = logging.getLogger(__name__)


DEFAULT_SEARCH_SITES = [
    "gupy.io/jobs",
    "linkedin.com/jobs",
    "indeed.com",
    "infojobs.com.br",
    "glassdoor.com.br",
]


class SearchEngineSource(JobSource):
    name = "BuscaPublica"

    def __init__(
        self,
        settings,
        site_filter: str | None = None,
        source_name: str | None = None,
        search_sites: list[str] | None = None,
    ) -> None:
        super().__init__(settings)
        if site_filter:
            self.search_sites = [site_filter]
        else:
            self.search_sites = search_sites or DEFAULT_SEARCH_SITES
        if source_name:
            self.name = source_name

    def fetch(self, keywords: list[str], locations: list[str]) -> list[JobListing]:
        if not self.settings.enable_web_search:
            logger.info("Busca publica desativada por ENABLE_WEB_SEARCH=false.")
            return []

        jobs: list[JobListing] = []
        for query, location in self.build_queries(keywords, locations):
            try:
                jobs.extend(self._search_duckduckgo(query, location))
            except requests.RequestException as exc:
                logger.warning("Falha na busca publica para '%s': %s", query, exc)
            self.polite_pause()
        return jobs

    def build_queries(self, titles: list[str], locations: list[str]) -> list[tuple[str, str]]:
        queries: list[tuple[str, str]] = []
        for site in self.search_sites:
            for title in titles:
                for location in locations:
                    queries.append((self._build_query(site, title, location), location))
                    if len(queries) >= self.settings.max_search_queries:
                        return queries
        return queries

    def _build_query(self, site: str, title: str, location: str) -> str:
        return f'site:{site} "{title}" "{location}"'

    def _search_duckduckgo(self, query: str, location: str) -> list[JobListing]:
        response = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "jobradar-engineer/0.2 (+local personal job search)"},
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[JobListing] = []

        for result in soup.select(".result")[:5]:
            link = result.select_one("a.result__a")
            if not link:
                continue
            url = self._clean_result_url(link.get("href", ""))
            title = unescape(link.get_text(" ", strip=True))
            snippet_node = result.select_one(".result__snippet")
            snippet = unescape(snippet_node.get_text(" ", strip=True)) if snippet_node else ""
            if not url or "duckduckgo.com" in url:
                continue

            results.append(
                JobListing(
                    title=title[:300],
                    company=self._guess_company(url),
                    location=location,
                    source=self.name,
                    url=url,
                    description_snippet=snippet[:1000],
                    published_date=None,
                    query_used=query,
                )
            )
        return results

    def _clean_result_url(self, raw_url: str) -> str:
        if not raw_url:
            return ""
        parsed = urlparse(raw_url)
        if parsed.netloc.endswith("duckduckgo.com"):
            target = parse_qs(parsed.query).get("uddg", [""])[0]
            return target or raw_url
        return raw_url

    def _guess_company(self, url: str) -> str:
        host = urlparse(url).netloc.replace("www.", "")
        return host.split(".")[0].title() if host else "Nao informado"
