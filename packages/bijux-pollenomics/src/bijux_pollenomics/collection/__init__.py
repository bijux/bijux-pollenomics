"""Public source-collection API exports for bijux-pollenomics."""

from __future__ import annotations

from importlib import import_module as _import_module
import typing as _typing

if _typing.TYPE_CHECKING:
    from .api import (
        AVAILABLE_SOURCES,
        SOURCE_IDENTITIES,
        AadrAnnoDownloadReport,
        ContextDataReport,
        DataCollectionReport,
        DataCollectionSummary,
        SourceAcquisitionMetadata,
        SourceHashes,
        SourceIdentity,
        SourceProvenanceRecord,
        SourceReplacementRule,
        SourceSupportStatus,
        SourceTraceabilityRecord,
        build_source_hashes,
        build_source_provenance,
        build_source_replacement_rules,
        build_source_support_matrix,
        build_source_traceability_records,
        collect_context_data,
        collect_data,
        download_aadr_anno_files,
        validate_collection_summary_file,
        validate_collection_summary_payload,
    )

__all__ = [
    "AVAILABLE_SOURCES",
    "SOURCE_IDENTITIES",
    "AadrAnnoDownloadReport",
    "ContextDataReport",
    "DataCollectionReport",
    "DataCollectionSummary",
    "SourceAcquisitionMetadata",
    "SourceHashes",
    "SourceIdentity",
    "SourceProvenanceRecord",
    "SourceReplacementRule",
    "SourceSupportStatus",
    "SourceTraceabilityRecord",
    "build_source_hashes",
    "build_source_provenance",
    "build_source_replacement_rules",
    "build_source_support_matrix",
    "build_source_traceability_records",
    "collect_context_data",
    "collect_data",
    "download_aadr_anno_files",
    "validate_collection_summary_file",
    "validate_collection_summary_payload",
]

_EXPORT_MODULES = {
    "AVAILABLE_SOURCES": ".api",
    "SOURCE_IDENTITIES": ".api",
    "AadrAnnoDownloadReport": ".api",
    "ContextDataReport": ".api",
    "DataCollectionReport": ".api",
    "DataCollectionSummary": ".api",
    "SourceAcquisitionMetadata": ".api",
    "SourceHashes": ".api",
    "SourceIdentity": ".api",
    "SourceProvenanceRecord": ".api",
    "SourceReplacementRule": ".api",
    "SourceSupportStatus": ".api",
    "SourceTraceabilityRecord": ".api",
    "build_source_hashes": ".api",
    "build_source_provenance": ".api",
    "build_source_replacement_rules": ".api",
    "build_source_support_matrix": ".api",
    "build_source_traceability_records": ".api",
    "collect_context_data": ".api",
    "collect_data": ".api",
    "download_aadr_anno_files": ".api",
    "validate_collection_summary_file": ".api",
    "validate_collection_summary_payload": ".api",
}
_SUBMODULES = frozenset(
    {
        "api",
        "catalog",
        "contracts",
        "exports",
        "intake",
        "sources",
        "spatial",
        "workflow",
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
