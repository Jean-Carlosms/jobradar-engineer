from __future__ import annotations

from src.sources.search_engine_source import SearchEngineSource


class IndeedSource(SearchEngineSource):
    """Experimental public-search fallback constrained to Indeed pages."""

    def __init__(self, settings) -> None:
        super().__init__(settings, site_filter="br.indeed.com", source_name="IndeedBuscaPublica")
