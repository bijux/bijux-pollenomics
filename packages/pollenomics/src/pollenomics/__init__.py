"""Compatibility alias module for bijux-pollenomics."""

from importlib import metadata

from bijux_pollenomics import (
    ContextDataReport,
    CountryReport,
    DataCollectionReport,
    MultiCountryMapReport,
    PublishedReportsReport,
    collect_context_data,
    collect_data,
    generate_country_report,
    generate_multi_country_map,
    generate_published_reports,
)

try:
    __version__ = metadata.version("pollenomics")
except metadata.PackageNotFoundError:
    __version__ = "0.1.2"

__all__ = [
    "ContextDataReport",
    "CountryReport",
    "DataCollectionReport",
    "MultiCountryMapReport",
    "PublishedReportsReport",
    "__version__",
    "collect_data",
    "collect_context_data",
    "generate_country_report",
    "generate_multi_country_map",
    "generate_published_reports",
]
