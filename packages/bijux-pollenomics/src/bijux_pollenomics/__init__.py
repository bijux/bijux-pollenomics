"""Data collection, reporting, and mapping tools for bijux-pollenomics."""

from importlib import metadata

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
