from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_phase5_scripts_exist():
    expected_scripts = [
        ROOT / "scripts" / "run_jobradar_daily.bat",
        ROOT / "scripts" / "run_jobradar_dry_run.bat",
        ROOT / "scripts" / "open_dashboard.bat",
    ]

    for script in expected_scripts:
        assert script.exists(), f"Missing script: {script}"


def test_phase5_docs_exist():
    expected_docs = [
        ROOT / "docs" / "windows_task_scheduler.md",
        ROOT / "docs" / "production_setup.md",
    ]

    for doc in expected_docs:
        assert doc.exists(), f"Missing doc: {doc}"


def test_gitignore_excludes_sensitive_runtime_files():
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


def test_daily_script_uses_expected_production_command():
    script = (ROOT / "scripts" / "run_jobradar_daily.bat").read_text(encoding="utf-8")

    assert "python -m src.main" in script
    assert "--source all" in script
    assert "--analyze" in script
    assert "--send-email" in script
    assert "--run-report" in script
    assert "--analysis-min-score 50" in script
    assert "logs\\jobradar_daily_" in script
