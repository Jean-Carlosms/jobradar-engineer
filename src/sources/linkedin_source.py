from __future__ import annotations

from src.sources.search_engine_source import SearchEngineSource


class LinkedInSource(SearchEngineSource):
    def __init__(self, settings) -> None:
        super().__init__(settings, site_filter="linkedin.com/jobs/view", source_name="LinkedInBuscaPublica")
