from __future__ import annotations

from pathlib import Path

from .models import SourceAcquisitionMetadata, SourceProvenanceRecord
from .source_identity import resolve_source_identity

__all__ = ["build_source_provenance"]


def build_source_provenance(
    *,
    selected_sources: tuple[str, ...],
    source_output_roots: dict[str, str],
    source_metadata: dict[str, SourceAcquisitionMetadata],
    source_hashes: dict[str, dict[str, str]],
) -> dict[str, SourceProvenanceRecord]:
    """Build provenance rows that survive downstream normalization and reporting."""
    provenance: dict[str, SourceProvenanceRecord] = {}
    for source in selected_sources:
        identity = resolve_source_identity(source)
        metadata = source_metadata[source]
        hashes = source_hashes[source]
        source_root = Path(source_output_roots[source])
        provenance[source] = SourceProvenanceRecord(
            source=source,
            display_name=identity.display_name,
            evidence_family=identity.evidence_family,
            version=metadata.version,
            license=metadata.license,
            retrieved_on=metadata.retrieved_on,
            acquisition_method=metadata.acquisition_method,
            snapshot_root=str(source_root),
            normalized_root=str(source_root / "normalized"),
            snapshot_sha256=hashes["snapshot_sha256"],
            normalized_sha256=hashes["normalized_sha256"],
        )
    return provenance
