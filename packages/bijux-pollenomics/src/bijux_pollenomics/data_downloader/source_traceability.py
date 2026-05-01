from __future__ import annotations

from .models import SourceAcquisitionMetadata, SourceTraceabilityRecord
from .source_identity import resolve_source_identity

__all__ = ["build_source_traceability_records"]


def build_source_traceability_records(
    *,
    selected_sources: tuple[str, ...],
    source_metadata: dict[str, SourceAcquisitionMetadata],
    source_hashes: dict[str, dict[str, str]],
) -> dict[str, SourceTraceabilityRecord]:
    """Build source trace records suitable for downstream evidence disputes."""
    records: dict[str, SourceTraceabilityRecord] = {}
    for source in selected_sources:
        identity = resolve_source_identity(source)
        metadata = source_metadata[source]
        hashes = source_hashes[source]
        records[source] = SourceTraceabilityRecord(
            source=source,
            source_identity=identity.key,
            source_version=metadata.version,
            snapshot_sha256=hashes["snapshot_sha256"],
            normalized_sha256=hashes["normalized_sha256"],
            dispute_token=_build_dispute_token(
                source=source,
                version=metadata.version,
                snapshot_sha256=hashes["snapshot_sha256"],
            ),
        )
    return records


def _build_dispute_token(*, source: str, version: str, snapshot_sha256: str) -> str:
    hash_prefix = snapshot_sha256[:12]
    return f"{source}@{version}:{hash_prefix}"
