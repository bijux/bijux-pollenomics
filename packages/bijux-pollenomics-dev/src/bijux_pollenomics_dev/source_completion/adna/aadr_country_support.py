"""Compare source coordinate claims with pinned country geometry without admission."""

from __future__ import annotations

from collections.abc import Sequence

from bijux_pollenomics.adna.species.homo_sapiens.materialization.models import (
    AadrCoordinateEvidence,
)
from bijux_pollenomics.collection.spatial.country_classification import (
    decide_country_attribution,
)
from bijux_pollenomics.core.geospatial.geojson import CountryBoundaryCollection


def coordinate_country_support(
    coordinates: Sequence[AadrCoordinateEvidence],
    *,
    source_country: str,
    boundaries: CountryBoundaryCollection,
    boundary_digest: str,
    boundary_version: str,
) -> dict[str, str | None]:
    """Retain missing/conflicting evidence; classify only one distinct usable pair.

    Missing panel claims can complement a usable pair. Equivalent parsed pairs
    may retain different raw tokens. Neither case supplies geography review or
    promotes the source Political Entity into a governed country assignment.
    """
    pairs = {(item.longitude, item.latitude) for item in coordinates if item.admitted}
    reason = (
        "coordinate_conflict"
        if len(pairs) > 1
        else "coordinate_unresolved"
        if any(item.status not in {"admitted", "missing"} for item in coordinates)
        else "coordinate_missing"
        if not pairs
        else None
    )
    if reason is not None:
        return {
            "spatial_status": "refused",
            "spatial_method": "coordinate_evidence",
            "spatial_country": None,
            "spatial_candidates": "",
            "spatial_reason": reason,
        }
    longitude, latitude = next(iter(pairs))
    if longitude is None or latitude is None:
        raise ValueError("Usable AADR coordinate evidence lacks its parsed pair")
    result = decide_country_attribution(
        longitude,
        latitude,
        boundaries,
        boundary_artifact_digest=boundary_digest,
        boundary_version=boundary_version,
        raw_country=source_country,
    )
    return {
        "spatial_status": result.decision_status,
        "spatial_method": result.decision_method,
        "spatial_country": result.derived_country,
        "spatial_candidates": ";".join(result.candidate_countries),
        "spatial_reason": result.ambiguity_reason or result.refusal_reason,
    }
