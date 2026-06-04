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
    assert "python -m pytest" in commands


def test_ci_workflow_uses_windows_and_ubuntu_with_python_311():
    workflow = yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))
    matrix = workflow["jobs"]["quality"]["strategy"]["matrix"]

    assert "ubuntu-latest" in matrix["os"]
    assert "windows-latest" in matrix["os"]
    assert "3.11" in matrix["python-version"]


def test_requirements_dev_keeps_runtime_requirements_and_adds_ruff():
    requirements_dev = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")

    assert "-r requirements.txt" in requirements_dev
    assert "ruff" in requirements_dev
