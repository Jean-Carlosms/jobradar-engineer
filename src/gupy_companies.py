from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class GupyCompany:
    name: str
    slug: str
    base_url: str
    category: str = "uncategorized"
    priority: bool = False
    status: str = "unknown"
    notes: str = ""


def load_gupy_companies(path: str | Path) -> list[GupyCompany]:
    companies_path = Path(path)
    with companies_path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"Gupy companies file must contain a YAML mapping: {companies_path}")

    companies = _collect_company_mappings(raw)

    return [_company_from_mapping(item) for item in companies]


def _collect_company_mappings(raw: dict) -> list[dict]:
    companies = raw.get("companies", [])
    categories = raw.get("categories", {})
    mappings: list[dict] = []

    if companies:
        if not isinstance(companies, list):
            raise ValueError("`companies` must be a YAML list.")
        mappings.extend(companies)

    if categories:
        if not isinstance(categories, dict):
            raise ValueError("`categories` must be a YAML mapping.")
        for category, items in categories.items():
            if not isinstance(items, list):
                raise ValueError("Each Gupy category must contain a YAML list.")
            for item in items:
                if not isinstance(item, dict):
                    raise ValueError("Each Gupy company must be a YAML mapping.")
                with_category = {"category": str(category), **item}
                mappings.append(with_category)

    if not mappings:
        raise ValueError("Gupy companies file must define `companies` or `categories`.")

    return mappings


def _company_from_mapping(raw: Any) -> GupyCompany:
    if not isinstance(raw, dict):
        raise ValueError("Each Gupy company must be a YAML mapping.")

    name = str(raw.get("name", "")).strip()
    slug = str(raw.get("slug", "")).strip()
    base_url = str(raw.get("base_url", "")).strip().rstrip("/")

    category = str(raw.get("category", "uncategorized")).strip() or "uncategorized"
    priority = _bool_value(raw.get("priority", False))
    status = str(raw.get("status", "unknown")).strip() or "unknown"
    notes = str(raw.get("notes", "")).strip()

    if not name or not slug or not base_url:
        raise ValueError("Gupy companies require name, slug and base_url.")

    return GupyCompany(
        name=name,
        slug=slug,
        base_url=base_url,
        category=category,
        priority=priority,
        status=status,
        notes=notes,
    )


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "sim", "y"}
