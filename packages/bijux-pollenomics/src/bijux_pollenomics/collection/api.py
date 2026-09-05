"""Public data-collection API for tracked context-source refreshes."""

from pathlib import Path

from .contracts.summary import (
    validate_collection_summary_file,
    validate_collection_summary_payload,
)
from .collector import AVAILABLE_SOURCES, DataCollectionReport, collect_data
from .contracts.models import (
    ContextDataReport,
    DataCollectionSummary,
    SourceAcquisitionMetadata,
    SourceProvenanceRecord,
    SourceReplacementRule,
    SourceTraceabilityRecord,
)
from .catalog.hashes import SourceHashes, build_source_hashes
from .catalog.identity import SOURCE_IDENTITIES, SourceIdentity
from .catalog.provenance import build_source_provenance
from .catalog.replacement import build_source_replacement_rules
from .catalog.support import SourceSupportStatus, build_source_support_matrix
from .catalog.traceability import build_source_traceability_records
from .sources.aadr import AadrAnnoDownloadReport, download_aadr_anno_files

__all__ = [
    "SOURCE_IDENTITIES",
    "SourceIdentity",
    "AadrAnnoDownloadReport",
    "AVAILABLE_SOURCES",
    "ContextDataReport",
    "DataCollectionReport",
    "DataCollectionSummary",
    "SourceAcquisitionMetadata",
    "SourceProvenanceRecord",
    "SourceReplacementRule",
    "SourceTraceabilityRecord",
    "SourceHashes",
    "SourceSupportStatus",
    "validate_collection_summary_file",
    "validate_collection_summary_payload",
    "collect_context_data",
    "collect_data",
    "build_source_support_matrix",
    "build_source_hashes",
    "build_source_provenance",
    "build_source_replacement_rules",
    "build_source_traceability_records",
    "download_aadr_anno_files",
]


def collect_context_data(output_root: Path) -> ContextDataReport:
    """Collect the tracked context sources into the project data tree."""
    report = collect_data(
        output_root=Path(output_root),
        sources=("boundaries", "landclim", "neotoma", "sead", "raa", "svar"),
    )
    return ContextDataReport(
        generated_on=report.generated_on,
        output_root=report.output_root,
        landclim_site_count=report.landclim_site_count,
        landclim_grid_cell_count=report.landclim_grid_cell_count,
        landclim_temporal_grid_feature_count=(
            report.landclim_temporal_grid_feature_count
        ),
        neotoma_point_count=report.neotoma_point_count,
        sead_point_count=report.sead_point_count,
        raa_total_site_count=report.raa_total_site_count,
        raa_heritage_site_count=report.raa_heritage_site_count,
        svar_lake_count=report.svar_lake_count,
    )
