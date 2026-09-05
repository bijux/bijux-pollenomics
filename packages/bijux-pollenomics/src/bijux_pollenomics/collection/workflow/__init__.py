"""Collection orchestration and repository materialization workflows."""

from .materialization.reports import (
    build_data_collection_report,
    build_data_collection_summary,
    initialize_source_counts,
)
from .context_collection import collect_context_source, collect_context_source_into_dir
from .planning.requests import normalize_requested_sources
from .planning.source_registry import (
    CONTEXT_SOURCE_SPECS,
    ContextSourceSpec,
    resolve_context_collect_function,
)
from .materialization.staging import build_staging_output_dir, collect_into_staging_dir
from .materialization.summary import write_collection_summary

__all__ = [
    "CONTEXT_SOURCE_SPECS",
    "ContextSourceSpec",
    "build_data_collection_report",
    "build_data_collection_summary",
    "build_staging_output_dir",
    "collect_context_source",
    "collect_context_source_into_dir",
    "collect_into_staging_dir",
    "initialize_source_counts",
    "normalize_requested_sources",
    "resolve_context_collect_function",
    "write_collection_summary",
]
