from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import cast

__all__ = [
    "validate_collection_summary_file",
    "validate_collection_summary_payload",
]

_REQUIRED_TOP_LEVEL_KEYS = (
    "generated_on",
    "output_root",
    "version",
    "collected_sources",
    "source_output_roots",
    "source_metadata",
    "source_hashes",
    "source_provenance",
    "source_replacement_rules",
    "source_traceability",
    "summary_path",
)


def validate_collection_summary_payload(payload: Mapping[str, object]) -> None:
    """Validate one collection-summary payload independent of collection runtime."""
    for key in _REQUIRED_TOP_LEVEL_KEYS:
        if key not in payload:
            raise ValueError(f"collection summary missing required field: {key}")

    collected_sources = payload["collected_sources"]
    if not isinstance(collected_sources, list):
        raise ValueError("collection summary field `collected_sources` must be a list")
    for source in collected_sources:
        if not isinstance(source, str) or not source:
            raise ValueError("collection summary contains invalid source key")

    _validate_mapping(payload, "source_output_roots")
    _validate_mapping(payload, "source_metadata")
    _validate_mapping(payload, "source_hashes")
    _validate_mapping(payload, "source_provenance")
    _validate_mapping(payload, "source_replacement_rules")
    _validate_mapping(payload, "source_traceability")

    source_output_roots = cast(Mapping[str, object], payload["source_output_roots"])
    source_metadata = cast(Mapping[str, object], payload["source_metadata"])
    source_hashes = cast(Mapping[str, object], payload["source_hashes"])
    source_provenance = cast(Mapping[str, object], payload["source_provenance"])
    source_replacement_rules = cast(
        Mapping[str, object], payload["source_replacement_rules"]
    )
    source_traceability = cast(Mapping[str, object], payload["source_traceability"])

    for source in collected_sources:
        if source not in source_output_roots:
            raise ValueError(
                f"collection summary missing output root for source: {source}"
            )
        if source not in source_metadata:
            raise ValueError(
                f"collection summary missing metadata for source: {source}"
            )
        if source not in source_hashes:
            raise ValueError(f"collection summary missing hashes for source: {source}")
        if source not in source_provenance:
            raise ValueError(
                f"collection summary missing provenance record for source: {source}"
            )
        if source not in source_replacement_rules:
            raise ValueError(
                f"collection summary missing replacement rules for source: {source}"
            )
        if source not in source_traceability:
            raise ValueError(
                f"collection summary missing traceability record for source: {source}"
            )


def validate_collection_summary_file(summary_path: Path) -> dict[str, object]:
    """Load and validate one collection-summary file."""
    payload = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("collection summary payload must be a JSON object")
    validate_collection_summary_payload(payload)
    return dict(payload)


def _validate_mapping(payload: Mapping[str, object], key: str) -> None:
    value = payload[key]
    if not isinstance(value, Mapping):
        raise ValueError(f"collection summary field `{key}` must be a JSON object")
