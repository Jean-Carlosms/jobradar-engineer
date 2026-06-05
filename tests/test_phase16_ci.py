from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_workflow_exists():
    assert CI_WORKFLOW.exists(), "Missing GitHub Actions CI workflow."


def test_ci_workflow_runs_required_quality_commands():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    jobs = workflow.get("jobs", {})
    assert "quality" in jobs

    steps = jobs["quality"]["steps"]
    commands = "\n".join(str(step.get("run", "")) for step in steps)

    assert "pip install -r requirements.txt" in commands
    assert "pip install -r requirements-dev.txt" in commands
    assert "python -m ruff check ." in commands
    assert "python scripts/check_publication_safety.py" in commands
    assert "python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=85" in commands


def test_ci_workflow_uses_windows_and_ubuntu_with_python_311():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    matrix = workflow["jobs"]["quality"]["strategy"]["matrix"]

    assert "ubuntu-latest" in matrix["os"]
    assert "windows-latest" in matrix["os"]
    assert "3.11" in matrix["python-version"]


def test_requirements_dev_keeps_runtime_requirements_and_adds_quality_tools():
    requirements_dev = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")

    assert "-r requirements.txt" in requirements_dev
    assert "ruff" in requirements_dev
    assert "pytest-cov" in requirements_dev


def test_coverage_outputs_are_not_versioned_and_documented():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs" / "PUBLISHING_CHECKLIST.md").read_text(encoding="utf-8")

    assert "htmlcov/" in gitignore
    assert ".coverage" in gitignore
    assert "coverage.xml" in gitignore
    assert "Cobertura de testes" in readme
    assert "limite minimo atual no CI e `85%`" in readme
    assert "cobertura local em torno de `91%`" in readme
    assert "--cov-fail-under=85" in checklist


def test_active_coverage_docs_do_not_reference_old_fail_under():
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    checklist = (ROOT / "docs" / "PUBLISHING_CHECKLIST.md").read_text(encoding="utf-8")
    portfolio = (ROOT / "PORTFOLIO_SUMMARY.md").read_text(encoding="utf-8")

    active_docs = "\n".join([workflow, readme, checklist, portfolio])

    old_limit = "--cov-fail-under=" + "80"
    assert old_limit not in active_docs
