"""Normalize source lake names and construct stable candidate identities."""

from __future__ import annotations

import re
import unicodedata

from ..models import (
    _GENERIC_LAKE_TOKENS,
    _LAKE_NAME_TERMS,
    _WETLAND_TERMS,
)

__all__ = []


def _resolve_basin_posture(name: str, description: str) -> str:
    normalized_name = _normalize_text(name)
    normalized_description = _normalize_text(description)
    if any(
        term in normalized_name or term in normalized_description
        for term in _LAKE_NAME_TERMS
    ):
        return "lake_basin"
    if any(
        term in normalized_name or term in normalized_description
        for term in _WETLAND_TERMS
    ):
        return "wetland_basin"
    return "ambiguous_basin"


def _build_lake_token(name: str, *, latitude: float, longitude: float) -> str:
    return (
        f"sweden_lake:{_lake_name_key(name)}:{round(latitude, 6)}:{round(longitude, 6)}"
    )


def _lake_name_key(value: str) -> str:
    tokens = _tokenize_lake_name(value)
    while tokens and (tokens[0] in _GENERIC_LAKE_TOKENS or len(tokens[0]) == 1):
        tokens = tokens[1:]
    return "".join(tokens)


def _tokenize_lake_name(value: str) -> list[str]:
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    return [token for token in re.findall(r"[a-z0-9]+", normalized.casefold()) if token]


def _clean_lake_name_display(value: str) -> str:
    cleaned = re.sub(r"^\s*lake\s+", "", value, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*[A-Za-zÅÄÖåäö]\.\s+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
    return cleaned or value.strip()


def _lake_name_source_priority(layer_key: str) -> int:
    priorities = {
        "landclim-sites": 3,
        "neotoma-pollen": 2,
    }
    return priorities.get(layer_key, 0)


def _name_has_non_ascii(value: str) -> int:
    return 1 if any(ord(character) > 127 for character in value) else 0


def _normalize_text(value: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "", normalized.casefold())
