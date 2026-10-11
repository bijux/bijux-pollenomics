"""Repository materialization service for compact AADR accountability."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    reconcile_aadr_panels,
)

from ..inputs import load_aadr_release_inputs
from .models import AadrReleaseManifestIdentity
from .projection import build_aadr_source_accountability_receipt
from .publication import write_aadr_source_accountability_receipt
from .validation import validate_aadr_source_accountability_receipt


@dataclass(frozen=True, slots=True)
class AadrSourceAccountabilityMaterialization:
    """Identity and content of one published compact accountability receipt."""

    output_path: Path
    receipt: Mapping[str, object]
    byte_count: int
    sha256: str


def materialize_aadr_source_accountability(
    data_root: Path,
    version: str,
) -> AadrSourceAccountabilityMaterialization:
    """Validate one governed AADR release and publish its compact receipt."""
    inputs = load_aadr_release_inputs(data_root, version)
    root = inputs.data_root
    source_release = inputs.source_release
    reconciliation = reconcile_aadr_panels(inputs.source_tables)
    receipt = build_aadr_source_accountability_receipt(
        reconciliation,
        release_manifest=AadrReleaseManifestIdentity(
            logical_path=(inputs.logical_manifest_path),
            source_release=source_release,
            sha256=inputs.manifest_sha256,
            byte_count=len(inputs.manifest_bytes),
        ),
    )
    validate_aadr_source_accountability_receipt(receipt)

    output_path = (
        root
        / "adna"
        / "species"
        / "homo_sapiens"
        / "review"
        / f"aadr_{source_release}_source_accountability.json"
    )
    inputs.verify_unchanged()
    published = write_aadr_source_accountability_receipt(
        output_path,
        receipt,
        governed_root=root,
    )
    return AadrSourceAccountabilityMaterialization(
        output_path=output_path,
        receipt=receipt,
        byte_count=len(published),
        sha256=sha256(published).hexdigest(),
    )


__all__ = [
    "AadrSourceAccountabilityMaterialization",
    "materialize_aadr_source_accountability",
]
