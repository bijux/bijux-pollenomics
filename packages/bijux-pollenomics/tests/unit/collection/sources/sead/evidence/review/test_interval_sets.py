"""Disjoint native chronology and refusal of SEAD site display envelopes."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.analysis.fieldwork.evidence_richness.models import (
    LakeEvidenceCandidate,
    _PointEvidence,
)
from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
    _attach_temporal_context,
    _context_point_has_numeric_interval,
    _context_point_overlaps_any_human,
    _human_context_overlap_ratio,
    _time_aware_ratio,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.sources.sead.evidence.review.interval_sets import (
    build_sead_interval_set_review,
    coalesce_intervals,
)

ROOT = next(
    parent
    for parent in Path(__file__).parents
    if (parent / "configs/pytest.ini").is_file()
)


def _point(layer_key: str, start: int, end: int) -> ContextPointRecord:
    return ContextPointRecord(
        source="SEAD",
        layer_key=layer_key,
        layer_label="SEAD",
        category="Chronology",
        country="Sweden",
        record_id="3840",
        name="SEAD site",
        latitude=59,
        longitude=18,
        geometry_type="Point",
        subtitle="Chronology",
        description="SEAD chronology",
        source_url="",
        record_count=1,
        popup_rows=(),
        time_start_bp=start,
        time_end_bp=end,
        time_mean_bp=(start + end) // 2,
        temporal_semantics={
            "comparability_posture": "numeric_interval",
            "time_start_bp": start,
            "time_end_bp": end,
        },
    )


def _candidate() -> LakeEvidenceCandidate:
    return LakeEvidenceCandidate(
        lake_name="Lake",
        lake_label="Lake",
        lake_token="lake",
        name_key="lake",
        latitude=59,
        longitude=18,
        basin_posture="known",
        direct_pollen_source_count=0,
        direct_pollen_record_count=0,
        time_aware_direct_pollen_records=0,
        pollen_sources=(),
        supporting_pollen_names=(),
        supporting_source_records=(),
        supporting_source_points=(),
        representative_source_record="",
        representative_source_layer_key="",
        representative_source_name="",
        representative_source_url="",
        coordinate_resolution_method="known",
        duplicate_name_count=0,
        coordinate_spread_km=0,
        ambiguity_flags=(),
        ambiguity_note="",
        direct_pollen_signal=0,
    )


def test_closed_interval_union_retains_real_gap() -> None:
    assert coalesce_intervals([(105, 107), (82, 83)]) == [(82, 83), (105, 107)]
    assert coalesce_intervals([(82, 83), (84, 90)]) == [(82, 90)]


def test_actual_pinned_site_retains_disjoint_phases_and_all_claims() -> None:
    report, rows = build_sead_interval_set_review(ROOT / "data")
    denominators = report["denominators"]
    assert denominators["native_reviewed_claims"] == 25_109
    assert denominators["eligible_record_claims"] == 13_170
    assert denominators["refused_or_contextual_claims_excluded"] == 11_939
    assert denominators["exported_record_intervals"] == 7_244
    assert denominators["exported_sites"] == len(rows) == 2_069
    assert denominators["sites_with_record_intervals"] == 370
    site = next(row for row in rows if row["source_site_id"] == "3840")
    assert (site["display_start_bp"], site["display_end_bp"]) == (82, 107)
    assert json.loads(str(site["phases_json"])) == [[82, 83], [105, 107]]
    assert json.loads(str(site["gaps_json"])) == [[84, 104]]
    assert site["eligible_claim_count"] == 79
    assert site["record_interval_count"] == 11
    gold = next(
        example
        for example in report["gold_disjoint_sites"]
        if example["source_site_id"] == "3840"
    )
    assert len(gold["native_claims"]) == 79
    assert {
        (claim["younger_bp"], claim["older_bp"]) for claim in gold["native_claims"]
    } == {(82, 82), (83, 83), (105, 105), (106, 106), (107, 107)}
    assert (
        report["analytic_posture"]["site_display_envelope_is_analytic_interval"]
        is False
    )


def test_site_envelope_cannot_create_false_gap_overlap_or_lake_anchor() -> None:
    site = _point("sead-sites", 82, 107)
    record = _point("sead-temporal-evidence", 82, 83)
    human_in_gap = _PointEvidence(
        latitude=59, longitude=18, time_start_bp=90, time_end_bp=90
    )
    assert not _context_point_has_numeric_interval(site)
    assert _context_point_has_numeric_interval(record)
    assert _time_aware_ratio((site,)) == 0
    assert _human_context_overlap_ratio((site,), (human_in_gap,)) == 0
    assert not _context_point_overlaps_any_human(record, (human_in_gap,))
    candidate = _attach_temporal_context(
        (_candidate(),),
        pollen_points=(),
        human_points=(),
        animal_points=(),
        sead_points=(site,),
    )[0]
    assert candidate.temporal_context_points == ()
