from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

from src.database import JobRepository
from src.models.job import Job
from src.services.job_review_service import REVIEW_STATUSES
from src.utils.text_cleaner import normalize_text


INSIGHT_COLUMNS = [
    "insight_type",
    "candidate",
    "count",
    "evidence",
    "recommendation",
    "confidence",
]

REVIEWED_STATUSES = {"relevant", "irrelevant", "maybe", "applied", "ignored"}
POSITIVE_STATUSES = {"relevant", "applied"}
NEGATIVE_STATUSES = {"irrelevant", "ignored"}

STOPWORDS = {
    "para",
    "como",
    "com",
    "das",
    "dos",
    "uma",
    "por",
    "que",
    "vaga",
    "vagas",
    "empresa",
    "local",
    "score",
    "motivo",
    "aderencia",
    "alta",
    "media",
    "baixa",
    "perfil",
    "conter",
    "nao",
    "sim",
    "nivel",
    "pleno",
    "senior",
    "junior",
    "remoto",
    "hibrido",
    "presencial",
    "sao",
    "paulo",
}


@dataclass(frozen=True)
class FeedbackInsight:
    insight_type: str
    candidate: str
    count: int
    evidence: str
    recommendation: str
    confidence: str


@dataclass(frozen=True)
class FeedbackInsightsResult:
    markdown_path: Path
    csv_path: Path
    reviewed_count: int
    status_counts: dict[str, int]
    low_confidence: bool
    insights: list[FeedbackInsight]


class FeedbackInsightsService:
    def __init__(
        self,
        repository: JobRepository,
        high_score_threshold: float = 70.0,
        low_score_threshold: float = 40.0,
    ) -> None:
        self.repository = repository
        self.high_score_threshold = high_score_threshold
        self.low_score_threshold = low_score_threshold

    def generate(self, reports_dir: str | Path = "reports", min_reviewed: int = 5) -> FeedbackInsightsResult:
        reviewed_jobs = self._reviewed_jobs()
        status_counts = self._status_counts(reviewed_jobs)
        low_confidence = len(reviewed_jobs) < min_reviewed
        insights = self.build_insights(reviewed_jobs, low_confidence=low_confidence)

        reports_path = Path(reports_dir)
        reports_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        markdown_path = reports_path / f"feedback_insights_{timestamp}.md"
        csv_path = reports_path / f"feedback_insights_{timestamp}.csv"

        self._write_csv(insights, csv_path)
        markdown_path.write_text(
            self.render_markdown(
                reviewed_jobs=reviewed_jobs,
                status_counts=status_counts,
                insights=insights,
                low_confidence=low_confidence,
                min_reviewed=min_reviewed,
            ),
            encoding="utf-8",
        )

        return FeedbackInsightsResult(
            markdown_path=markdown_path,
            csv_path=csv_path,
            reviewed_count=len(reviewed_jobs),
            status_counts=status_counts,
            low_confidence=low_confidence,
            insights=insights,
        )

    def summarize(self) -> dict[str, object]:
        reviewed_jobs = self._reviewed_jobs()
        relevant_jobs = [job for job in reviewed_jobs if job.review_status in POSITIVE_STATUSES]
        irrelevant_jobs = [job for job in reviewed_jobs if job.review_status in NEGATIVE_STATUSES]
        return {
            "reviewed_count": len(reviewed_jobs),
            "status_counts": self._status_counts(reviewed_jobs),
            "top_relevant_companies": self._counter_top(job.company for job in relevant_jobs),
            "top_irrelevant_companies": self._counter_top(job.company for job in irrelevant_jobs),
        }

    def build_insights(self, reviewed_jobs: list[Job], low_confidence: bool = False) -> list[FeedbackInsight]:
        insights: list[FeedbackInsight] = []
        relevant_jobs = [job for job in reviewed_jobs if job.review_status in POSITIVE_STATUSES]
        irrelevant_jobs = [job for job in reviewed_jobs if job.review_status in NEGATIVE_STATUSES]
        maybe_jobs = [job for job in reviewed_jobs if job.review_status == "maybe"]
        favorite_jobs = [job for job in reviewed_jobs if job.is_favorite]

        insights.extend(
            self._term_insights(
                "positive_term_candidate",
                relevant_jobs,
                "Avaliar inclusao em high_weight_keywords, medium_weight_keywords ou technical_area_keywords.",
                low_confidence,
            )
        )
        insights.extend(
            self._term_insights(
                "negative_term_candidate",
                irrelevant_jobs,
                "Avaliar inclusao em negative_keywords, strong_negative_title_keywords ou weak_negative_title_keywords.",
                low_confidence,
            )
        )
        insights.extend(
            self._term_insights(
                "maybe_term_candidate",
                maybe_jobs,
                "Revisar manualmente antes de promover como positivo ou negativo.",
                low_confidence,
            )
        )
        insights.extend(self._company_ratio_insights(reviewed_jobs, positive=True, low_confidence=low_confidence))
        insights.extend(self._company_ratio_insights(reviewed_jobs, positive=False, low_confidence=low_confidence))
        insights.extend(self._field_counter_insights("promising_title", relevant_jobs, "title", low_confidence))
        insights.extend(self._field_counter_insights("noisy_title", irrelevant_jobs, "title", low_confidence))
        insights.extend(self._field_counter_insights("relevant_location", relevant_jobs, "location", low_confidence))
        insights.extend(self._false_positive_insights(irrelevant_jobs, low_confidence))
        insights.extend(self._false_negative_insights(relevant_jobs, low_confidence))
        insights.extend(self._favorite_insights(favorite_jobs, low_confidence))
        return insights

    def render_markdown(
        self,
        reviewed_jobs: list[Job],
        status_counts: dict[str, int],
        insights: list[FeedbackInsight],
        low_confidence: bool,
        min_reviewed: int,
    ) -> str:
        lines = [
            "# Feedback Insights",
            "",
            "## Resumo executivo",
            "",
            f"- Vagas revisadas: {len(reviewed_jobs)}",
            f"- Minimo recomendado para confianca: {min_reviewed}",
            f"- Confianca geral: {'baixa' if low_confidence else 'normal'}",
            "- As sugestoes sao assistivas e exigem revisao humana antes de qualquer alteracao no YAML.",
            "- Este relatorio nao altera `profile_keywords.yaml` automaticamente.",
            "",
            "## Distribuicao por review_status",
            "",
        ]
        for status in REVIEW_STATUSES:
            lines.append(f"- {status}: {status_counts.get(status, 0)}")
        if low_confidence:
            lines.extend(
                [
                    "",
                    "## Aviso de baixa confianca",
                    "",
                    "A amostra revisada ainda e pequena. Use os candidatos abaixo como pistas, nao como conclusoes.",
                ]
            )

        sections = [
            ("Termos candidatos a positivos", "positive_term_candidate"),
            ("Termos candidatos a negativos", "negative_term_candidate"),
            ("Termos candidatos a talvez", "maybe_term_candidate"),
            ("Empresas para priorizar", "priority_company_candidate"),
            ("Empresas com ruido", "noisy_company_candidate"),
            ("Titulos promissores", "promising_title"),
            ("Titulos ruidosos", "noisy_title"),
            ("Localidades relevantes", "relevant_location"),
            ("Possiveis falsos positivos", "false_positive"),
            ("Possiveis falsos negativos", "false_negative"),
            ("Vagas favoritas", "favorite_job"),
        ]
        for title, insight_type in sections:
            lines.extend(self._markdown_table(title, self._filter_insights(insights, insight_type)))

        lines.extend(
            [
                "## Recomendacoes para profile_keywords.yaml",
                "",
                "- Revise termos positivos recorrentes antes de adicionar em `high_weight_keywords` ou `technical_area_keywords`.",
                "- Revise termos negativos recorrentes antes de adicionar em `negative_keywords` ou listas negativas do pre-filtro.",
                "- Empresas com alta proporcao de vagas relevantes podem entrar em `priority_companies` ou ganhar prioridade na curadoria Gupy.",
                "- Empresas com ruido recorrente podem exigir termos negativos especificos ou menor prioridade.",
                "- Falsos positivos ajudam a endurecer filtros; falsos negativos ajudam a recuperar bons sinais perdidos.",
                "",
                "## Aviso final",
                "",
                "Estas sugestoes sao assistivas. A decisao final deve ser humana, contextual e aplicada manualmente.",
                "",
            ]
        )
        return "\n".join(lines)

    def _reviewed_jobs(self) -> list[Job]:
        with self.repository.session_factory() as session:
            statement = (
                select(Job)
                .where(Job.review_status.in_(REVIEWED_STATUSES))
                .order_by(Job.reviewed_at.desc().nullslast(), Job.match_score.desc())
            )
            return list(session.scalars(statement).unique().all())

    def _status_counts(self, jobs: list[Job]) -> dict[str, int]:
        counts = {status: 0 for status in REVIEW_STATUSES}
        for job in jobs:
            counts[job.review_status or "unreviewed"] = counts.get(job.review_status or "unreviewed", 0) + 1
        return counts

    def _term_insights(
        self,
        insight_type: str,
        jobs: list[Job],
        recommendation: str,
        low_confidence: bool,
    ) -> list[FeedbackInsight]:
        evidence: dict[str, list[str]] = defaultdict(list)
        for job in jobs:
            for term in self._terms_for_job(job):
                evidence[term].append(self._job_label(job))
        return [
            FeedbackInsight(
                insight_type=insight_type,
                candidate=term,
                count=len(labels),
                evidence=self._join_evidence(labels),
                recommendation=recommendation,
                confidence=self._confidence(len(labels), low_confidence),
            )
            for term, labels in self._counter_top_from_mapping(evidence)
        ]

    def _company_ratio_insights(
        self,
        jobs: list[Job],
        positive: bool,
        low_confidence: bool,
    ) -> list[FeedbackInsight]:
        by_company: dict[str, list[Job]] = defaultdict(list)
        for job in jobs:
            company = (job.company or "Nao informado").strip() or "Nao informado"
            by_company[company].append(job)

        rows: list[tuple[float, str, list[Job], int]] = []
        target_statuses = POSITIVE_STATUSES if positive else NEGATIVE_STATUSES
        for company, company_jobs in by_company.items():
            target_count = sum(1 for job in company_jobs if job.review_status in target_statuses)
            if target_count == 0:
                continue
            ratio = target_count / len(company_jobs)
            if ratio >= 0.6:
                rows.append((ratio, company, company_jobs, target_count))
        rows.sort(key=lambda item: (item[0], item[3], item[1]), reverse=True)

        insight_type = "priority_company_candidate" if positive else "noisy_company_candidate"
        recommendation = (
            "Avaliar inclusao ou reforco em priority_companies."
            if positive
            else "Avaliar reducao de prioridade, termos negativos ou revisao de slugs/fontes."
        )
        return [
            FeedbackInsight(
                insight_type=insight_type,
                candidate=company,
                count=target_count,
                evidence=f"{target_count}/{len(company_jobs)} revisadas ({ratio:.0%}); {self._join_evidence(self._job_label(job) for job in company_jobs)}",
                recommendation=recommendation,
                confidence=self._confidence(target_count, low_confidence),
            )
            for ratio, company, company_jobs, target_count in rows[:10]
        ]

    def _field_counter_insights(
        self,
        insight_type: str,
        jobs: list[Job],
        field: str,
        low_confidence: bool,
    ) -> list[FeedbackInsight]:
        evidence: dict[str, list[str]] = defaultdict(list)
        for job in jobs:
            value = (getattr(job, field, "") or "Nao informado").strip() or "Nao informado"
            evidence[value].append(self._job_label(job))

        recommendations = {
            "promising_title": "Avaliar termos do titulo em desired_titles ou technical_title_keywords.",
            "noisy_title": "Avaliar termos do titulo em listas negativas do perfil ou pre-filtro.",
            "relevant_location": "Avaliar reforco em desired_locations ou location_boost_keywords.",
        }
        return [
            FeedbackInsight(
                insight_type=insight_type,
                candidate=value,
                count=len(labels),
                evidence=self._join_evidence(labels),
                recommendation=recommendations.get(insight_type, "Revisar manualmente."),
                confidence=self._confidence(len(labels), low_confidence),
            )
            for value, labels in self._counter_top_from_mapping(evidence)
        ]

    def _false_positive_insights(self, jobs: list[Job], low_confidence: bool) -> list[FeedbackInsight]:
        false_positives = [job for job in jobs if (job.match_score or 0) >= self.high_score_threshold]
        false_positives.sort(key=lambda job: job.match_score or 0, reverse=True)
        return [
            FeedbackInsight(
                insight_type="false_positive",
                candidate=job.title,
                count=1,
                evidence=f"{self._job_label(job)} | score={job.match_score:.1f} | {job.url}",
                recommendation="Revisar termos positivos que elevaram o score e considerar negativos especificos.",
                confidence=self._confidence(1, low_confidence),
            )
            for job in false_positives[:10]
        ]

    def _false_negative_insights(self, jobs: list[Job], low_confidence: bool) -> list[FeedbackInsight]:
        false_negatives = [job for job in jobs if (job.match_score or 0) <= self.low_score_threshold]
        false_negatives.sort(key=lambda job: job.match_score or 0)
        return [
            FeedbackInsight(
                insight_type="false_negative",
                candidate=job.title,
                count=1,
                evidence=f"{self._job_label(job)} | score={job.match_score:.1f} | {job.url}",
                recommendation="Revisar termos ausentes e considerar novos positivos ou boosts de localidade/empresa.",
                confidence=self._confidence(1, low_confidence),
            )
            for job in false_negatives[:10]
        ]

    def _favorite_insights(self, jobs: list[Job], low_confidence: bool) -> list[FeedbackInsight]:
        jobs = sorted(jobs, key=lambda job: (job.match_score or 0), reverse=True)
        return [
            FeedbackInsight(
                insight_type="favorite_job",
                candidate=job.title,
                count=1,
                evidence=f"{self._job_label(job)} | status={job.review_status} | score={job.match_score:.1f}",
                recommendation="Usar como exemplo positivo ao calibrar palavras-chave e empresas prioritarias.",
                confidence=self._confidence(1, low_confidence),
            )
            for job in jobs[:10]
        ]

    def _terms_for_job(self, job: Job) -> list[str]:
        text = " ".join(
            [
                job.title or "",
                job.company or "",
                job.location or "",
                job.description_snippet or "",
                job.match_reason or "",
                job.prefilter_reason or "",
                job.review_notes or "",
            ]
        )
        terms = []
        for token in normalize_text(text).split():
            if len(token) < 4 or token in STOPWORDS or token.isdigit():
                continue
            terms.append(token)
        return sorted(set(terms))

    def _counter_top_from_mapping(self, evidence: dict[str, list[str]], limit: int = 12) -> list[tuple[str, list[str]]]:
        return sorted(evidence.items(), key=lambda item: (len(item[1]), item[0]), reverse=True)[:limit]

    def _counter_top(self, values) -> list[tuple[str, int]]:
        cleaned = [str(value or "Nao informado").strip() or "Nao informado" for value in values]
        return Counter(cleaned).most_common(10)

    def _confidence(self, count: int, low_confidence: bool) -> str:
        if low_confidence or count <= 1:
            return "low"
        if count <= 3:
            return "medium"
        return "high"

    def _write_csv(self, insights: list[FeedbackInsight], path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=INSIGHT_COLUMNS)
            writer.writeheader()
            for insight in insights:
                writer.writerow(
                    {
                        "insight_type": insight.insight_type,
                        "candidate": insight.candidate,
                        "count": insight.count,
                        "evidence": insight.evidence,
                        "recommendation": insight.recommendation,
                        "confidence": insight.confidence,
                    }
                )

    def _markdown_table(self, title: str, insights: list[FeedbackInsight]) -> list[str]:
        lines = [f"## {title}", ""]
        if not insights:
            return lines + ["Nenhum insight nesta categoria.", ""]
        lines.extend(["| Candidato | Total | Evidencia | Confianca |", "| --- | ---: | --- | --- |"])
        for insight in insights[:10]:
            lines.append(
                f"| {self._escape_md(insight.candidate)} | {insight.count} | "
                f"{self._escape_md(insight.evidence)} | {insight.confidence} |"
            )
        lines.append("")
        return lines

    def _filter_insights(self, insights: list[FeedbackInsight], insight_type: str) -> list[FeedbackInsight]:
        return [insight for insight in insights if insight.insight_type == insight_type]

    def _join_evidence(self, labels) -> str:
        unique = []
        seen = set()
        for label in labels:
            if label in seen:
                continue
            unique.append(label)
            seen.add(label)
        return "; ".join(unique[:5])

    def _job_label(self, job: Job) -> str:
        return f"{job.title} | {job.company} | {job.location}"

    def _escape_md(self, value: str) -> str:
        return str(value).replace("|", "\\|").replace("\n", " ").strip()
