"""Shared path-safe slug normalization helpers."""

from __future__ import annotations

import unicodedata


def normalize_slug(value: str, *, fallback: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    parts: list[str] = []
    previous_dash = False
    for char in normalized:
        if char.isalnum() or char == "_":
            parts.append(char.lower())
            previous_dash = False
            continue
        if not previous_dash:
            parts.append("-")
            previous_dash = True
    slug = "".join(parts).strip("-").strip(".")
    return slug or fallback
