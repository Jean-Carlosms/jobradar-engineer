import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


PHASE7_DOCS = [
    ROOT / "docs" / "PUBLISHING_CHECKLIST.md",
    ROOT / "docs" / "GITHUB_DESCRIPTION.md",
    ROOT / "docs" / "LINKEDIN_POST.md",
    ROOT / "docs" / "INTERVIEW_PITCH.md",
]


def test_phase7_publication_docs_exist():
    for path in PHASE7_DOCS:
        assert path.exists(), f"Missing publication doc: {path}"


def test_publication_safety_script_exists():
    assert (ROOT / "scripts" / "check_publication_safety.py").exists()


def test_publication_safety_script_passes():
    result = subprocess.run(
        [sys.executable, "scripts/check_publication_safety.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "publication safety checks passed" in result.stdout


def test_phase7_docs_do_not_contain_real_secret_patterns():
    forbidden_patterns = [
        re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
        re.compile(r"token\s*[:=]\s*\S+", re.IGNORECASE),
        re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE),
        re.compile(r"senha\s*[:=]\s*\S+", re.IGNORECASE),
        re.compile(r"api[_-]?key\s*[:=]\s*\S+", re.IGNORECASE),
    ]

    for path in PHASE7_DOCS + [ROOT / "README.md", ROOT / "SECURITY.md"]:
        content = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            assert not pattern.search(content), f"Potential secret-like pattern in {path}: {pattern.pattern}"


def test_release_docs_reference_v1():
    release_notes = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs" / "PUBLISHING_CHECKLIST.md").read_text(encoding="utf-8")
    portfolio = (ROOT / "PORTFOLIO_SUMMARY.md").read_text(encoding="utf-8")

    assert "v3.0.0 - Indices de performance e saude do banco" in release_notes
    assert "Status atual: `v3.0.0 - Indices de performance e saude do banco`" in readme
    assert "198 testes" in readme
    assert "cobertura local em torno de `91%`" in readme
    assert "limite minimo de cobertura `85%`" in readme
    assert "Publishing Checklist v3.0.0" in checklist
    assert "JobRadar Engineer v3.0.0" in portfolio
    assert "16 indices" in portfolio


def test_schema_migration_docs_are_publication_ready():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs" / "PUBLISHING_CHECKLIST.md").read_text(encoding="utf-8")
    production_setup = (ROOT / "docs" / "production_setup.md").read_text(encoding="utf-8")

    assert "## Schema versionado" in readme
    assert "python -m src.main --schema-status" in readme
    assert "python -m src.main --migrate-schema" in readme
    assert "python -m src.main --db-health" in readme
    assert "python -m src.main --export-db-health" in readme
    assert "python -m src.main --schema-status" in checklist
    assert "python -m src.main --db-health" in checklist
    assert "git check-ignore -v .env data/jobs.db logs reports runs backups htmlcov .coverage .venv" in checklist
    assert "before schema migration" in production_setup
    assert "python -m src.main --export-db-health" in production_setup
    assert "sem Alembic" in production_setup


def test_release_publication_materials_are_v3_ready():
    linkedin = (ROOT / "docs" / "LINKEDIN_POST.md").read_text(encoding="utf-8")
    pitch = (ROOT / "docs" / "INTERVIEW_PITCH.md").read_text(encoding="utf-8")
    demo = (ROOT / "docs" / "DEMO_SCRIPT.md").read_text(encoding="utf-8")

    assert "versao v3.0.0" in linkedin
    assert "dados ficticios" in linkedin
    assert "nao faz login" in linkedin
    assert "nao automatiza candidatura" in linkedin
    assert "nao tenta contornar captcha" in linkedin
    assert "Python, SQLite, SQLAlchemy, Streamlit, pytest, Ruff, GitHub Actions, YAML" in linkedin

    assert "JobRadar Engineer v3.0.0" in pitch
    assert "198 testes" in pitch
    assert "schema versionado" in pitch
    assert "backup/restauracao protegida" in pitch

    assert "Historico de Execucoes" in demo
    assert "Alertas Operacionais" in demo
    assert "Backups e Banco" in demo
    assert "Saude do Banco" in demo


def test_publication_safety_checks_coverage_artifacts():
    safety_script = (ROOT / "scripts" / "check_publication_safety.py").read_text(encoding="utf-8")

    assert "htmlcov/" in safety_script
    assert ".coverage" in safety_script
    assert "coverage.xml" in safety_script


def test_publication_docs_warn_about_runtime_paths():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs" / "PUBLISHING_CHECKLIST.md").read_text(encoding="utf-8")

    for protected_path in [".env", ".venv/", "data/jobs.db", "logs/", "reports/", "runs/", "backups/"]:
        assert protected_path in readme
        assert protected_path in checklist
