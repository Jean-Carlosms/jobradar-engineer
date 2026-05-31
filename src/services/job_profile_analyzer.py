from __future__ import annotations

from dataclasses import dataclass

from src.profile_summary import ProfileSummary
from src.utils.text_cleaner import normalize_text


NEGATIVE_ALIGNMENT_TERMS = [
    "estagio",
    "jovem aprendiz",
    "vendedor",
    "telemarketing",
    "comercial puro",
    "operador",
    "suporte nivel 1",
]


@dataclass(frozen=True)
class JobProfileAnalysis:
    fit_level: str
    fit_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    risks: list[str]
    resume_keywords: list[str]
    recruiter_message: str
    analysis_summary: str


class JobProfileAnalyzer:
    def __init__(self, profile: ProfileSummary) -> None:
        self.profile = profile

    def analyze(self, job) -> JobProfileAnalysis:
        text = self._job_text(job)
        matched_skills = self._matched_terms(text, self._profile_terms())
        missing_skills = self._missing_important_terms(matched_skills)
        risks = self._risks(text, missing_skills)
        strengths = self._strengths(matched_skills)
        fit_score = self._fit_score(job, matched_skills, missing_skills, risks)
        fit_level = self._fit_level(fit_score)
        resume_keywords = self._resume_keywords(matched_skills, missing_skills)
        title = getattr(job, "title", "vaga")
        company = getattr(job, "company", "empresa")

        return JobProfileAnalysis(
            fit_level=fit_level,
            fit_score=fit_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            strengths=strengths,
            risks=risks,
            resume_keywords=resume_keywords,
            recruiter_message=self._recruiter_message(title, company, matched_skills),
            analysis_summary=self._analysis_summary(fit_level, fit_score, matched_skills, missing_skills, risks),
        )

    def _profile_terms(self) -> list[str]:
        return _unique_preserving_order(
            self.profile.core_skills
            + self.profile.tools
            + self.profile.interest_areas
            + self.profile.target_roles
            + self.profile.target_companies
        )

    def _job_text(self, job) -> str:
        parts = [
            getattr(job, "title", ""),
            getattr(job, "company", ""),
            getattr(job, "location", ""),
            getattr(job, "description_snippet", ""),
            getattr(job, "match_reason", ""),
            getattr(job, "query_used", ""),
        ]
        return normalize_text(" ".join(str(part or "") for part in parts))

    def _matched_terms(self, normalized_text: str, terms: list[str]) -> list[str]:
        matches = []
        seen = set()
        for term in terms:
            normalized_term = normalize_text(term)
            if normalized_term and normalized_term in normalized_text and normalized_term not in seen:
                matches.append(term)
                seen.add(normalized_term)
        return matches

    def _missing_important_terms(self, matched_skills: list[str]) -> list[str]:
        matched_normalized = {normalize_text(skill) for skill in matched_skills}
        important_terms = _unique_preserving_order(
            self.profile.core_skills[:12] + self.profile.tools[:8] + self.profile.interest_areas[:5]
        )
        return [term for term in important_terms if normalize_text(term) not in matched_normalized][:8]

    def _risks(self, normalized_text: str, missing_skills: list[str]) -> list[str]:
        risks = []
        for term in NEGATIVE_ALIGNMENT_TERMS:
            if normalize_text(term) in normalized_text:
                risks.append(f"Possivel desalinhamento por conter '{term}'.")
        if len(missing_skills) >= 6:
            risks.append("Vaga menciona poucas competencias centrais do perfil.")
        if "ingles avancado" in normalized_text or "advanced english" in normalized_text:
            risks.append("Pode exigir ingles avancado.")
        if "cloud" in normalized_text and "cloud" not in {normalize_text(skill) for skill in self.profile.core_skills}:
            risks.append("Pode exigir profundidade em cloud alem do foco principal.")
        return risks or ["Nenhum risco relevante identificado nas regras locais."]

    def _strengths(self, matched_skills: list[str]) -> list[str]:
        normalized_matches = {normalize_text(skill) for skill in matched_skills}
        selected = []
        for strength in self.profile.strengths:
            normalized_strength = normalize_text(strength)
            if any(match in normalized_strength or normalized_strength in match for match in normalized_matches):
                selected.append(strength)
        if selected:
            return selected[:4]
        if matched_skills:
            return [f"Perfil aderente por combinar com {', '.join(matched_skills[:4])}."]
        return ["Poucos pontos fortes foram identificados automaticamente para esta vaga."]

    def _fit_score(self, job, matched_skills: list[str], missing_skills: list[str], risks: list[str]) -> int:
        profile_term_count = max(len(self._profile_terms()), 1)
        coverage_score = min((len(matched_skills) / profile_term_count) * 100 * 2.3, 70)
        original_score = min(float(getattr(job, "match_score", 0) or 0), 100) * 0.25
        priority_bonus = 8 if getattr(job, "priority_company", False) else 0
        missing_penalty = min(len(missing_skills) * 2, 12)
        risk_penalty = 0 if risks == ["Nenhum risco relevante identificado nas regras locais."] else min(len(risks) * 8, 24)
        return int(max(min(coverage_score + original_score + priority_bonus - missing_penalty - risk_penalty, 100), 0))

    def _fit_level(self, fit_score: int) -> str:
        if fit_score >= 70:
            return "alto"
        if fit_score >= 40:
            return "medio"
        return "baixo"

    def _resume_keywords(self, matched_skills: list[str], missing_skills: list[str]) -> list[str]:
        return _unique_preserving_order(matched_skills[:8] + missing_skills[:5])

    def _recruiter_message(self, title: str, company: str, matched_skills: list[str]) -> str:
        skills = ", ".join(matched_skills[:4]) if matched_skills else "engenharia, automacao e melhoria de processos"
        return (
            f"Ola! Tenho interesse na vaga de {title} na {company}. "
            f"Minha experiencia com {skills} parece bem alinhada aos desafios da posicao."
        )

    def _analysis_summary(
        self,
        fit_level: str,
        fit_score: int,
        matched_skills: list[str],
        missing_skills: list[str],
        risks: list[str],
    ) -> str:
        matched = ", ".join(matched_skills[:5]) if matched_skills else "poucas competencias explicitas"
        missing = ", ".join(missing_skills[:4]) if missing_skills else "sem lacunas relevantes"
        risk_text = " ".join(risks[:2])
        return (
            f"Aderencia {fit_level} ({fit_score}/100). "
            f"Competencias encontradas: {matched}. "
            f"Lacunas principais: {missing}. "
            f"{risk_text}"
        )


def _unique_preserving_order(items: list[str]) -> list[str]:
    result = []
    seen = set()
    for item in items:
        key = normalize_text(item)
        if key and key not in seen:
            result.append(item)
            seen.add(key)
    return result
