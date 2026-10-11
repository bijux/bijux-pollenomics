"""Representative localities and source-context points for ranking tests."""

from __future__ import annotations

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord


def _locality(
    name: str,
    latitude: float,
    longitude: float,
    *,
    token: str | None = None,
    species_latin_name: str = "Homo sapiens",
    species_common_name: str = "human",
    modality: str = "metadata_only",
    sample_count: int = 2,
) -> AdnaLocalitySummary:
    locality_token = (
        token or f"{name.casefold().replace(' ', '-')}-{latitude}-{longitude}"
    )
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace="shared_locality",
            stable_token=locality_token,
            locality_text=name,
            political_entity="Sweden",
            source_anchor_tokens=("shared", str(latitude), str(longitude)),
        ),
        species_latin_name=species_latin_name,
        species_common_name=species_common_name,
        source_family="AADR" if species_latin_name == "Homo sapiens" else "ENA",
        source_releases=("v66",),
        record_modalities=(modality,),
        review_strengths=("primary_paper_pinned",),
        provenance_qualities=("release_manifest_pinned",),
        locality=name,
        coordinates=AdnaCoordinate(
            latitude=latitude,
            longitude=longitude,
            latitude_text=str(latitude),
            longitude_text=str(longitude),
            confidence="unknown",
        ),
        sample_count=sample_count,
        sample_ids=tuple(f"S{index}" for index in range(sample_count)),
        datasets=("dataset",),
        chronology=AdnaChronology(
            original_text="3000 BP",
            time_start_bp=2500,
            time_end_bp=3500,
            time_mean_bp=3000,
            dating_basis="bp_window",
        ),
        sample_namespace="shared:sample",
    )


def _point(
    record_id: str,
    latitude: float,
    longitude: float,
    *,
    layer_key: str = "neotoma-sites",
    time_start_bp: int | None = 2400,
    time_end_bp: int | None = 3600,
) -> ContextPointRecord:
    return ContextPointRecord(
        source="context",
        layer_key=layer_key,
        layer_label=layer_key,
        category="context",
        country="Sweden",
        record_id=record_id,
        name=record_id,
        latitude=latitude,
        longitude=longitude,
        geometry_type="Point",
        subtitle="",
        description="",
        source_url="https://example.test",
        record_count=1,
        popup_rows=(),
        time_start_bp=time_start_bp,
        time_end_bp=time_end_bp,
        time_mean_bp=3000 if time_start_bp is not None else None,
        time_label="3000 BP" if time_start_bp is not None else "",
    )
