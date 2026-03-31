from __future__ import annotations

from collections.abc import Iterable

from ..data_layout import AVAILABLE_SOURCES

__all__ = ["normalize_requested_sources"]


def normalize_requested_sources(sources: Iterable[str]) -> tuple[str, ...]:
    """Normalize user-selected sources and expand `all`."""
    requested = tuple(source.strip().casefold() for source in sources if source.strip())
    if not requested:
        raise ValueError("At least one data source is required")
    if "all" in requested:
        return AVAILABLE_SOURCES

    unique_sources: list[str] = []
    for source in requested:
        if source not in AVAILABLE_SOURCES:
            raise ValueError(f"Unsupported data source: {source}")
        if source not in unique_sources:
            unique_sources.append(source)
    return tuple(unique_sources)
