from __future__ import annotations

from collections.abc import Iterable


def normalize_requested_countries(countries: Iterable[str]) -> tuple[str, ...]:
    """Normalize user-selected countries while preserving the first occurrence order."""
    return tuple(
        dict.fromkeys(country.strip() for country in countries if country.strip())
    )


__all__ = ["normalize_requested_countries"]
