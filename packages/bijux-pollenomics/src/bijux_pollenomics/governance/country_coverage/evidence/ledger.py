"""Cross-source coverage evidence assembly."""

from __future__ import annotations

from collections.abc import Mapping

from bijux_pollenomics.core.geospatial.geojson import CountryBoundaryCollection

from .landclim import add_landclim_evidence
from .neotoma import add_neotoma_evidence
from .partitions import EvidenceMap
from .sead import add_sead_evidence
from .supplementary import (
    add_aadr_evidence,
    add_animal_adna_evidence,
    add_boundary_evidence,
)


def _coverage_evidence(
    documents: Mapping[str, Mapping[str, object]],
    *,
    input_bytes: Mapping[str, bytes],
    boundary_digest: str,
    boundary_version: str,
    boundary_collections: CountryBoundaryCollection,
    boundary_counts: Mapping[str, int],
    sead_claim_document: Mapping[str, object],
) -> dict[tuple[str, str, str], dict[str, int | None]]:
    evidence: EvidenceMap = {}
    add_landclim_evidence(evidence, documents)
    add_neotoma_evidence(evidence, documents)
    add_sead_evidence(
        evidence,
        documents,
        input_bytes=input_bytes,
        boundary_digest=boundary_digest,
        boundary_version=boundary_version,
        boundary_collections=boundary_collections,
        boundary_counts=boundary_counts,
        claim_document=sead_claim_document,
    )
    add_boundary_evidence(evidence, boundary_counts)
    add_aadr_evidence(evidence, documents)
    add_animal_adna_evidence(evidence, documents)
    return evidence
