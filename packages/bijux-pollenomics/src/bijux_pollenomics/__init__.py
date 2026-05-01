"""Data collection, reporting, and mapping tools for bijux-pollenomics."""

from importlib import metadata

from .foundation import (
    CompatibilityAliasContract,
    ProductScope,
    RuntimeSurfaceContract,
    SurfaceMap,
    build_product_scope,
    build_surface_map,
    compatibility_alias_contract,
    runtime_surface_contract,
)

from .data_downloader.api import (
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
    "ProductScope",
    "RuntimeSurfaceContract",
    "SurfaceMap",
    "ContextDataReport",
    "CountryReport",
    "DataCollectionReport",
    "MultiCountryMapReport",
    "PublishedReportsReport",
    "__version__",
    "collect_data",
    "collect_context_data",
    "build_product_scope",
    "build_surface_map",
    "generate_country_report",
    "generate_multi_country_map",
    "generate_published_reports",
    "runtime_surface_contract",
    "compatibility_alias_contract",
]
