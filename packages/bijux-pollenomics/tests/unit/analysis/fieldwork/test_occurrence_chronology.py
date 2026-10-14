"""Source-declared coverage stays spatial context across analytical consumers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
    _attach_temporal_context,
    _context_point_evidence,
    _context_point_has_numeric_interval,
    _extract_human_points,
    _human_context_overlap_ratio,
    _time_aware_ratio,
)
from bijux_pollenomics.analysis.fieldwork.ranking import build_candidate_context
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.contracts.occurrence_chronology import (
    occurrence_support_interval,
)
from bijux_pollenomics.collection.sources.landclim.sites import (
    landclim_site_temporal_semantics,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization.site_temporal_semantics import (
    build_sead_temporal_semantics,
)
from bijux_pollenomics.core.temporal_semantics import (
    BpInterval,
    build_temporal_semantics,
)
from bijux_pollenomics.evidence.scientific_review.chronology import _LayerIntervals
from bijux_pollenomics.evidence.scientific_review.temporal import (
    _context_point_interval,
)

from .lake_fieldwork_preparation.support import _candidate
from .ranking_examples import _locality, _point


def _semantics(evidence_class: str, precision: str) -> dict[str, object]:
    return build_temporal_semantics(
        source_family="controlled_source",
        evidence_class=evidence_class,
        precision_posture=precision,
        comparability_posture="numeric_interval_with_caveat",
        time_start_bp=2500,
        time_end_bp=3500,
        time_mean_bp=3000,
    ).as_dict()


def _coverage() -> tuple[dict[str, object], ...]:
    return (
        landclim_site_temporal_semantics(
            dataset_id="897303",
            interval=(2500, 3500),
            summary_label="2500-3500 BP",
            provenance_locator="SiteData:controlled",
        ),
        build_sead_temporal_semantics({}, time_interval=(2500, 3500)),
        build_sead_temporal_semantics(
            {"dating_range_rows": [{"uncertainty_label": "controlled qualifier"}]},
            time_interval=(2500, 3500),
        ),
        build_sead_temporal_semantics(
            {
                "relative_period_rows": [
                    {"relative_age_label": "controlled source period"}
                ]
            },
            time_interval=(2500, 3500),
        ),
        _semantics("nearby_lake_context_summary", "source_interval_window_summary"),
    )


def _context(
    semantics: dict[str, object] | None, *, layer: str = "controlled"
) -> ContextPointRecord:
    return replace(
        _point(layer, 59, 18, time_start_bp=2500, time_end_bp=3500),
        layer_key=layer,
        temporal_semantics=semantics,
    )


@pytest.mark.parametrize("semantics", _coverage())
def test_actual_source_coverage_declarations_never_become_occurrence_support(
    semantics: dict[str, object],
) -> None:
    original = deepcopy(semantics)
    point = _context(semantics)
    locality = _locality("source anchor", 59, 18)
    ranking = build_candidate_context(locality, [point])
    assert ranking.nearby_context_points == 1
    assert ranking.time_aware_context_points == 0
    assert ranking.temporal_overlap_points == 0
    assert not _context_point_has_numeric_interval(point)
    assert _time_aware_ratio([point]) == 0
    assert _human_context_overlap_ratio([point], _extract_human_points([locality])) == 0
    assert _context_point_interval(point) is None
    assert semantics == original and point.time_start_bp == 2500


@pytest.mark.parametrize(
    "evidence_class,precision",
    [
        ("sead_dating_range", "linked_record_interval"),
        ("sead_dendrochronology", "linked_record_interval"),
        ("modeled_vegetation_time_window", "published_reveals_grid_window"),
    ],
)
def test_individual_source_dates_and_explicit_model_windows_remain_supported(
    evidence_class: str, precision: str
) -> None:
    point = _context(_semantics(evidence_class, precision))
    locality = _locality("source anchor", 59, 18)
    ranking = build_candidate_context(locality, [point])
    assert (
        ranking.nearby_context_points
        == ranking.time_aware_context_points
        == ranking.temporal_overlap_points
        == 1
    )
    assert _context_point_has_numeric_interval(point)
    assert _time_aware_ratio([point]) == 1
    assert _human_context_overlap_ratio([point], _extract_human_points([locality])) == 1
    assert _context_point_interval(point) is not None


def test_richness_attachment_and_ratio_apply_the_same_support_contract() -> None:
    coverage = [
        _context(semantics, layer=f"coverage-{index}")
        for index, semantics in enumerate(_coverage())
    ]
    eligible = [
        _context(
            _semantics("sead_dating_range", "linked_record_interval"),
            layer="dated-sead",
        ),
        _context(
            _semantics(
                "modeled_vegetation_time_window", "published_reveals_grid_window"
            ),
            layer="modeled-window",
        ),
    ]
    points = [*coverage, *eligible]
    candidate = _candidate(
        lake_name="Controlled lake",
        lake_label="Controlled lake",
        latitude=59,
        longitude=18,
        ambiguity_flags=(),
        direct_pollen_source_count=1,
    )
    result = _attach_temporal_context(
        [candidate],
        pollen_points=points,
        human_points=(),
        animal_points=(),
        sead_points=(),
    )[0]
    assert {anchor.source_layer_key for anchor in result.temporal_context_points} == {
        "dated-sead",
        "modeled-window",
    }
    assert sum(anchor.record_count for anchor in result.temporal_context_points) == 2
    assert _time_aware_ratio(points) == round(2 / len(points), 4)
    assert _context_point_evidence(coverage[0]).time_start_bp == 2500


@pytest.mark.parametrize(
    "semantics",
    [
        None,
        {},
        {"comparability_posture": "contextual_label_only"},
        {
            "comparability_posture": "numeric_interval",
            "refusal_reason_code": "source_refusal",
            "time_start_bp": 2500,
            "time_end_bp": 3500,
        },
    ],
)
def test_missing_contextual_and_refused_postures_have_no_occurrence_permission(
    semantics: dict[str, object] | None,
) -> None:
    point = _context(semantics)
    assert not _context_point_has_numeric_interval(point)
    assert _context_point_interval(point) is None


@pytest.mark.parametrize(
    "key,value",
    [
        ("time_start_bp", None),
        ("time_end_bp", True),
        ("time_mean_bp", 2500.25),
        ("evidence_class", []),
        ("precision_posture", {}),
        ("schema_version", "temporal-semantics.v99"),
        ("refusal_reason_code", None),
        ("chronology_role", "locality_sample_coverage_hull"),
    ],
)
def test_malformed_or_coverage_metadata_does_not_grant_record_support(
    key: str, value: object
) -> None:
    semantics = _semantics("sead_dating_range", "linked_record_interval")
    semantics[key] = value
    assert (
        occurrence_support_interval(
            temporal_semantics=semantics, time_start_bp=2500, time_end_bp=3500
        )
        is None
    )


def test_source_flat_bounds_must_agree_with_its_declared_semantics() -> None:
    assert (
        occurrence_support_interval(
            temporal_semantics=_semantics(
                "sead_dating_range", "linked_record_interval"
            ),
            time_start_bp=0,
            time_end_bp=0,
        )
        is None
    )


def test_scientific_review_index_filters_coverage_before_preserving_component_gaps() -> (
    None
):
    def dated(start: int, end: int) -> ContextPointRecord:
        semantics = _semantics("sead_dating_range", "linked_record_interval")
        semantics.update(time_start_bp=start, time_end_bp=end, time_mean_bp=start)
        return replace(
            _context(semantics),
            time_start_bp=start,
            time_end_bp=end,
            time_mean_bp=start,
        )

    coverage = _context(
        landclim_site_temporal_semantics(
            dataset_id="897303",
            interval=(100, 310),
            summary_label="100-310 BP",
            provenance_locator="controlled",
        )
    )
    dated_points = [dated(100, 110), dated(300, 310)]
    index = _LayerIntervals.from_points([coverage, *dated_points])
    assert index == _LayerIntervals.from_points(dated_points)
    assert not index.overlaps(BpInterval(200, 200))
    assert index.overlaps(BpInterval(110, 110))


def test_site_coverage_remains_a_spatial_lake_anchor_without_direct_numeric_claims() -> (
    None
):
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.candidates.pollen import (
        _derive_lake_candidates,
    )
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.methodology import (
        _temporal_navigation_summary,
    )
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.models import (
        LakeEvidenceSourceAnchor,
    )
    from bijux_pollenomics.analysis.review.fieldwork.lake_evidence_richness_packets.candidate_features import (
        _candidate_direct_temporal_sources,
        _candidate_temporal_sources,
    )

    point = replace(
        _context(_coverage()[0]),
        name="Controlled Lake",
        layer_key="landclim-sites",
        source="LandClim",
    )
    candidates = _derive_lake_candidates([point], neotoma_position_notes={})
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.direct_pollen_record_count == 1
    assert candidate.time_aware_direct_pollen_records == 0
    assert candidate.supporting_source_points[0].time_start_bp == 2500
    assert (
        candidate.supporting_source_points[0].temporal_semantics
        == point.temporal_semantics
    )
    assert (
        _temporal_navigation_summary(candidates)[
            "candidate_with_direct_numeric_pollen_count"
        ]
        == 0
    )
    assert _candidate_direct_temporal_sources(candidate) == ()
    navigation = LakeEvidenceSourceAnchor(
        source_record="controlled-nearby",
        source_name="Controlled nearby navigation",
        source_layer_key="controlled-context",
        latitude=59,
        longitude=18,
        source_url="",
        time_start_bp=1001,
        time_end_bp=3000,
        temporal_semantics=_semantics(
            "nearby_lake_context_summary", "source_interval_window_summary"
        ),
        evidence_role="nearby_temporal_context",
    )
    with_navigation = replace(candidate, temporal_context_points=(navigation,))
    assert _candidate_temporal_sources(with_navigation) == (navigation,)


@pytest.mark.parametrize("posture", [[], {}, None, True, 1])
def test_malformed_aggregate_posture_refuses_components_without_raising(
    posture: object,
) -> None:
    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        ContextOccurrenceSupport,
        occurrence_support_intervals,
    )

    support = ContextOccurrenceSupport(
        "owned", 2500, 3500, _semantics("sead_dating_range", "linked_record_interval")
    )
    assert not occurrence_support_intervals(
        temporal_semantics={"comparability_posture": posture},
        time_start_bp=2500,
        time_end_bp=3500,
        occurrence_supports=(support,),
    )


def test_explicit_empty_component_collection_never_falls_back_to_a_hull() -> None:
    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        occurrence_support_intervals,
    )

    semantics = _semantics("sead_dating_range", "linked_record_interval")
    assert not occurrence_support_intervals(
        temporal_semantics=semantics,
        time_start_bp=2500,
        time_end_bp=3500,
        occurrence_supports=(),
    )
    assert occurrence_support_intervals(
        temporal_semantics=semantics,
        time_start_bp=2500,
        time_end_bp=3500,
        occurrence_supports=None,
    )


def test_optimized_occurrence_index_matches_canonical_closed_relation_for_component_queries() -> (
    None
):
    from hypothesis import given, settings
    from hypothesis import strategies as st

    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        ContextOccurrenceSupport,
        occurrence_support_intervals,
    )
    from bijux_pollenomics.core.temporal_semantics import closed_bp_intervals_overlap

    @settings(max_examples=60, derandomize=True, deadline=None)
    @given(
        st.lists(st.tuples(st.integers(0, 500), st.integers(0, 500)), max_size=25),
        st.integers(0, 2000),
        st.integers(0, 2000),
    )
    def check(raw: list[tuple[int, int]], left: int, right: int) -> None:
        supports = []
        for index, (first, last) in enumerate(raw):
            start, end = sorted((first, last))
            semantics = build_temporal_semantics(
                source_family="controlled_source",
                evidence_class="sead_dating_range",
                precision_posture="linked_record_interval",
                comparability_posture="numeric_interval",
                time_start_bp=start,
                time_end_bp=end,
            ).as_dict()
            supports.append(ContextOccurrenceSupport(str(index), start, end, semantics))
        point = replace(_context(None), occurrence_supports=tuple(supports))
        query = BpInterval(min(left, right) / 4, max(left, right) / 4)
        expected = occurrence_support_intervals(
            temporal_semantics=point.temporal_semantics,
            time_start_bp=point.time_start_bp,
            time_end_bp=point.time_end_bp,
            occurrence_supports=point.occurrence_supports,
        )
        assert _LayerIntervals.from_points([point]).overlaps(query) == any(
            closed_bp_intervals_overlap(interval, query) for interval in expected
        )

    check()


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
