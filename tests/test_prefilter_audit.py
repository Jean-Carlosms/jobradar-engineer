import csv

from src.config import Settings
from src.main import run_prefilter_audit_only
from src.services.prefilter_audit import classify_audit_bucket, generate_prefilter_audit, load_prefilter_rows


def write_prefilter_csv(path):
    rows = [
        {
            "title": "Engenheiro de Automacao",
            "company": "Facens",
            "location": "Sorocaba",
            "url": "https://example.com/1",
            "prefilter_score": "72",
            "prefilter_reason": "manter e enriquecer: termos tecnicos no titulo: engenheiro.",
            "should_keep": "True",
            "should_enrich": "True",
        },
        {
            "title": "Assistente de Dados",
            "company": "Empresa",
            "location": "Campinas",
            "url": "https://example.com/2",
            "prefilter_score": "18",
            "prefilter_reason": "manter sem enriquecer: negativo fraco: assistente.",
            "should_keep": "True",
            "should_enrich": "False",
        },
        {
            "title": "Vendedor de Loja",
            "company": "Loja",
            "location": "Sao Paulo",
            "url": "https://example.com/3",
            "prefilter_score": "0",
            "prefilter_reason": "descartar: negativo forte: vendedor e loja.",
            "should_keep": "False",
            "should_enrich": "False",
        },
        {
            "title": "Analista Generalista",
            "company": "Empresa",
            "location": "Remoto",
            "url": "https://example.com/4",
            "prefilter_score": "0",
            "prefilter_reason": "descartar: sem sinais tecnicos suficientes.",
            "should_keep": "False",
            "should_enrich": "False",
        },
        {
            "title": "Coordenador Administrativo",
            "company": "Empresa",
            "location": "Remoto",
            "url": "https://example.com/5",
            "prefilter_score": "36",
            "prefilter_reason": "descartar: sem sinais tecnicos suficientes.",
            "should_keep": "False",
            "should_enrich": "False",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return path


def test_classify_audit_bucket():
    assert classify_audit_bucket({"prefilter_score": "70", "should_keep": "True", "prefilter_reason": ""}) == "kept_high_score"
    assert classify_audit_bucket({"prefilter_score": "10", "should_keep": "True", "prefilter_reason": ""}) == "kept_low_score"
    assert classify_audit_bucket({"prefilter_score": "40", "should_keep": "False", "prefilter_reason": ""}) == "discarded_high_score"
    assert (
        classify_audit_bucket({"prefilter_score": "0", "should_keep": "False", "prefilter_reason": "negativo forte"})
        == "discarded_strong_negative"
    )
    assert (
        classify_audit_bucket(
            {"prefilter_score": "0", "should_keep": "False", "prefilter_reason": "sem sinais tecnicos suficientes"}
        )
        == "discarded_no_technical_term"
    )


def test_load_prefilter_rows_adds_bucket(tmp_path):
    path = write_prefilter_csv(tmp_path / "prefilter.csv")

    rows = load_prefilter_rows(path)

    assert len(rows) == 5
    assert rows[0]["audit_bucket"] == "kept_high_score"
    assert rows[2]["audit_bucket"] == "discarded_strong_negative"


def test_generate_prefilter_audit_creates_markdown_and_csv(tmp_path):
    input_path = write_prefilter_csv(tmp_path / "prefilter.csv")
    reports_dir = tmp_path / "reports"

    result = generate_prefilter_audit(input_path, reports_dir=reports_dir)

    assert result.total == 5
    assert result.kept == 2
    assert result.discarded == 3
    assert result.enrich == 1
    assert result.markdown_path.exists()
    assert result.csv_path.exists()
    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert "Resumo executivo" in markdown
    assert "Vagas descartadas por negativo forte" in markdown
    assert "Recomendacoes de ajuste" in markdown
    with result.csv_path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert "audit_bucket" in rows[0]


def test_generate_prefilter_audit_summary_fields(tmp_path):
    result = generate_prefilter_audit(write_prefilter_csv(tmp_path / "prefilter.csv"), reports_dir=tmp_path / "reports")

    assert result.buckets["kept_high_score"] == 1
    assert result.top_discard_reasons[0][0] in {"sem sinais tecnicos", "negativo forte"}
    assert result.top_kept_companies[0][0] == "Facens"


def test_run_prefilter_audit_only_with_input(tmp_path):
    input_path = write_prefilter_csv(tmp_path / "prefilter.csv")

    result = run_prefilter_audit_only(settings=Settings(project_root=tmp_path), audit_input=str(input_path))

    assert result is not None
    assert result.markdown_path.exists()
    assert result.csv_path.exists()
