from __future__ import annotations

from src.sources.search_engine_source import SearchEngineSource


class InfoJobsSource(SearchEngineSource):
    """Experimental public-search fallback constrained to InfoJobs pages."""

    def __init__(self, settings) -> None:
        super().__init__(settings, site_filter="infojobs.com.br", source_name="InfoJobsBuscaPublica")
