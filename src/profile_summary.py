from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ProfileSummary:
    professional_summary: str = ""
    core_skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    interest_areas: list[str] = field(default_factory=list)
    target_roles: list[str] = field(default_factory=list)
    target_companies: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    current_gaps: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    location_preferences: list[str] = field(default_factory=list)


def load_profile_summary(path: str | Path) -> ProfileSummary:
    profile_path = Path(path)
    with profile_path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Profile summary must contain a YAML mapping: {profile_path}")

    return ProfileSummary(
        professional_summary=str(raw.get("professional_summary", "")).strip(),
        core_skills=_as_string_list(raw.get("core_skills")),
        tools=_as_string_list(raw.get("tools")),
        interest_areas=_as_string_list(raw.get("interest_areas")),
        target_roles=_as_string_list(raw.get("target_roles")),
        target_companies=_as_string_list(raw.get("target_companies")),
        strengths=_as_string_list(raw.get("strengths")),
        current_gaps=_as_string_list(raw.get("current_gaps")),
        languages=_as_string_list(raw.get("languages")),
        location_preferences=_as_string_list(raw.get("location_preferences")),
    )


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Profile summary list fields must be YAML lists.")
    return [str(item).strip() for item in value if str(item).strip()]
