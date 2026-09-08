"""Shared ancient-DNA locality builder for candidate tests."""

from __future__ import annotations

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)


def locality(
    sample_count: int,
    *,
    species_latin_name: str = "Homo sapiens",
    species_common_name: str = "human",
    modality: str = "metadata_only",
    review_strength: str = "curated_release_metadata",
    provenance_quality: str = "release_manifest_pinned",
    locality_token: str = "shared:sweden:lake-example",
    chronology: tuple[int | None, int | None, int | None] = (3500, 2500, 3000),
) -> AdnaLocalitySummary:
    """Build a locality with explicit evidence and chronology posture."""
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace="shared_locality",
            stable_token=locality_token,
            locality_text="Lake Example",
            political_entity="Sweden",
            source_anchor_tokens=("AADR", "59.0", "18.0"),
        ),
        species_latin_name=species_latin_name,
        species_common_name=species_common_name,
        source_family="AADR" if species_latin_name == "Homo sapiens" else "ENA",
        source_releases=("v66",),
        record_modalities=(modality,),
        review_strengths=(review_strength,),
        provenance_qualities=(provenance_quality,),
        locality="Lake Example",
        coordinates=AdnaCoordinate(
            latitude=59.0,
            longitude=18.0,
            latitude_text="59.0",
            longitude_text="18.0",
            confidence="unknown",
        ),
        sample_count=sample_count,
        sample_ids=tuple(f"I{index}" for index in range(sample_count)),
        datasets=("dataset",),
        chronology=AdnaChronology(
            original_text="3000 BP" if chronology[2] is not None else "",
            time_start_bp=chronology[0],
            time_end_bp=chronology[1],
            time_mean_bp=chronology[2],
            dating_basis="bp_window" if chronology[0] is not None else "unknown",
        ),
        sample_namespace="shared:sample",
    )
