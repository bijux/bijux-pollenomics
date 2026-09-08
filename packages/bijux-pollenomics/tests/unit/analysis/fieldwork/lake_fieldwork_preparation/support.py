"""Typed canonical evidence fixtures for fieldwork preparation tests."""

from __future__ import annotations

from bijux_pollenomics.analysis import (
    LakeEvidenceBandScore,
    LakeEvidenceCandidate,
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
    LakeEvidenceSourceAnchor,
)


def _source_point(
    *,
    source_record: str,
    source_name: str,
    source_layer_key: str,
    latitude: float,
    longitude: float,
    source_url: str = "https://example.test/source",
) -> LakeEvidenceSourceAnchor:
    return LakeEvidenceSourceAnchor(
        source_record=source_record,
        source_name=source_name,
        source_layer_key=source_layer_key,
        latitude=latitude,
        longitude=longitude,
        source_url=source_url,
    )


def _candidate(
    *,
    lake_name: str,
    lake_label: str,
    latitude: float,
    longitude: float,
    ambiguity_flags: tuple[str, ...],
    direct_pollen_source_count: int,
    lake_sampling_posture: str = "sampling_lake_candidate",
    lake_sampling_fit: float = 1.0,
    lake_area_km2: float | None = 1.6,
) -> LakeEvidenceCandidate:
    token = lake_name.casefold().replace(" ", "-")
    return LakeEvidenceCandidate(
        lake_name=lake_name,
        lake_label=lake_label,
        lake_token=token,
        name_key=lake_name.casefold().replace(" ", ""),
        latitude=latitude,
        longitude=longitude,
        basin_posture="lake_basin",
        direct_pollen_source_count=direct_pollen_source_count,
        direct_pollen_record_count=direct_pollen_source_count,
        time_aware_direct_pollen_records=direct_pollen_source_count,
        pollen_sources=("landclim-sites", "neotoma-pollen")[
            :direct_pollen_source_count
        ],
        supporting_pollen_names=(lake_name,),
        supporting_source_records=("landclim-sites:l1", "neotoma-pollen:n1")[
            :direct_pollen_source_count
        ],
        supporting_source_points=(
            _source_point(
                source_record="landclim-sites:l1",
                source_name=lake_name,
                source_layer_key="landclim-sites",
                latitude=latitude,
                longitude=longitude,
            ),
        ),
        representative_source_record="landclim-sites:l1",
        representative_source_layer_key="landclim-sites",
        representative_source_name=lake_name,
        representative_source_url="https://example.test/source",
        coordinate_resolution_method="shared_source_coordinate",
        duplicate_name_count=2 if "duplicate_sweden_name" in ambiguity_flags else 1,
        coordinate_spread_km=(
            0.9 if "source_coordinate_spread" in ambiguity_flags else 0.0
        ),
        ambiguity_flags=ambiguity_flags,
        ambiguity_note="identity review required" if ambiguity_flags else "",
        direct_pollen_signal=0.8,
        lake_registry_id=f"test-{token}",
        lake_water_identity=f"water-{token}",
        lake_name_status="official_register_name",
        lake_area_km2=lake_area_km2,
        lake_sampling_posture=lake_sampling_posture,
        lake_sampling_fit=lake_sampling_fit,
    )


def _band(
    radius_km: int,
    *,
    band_rank: int,
    total_score: float,
    sead_site_count: int,
    evidence_family_count: int,
    human_adna_locality_count: int,
    domesticated_animal_locality_count: int = 0,
) -> LakeEvidenceBandScore:
    return LakeEvidenceBandScore(
        radius_km=radius_km,
        band_rank=band_rank,
        total_score=total_score,
        nearby_pollen_lake_count=2,
        time_aware_pollen_site_count=2,
        human_overlap_pollen_site_count=1,
        human_adna_locality_count=human_adna_locality_count,
        human_adna_sample_count=human_adna_locality_count * 4,
        domesticated_animal_locality_count=domesticated_animal_locality_count,
        domesticated_animal_sample_count=domesticated_animal_locality_count,
        sead_site_count=sead_site_count,
        time_aware_sead_site_count=sead_site_count,
        human_overlap_sead_site_count=min(sead_site_count, human_adna_locality_count),
        raa_density_site_count=100,
        evidence_family_count=evidence_family_count,
        nearby_pollen_signal=0.7,
        human_signal=0.5,
        animal_signal=0.0,
        archaeology_signal=0.7,
        diversity_signal=0.8,
    )


def _assessment(
    *,
    lake_name: str,
    lake_label: str,
    latitude: float,
    longitude: float,
    ambiguity_flags: tuple[str, ...],
    rank: int,
    aggregate_score: float,
    band_values: tuple[tuple[int, float, int, int, int], ...],
) -> LakeEvidenceRichnessAssessment:
    return LakeEvidenceRichnessAssessment(
        candidate=_candidate(
            lake_name=lake_name,
            lake_label=lake_label,
            latitude=latitude,
            longitude=longitude,
            ambiguity_flags=ambiguity_flags,
            direct_pollen_source_count=2,
        ),
        aggregate_rank=rank,
        aggregate_score=aggregate_score,
        band_scores=tuple(
            _band(
                radius,
                band_rank=rank,
                total_score=score,
                sead_site_count=sead_count,
                evidence_family_count=family_count,
                human_adna_locality_count=human_count,
            )
            for radius, score, sead_count, family_count, human_count in band_values
        ),
    )


def _report() -> LakeEvidenceRichnessReport:
    strong = _assessment(
        lake_name="Lake Clear",
        lake_label="Lake Clear",
        latitude=57.1,
        longitude=14.2,
        ambiguity_flags=(),
        rank=1,
        aggregate_score=0.62,
        band_values=(
            (10, 0.55, 9, 3, 1),
            (20, 0.63, 24, 4, 2),
            (30, 0.60, 30, 4, 2),
            (40, 0.58, 36, 4, 2),
            (50, 0.57, 40, 4, 2),
        ),
    )
    ambiguous = _assessment(
        lake_name="Lake Shared",
        lake_label="Lake Shared (57.500000, 15.500000)",
        latitude=57.5,
        longitude=15.5,
        ambiguity_flags=("duplicate_sweden_name", "source_coordinate_spread"),
        rank=2,
        aggregate_score=0.51,
        band_values=(
            (10, 0.48, 3, 3, 0),
            (20, 0.52, 7, 4, 1),
            (30, 0.50, 10, 4, 1),
            (40, 0.49, 12, 4, 1),
            (50, 0.47, 15, 4, 1),
        ),
    )
    return LakeEvidenceRichnessReport(
        schema_version="sweden-lake-evidence-richness.v2",
        country="Sweden",
        radii_km=(10, 20, 30, 40, 50),
        methodology={},
        candidate_count=2,
        assessments=(strong, ambiguous),
    )
