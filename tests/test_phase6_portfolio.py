import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SCREENSHOT_IMAGES = [
    "dashboard-overview.png",
    "job-funnel.png",
    "top-jobs.png",
    "job-profile-analysis.png",
    "human-review.png",
    "prefilter-audit.png",
    "feedback-insights.png",
]


def test_phase6_documentation_files_exist():
    expected_files = [
        ROOT / "docs" / "SCREENSHOTS_GUIDE.md",
        ROOT / "docs" / "DEMO_SCRIPT.md",
        ROOT / "docs" / "COVERAGE_REVIEW.md",
        ROOT / "PORTFOLIO_SUMMARY.md",
        ROOT / "RELEASE_NOTES.md",
        ROOT / "SECURITY.md",
        ROOT / "LICENSE",
        ROOT / "reports" / ".gitkeep",
        ROOT / "backups" / ".gitkeep",
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
    assert "runs/*" in gitignore
    assert "!runs/.gitkeep" in gitignore
    assert "backups/*" in gitignore
    assert "!backups/.gitkeep" in gitignore
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


def test_visual_demo_docs_reference_expected_screenshots():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    screenshots_guide = (ROOT / "docs" / "SCREENSHOTS_GUIDE.md").read_text(encoding="utf-8")
    demo_script = (ROOT / "docs" / "DEMO_SCRIPT.md").read_text(encoding="utf-8")

    assert "## Demonstração visual" in readme
    assert "Dados ficticios" in screenshots_guide
    assert "1366x768" in screenshots_guide
    assert "1440x900" in screenshots_guide
    assert "python scripts\\check_publication_safety.py" in screenshots_guide
    assert "3 minutos" in demo_script
    assert "Roteiro com screenshots" in demo_script
    for image_name in EXPECTED_SCREENSHOT_IMAGES:
        assert image_name in readme
        assert image_name in screenshots_guide
        assert image_name in demo_script


def test_screenshot_placeholders_exist_and_describe_safe_capture():
    for image_name in EXPECTED_SCREENSHOT_IMAGES:
        placeholder = ROOT / "docs" / "images" / image_name.replace(".png", ".placeholder.txt")

        assert placeholder.exists(), f"Missing placeholder: {placeholder}"
        content = placeholder.read_text(encoding="utf-8")
        assert "Dados ficticios" in content
        assert f"docs/images/{image_name}" in content
        assert "Aba do dashboard" in content


def test_coverage_review_documents_experimental_sources():
    coverage_review = (ROOT / "docs" / "COVERAGE_REVIEW.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "SearchEngineSource" in coverage_review
    assert "fallback experimental" in coverage_review
    assert "scheduler.py" in coverage_review
    assert "GlassdoorSource" in coverage_review
    assert "GupyPublicSource" in coverage_review
    assert "fallback experimental" in readme
