"""Source-declared coverage stays spatial context across analytical consumers."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis import build_sweden_lake_evidence_richness_report
from bijux_pollenomics.analysis.fieldwork.evidence_richness.inputs import (
    _load_sweden_context_points,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
    _attach_temporal_context,
    _context_point_evidence,
    _time_aware_ratio,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.contracts.occurrence_chronology import (
    ContextOccurrenceSupport,
)
from bijux_pollenomics.collection.exports import write_context_points_geojson
from bijux_pollenomics.collection.sources.landclim.sites import (
    landclim_site_temporal_semantics,
)
from bijux_pollenomics.core.temporal_semantics import (
    BpInterval,
    build_temporal_semantics,
)
from bijux_pollenomics.evidence.scientific_review.chronology import _LayerIntervals

from ..lake_fieldwork_preparation.support import _candidate
from .support import _context, _coverage, _semantics


def _multiperiod_context(aggregate_mean: int | None) -> ContextPointRecord:
    supports = tuple(
        ContextOccurrenceSupport(
            f"owned-{age}",
            age,
            age,
            build_temporal_semantics(
                source_family="controlled_source",
                evidence_class="sead_dating_range",
                precision_posture="linked_record_interval",
                comparability_posture="numeric_interval",
                time_start_bp=age,
                time_end_bp=age,
            ).as_dict(),
        )
        for age in (500, 4500, 7500)
    )
    refused = ContextOccurrenceSupport(
        "refused",
        None,
        None,
        {
            "comparability_posture": "context_only",
            "refusal_reason_code": "source_date_unavailable",
        },
    )
    return replace(
        _context(None, layer="controlled-multiperiod"),
        time_start_bp=100,
        time_end_bp=9000,
        time_mean_bp=aggregate_mean,
        occurrence_supports=(*supports, refused),
    )


@pytest.mark.parametrize("aggregate_mean", [None, 5000, 50])
def test_navigation_labels_follow_owned_component_windows(
    aggregate_mean: int | None,
) -> None:
    candidate = _candidate(
        lake_name="Controlled lake",
        lake_label="Controlled lake",
        latitude=59,
        longitude=18,
        ambiguity_flags=(),
        direct_pollen_source_count=1,
    )
    point = _multiperiod_context(aggregate_mean)
    result = _attach_temporal_context(
        [candidate],
        pollen_points=[point],
        human_points=(),
        animal_points=(),
        sead_points=(),
    )[0]
    anchors = result.temporal_context_points
    assert [
        (anchor.time_start_bp, anchor.time_end_bp, anchor.time_mean_bp)
        for anchor in anchors
    ] == [(6001, 7500, 7500), (3001, 6000, 4500), (0, 1000, 500)]
    assert [anchor.time_label for anchor in anchors] == [
        "Early Holocene and older (6001+ BP)",
        "Mid-Holocene (3001-6000 BP)",
        "Recent and historical (0-1000 BP)",
    ]
    for anchor in anchors:
        row = anchor.as_dict()
        semantics = row["temporal_semantics"]
        assert isinstance(semantics, dict)
        assert row["source_name"] == (
            f"{anchor.time_label} nearby controlled-multiperiod context"
        )
        assert semantics["summary_label"] == anchor.time_label
        assert semantics["temporal_window_label"] == anchor.time_label
        assert f"provide {anchor.time_label} context" in str(
            semantics["comparison_note"]
        )
        assert semantics["evidence_class"] == "nearby_lake_context_summary"
        assert semantics["precision_posture"] == "source_interval_window_summary"
        assert semantics["uncertainty_notes"] == [
            "Underlying source intervals may extend beyond this navigation window.",
            "The summary is nearby context and is not a lake-owned date.",
        ]
        assert anchor.record_count == anchor.sample_count == 1
    assert point == _multiperiod_context(aggregate_mean)
    assert not any(anchor.time_start_bp == 1001 for anchor in anchors)


def test_component_navigation_is_independent_of_source_and_component_order() -> None:
    candidate = _candidate(
        lake_name="Controlled lake",
        lake_label="Controlled lake",
        latitude=59,
        longitude=18,
        ambiguity_flags=(),
        direct_pollen_source_count=1,
    )
    first = _multiperiod_context(5000)
    second = replace(_multiperiod_context(None), record_id="second")

    def summarized(points: list[ContextPointRecord]) -> dict[str, object]:
        return _attach_temporal_context(
            [candidate],
            pollen_points=points,
            human_points=(),
            animal_points=(),
            sead_points=(),
        )[0].as_dict()

    assert first.occurrence_supports is not None
    assert second.occurrence_supports is not None
    reordered = [
        replace(
            second, occurrence_supports=tuple(reversed(second.occurrence_supports))
        ),
        replace(first, occurrence_supports=tuple(reversed(first.occurrence_supports))),
    ]
    assert summarized([first, second]) == summarized(reordered)


@pytest.mark.parametrize(
    ("component_state", "expected_labels"),
    [
        ("populated", 3),
        ("empty", 0),
        ("absent", 1),
        ("component_only", 3),
        ("explicit_empty_aggregate", 0),
        ("refused_aggregate", 0),
    ],
)
def test_exported_components_reach_public_fieldwork_report(
    tmp_path: Path, component_state: str, expected_labels: int
) -> None:
    point = replace(
        _multiperiod_context(5000),
        name="Controlled Lake",
        description="Controlled lake-basin pollen context",
        layer_key="neotoma-pollen",
        temporal_semantics=build_temporal_semantics(
            source_family="controlled_source",
            evidence_class="sead_dating_range",
            precision_posture="linked_record_interval",
            comparability_posture="numeric_interval",
            time_start_bp=100,
            time_end_bp=9000,
            time_mean_bp=5000,
        ).as_dict(),
    )
    if component_state == "empty":
        point = replace(point, occurrence_supports=())
    elif component_state == "absent":
        point = replace(point, occurrence_supports=None)
    elif component_state == "component_only":
        point = replace(
            point,
            time_start_bp=None,
            time_end_bp=None,
            time_mean_bp=None,
            temporal_semantics=None,
        )
    elif component_state == "explicit_empty_aggregate":
        point = replace(point, temporal_semantics={})
    elif component_state == "refused_aggregate":
        point = replace(
            point,
            temporal_semantics={
                "comparability_posture": "context_only",
                "refusal_reason_code": "source_date_unavailable",
            },
        )
    path = tmp_path / "neotoma/normalized/nordic_pollen_sites.geojson"
    path.parent.mkdir(parents=True)
    write_context_points_geojson(path, [point])
    loaded = _load_sweden_context_points(path, country="Sweden")
    assert loaded[0].occurrence_supports == point.occurrence_supports
    assert loaded[0].temporal_semantics == point.temporal_semantics
    report = build_sweden_lake_evidence_richness_report(
        context_root=tmp_path, human_localities=(), animal_localities=()
    )
    assert report.candidate_count == 1
    anchors = report.assessments[0].candidate.temporal_context_points
    assert len(anchors) == expected_labels
    if expected_labels == 3:
        assert [anchor.time_label for anchor in anchors] == [
            "Early Holocene and older (6001+ BP)",
            "Mid-Holocene (3001-6000 BP)",
            "Recent and historical (0-1000 BP)",
        ]
        assert [anchor.time_mean_bp for anchor in anchors] == [7500, 4500, 500]
        assert all(
            anchor.record_count == anchor.sample_count == 1 for anchor in anchors
        )
    elif expected_labels == 1:
        assert anchors[0].time_label == "Mid-Holocene (3001-6000 BP)"
        assert anchors[0].time_mean_bp == 5000


@pytest.mark.parametrize(
    "malformation",
    [
        "null",
        "object",
        "member",
        "missing",
        "blank",
        "duplicate",
        "bool",
        "text",
        "semantics",
    ],
)
def test_public_fieldwork_reader_refuses_malformed_components(
    tmp_path: Path, malformation: str
) -> None:
    point = replace(_multiperiod_context(5000), name="Controlled Lake")
    path = tmp_path / "context.geojson"
    write_context_points_geojson(path, [point])
    payload = json.loads(path.read_text(encoding="utf-8"))
    properties = payload["features"][0]["properties"]
    row = properties["occurrence_supports"][0]
    if malformation == "null":
        properties["occurrence_supports"] = None
    elif malformation == "object":
        properties["occurrence_supports"] = {}
    elif malformation == "member":
        properties["occurrence_supports"] = [None]
    elif malformation == "missing":
        del row["time_start_bp"]
    elif malformation == "blank":
        row["support_id"] = " "
    elif malformation == "duplicate":
        properties["occurrence_supports"].append(row.copy())
    elif malformation == "bool":
        row["time_start_bp"] = True
    elif malformation == "text":
        row["time_end_bp"] = "500"
    else:
        row["temporal_semantics"] = None
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(
        ValueError, match="context.geojson context feature.*occurrence_supports"
    ):
        _load_sweden_context_points(path, country="Sweden")


def test_component_reader_preserves_zero_and_refused_negative_intervals(
    tmp_path: Path,
) -> None:
    point = _multiperiod_context(None)
    assert point.occurrence_supports is not None
    support = point.occurrence_supports[0]
    supports = tuple(
        replace(
            support,
            support_id=f"native-{age}",
            time_start_bp=age,
            time_end_bp=age,
            temporal_semantics={
                **support.temporal_semantics,
                "time_start_bp": age,
                "time_end_bp": age,
            },
        )
        for age in (-1, 0)
    )
    point = replace(point, occurrence_supports=supports)
    path = tmp_path / "context.geojson"
    write_context_points_geojson(path, [point])
    loaded = _load_sweden_context_points(path, country="Sweden")[0]
    assert loaded.occurrence_supports == supports
    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        occurrence_support_intervals,
    )

    assert occurrence_support_intervals(
        temporal_semantics=loaded.temporal_semantics,
        time_start_bp=loaded.time_start_bp,
        time_end_bp=loaded.time_end_bp,
        occurrence_supports=loaded.occurrence_supports,
    ) == (BpInterval(0, 0),)


@pytest.mark.parametrize(
    ("latitude", "longitude", "accepted"),
    [
        (True, 18, False),
        (59, False, False),
        (float("nan"), 18, False),
        (59, float("nan"), False),
        (float("-inf"), 18, False),
        (59, float("inf"), False),
        (91, 18, False),
        (-91, 18, False),
        (59, 181, False),
        (59, -181, False),
        (10**400, 18, False),
        (-(10**400), 18, False),
        (59, 10**400, False),
        (59, -(10**400), False),
        (0, 0, True),
        (90, 180, True),
        (-90, -180, True),
        (59, 18, True),
    ],
)
def test_public_fieldwork_reader_applies_geographic_coordinate_contract(
    tmp_path: Path, latitude: float, longitude: float, accepted: bool
) -> None:
    point = replace(
        _multiperiod_context(None),
        name="Controlled Lake",
        latitude=latitude,
        longitude=longitude,
    )
    path = tmp_path / "neotoma/normalized/nordic_pollen_sites.geojson"
    path.parent.mkdir(parents=True)
    write_context_points_geojson(path, [point])
    loaded = _load_sweden_context_points(path, country="Sweden")
    report = build_sweden_lake_evidence_richness_report(
        context_root=tmp_path, human_localities=(), animal_localities=()
    )
    assert len(loaded) == report.candidate_count == int(accepted)
    if accepted:
        candidate = report.assessments[0].candidate
        assert (candidate.latitude, candidate.longitude) == (latitude, longitude)
    json.dumps(report.as_dict(), allow_nan=False)


def test_invalid_coordinate_feature_does_not_discard_valid_lake(tmp_path: Path) -> None:
    valid = replace(_multiperiod_context(None), name="Controlled Lake")
    invalid = replace(valid, record_id="invalid", name="Invalid Lake", longitude=True)
    path = tmp_path / "neotoma/normalized/nordic_pollen_sites.geojson"
    path.parent.mkdir(parents=True)
    write_context_points_geojson(path, [invalid, valid])
    assert _load_sweden_context_points(path, country="Sweden") == (valid,)
    report = build_sweden_lake_evidence_richness_report(
        context_root=tmp_path, human_localities=(), animal_localities=()
    )
    assert report.candidate_count == 1
    assert report.assessments[0].candidate.lake_name == "Controlled Lake"


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
