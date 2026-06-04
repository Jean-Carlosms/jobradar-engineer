import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase6_documentation_files_exist():
    expected_files = [
        ROOT / "docs" / "SCREENSHOTS_GUIDE.md",
        ROOT / "PORTFOLIO_SUMMARY.md",
        ROOT / "RELEASE_NOTES.md",
        ROOT / "SECURITY.md",
        ROOT / "LICENSE",
        ROOT / "reports" / ".gitkeep",
        ROOT / "docs" / "images" / ".gitkeep",
    ]

    for path in expected_files:
        assert path.exists(), f"Missing Phase 6 file: {path}"


def test_sample_jobs_csv_has_required_columns():
    csv_path = ROOT / "examples" / "sample_jobs.csv"
    required_columns = {
        "title",
        "company",
        "location",
        "source",
        "url",
        "description_snippet",
        "match_score",
        "match_reason",
        "priority_company",
        "query_used",
        "already_sent",
        "fit_level",
        "fit_score",
        "analysis_summary",
    }

    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    assert csv_path.exists()
    assert required_columns.issubset(set(reader.fieldnames or []))
    assert len(rows) >= 5
    assert all("example.com" in row["url"] for row in rows)


def test_load_sample_data_script_exists():
    script = ROOT / "scripts" / "load_sample_data.py"

    assert script.exists()
    assert "sample_jobs.db" in script.read_text(encoding="utf-8")
    assert "jobs.db" in script.read_text(encoding="utf-8")


def test_gitignore_keeps_sensitive_files_out_and_allows_sample_db():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".env" in gitignore
    assert ".venv/" in gitignore
    assert "logs/" in gitignore
    assert "reports/*" in gitignore
    assert "!reports/.gitkeep" in gitignore
    assert "data/jobs.db" in gitignore
    assert "!data/sample_jobs.db" in gitignore
    assert "!data/.gitkeep" in gitignore


def test_readme_contains_professional_sections():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    sections = [
        "## Visao geral",
        "## Problema",
        "## Solucao",
        "## Funcionalidades",
        "## Arquitetura",
        "## Tecnologias",
        "## Como rodar",
        "## Como rodar com dados ficticios",
        "## Dashboard",
        "## Agendamento no Windows",
        "## Seguranca e compliance",
        "## Limitacoes",
        "## Roadmap",
        "## Screenshots futuros",
        "## Status do projeto",
    ]

    for section in sections:
        assert section in readme
