"""Data collection, reporting, and mapping tools for bijux-pollenomics."""

from __future__ import annotations

from importlib import import_module as _import_module
from importlib import metadata
import typing as _typing

if _typing.TYPE_CHECKING:
    from .architecture import (
        CompatibilityAliasContract,
        OwnershipMapEntry,
        ProductScope,
        RuntimeSurfaceContract,
        SurfaceMap,
        build_ownership_map,
        build_product_scope,
        build_surface_map,
        compatibility_alias_contract,
        runtime_surface_contract,
    )
    from .collection.api import (
        ContextDataReport,
        DataCollectionReport,
        collect_context_data,
        collect_data,
    )
    from .reporting.api import (
        CountryReport,
        MultiCountryMapReport,
        PublishedReportsReport,
        generate_country_report,
        generate_multi_country_map,
        generate_published_reports,
    )

try:
    __version__ = metadata.version("bijux-pollenomics")
except metadata.PackageNotFoundError:
    __version__ = "0.1.5"

__all__ = [
    "CompatibilityAliasContract",
    "ContextDataReport",
    "CountryReport",
    "DataCollectionReport",
    "MultiCountryMapReport",
    "OwnershipMapEntry",
    "ProductScope",
    "PublishedReportsReport",
    "RuntimeSurfaceContract",
    "SurfaceMap",
    "__version__",
    "build_ownership_map",
    "build_product_scope",
    "build_surface_map",
    "collect_context_data",
    "collect_data",
    "compatibility_alias_contract",
    "generate_country_report",
    "generate_multi_country_map",
    "generate_published_reports",
    "runtime_surface_contract",
]

_EXPORT_MODULES = {
    "CompatibilityAliasContract": ".architecture",
    "OwnershipMapEntry": ".architecture",
    "ProductScope": ".architecture",
    "RuntimeSurfaceContract": ".architecture",
    "SurfaceMap": ".architecture",
    "build_ownership_map": ".architecture",
    "build_product_scope": ".architecture",
    "build_surface_map": ".architecture",
    "compatibility_alias_contract": ".architecture",
    "runtime_surface_contract": ".architecture",
    "ContextDataReport": ".collection.api",
    "DataCollectionReport": ".collection.api",
    "collect_context_data": ".collection.api",
    "collect_data": ".collection.api",
    "CountryReport": ".reporting.api",
    "MultiCountryMapReport": ".reporting.api",
    "PublishedReportsReport": ".reporting.api",
    "generate_country_report": ".reporting.api",
    "generate_multi_country_map": ".reporting.api",
    "generate_published_reports": ".reporting.api",
}
_SUBMODULES = frozenset(
    {
        "adna",
        "analysis",
        "architecture",
        "collection",
        "config",
        "core",
        "evidence",
        "governance",
        "publication_policy",
        "reporting",
    }
)


if not _typing.TYPE_CHECKING:

    def __getattr__(name: str) -> _typing.Any:
        """Resolve the declared owner only when its public API is requested."""
        if name in globals():
            return globals()[name]
        owner = _EXPORT_MODULES.get(name)
        if owner is not None:
            value = getattr(_import_module(owner, __name__), name)
        elif name in _SUBMODULES:
            value = _import_module("." + name, __name__)
        else:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        return globals().setdefault(name, value)


def __dir__() -> list[str]:
    """Discover public exports and child modules without importing their owners."""
    return sorted(set(globals()) | set(__all__) | _SUBMODULES)
