"""Source-declared coverage stays spatial context across analytical consumers."""

from __future__ import annotations

from dataclasses import replace

import pytest

from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
    _attach_temporal_context,
    _extract_human_points,
)
from bijux_pollenomics.collection.contracts.occurrence_chronology import (
    occurrence_support_interval,
)

from ..lake_fieldwork_preparation.support import _candidate
from ..ranking_examples import _locality


def test_unknown_owned_sample_precision_does_not_gain_temporal_support_from_flat_bounds() -> (
    None
):
    locality = _locality("Unknown source precision", 59, 18, sample_count=2)
    unknown = replace(
        locality,
        sample_chronologies=tuple(
            replace(
                support,
                chronology=replace(support.chronology, precision_posture="unresolved"),
            )
            for support in locality.sample_chronologies
        ),
    )
    assert unknown.time_start_bp == locality.time_start_bp
    assert unknown.time_end_bp == locality.time_end_bp
    unknown_points = _extract_human_points([unknown])
    assert len(unknown_points) == 1
    assert unknown_points[0].sample_count == 2
    assert unknown_points[0].time_start_bp is None
    assert unknown_points[0].temporal_semantics is None
    assert len(_extract_human_points([locality])) == 2


def test_sample_members_count_one_native_locality_and_keep_all_samples() -> None:
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.scoring import (
        _build_raw_band_metrics,
    )

    locality = _locality("Native owned locality", 59, 18, sample_count=3)
    points = _extract_human_points([locality])
    metrics = _build_raw_band_metrics(
        _candidate(
            lake_name="Controlled",
            lake_label="Controlled",
            latitude=59,
            longitude=18,
            ambiguity_flags=(),
            direct_pollen_source_count=0,
        ),
        (),
        points,
        (),
        (),
        (),
        radius_km=10,
    )
    assert metrics["human_adna_locality_count"] == 1
    assert metrics["human_adna_sample_count"] == 3


def test_undated_native_locality_preserves_spatial_count_and_sample_denominator() -> (
    None
):
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.scoring import (
        _build_raw_band_metrics,
    )
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
        _extract_animal_points,
    )

    locality = _locality("Spatial source locality", 59, 18, sample_count=3)
    unknown = replace(
        locality,
        sample_chronologies=tuple(
            replace(
                support,
                chronology=replace(support.chronology, precision_posture="unresolved"),
            )
            for support in locality.sample_chronologies
        ),
    )
    candidate = _candidate(
        lake_name="Controlled",
        lake_label="Controlled",
        latitude=59,
        longitude=18,
        ambiguity_flags=(),
        direct_pollen_source_count=0,
    )
    humans = _extract_human_points([unknown])
    animals = _extract_animal_points(
        [
            {
                "latitude": 59,
                "longitude": 18,
                "locality": "Source animal site",
                "sample_count": 4,
            }
        ]
    )
    metrics = _build_raw_band_metrics(
        candidate, (), humans, animals, (), (), radius_km=10
    )
    assert metrics["human_adna_locality_count"] == 1
    assert metrics["human_adna_sample_count"] == 3
    assert metrics["domesticated_animal_locality_count"] == 1
    assert metrics["domesticated_animal_sample_count"] == 4
    assert (
        _attach_temporal_context(
            [candidate],
            pollen_points=(),
            human_points=humans,
            animal_points=animals,
            sead_points=(),
        )[0].temporal_context_points
        == ()
    )


@pytest.mark.parametrize("state", ["mixed", "refused", "zero", "distinct"])
def test_native_spatial_population_and_eligible_members_have_separate_denominators(
    state: str,
) -> None:
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.scoring import (
        _build_raw_band_metrics,
    )

    locality = _locality(
        "Co-located source", 59, 18, sample_count=3 if state != "zero" else 0
    )
    if state == "mixed":
        locality = replace(
            locality,
            sample_chronologies=tuple(
                replace(
                    support,
                    chronology=replace(
                        support.chronology, precision_posture="unresolved"
                    ),
                )
                if index
                else support
                for index, support in enumerate(locality.sample_chronologies)
            ),
        )
    if state == "refused":
        locality = replace(
            locality,
            sample_chronologies=tuple(
                replace(
                    support,
                    chronology=replace(
                        support.chronology, refusal_reason_code="source_refusal"
                    ),
                )
                for support in locality.sample_chronologies
            ),
        )
    localities = [locality]
    if state == "distinct":
        localities = [
            replace(
                locality,
                identity=replace(locality.identity, namespace="a:b", stable_token="c"),
            ),
            replace(
                locality,
                identity=replace(locality.identity, namespace="a", stable_token="b:c"),
            ),
        ]
    points = _extract_human_points(localities)
    candidate = _candidate(
        lake_name="Controlled",
        lake_label="Controlled",
        latitude=59,
        longitude=18,
        ambiguity_flags=(),
        direct_pollen_source_count=0,
    )
    metrics = _build_raw_band_metrics(candidate, (), points, (), (), (), radius_km=10)
    assert metrics["human_adna_locality_count"] == len(localities)
    assert metrics["human_adna_sample_count"] == sum(
        row.sample_count for row in localities
    )
    numeric = [
        point
        for point in points
        if occurrence_support_interval(
            temporal_semantics=point.temporal_semantics,
            time_start_bp=point.time_start_bp,
            time_end_bp=point.time_end_bp,
        )
    ]
    assert (
        sum(point.sample_count for point in numeric)
        == {"mixed": 1, "refused": 0, "zero": 0, "distinct": 6}[state]
    )
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
        _extract_animal_points,
    )

    payloads = [
        row.as_dict() | {"latitude": row.latitude, "longitude": row.longitude}
        for row in localities
    ]
    animals = _extract_animal_points(payloads)
    animal_metrics = _build_raw_band_metrics(
        candidate, (), (), animals, (), (), radius_km=10
    )
    assert animal_metrics["domesticated_animal_locality_count"] == len(localities)
    assert animal_metrics["domesticated_animal_sample_count"] == sum(
        row.sample_count for row in localities
    )
    animal_numeric = [
        point
        for point in animals
        if occurrence_support_interval(
            temporal_semantics=point.temporal_semantics,
            time_start_bp=point.time_start_bp,
            time_end_bp=point.time_end_bp,
        )
    ]
    assert (
        sum(point.sample_count for point in animal_numeric)
        == {"mixed": 1, "refused": 0, "zero": 0, "distinct": 6}[state]
    )
