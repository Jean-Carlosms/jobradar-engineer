from __future__ import annotations

import re
from dataclasses import dataclass

from src.models.job import JobListing
from src.profile import ProfileConfig
from src.utils.text_cleaner import normalize_text


DEFAULT_TECHNICAL_TITLE_KEYWORDS = [
    "engenharia",
    "engineer",
    "engenheiro",
    "engenheira",
    "automacao",
    "mecatronica",
    "manutencao",
    "projetos",
    "processos",
    "manufatura",
    "industrial",
    "qualidade",
    "dados",
    "data",
    "analytics",
    "BI",
    "Power BI",
    "Python",
    "sistemas",
    "software",
    "hardware",
    "firmware",
    "robotica",
    "tecnico",
    "tecnica",
    "tecnologia",
    "PCM",
    "PCP",
]
DEFAULT_TECHNICAL_AREA_KEYWORDS = [
    "automacao industrial",
    "engenharia de projetos",
    "melhoria continua",
    "industria 4.0",
    "CLP",
    "PLC",
    "Power BI",
    "Python",
    "dashboard",
    "analytics",
    "dados",
    "manufatura",
    "manutencao",
    "processos",
    "qualidade",
    "robotica",
]
DEFAULT_STRONG_NEGATIVE_TITLE_KEYWORDS = [
    "estagio",
    "estagiario",
    "jovem aprendiz",
    "aprendiz",
    "vendedor",
    "vendedora",
    "vendas",
    "loja",
    "caixa",
    "atendente",
    "telemarketing",
    "call center",
    "operador de loja",
    "auxiliar de loja",
]
DEFAULT_WEAK_NEGATIVE_TITLE_KEYWORDS = [
    "assistente",
    "auxiliar",
    "administrativo",
    "comercial",
    "representante",
    "consultor de vendas",
    "promotor",
]


@dataclass(frozen=True)
class JobPrefilterResult:
    prefilter_score: float
    prefilter_reason: str
    should_enrich: bool
    should_keep: bool
    technical_matches: list[str]
    area_matches: list[str]
    strong_negative_matches: list[str]
    weak_negative_matches: list[str]
    location_matches: list[str]
    priority_company: bool = False


class JobPrefilter:
    def __init__(
        self,
        profile: ProfileConfig | None = None,
        keep_threshold: float = 12.0,
        enrich_threshold: float = 30.0,
    ) -> None:
        self.profile = profile or ProfileConfig()
        self.keep_threshold = keep_threshold
        self.enrich_threshold = enrich_threshold

    def evaluate(
        self,
        listing: JobListing,
        company_category: str = "",
        company_priority: bool = False,
    ) -> JobPrefilterResult:
        title = normalize_text(listing.title)
        text = normalize_text(
            " ".join(
                [
                    listing.title,
                    listing.company,
                    listing.location,
                    listing.url,
                    listing.query_used,
                    listing.description_snippet,
                    company_category,
                ]
            )
        )

        technical_matches = self._collect_matches(title, self._technical_title_keywords())
        area_matches = self._collect_matches(text, self._technical_area_keywords())
        strong_negative_matches = self._collect_matches(title, self._strong_negative_title_keywords())
        weak_negative_matches = self._collect_matches(title, self._weak_negative_title_keywords())
        location_matches = self._collect_matches(
            normalize_text(f"{listing.location} {listing.title}"),
            self.profile.location_boost_keywords or self.profile.desired_locations,
        )
        priority_company = company_priority or self._is_priority_company(listing.company)

        score = 0.0
        score += len(technical_matches) * 18.0
        score += len(area_matches) * 8.0
        score += len(location_matches) * 6.0
        if priority_company:
            score += self.profile.priority_company_boost
        score -= len(weak_negative_matches) * 8.0
        score -= len(strong_negative_matches) * 35.0
        score = max(score, 0.0)

        has_technical_signal = bool(technical_matches or area_matches)
        has_strong_negative_without_technical = bool(strong_negative_matches and not has_technical_signal)
        should_keep = not has_strong_negative_without_technical and (score >= self.keep_threshold or has_technical_signal)
        should_enrich = should_keep and score >= self.enrich_threshold

        return JobPrefilterResult(
            prefilter_score=score,
            prefilter_reason=self._build_reason(
                technical_matches=technical_matches,
                area_matches=area_matches,
                strong_negative_matches=strong_negative_matches,
                weak_negative_matches=weak_negative_matches,
                location_matches=location_matches,
                priority_company=priority_company,
                should_keep=should_keep,
                should_enrich=should_enrich,
            ),
            should_enrich=should_enrich,
            should_keep=should_keep,
            technical_matches=technical_matches,
            area_matches=area_matches,
            strong_negative_matches=strong_negative_matches,
            weak_negative_matches=weak_negative_matches,
            location_matches=location_matches,
            priority_company=priority_company,
        )

    def _collect_matches(self, text: str, keywords: list[str]) -> list[str]:
        matches: list[str] = []
        seen: set[str] = set()
        for keyword in keywords:
            normalized_keyword = normalize_text(keyword)
            if not normalized_keyword or normalized_keyword in seen:
                continue
            if self._contains_keyword(text, normalized_keyword):
                seen.add(normalized_keyword)
                matches.append(keyword)
        return matches

    def _contains_keyword(self, text: str, keyword: str) -> bool:
        pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
        return re.search(pattern, text) is not None

    def _is_priority_company(self, company: str) -> bool:
        normalized_company = normalize_text(company)
        return any(
            self._contains_keyword(normalized_company, normalize_text(priority))
            for priority in self.profile.priority_companies
        )

    def _technical_title_keywords(self) -> list[str]:
        return self.profile.technical_title_keywords or DEFAULT_TECHNICAL_TITLE_KEYWORDS

    def _technical_area_keywords(self) -> list[str]:
        return self.profile.technical_area_keywords or DEFAULT_TECHNICAL_AREA_KEYWORDS

    def _strong_negative_title_keywords(self) -> list[str]:
        return self.profile.strong_negative_title_keywords or DEFAULT_STRONG_NEGATIVE_TITLE_KEYWORDS

    def _weak_negative_title_keywords(self) -> list[str]:
        return self.profile.weak_negative_title_keywords or DEFAULT_WEAK_NEGATIVE_TITLE_KEYWORDS

    def _build_reason(
        self,
        technical_matches: list[str],
        area_matches: list[str],
        strong_negative_matches: list[str],
        weak_negative_matches: list[str],
        location_matches: list[str],
        priority_company: bool,
        should_keep: bool,
        should_enrich: bool,
    ) -> str:
        parts: list[str] = []
        if technical_matches:
            parts.append(f"termos tecnicos no titulo: {self._join_terms(technical_matches)}")
        if area_matches:
            parts.append(f"area tecnica: {self._join_terms(area_matches)}")
        if location_matches:
            parts.append(f"localidade desejada: {self._join_terms(location_matches)}")
        if priority_company:
            parts.append("empresa prioritaria")
        if strong_negative_matches:
            parts.append(f"negativo forte: {self._join_terms(strong_negative_matches)}")
        if weak_negative_matches:
            parts.append(f"negativo fraco: {self._join_terms(weak_negative_matches)}")

        decision = "manter e enriquecer" if should_enrich else "manter sem enriquecer" if should_keep else "descartar"
        if not parts:
            parts.append("sem sinais tecnicos suficientes")
        return f"{decision}: " + "; ".join(parts) + "."

    def _join_terms(self, terms: list[str]) -> str:
        if not terms:
            return ""
        if len(terms) == 1:
            return terms[0]
        return ", ".join(terms[:-1]) + f" e {terms[-1]}"
