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

    assert "v1.3.0 - Visual polish e demo para portfolio" in release_notes
    assert "Status atual: `v1.3.0 - Visual polish e demo para portfolio`" in readme
    assert "Publishing Checklist v1.3.0" in checklist
    assert "JobRadar Engineer v1.3.0" in portfolio


def test_publication_docs_warn_about_runtime_paths():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs" / "PUBLISHING_CHECKLIST.md").read_text(encoding="utf-8")

    for protected_path in [".env", ".venv/", "data/jobs.db", "logs/", "reports/"]:
        assert protected_path in readme
        assert protected_path in checklist
