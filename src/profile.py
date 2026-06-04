from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ProfileConfig:
    desired_titles: list[str] = field(default_factory=list)
    desired_locations: list[str] = field(default_factory=list)
    high_weight_keywords: list[str] = field(default_factory=list)
    medium_weight_keywords: list[str] = field(default_factory=list)
    negative_keywords: list[str] = field(default_factory=list)
    priority_companies: list[str] = field(default_factory=list)
    technical_title_keywords: list[str] = field(default_factory=list)
    technical_area_keywords: list[str] = field(default_factory=list)
    strong_negative_title_keywords: list[str] = field(default_factory=list)
    weak_negative_title_keywords: list[str] = field(default_factory=list)
    location_boost_keywords: list[str] = field(default_factory=list)
    priority_company_boost: float = 10.0
    min_score_to_email: float = 50.0
    max_email_jobs: int = 10


def load_profile(path: str | Path) -> ProfileConfig:
    profile_path = Path(path)
    with profile_path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Profile file must contain a YAML mapping: {profile_path}")
    return _profile_from_mapping(raw)


def _profile_from_mapping(raw: dict[str, Any]) -> ProfileConfig:
    return ProfileConfig(
        desired_titles=_as_string_list(raw.get("desired_titles")),
        desired_locations=_as_string_list(raw.get("desired_locations")),
        high_weight_keywords=_as_string_list(raw.get("high_weight_keywords")),
        medium_weight_keywords=_as_string_list(raw.get("medium_weight_keywords")),
        negative_keywords=_as_string_list(raw.get("negative_keywords")),
        priority_companies=_as_string_list(raw.get("priority_companies")),
        technical_title_keywords=_as_string_list(raw.get("technical_title_keywords")),
        technical_area_keywords=_as_string_list(raw.get("technical_area_keywords")),
        strong_negative_title_keywords=_as_string_list(raw.get("strong_negative_title_keywords")),
        weak_negative_title_keywords=_as_string_list(raw.get("weak_negative_title_keywords")),
        location_boost_keywords=_as_string_list(raw.get("location_boost_keywords")),
        priority_company_boost=float(raw.get("priority_company_boost", 10)),
        min_score_to_email=float(raw.get("min_score_to_email", 50)),
        max_email_jobs=int(raw.get("max_email_jobs", 10)),
    )


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("Profile list fields must be YAML lists.")
    return [str(item).strip() for item in value if str(item).strip()]
