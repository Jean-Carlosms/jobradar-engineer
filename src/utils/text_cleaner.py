from __future__ import annotations

import re
import unicodedata


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_text(text: str) -> str:
    text = strip_accents(text).lower()
    text = re.sub(r"[^a-z0-9.+# ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def compact_key(*parts: str) -> str:
    return "|".join(normalize_text(part) for part in parts)
