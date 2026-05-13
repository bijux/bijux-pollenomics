from __future__ import annotations

from hypothesis import assume, given
from hypothesis import strategies as st

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
    build_species_support_matrix,
    normalize_coordinate_resolution,
    normalize_explicit_bp_window,
    resolve_species_definition,
)
from bijux_pollenomics.data_downloader.models import ContextPointRecord
from bijux_pollenomics.evidence import build_scientific_review_surface


@given(
    start_bp=st.integers(min_value=0, max_value=9000),
    span=st.integers(min_value=0, max_value=2000),
)
def test_explicit_bp_windows_keep_valid_bounds_and_mean(
    start_bp: int,
    span: int,
) -> None:
    end_bp = start_bp + span

    chronology = normalize_explicit_bp_window(
        start_bp,
        end_bp,
        original_text=f"{start_bp}-{end_bp} BP",
    )

    assert chronology.time_start_bp == start_bp
    assert chronology.time_end_bp == end_bp
    assert chronology.time_start_bp <= chronology.time_mean_bp <= chronology.time_end_bp


@given(
    latitude=st.floats(
        min_value=-90,
        max_value=90,
        allow_nan=False,
        allow_infinity=False,
    ),
    longitude=st.floats(
        min_value=-180,
        max_value=180,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_coordinate_resolution_accepts_any_valid_pair(
    latitude: float,
    longitude: float,
) -> None:
    resolution = normalize_coordinate_resolution(
        latitude_text=str(latitude),
        longitude_text=str(longitude),
        geographic_basis="exact_coordinates",
    )

    assert resolution.confidence == "exact"
    assert resolution.coordinate is not None
    assert resolution.coordinate.latitude == latitude
    assert resolution.coordinate.longitude == longitude


_ALIAS_TO_LATIN_NAME = {
    alias: row.latin_name
    for row in build_species_support_matrix()
    for alias in (row.latin_name, *row.aliases)
}


@given(alias=st.sampled_from(sorted(_ALIAS_TO_LATIN_NAME)))
def test_species_alias_resolution_never_crosses_species_boundaries(alias: str) -> None:
    resolved = resolve_species_definition(alias)

    assert resolved.latin_name == _ALIAS_TO_LATIN_NAME[alias]


@given(
    locality_start=st.integers(min_value=0, max_value=8000),
    locality_span=st.integers(min_value=1, max_value=500),
    point_left_extension=st.integers(min_value=0, max_value=200),
    point_right_extension=st.integers(min_value=0, max_value=200),
)
def test_scientific_review_marks_overlapping_human_and_context_windows_as_overlapping(
    locality_start: int,
    locality_span: int,
    point_left_extension: int,
    point_right_extension: int,
) -> None:
    locality_end = locality_start + locality_span
    point_start = max(0, locality_start - point_left_extension)
    point_end = locality_end + point_right_extension
    assume(point_start <= point_end)

    surface = build_scientific_review_surface(
        countries=("Sweden",),
        human_localities=(
            AdnaLocalitySummary(
                identity=AdnaLocalityIdentity(
                    namespace="aadr-locality",
                    stable_token="homo-sapiens:property",
                    locality_text="Property Locality",
                    political_entity="Sweden",
                    source_anchor_tokens=("SE1",),
                ),
                species_latin_name="Homo sapiens",
                species_common_name="human",
                source_family="AADR",
                source_releases=("v66",),
                record_modalities=("metadata_only",),
                review_strengths=("published_release",),
                provenance_qualities=("curated_release",),
                locality="Property Locality",
                coordinates=AdnaCoordinate(
                    latitude=59.0,
                    longitude=18.0,
                    latitude_text="59.0",
                    longitude_text="18.0",
                    confidence="exact",
                ),
                sample_count=1,
                sample_ids=("SE1",),
                datasets=("ho",),
                chronology=AdnaChronology(
                    original_text=f"{locality_start}-{locality_end} BP",
                    time_start_bp=locality_start,
                    time_end_bp=locality_end,
                    time_mean_bp=(locality_start + locality_end) // 2,
                    dating_basis="bp_window",
                ),
                sample_namespace="aadr-sample",
            ),
        ),
        include_tracked_nonhuman_review=False,
        context_points=(
            ContextPointRecord(
                source="Context",
                layer_key="neotoma-pollen",
                layer_label="Neotoma pollen",
                category="environment",
                country="Sweden",
                record_id="ctx-overlap",
                name="Context overlap",
                latitude=59.1,
                longitude=18.1,
                geometry_type="Point",
                subtitle="environment",
                description="Overlap context point",
                source_url="https://example.org/context",
                record_count=1,
                popup_rows=(),
                time_start_bp=point_start,
                time_end_bp=point_end,
                time_mean_bp=(point_start + point_end) // 2,
                time_label=f"{point_start}-{point_end} BP",
            ),
        ),
    )

    row = next(
        item
        for item in surface.chronology_overlaps
        if item.species_latin_name == "Homo sapiens"
        and item.context_layer_key == "neotoma-pollen"
    )
    assert row.overlap_status == "locality_level_overlap_available"
    assert row.overlapping_direct_localities == 1
