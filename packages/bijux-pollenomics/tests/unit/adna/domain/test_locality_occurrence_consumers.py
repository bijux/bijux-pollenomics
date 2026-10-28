"""Sample-owned chronology survives analytical and serialized boundaries."""

from __future__ import annotations

import csv
from dataclasses import replace
import json
from pathlib import Path

import pytest

from bijux_pollenomics.adna.domain.locality import (
    mapping_sample_intervals,
    summarize_sample_localities,
)
from bijux_pollenomics.adna.domain.models.localities import AdnaSampleChronologySupport
from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
    _extract_animal_points,
    _extract_human_points,
)
from bijux_pollenomics.analysis.fieldwork.ranking import temporal_overlap
from bijux_pollenomics.analysis.propagation.candidates.scoring import _windows_overlap
from bijux_pollenomics.reporting.adna.atlas_evidence_rows.localities import (
    _parse_locality_summary,
)
from bijux_pollenomics.reporting.rendering.record_exports import (
    serialize_locality_summary,
    write_localities_csv,
)

from ...core.test_temporal_overlap_consumers import _context_point
from .test_adna_temporal_query import _sample_with_interval
from .test_locality_occurrence_chronology import _locality


def test_ranking_and_cross_species_alignment_preserve_gap() -> None:
    locality = _locality()
    gap = summarize_sample_localities([_sample_with_interval(200, 200)])[0]
    assert not temporal_overlap(locality, _context_point(younger_bp=200, older_bp=200))
    assert not _windows_overlap(locality, gap)
    assert _windows_overlap(locality, locality)


def test_temporal_evidence_uses_one_count_per_dated_sample() -> None:
    locality = _locality()
    human = _extract_human_points([locality])
    payload = locality.as_dict() | {
        "latitude": locality.latitude,
        "longitude": locality.longitude,
    }
    animal = _extract_animal_points([payload])
    for all_rows in (human, animal):
        assert sum(row.sample_count for row in all_rows) == locality.sample_count
        rows = tuple(row for row in all_rows if row.time_start_bp is not None)
        assert len(rows) == 2
        assert sum(row.sample_count for row in rows) == 2
        assert {(row.time_start_bp, row.time_end_bp) for row in rows} == {
            (100, 110),
            (300, 310),
        }
        assert len({row.source_record for row in rows}) == 2


def test_locality_deserialization_preserves_full_sample_support() -> None:
    locality = _locality()
    row = locality.sample_chronologies[0]
    row = replace(
        row,
        reference_epoch="source-explicit epoch",
        age_type="source age type",
        calibration_status="source calibration",
        model="source model",
    )
    locality = replace(
        locality, sample_chronologies=(row, *locality.sample_chronologies[1:])
    )
    parsed = _parse_locality_summary(locality.as_dict())
    assert parsed.sample_chronologies == locality.sample_chronologies
    assert [support.as_dict() for support in parsed.sample_chronologies] == [
        support.as_dict() for support in locality.sample_chronologies
    ]


def test_locality_csv_version_and_support_round_trip(tmp_path: Path) -> None:
    locality = _locality()
    raw = serialize_locality_summary(locality)
    assert raw["schema_version"] == "adna-locality-summary-export.v2"
    assert raw["chronology_role"] == "locality_sample_coverage_hull"
    destination = tmp_path / "localities.csv"
    write_localities_csv(destination, [locality])
    with destination.open(newline="") as stream:
        row = next(csv.DictReader(stream))
    assert json.loads(row["sample_chronologies"]) == [
        support.as_dict() for support in locality.sample_chronologies
    ]
    assert row["sample_ids"].split(";") == list(locality.sample_ids)


@pytest.mark.parametrize(
    "kind", ["legacy", "unknown_member", "duplicate", "wrong_schema", "boolean_bp"]
)
def test_mapping_never_infers_occurrence_from_hull_or_malformed_support(
    kind: str,
) -> None:
    payload = _locality().as_dict()
    supports = [support.as_dict() for support in _locality().sample_chronologies]
    if kind == "legacy":
        supports = []
    elif kind == "unknown_member":
        supports[0]["sample_id"] = "unowned"
    elif kind == "duplicate":
        supports.append(supports[0])
    elif kind == "wrong_schema":
        supports[0]["schema_version"] = "unqualified"
    else:
        supports[0]["chronology"] = {"time_start_bp": True, "time_end_bp": 10}
    payload["sample_chronologies"] = supports
    assert mapping_sample_intervals(payload) == ()


def test_support_parser_keeps_absent_metadata_explicit() -> None:
    original = _locality().sample_chronologies[0]
    payload = original.as_dict()
    for field in ("reference_epoch", "age_type", "calibration_status", "model"):
        del payload[field]
    parsed = AdnaSampleChronologySupport.from_dict(payload)
    assert parsed.reference_epoch == "not_separately_declared"
    assert parsed.chronology == original.chronology
