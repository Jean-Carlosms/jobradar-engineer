from __future__ import annotations

import sqlite3
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from src.config import Settings
from src.database import JobRepository
from src.services.feedback_insights import FeedbackInsightsService
from src.services.job_review_service import REVIEW_STATUSES, JobReviewService


DEFAULT_DB_PATH = Path("data/jobs.db")
SAMPLE_DB_PATH = Path("data/sample_jobs.db")
PREFILTER_DEBUG_DIR = Path("logs/gupy_debug")
JOBS_TABLE = "jobs"
ANALYSES_TABLE = "job_analyses"

RAW_COLUMNS = [
    "id",
    "title",
    "company",
    "location",
    "source",
    "url",
    "description_snippet",
    "published_date",
    "collected_at",
    "match_score",
    "match_reason",
    "priority_company",
    "query_used",
    "prefilter_score",
    "prefilter_reason",
    "review_status",
    "review_notes",
    "is_favorite",
    "viewed_at",
    "reviewed_at",
    "already_sent",
    "fit_level",
    "fit_score",
    "matched_skills_json",
    "missing_skills_json",
    "strengths_json",
    "risks_json",
    "resume_keywords_json",
    "recruiter_message",
    "analysis_summary",
]

DERIVED_ANALYSIS_COLUMNS = [
    "matched_skills",
    "missing_skills",
    "strengths",
    "risks",
    "resume_keywords",
]

DISPLAY_COLUMNS = {
    "title": "titulo",
    "company": "empresa",
    "location": "local",
    "source": "fonte",
    "match_score": "score",
    "match_reason": "motivo de aderencia",
    "priority_company": "empresa prioritaria",
    "prefilter_score": "score pre-filtro",
    "prefilter_reason": "motivo pre-filtro",
    "review_status": "status revisao",
    "is_favorite": "favorita",
    "viewed_at": "visualizada em",
    "already_sent": "enviada",
    "query_used": "query usada",
    "fit_level": "fit level",
    "fit_score": "fit score",
    "matched_skills": "competencias encontradas",
    "missing_skills": "competencias faltantes",
    "analysis_summary": "resumo da analise",
    "recruiter_message": "mensagem recrutador",
    "url": "link",
}


def empty_jobs_dataframe() -> pd.DataFrame:
    return pd.DataFrame(columns=RAW_COLUMNS + DERIVED_ANALYSIS_COLUMNS)


def load_jobs(db_path: str | Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    path = Path(db_path)
    if not path.exists():
        return empty_jobs_dataframe()

    try:
        with sqlite3.connect(path) as connection:
            if not _table_exists(connection, JOBS_TABLE):
                return empty_jobs_dataframe()
            dataframe = pd.read_sql_query(_jobs_query(connection), connection)
    except sqlite3.Error:
        return empty_jobs_dataframe()

    return normalize_jobs_dataframe(dataframe)


def normalize_jobs_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    for column in RAW_COLUMNS:
        if column not in dataframe.columns:
            dataframe[column] = _default_value_for(column)

    dataframe["match_score"] = pd.to_numeric(dataframe["match_score"], errors="coerce").fillna(0.0)
    dataframe["prefilter_score"] = pd.to_numeric(dataframe["prefilter_score"], errors="coerce").fillna(0.0)
    dataframe["fit_score"] = pd.to_numeric(dataframe["fit_score"], errors="coerce").fillna(0).astype(int)
    dataframe["priority_company"] = dataframe["priority_company"].fillna(False).astype(bool)
    dataframe["is_favorite"] = dataframe["is_favorite"].fillna(False).astype(bool)
    dataframe["already_sent"] = dataframe["already_sent"].fillna(False).astype(bool)

    text_columns = [
        "title",
        "company",
        "location",
        "source",
        "url",
        "match_reason",
        "query_used",
        "prefilter_reason",
        "review_status",
        "review_notes",
        "viewed_at",
        "reviewed_at",
        "fit_level",
        "matched_skills_json",
        "missing_skills_json",
        "strengths_json",
        "risks_json",
        "resume_keywords_json",
        "recruiter_message",
        "analysis_summary",
    ]
    for column in text_columns:
        dataframe[column] = dataframe[column].fillna("").astype(str)

    dataframe["matched_skills"] = dataframe["matched_skills_json"].map(json_list_to_text)
    dataframe["missing_skills"] = dataframe["missing_skills_json"].map(json_list_to_text)
    dataframe["strengths"] = dataframe["strengths_json"].map(json_list_to_text)
    dataframe["risks"] = dataframe["risks_json"].map(json_list_to_text)
    dataframe["resume_keywords"] = dataframe["resume_keywords_json"].map(json_list_to_text)

    return dataframe[RAW_COLUMNS + DERIVED_ANALYSIS_COLUMNS]


def calculate_metrics(dataframe: pd.DataFrame) -> dict[str, Any]:
    if dataframe.empty:
        return {
            "total_jobs": 0,
            "sent_jobs": 0,
            "unsent_jobs": 0,
            "average_score": 0.0,
            "max_score": 0.0,
        "priority_companies": 0,
        "reviewed_jobs": 0,
        "relevant_jobs": 0,
        "irrelevant_jobs": 0,
        "maybe_jobs": 0,
        "applied_jobs": 0,
        "favorite_jobs": 0,
        }

    return {
        "total_jobs": int(len(dataframe)),
        "sent_jobs": int(dataframe["already_sent"].sum()),
        "unsent_jobs": int((~dataframe["already_sent"]).sum()),
        "average_score": float(dataframe["match_score"].mean()),
        "max_score": float(dataframe["match_score"].max()),
        "priority_companies": int(dataframe["priority_company"].sum()),
        "reviewed_jobs": int((dataframe["review_status"] != "unreviewed").sum()),
        "relevant_jobs": int((dataframe["review_status"] == "relevant").sum()),
        "irrelevant_jobs": int((dataframe["review_status"] == "irrelevant").sum()),
        "maybe_jobs": int((dataframe["review_status"] == "maybe").sum()),
        "applied_jobs": int((dataframe["review_status"] == "applied").sum()),
        "favorite_jobs": int(dataframe["is_favorite"].sum()),
    }


def filter_jobs(
    dataframe: pd.DataFrame,
    min_score: float = 0.0,
    source: str = "Todas",
    company: str = "Todas",
    location: str = "Todas",
    sent_status: str = "Todas",
    priority_only: bool = False,
    review_status: str = "Todos",
    favorite_only: bool = False,
    text_search: str = "",
) -> pd.DataFrame:
    filtered = dataframe.copy()
    if filtered.empty:
        return filtered

    filtered = filtered[filtered["match_score"] >= min_score]

    if source != "Todas":
        filtered = filtered[filtered["source"] == source]
    if company != "Todas":
        filtered = filtered[filtered["company"] == company]
    if location != "Todas":
        filtered = filtered[filtered["location"] == location]
    if sent_status == "Enviadas":
        filtered = filtered[filtered["already_sent"]]
    elif sent_status == "Nao enviadas":
        filtered = filtered[~filtered["already_sent"]]
    if priority_only:
        filtered = filtered[filtered["priority_company"]]
    if review_status != "Todos":
        filtered = filtered[filtered["review_status"] == review_status]
    if favorite_only:
        filtered = filtered[filtered["is_favorite"]]
    if text_search.strip():
        term = text_search.strip().casefold()
        search_area = (
            filtered["title"].str.casefold()
            + " "
            + filtered["company"].str.casefold()
            + " "
            + filtered["match_reason"].str.casefold()
        )
        filtered = filtered[search_area.str.contains(term, na=False, regex=False)]

    return filtered.sort_values(["match_score", "collected_at"], ascending=[False, False])


def to_display_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    display_columns = list(DISPLAY_COLUMNS.keys())
    working = dataframe.copy()
    for column in ["matched_skills", "missing_skills"]:
        if column not in working.columns:
            working[column] = ""
    display = working[display_columns].rename(columns=DISPLAY_COLUMNS)
    display["score"] = display["score"].round(1)
    display["score pre-filtro"] = display["score pre-filtro"].round(1)
    display["empresa prioritaria"] = display["empresa prioritaria"].map({True: "sim", False: "nao"})
    display["favorita"] = display["favorita"].map({True: "sim", False: "nao"})
    display["enviada"] = display["enviada"].map({True: "sim", False: "nao"})
    return display


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    cursor = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _jobs_query(connection: sqlite3.Connection) -> str:
    job_columns = ", ".join(_job_select_columns(connection))
    if not _table_exists(connection, ANALYSES_TABLE):
        return f"""
            SELECT
                {job_columns},
                '' AS fit_level,
                0 AS fit_score,
                '[]' AS matched_skills_json,
                '[]' AS missing_skills_json,
                '[]' AS strengths_json,
                '[]' AS risks_json,
                '[]' AS resume_keywords_json,
                '' AS recruiter_message,
                '' AS analysis_summary
            FROM {JOBS_TABLE} j
        """
    return f"""
        SELECT
            {job_columns},
            COALESCE(a.fit_level, '') AS fit_level,
            COALESCE(a.fit_score, 0) AS fit_score,
            COALESCE(a.matched_skills_json, '[]') AS matched_skills_json,
            COALESCE(a.missing_skills_json, '[]') AS missing_skills_json,
            COALESCE(a.strengths_json, '[]') AS strengths_json,
            COALESCE(a.risks_json, '[]') AS risks_json,
            COALESCE(a.resume_keywords_json, '[]') AS resume_keywords_json,
            COALESCE(a.recruiter_message, '') AS recruiter_message,
            COALESCE(a.analysis_summary, '') AS analysis_summary
        FROM {JOBS_TABLE} j
        LEFT JOIN {ANALYSES_TABLE} a ON a.job_id = j.id
    """


def _job_select_columns(connection: sqlite3.Connection) -> list[str]:
    existing_columns = _table_columns(connection, JOBS_TABLE)
    select_columns = []
    for column in RAW_COLUMNS[:21]:
        if column in existing_columns:
            select_columns.append(f"j.{column}")
        else:
            default = _sql_default_for(column)
            select_columns.append(f"{default} AS {column}")
    return select_columns


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    cursor = connection.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def _sql_default_for(column: str) -> str:
    if column in {"match_score", "prefilter_score"}:
        return "0"
    if column in {"priority_company", "is_favorite", "already_sent"}:
        return "0"
    return "''"


def json_list_to_text(value: str) -> str:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return ""
    if not isinstance(parsed, list):
        return ""
    return ", ".join(str(item) for item in parsed)


def _default_value_for(column: str) -> Any:
    if column in {"match_score", "prefilter_score"}:
        return 0.0
    if column in {"priority_company", "is_favorite", "already_sent"}:
        return False
    if column == "review_status":
        return "unreviewed"
    return ""


def run_dashboard() -> None:
    st.set_page_config(page_title="JobRadar Engineer", layout="wide")
    st.title("JobRadar Engineer")
    st.caption("Dashboard local das vagas coletadas no SQLite.")

    db_path = select_database_path()
    jobs = load_jobs(db_path)

    if not Path(db_path).exists():
        if Path(db_path) == SAMPLE_DB_PATH:
            st.info("O banco `data/sample_jobs.db` ainda nao existe. Rode `python scripts/load_sample_data.py` primeiro.")
        else:
            st.info("O banco `data/jobs.db` ainda nao existe. Rode `python -m src.main --dry-run --source mock` primeiro.")
        return

    if jobs.empty:
        st.info("Nenhuma vaga coletada ainda. Execute o robo para popular o banco local.")
        return

    metrics = calculate_metrics(jobs)
    metric_columns = st.columns(6)
    metric_columns[0].metric("Total", metrics["total_jobs"])
    metric_columns[1].metric("Enviadas", metrics["sent_jobs"])
    metric_columns[2].metric("Nao enviadas", metrics["unsent_jobs"])
    metric_columns[3].metric("Score medio", f"{metrics['average_score']:.1f}")
    metric_columns[4].metric("Maior score", f"{metrics['max_score']:.1f}")
    metric_columns[5].metric("Prioritarias", metrics["priority_companies"])
    review_columns = st.columns(6)
    review_columns[0].metric("Revisadas", metrics["reviewed_jobs"])
    review_columns[1].metric("Relevantes", metrics["relevant_jobs"])
    review_columns[2].metric("Irrelevantes", metrics["irrelevant_jobs"])
    review_columns[3].metric("Talvez", metrics["maybe_jobs"])
    review_columns[4].metric("Aplicadas", metrics["applied_jobs"])
    review_columns[5].metric("Favoritas", metrics["favorite_jobs"])

    filtered = render_sidebar_filters(jobs)

    st.subheader("Vagas filtradas")
    if filtered.empty:
        st.warning("Nenhuma vaga atende aos filtros selecionados.")
        return

    display = to_display_dataframe(filtered)
    st.download_button(
        "Exportar CSV",
        data=display.to_csv(index=False).encode("utf-8-sig"),
        file_name="jobradar_vagas_filtradas.csv",
        mime="text/csv",
    )
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={"link": st.column_config.LinkColumn("link")},
    )

    st.subheader("Top Vagas")
    st.dataframe(
        to_display_dataframe(filtered.head(10)),
        use_container_width=True,
        hide_index=True,
        column_config={"link": st.column_config.LinkColumn("link")},
    )

    priority_jobs = filtered[filtered["priority_company"]]
    st.subheader("Empresas Prioritarias")
    if priority_jobs.empty:
        st.info("Nenhuma vaga filtrada pertence a empresas prioritarias.")
    else:
        st.dataframe(
            to_display_dataframe(priority_jobs),
            use_container_width=True,
            hide_index=True,
            column_config={"link": st.column_config.LinkColumn("link")},
        )

    render_human_review_section(filtered, db_path)
    render_feedback_insights_section(db_path)
    render_analysis_section(filtered)
    render_charts(filtered)
    render_prefilter_audit_section()


def select_database_path() -> Path:
    env_path = os.getenv("JOBRADAR_DASHBOARD_DB")
    if env_path:
        st.sidebar.caption(f"Banco via JOBRADAR_DASHBOARD_DB: {env_path}")
        return Path(env_path)

    selected = st.sidebar.radio(
        "Banco de dados",
        ["Real local", "Dados ficticios"],
        index=0,
        help="Use dados ficticios para prints de portfolio e publicacao no GitHub.",
    )
    if selected == "Dados ficticios":
        return SAMPLE_DB_PATH
    return DEFAULT_DB_PATH


def render_sidebar_filters(jobs: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtros")

    max_score = float(jobs["match_score"].max()) if not jobs.empty else 100.0
    min_score = st.sidebar.slider("Score minimo", 0.0, max(100.0, max_score), 0.0, 1.0)
    source = st.sidebar.selectbox("Fonte", _options(jobs, "source"))
    company = st.sidebar.selectbox("Empresa", _options(jobs, "company"))
    location = st.sidebar.selectbox("Localidade", _options(jobs, "location"))
    sent_status = st.sidebar.selectbox("Status de envio", ["Todas", "Enviadas", "Nao enviadas"])
    priority_only = st.sidebar.checkbox("Somente empresas prioritarias")
    review_status = st.sidebar.selectbox("Status de revisao", ["Todos", *REVIEW_STATUSES])
    favorite_only = st.sidebar.checkbox("Somente favoritas")
    text_search = st.sidebar.text_input("Buscar por titulo, empresa ou motivo")

    return filter_jobs(
        jobs,
        min_score=min_score,
        source=source,
        company=company,
        location=location,
        sent_status=sent_status,
        priority_only=priority_only,
        review_status=review_status,
        favorite_only=favorite_only,
        text_search=text_search,
    )


def render_charts(dataframe: pd.DataFrame) -> None:
    st.subheader("Graficos")
    left, right = st.columns(2)

    with left:
        st.write("Vagas por fonte")
        st.bar_chart(dataframe["source"].value_counts())

        st.write("Distribuicao de score")
        st.bar_chart(dataframe["match_score"].round(0).value_counts().sort_index())

    with right:
        st.write("Vagas por localidade")
        st.bar_chart(dataframe["location"].value_counts())

        st.write("Vagas por empresa")
        st.bar_chart(dataframe["company"].value_counts().head(15))


def load_latest_prefilter_debug(debug_dir: str | Path = PREFILTER_DEBUG_DIR) -> pd.DataFrame:
    path = latest_prefilter_debug_path(debug_dir)
    if path is None:
        return pd.DataFrame()
    try:
        dataframe = pd.read_csv(path)
    except (OSError, pd.errors.ParserError):
        return pd.DataFrame()
    if "prefilter_score" in dataframe.columns:
        dataframe["prefilter_score"] = pd.to_numeric(dataframe["prefilter_score"], errors="coerce").fillna(0.0)
    for column in ["should_keep", "should_enrich"]:
        if column in dataframe.columns:
            dataframe[column] = dataframe[column].astype(str).str.casefold().isin(["true", "1", "yes", "sim"])
    return dataframe


def latest_prefilter_debug_path(debug_dir: str | Path = PREFILTER_DEBUG_DIR) -> Path | None:
    candidates = sorted(Path(debug_dir).glob("prefilter_*.csv"), key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def render_prefilter_audit_section() -> None:
    st.subheader("Auditoria do Pre-filtro")
    path = latest_prefilter_debug_path()
    if path is None:
        st.info("Nenhum CSV de pre-filtro encontrado. Rode a Gupy com `--debug-search`.")
        return

    data = load_latest_prefilter_debug()
    if data.empty:
        st.info("Nao foi possivel carregar o CSV de pre-filtro mais recente.")
        return

    kept = data[data["should_keep"]]
    discarded = data[~data["should_keep"]]
    st.caption(f"CSV: {path}")
    left, middle, right = st.columns(3)
    left.metric("Mantidas", len(kept))
    middle.metric("Descartadas", len(discarded))
    right.metric("Enriquecimento", int(data["should_enrich"].sum()) if "should_enrich" in data else 0)

    st.write("Descartadas com maior score")
    st.dataframe(
        discarded.sort_values("prefilter_score", ascending=False).head(10),
        use_container_width=True,
        hide_index=True,
    )

    st.write("Mantidas com menor score")
    st.dataframe(
        kept.sort_values("prefilter_score", ascending=True).head(10),
        use_container_width=True,
        hide_index=True,
    )

    if "prefilter_reason" in discarded:
        st.write("Principais motivos de descarte")
        reasons = discarded["prefilter_reason"].fillna("").astype(str).map(_prefilter_reason_group).value_counts().head(10)
        st.dataframe(reasons.rename_axis("motivo").reset_index(name="total"), use_container_width=True, hide_index=True)


def _prefilter_reason_group(reason: str) -> str:
    lowered = reason.casefold()
    if "negativo forte" in lowered:
        return "negativo forte"
    if "sem sinais tecnicos" in lowered or "sem sinais técnicos" in lowered:
        return "sem sinais tecnicos"
    if "negativo fraco" in lowered:
        return "negativo fraco"
    return reason.split(":", 1)[0].strip() or "outros"


def render_human_review_section(dataframe: pd.DataFrame, db_path: str | Path) -> None:
    st.subheader("Revisao Humana")
    if dataframe.empty:
        st.info("Nenhuma vaga filtrada para revisar.")
        return

    sorted_jobs = dataframe.sort_values(["is_favorite", "match_score", "prefilter_score"], ascending=[False, False, False])
    options = {
        f"{row.title} | {row.company} | score {row.match_score:.1f} | id {row.id}": int(row.id)
        for row in sorted_jobs.itertuples()
    }
    selected_label = st.selectbox("Selecionar vaga para revisar", list(options.keys()))
    selected = dataframe[dataframe["id"] == options[selected_label]].iloc[0]

    left, right = st.columns(2)
    with left:
        st.write(f"Titulo: {selected['title']}")
        st.write(f"Empresa: {selected['company']}")
        st.write(f"Local: {selected['location']}")
        st.write(f"Link: {selected['url']}")
    with right:
        st.write(f"Match score: {selected['match_score']:.1f}")
        st.write(f"Fit score: {selected['fit_score']}")
        st.write(f"Pre-filtro: {selected['prefilter_score']:.1f}")
        st.write(f"Status atual: {selected['review_status'] or 'unreviewed'}")

    service = _review_service(db_path)
    if st.button("Marcar como visualizada"):
        service.mark_viewed(int(selected["id"]))
        st.success("Vaga marcada como visualizada.")

    current_status = selected["review_status"] if selected["review_status"] in REVIEW_STATUSES else "unreviewed"
    with st.form("job_review_form"):
        review_status = st.selectbox(
            "Status",
            REVIEW_STATUSES,
            index=REVIEW_STATUSES.index(current_status),
            format_func=_review_status_label,
        )
        is_favorite = st.checkbox("Favorita", value=bool(selected["is_favorite"]))
        review_notes = st.text_area("Observacoes", value=selected["review_notes"] or "", height=100)
        submitted = st.form_submit_button("Salvar feedback")

    if submitted:
        service.update_review(
            int(selected["id"]),
            review_status=review_status,
            review_notes=review_notes,
            is_favorite=is_favorite,
        )
        st.success("Feedback salvo no SQLite.")


def _review_service(db_path: str | Path) -> JobReviewService:
    settings = Settings(database_path=Path(db_path))
    repository = JobRepository(settings)
    repository.init_db()
    return JobReviewService(repository)


def render_feedback_insights_section(db_path: str | Path) -> None:
    st.subheader("Insights de Feedback")
    settings = Settings(database_path=Path(db_path))
    repository = JobRepository(settings)
    repository.init_db()
    summary = FeedbackInsightsService(repository).summarize()
    status_counts = summary["status_counts"]

    columns = st.columns(4)
    columns[0].metric("Revisadas", summary["reviewed_count"])
    columns[1].metric("Relevantes", status_counts.get("relevant", 0) + status_counts.get("applied", 0))
    columns[2].metric("Irrelevantes", status_counts.get("irrelevant", 0) + status_counts.get("ignored", 0))
    columns[3].metric("Talvez", status_counts.get("maybe", 0))

    left, right = st.columns(2)
    with left:
        st.write("Top empresas relevantes")
        st.dataframe(
            _counter_dataframe(summary["top_relevant_companies"]),
            use_container_width=True,
            hide_index=True,
        )
    with right:
        st.write("Top empresas irrelevantes")
        st.dataframe(
            _counter_dataframe(summary["top_irrelevant_companies"]),
            use_container_width=True,
            hide_index=True,
        )
    st.info("Gere o relatorio completo via CLI: `python -m src.main --feedback-insights`.")


def _counter_dataframe(items: list[tuple[str, int]]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame([{"item": "nenhum dado", "total": 0}])
    return pd.DataFrame([{"item": item, "total": count} for item, count in items])


def _review_status_label(status: str) -> str:
    labels = {
        "unreviewed": "Nao revisada",
        "relevant": "Relevante",
        "irrelevant": "Irrelevante",
        "maybe": "Talvez",
        "applied": "Aplicada",
        "ignored": "Ignorada",
    }
    return labels.get(status, status)


def render_analysis_section(dataframe: pd.DataFrame) -> None:
    st.subheader("Analise Vaga x Perfil")
    analyzed = dataframe[dataframe["fit_level"].astype(str).str.len() > 0]
    if analyzed.empty:
        st.info("Nenhuma analise encontrada para as vagas filtradas. Rode `python -m src.main --analyze-only`.")
        return

    st.download_button(
        "Exportar analises CSV",
        data=analysis_export_dataframe(analyzed).to_csv(index=False).encode("utf-8-sig"),
        file_name="jobradar_analises.csv",
        mime="text/csv",
    )

    options = {
        f"{row.title} | {row.company} | fit {row.fit_score}": row.id
        for row in analyzed.sort_values("fit_score", ascending=False).itertuples()
    }
    selected_label = st.selectbox("Selecionar vaga para analise detalhada", list(options.keys()))
    selected = analyzed[analyzed["id"] == options[selected_label]].iloc[0]

    left, right = st.columns(2)
    with left:
        st.write("Dados da vaga")
        st.write(f"Titulo: {selected['title']}")
        st.write(f"Empresa: {selected['company']}")
        st.write(f"Local: {selected['location']}")
        st.write(f"Score original: {selected['match_score']:.1f}")
        st.write(f"Fit score: {selected['fit_score']}/100")
        st.write(f"Fit level: {selected['fit_level']}")
    with right:
        st.write("Competencias")
        st.write(f"Encontradas: {selected['matched_skills'] or 'Nao informado'}")
        st.write(f"Faltantes: {selected['missing_skills'] or 'Nao informado'}")
        st.write(f"Keywords para curriculo: {selected['resume_keywords'] or 'Nao informado'}")

    st.write("Pontos fortes")
    st.write(selected["strengths"] or "Nao informado")
    st.write("Riscos")
    st.write(selected["risks"] or "Nao informado")
    st.write("Mensagem sugerida para recrutador")
    st.info(selected["recruiter_message"])
    st.write("Resumo da analise")
    st.write(selected["analysis_summary"])


def analysis_export_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "title",
        "company",
        "location",
        "source",
        "match_score",
        "fit_level",
        "fit_score",
        "matched_skills",
        "missing_skills",
        "strengths",
        "risks",
        "resume_keywords",
        "recruiter_message",
        "analysis_summary",
        "url",
    ]
    return dataframe[columns].rename(
        columns={
            "title": "titulo",
            "company": "empresa",
            "location": "local",
            "source": "fonte",
            "match_score": "score original",
            "url": "link",
        }
    )


def _options(dataframe: pd.DataFrame, column: str) -> list[str]:
    values = sorted(value for value in dataframe[column].dropna().unique().tolist() if str(value).strip())
    return ["Todas"] + values


if __name__ == "__main__":
    run_dashboard()
