"""Resolve public reporting owners without initializing publication dependencies."""

from __future__ import annotations

from importlib import import_module as _import_module
import typing as _typing

if _typing.TYPE_CHECKING:
    from .api import (
        AdnaLocalitySummary,
        AdnaSampleRecord,
        AnimalFoundationRefreshReport,
        CountryReport,
        MultiCountryMapReport,
        PublishedReportsReport,
        SchemaError,
        generate_country_report,
        generate_multi_country_map,
        generate_published_reports,
        load_country_samples,
        refresh_animal_adna_foundation,
        slugify,
        summarize_localities,
    )

__all__ = [
    "AdnaLocalitySummary",
    "AdnaSampleRecord",
    "AnimalFoundationRefreshReport",
    "CountryReport",
    "MultiCountryMapReport",
    "PublishedReportsReport",
    "SchemaError",
    "generate_country_report",
    "generate_multi_country_map",
    "generate_published_reports",
    "load_country_samples",
    "refresh_animal_adna_foundation",
    "slugify",
    "summarize_localities",
]

_SUBMODULES = frozenset({"api", "models", "service"})


if not _typing.TYPE_CHECKING:

    def __getattr__(name: str) -> _typing.Any:
        """Load the API on demand so model imports cannot reenter analysis setup."""
        if name in globals():
            return globals()[name]
        if name in __all__:
            value = getattr(_import_module(".api", __name__), name)
        elif name in _SUBMODULES:
            value = _import_module("." + name, __name__)
        else:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        return globals().setdefault(name, value)


def __dir__() -> list[str]:
    """Discover public exports without importing their publication graph."""
    return sorted(set(globals()) | set(__all__) | _SUBMODULES)
