from __future__ import annotations

from src.sources.search_engine_source import SearchEngineSource


class GlassdoorSource(SearchEngineSource):
    def __init__(self, settings) -> None:
        super().__init__(settings, site_filter="glassdoor.com.br", source_name="GlassdoorBuscaPublica")
