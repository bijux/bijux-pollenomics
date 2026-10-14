"""Actual public serializers retain source eligibility through external and map readers."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from bijux_pollenomics.adna import AdnaLocalitySummary
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.reporting.bundles.atlas_bundle.context import (
    extract_context_points,
)
from bijux_pollenomics.reporting.context import build_external_point_layer

from .support import _extracted_locality, _owned_locality_record, _record


def test_real_locality_export_components_survive_atlas_analytics_without_hull_or_count_inflation() -> (
    None
):
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
        _attach_temporal_context,
    )
    from bijux_pollenomics.analysis.fieldwork.ranking import build_candidate_context
    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        occurrence_support_intervals,
    )
    from bijux_pollenomics.core.temporal_semantics import BpInterval
    from bijux_pollenomics.evidence.scientific_review.chronology import _LayerIntervals

    from ....analysis.fieldwork.lake_fieldwork_preparation.support import _candidate
    from ....analysis.fieldwork.ranking_examples import _locality

    record = _owned_locality_record()
    point = _extracted_locality(record)
    assert point.source_record is not None
    assert point.source_record["sample_chronologies"] == record["sample_chronologies"]
    assert point.source_record["sample_ids"] == record["sample_ids"]
    assert point.record_count == 1 and point.occurrence_supports is not None
    assert len(point.occurrence_supports) == 4
    intervals = occurrence_support_intervals(
        temporal_semantics=point.temporal_semantics,
        time_start_bp=point.time_start_bp,
        time_end_bp=point.time_end_bp,
        occurrence_supports=point.occurrence_supports,
    )
    assert [(i.younger_bp, i.older_bp) for i in intervals] == [
        (100, 110),
        (105, 110),
        (300, 310),
    ]
    index = _LayerIntervals.from_points([point])
    assert not index.overlaps(BpInterval(200, 200))
    assert index.overlaps(BpInterval(110, 110))
    anchor = _locality("candidate", 59, 18, sample_count=1)
    support = anchor.sample_chronologies[0]

    def candidate_at(start: int, end: int) -> AdnaLocalitySummary:
        chronology = replace(
            support.chronology,
            time_start_bp=start,
            time_end_bp=end,
            time_mean_bp=start,
            precision_posture="sample_precise_interval",
            evidence_class="controlled_numeric_sample_date",
        )
        return replace(
            anchor, sample_chronologies=(replace(support, chronology=chronology),)
        )

    gap = build_candidate_context(candidate_at(200, 200), [point])
    assert gap.nearby_context_points == gap.time_aware_context_points == 1
    assert gap.temporal_overlap_points == 0
    young = build_candidate_context(candidate_at(105, 110), [point])
    assert young.temporal_overlap_points == 1
    candidate = _candidate(
        lake_name="Controlled lake",
        lake_label="Controlled lake",
        latitude=59,
        longitude=18,
        ambiguity_flags=(),
        direct_pollen_source_count=1,
    )
    attached = _attach_temporal_context(
        [candidate],
        pollen_points=[point],
        human_points=(),
        animal_points=(),
        sead_points=(),
    )[0]
    assert len(attached.temporal_context_points) == 1
    assert attached.temporal_context_points[0].record_count == 1
    assert attached.temporal_context_points[0].sample_count == 1


@pytest.mark.parametrize(
    "semantics",
    [
        {},
        {"comparability_posture": "contextual_label_only"},
        {"comparability_posture": "refused", "refusal_reason_code": "source_refusal"},
    ],
)
def test_explicit_outer_declaration_still_constrains_owned_components(
    semantics: dict[str, object],
) -> None:
    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        occurrence_support_intervals,
    )

    record = {**_owned_locality_record(), "temporal_semantics": semantics}
    point = _extracted_locality(record)
    assert (
        point.source_record is not None
        and point.source_record["sample_chronologies"] == record["sample_chronologies"]
    )
    assert not occurrence_support_intervals(
        temporal_semantics=point.temporal_semantics,
        time_start_bp=point.time_start_bp,
        time_end_bp=point.time_end_bp,
        occurrence_supports=point.occurrence_supports,
    )


def test_context_exports_preserve_named_source_and_components_with_legacy_bytes_unchanged(
    tmp_path: Path,
) -> None:
    import csv

    from bijux_pollenomics.collection.exports.context_points import (
        write_context_points_csv,
        write_context_points_geojson,
    )

    point = _extracted_locality(_owned_locality_record())
    geojson = tmp_path / "context.geojson"
    write_context_points_geojson(geojson, [point])
    payload = json.loads(geojson.read_text())
    properties = payload["features"][0]["properties"]
    assert properties["schema_version"] == "adna-locality-summary-export.v2"
    assert "temporal_semantics" not in properties
    roundtrip = cast(
        ContextPointRecord,
        extract_context_points(
            [build_external_point_layer(payload)],
            surface=SimpleNamespace(ContextPointRecord=ContextPointRecord),
        )[0],
    )
    assert roundtrip.occurrence_supports == point.occurrence_supports
    assert roundtrip.source_record is not None
    assert point.source_record is not None and point.occurrence_supports is not None
    assert (
        roundtrip.source_record["sample_chronologies"]
        == point.source_record["sample_chronologies"]
    )
    csv_path = tmp_path / "context.csv"
    write_context_points_csv(csv_path, [point])
    with csv_path.open(newline="") as stream:
        row = next(csv.DictReader(stream))
    assert json.loads(row["source_record_json"]) == point.source_record
    assert json.loads(row["occurrence_supports_json"]) == [
        support.as_dict() for support in point.occurrence_supports
    ]
    legacy = replace(point, source_record=None, occurrence_supports=None)
    write_context_points_csv(csv_path, [legacy])
    with csv_path.open(newline="") as stream:
        legacy_row = next(csv.DictReader(stream))
    assert (
        "source_record_json" not in legacy_row
        and "occurrence_supports_json" not in legacy_row
    )


def test_unknown_native_member_refuses_extracted_components_without_hull_fallback() -> (
    None
):
    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        occurrence_support_intervals,
    )

    record = _owned_locality_record()
    record["sample_chronologies"][0]["sample_id"] = "unknown-native-member"
    point = _extracted_locality(record)
    assert point.occurrence_supports == ()
    assert (
        point.source_record is not None
        and point.source_record["sample_chronologies"] == record["sample_chronologies"]
    )
    assert not occurrence_support_intervals(
        temporal_semantics=point.temporal_semantics,
        time_start_bp=point.time_start_bp,
        time_end_bp=point.time_end_bp,
        occurrence_supports=point.occurrence_supports,
    )


def test_refused_member_is_retained_without_suppressing_other_owned_intervals() -> None:
    from bijux_pollenomics.collection.contracts.occurrence_chronology import (
        occurrence_support_intervals,
    )

    record = _owned_locality_record()
    record["sample_chronologies"][0]["chronology"]["refusal_reason_code"] = (
        "source_refusal"
    )
    point = _extracted_locality(record)
    assert point.occurrence_supports is not None and len(point.occurrence_supports) == 4
    intervals = occurrence_support_intervals(
        temporal_semantics=point.temporal_semantics,
        time_start_bp=point.time_start_bp,
        time_end_bp=point.time_end_bp,
        occurrence_supports=point.occurrence_supports,
    )
    assert [(interval.younger_bp, interval.older_bp) for interval in intervals] == [
        (105, 110),
        (300, 310),
    ]
    assert (
        point.source_record is not None
        and point.source_record["sample_chronologies"] == record["sample_chronologies"]
    )


def test_preferred_singular_sample_keeps_native_identity_and_zero_after_extraction() -> (
    None
):
    from bijux_pollenomics.core.temporal_semantics import BpInterval
    from bijux_pollenomics.evidence.scientific_review.chronology import _LayerIntervals

    record = _record()
    point = _extracted_locality(record)
    assert (
        point.source_record is not None
        and point.source_record["sample_identity"] == record["sample_identity"]
    )
    assert point.occurrence_supports is None
    assert _LayerIntervals.from_points([point]).overlaps(BpInterval(0, 0))


def test_repeated_context_transport_preserves_semantics_and_literal_provenance(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.exports.context_points import (
        write_context_points_geojson,
    )
    from bijux_pollenomics.core.temporal_semantics import BpInterval
    from bijux_pollenomics.evidence.scientific_review.chronology import _LayerIntervals

    point = _extracted_locality(_owned_locality_record())
    for index in range(2):
        previous = point
        path = tmp_path / f"context-{index}.geojson"
        write_context_points_geojson(path, [previous])
        collection = json.loads(path.read_text())
        point = cast(
            ContextPointRecord,
            extract_context_points(
                [build_external_point_layer(collection)],
                surface=SimpleNamespace(ContextPointRecord=ContextPointRecord),
            )[0],
        )
        assert point.record_count == 1
        assert point.occurrence_supports == previous.occurrence_supports
        assert point.source_record is not None
        assert point.source_record["source_record"] == previous.source_record
        assert (
            point.source_record["schema_version"] == "adna-locality-summary-export.v2"
        )
        assert not _LayerIntervals.from_points([point]).overlaps(BpInterval(200, 200))
        assert _LayerIntervals.from_points([point]).overlaps(BpInterval(110, 110))
