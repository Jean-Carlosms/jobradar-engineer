from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_GITIGNORE_PATTERNS = [
    ".env",
    ".venv/",
    "logs/",
    "data/jobs.db",
]

REQUIRED_FILES = [
    "examples/sample_jobs.csv",
    "data/sample_jobs.db",
    "README.md",
    "SECURITY.md",
    "LICENSE",
    "PORTFOLIO_SUMMARY.md",
    "RELEASE_NOTES.md",
]

LOCAL_SENSITIVE_PATHS = [
    ".env",
    "data/jobs.db",
    "logs",
    ".venv",
]


def main() -> int:
    print("JobRadar Engineer - publication safety check")
    print("=" * 48)

    errors: list[str] = []
    warnings: list[str] = []

    gitignore = _read_gitignore(errors)
    if gitignore is not None:
        for pattern in EXPECTED_GITIGNORE_PATTERNS:
            if pattern not in gitignore:
                errors.append(f".gitignore missing expected protection: {pattern}")

    for relative_path in REQUIRED_FILES:
        if not (ROOT / relative_path).exists():
            errors.append(f"Required publication file is missing: {relative_path}")

    for relative_path in LOCAL_SENSITIVE_PATHS:
        path = ROOT / relative_path
        if path.exists():
            warnings.append(f"Local runtime path exists and must not be versioned: {relative_path}")

    _print_messages("Warnings", warnings)
    _print_messages("Errors", errors)

    if errors:
        print("Result: NOT SAFE for publication yet.")
        return 1

    print("Result: publication safety checks passed.")
    return 0


def _read_gitignore(errors: list[str]) -> str | None:
    gitignore_path = ROOT / ".gitignore"
    if not gitignore_path.exists():
        errors.append(".gitignore is missing")
        return None
    return gitignore_path.read_text(encoding="utf-8")


def _print_messages(title: str, messages: list[str]) -> None:
    if not messages:
        print(f"{title}: none")
        return
    print(f"{title}:")
    for message in messages:
        print(f"- {message}")


if __name__ == "__main__":
    raise SystemExit(main())
