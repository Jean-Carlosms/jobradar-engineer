from __future__ import annotations

from dataclasses import dataclass

from src.models.job import JobListing
from src.profile import ProfileConfig
from src.utils.text_cleaner import normalize_text


@dataclass(frozen=True)
class MatchResult:
    score: float
    reason_text: str
    high_matches: list[str]
    medium_matches: list[str]
    negative_matches: list[str]
    priority_company: bool = False


class JobMatcher:
    def __init__(
        self,
        profile: ProfileConfig | None = None,
        high_weight: float = 15.0,
        medium_weight: float = 6.0,
        negative_weight: float = -35.0,
        priority_company_bonus: float = 10.0,
        title_multiplier: float = 1.5,
    ) -> None:
        self.profile = profile or ProfileConfig()
        self.high_weight = high_weight
        self.medium_weight = medium_weight
        self.negative_weight = negative_weight
        self.priority_company_bonus = priority_company_bonus
        self.title_multiplier = title_multiplier

    def score_listing(self, listing: JobListing) -> JobListing:
        result = self.score_text(
            title=listing.title,
            description=listing.description_snippet,
            company=listing.company,
        )
        listing.match_score = result.score
        listing.match_reason = result.reason_text
        listing.priority_company = result.priority_company
        return listing

    def score_text(self, title: str, description: str = "", company: str = "") -> MatchResult:
        normalized_title = normalize_text(title)
        normalized_text = normalize_text(f"{title} {description}")

        high_matches, high_score = self._collect_matches(
            normalized_text,
            normalized_title,
            self.profile.high_weight_keywords,
            self.high_weight,
        )
        medium_matches, medium_score = self._collect_matches(
            normalized_text,
            normalized_title,
            self.profile.medium_weight_keywords,
            self.medium_weight,
        )
        negative_matches, negative_score = self._collect_matches(
            normalized_text,
            normalized_title,
            self.profile.negative_keywords,
            self.negative_weight,
        )

        priority_company = self._is_priority_company(company)
        priority_score = self.priority_company_bonus if priority_company else 0.0
        score = max(high_score + medium_score + negative_score + priority_score, 0.0)

        return MatchResult(
            score=score,
            reason_text=self._build_reason_text(
                high_matches=high_matches,
                medium_matches=medium_matches,
                negative_matches=negative_matches,
                priority_company=priority_company,
            ),
            high_matches=high_matches,
            medium_matches=medium_matches,
            negative_matches=negative_matches,
            priority_company=priority_company,
        )

    def _collect_matches(
        self,
        text: str,
        title: str,
        keywords: list[str],
        weight: float,
    ) -> tuple[list[str], float]:
        matches: list[str] = []
        score = 0.0
        seen: set[str] = set()

        for keyword in keywords:
            normalized_keyword = normalize_text(keyword)
            if not normalized_keyword or normalized_keyword in seen:
                continue
            if normalized_keyword in text:
                seen.add(normalized_keyword)
                matches.append(keyword)
                multiplier = self.title_multiplier if normalized_keyword in title else 1.0
                score += weight * multiplier

        return matches, score

    def _is_priority_company(self, company: str) -> bool:
        normalized_company = normalize_text(company)
        if not normalized_company:
            return False
        return any(normalize_text(priority) in normalized_company for priority in self.profile.priority_companies)

    def _build_reason_text(
        self,
        high_matches: list[str],
        medium_matches: list[str],
        negative_matches: list[str],
        priority_company: bool,
    ) -> str:
        parts: list[str] = []

        if negative_matches:
            parts.append(f"Baixa aderencia por conter termo negativo: {self._join_terms(negative_matches)}.")
        elif high_matches:
            parts.append(f"Alta aderencia por conter {self._join_terms(high_matches)}.")
        elif medium_matches:
            parts.append(f"Aderencia media por conter {self._join_terms(medium_matches)}.")
        else:
            parts.append("Baixa aderencia por nao conter palavras-chave fortes do perfil.")

        if negative_matches and (high_matches or medium_matches):
            positive_terms = high_matches + medium_matches
            parts.append(f"Tambem contem {self._join_terms(positive_terms)}.")
        if priority_company:
            parts.append("Empresa esta na lista de prioridade do perfil.")

        return " ".join(parts)

    def _join_terms(self, terms: list[str]) -> str:
        if not terms:
            return ""
        if len(terms) == 1:
            return terms[0]
        return ", ".join(terms[:-1]) + f" e {terms[-1]}"
