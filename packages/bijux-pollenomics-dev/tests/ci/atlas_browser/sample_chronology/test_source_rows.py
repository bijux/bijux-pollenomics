"""Controlled parser guards supplement the separately executed authentic source case."""

from __future__ import annotations

import pytest

from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_occurrence_intervals,
)
from bijux_pollenomics_dev.ci.atlas_browser.sample_chronology.source_rows import (
    feature_from_rows,
)


def _row(identifier: str, younger: str, older: str) -> dict[str, str]:
    return {
        "schema_version": "adna-sample-record-export.v1",
        "genetic_id": identifier,
        "master_id": "original-" + identifier,
        "source_family": "AADR",
        "accession_lineage": "release:v66",
        "locality": "Controlled source locality",
        "political_entity": "Sweden",
        "latitude": "59",
        "longitude": "18",
        "time_label": "literal original source label",
        "time_start_bp": younger,
        "time_end_bp": older,
        "time_mean_bp": str((int(younger) + int(older)) // 2) if younger else "",
        "date_stddev_bp": "3" if younger else "",
        "date_mean_bp": str((int(younger) + int(older)) // 2) if younger else "",
        "dating_basis": "bp_mean_and_stddev" if younger else "archaeological_period",
        "full_date": "literal original source label",
    }


def test_literal_disjoint_and_missing_support_never_becomes_hull_or_zero() -> None:
    feature = feature_from_rows(
        [
            _row("young", "100", "112"),
            _row("old", "300", "312"),
            _row("missing", "", ""),
        ],
        source_path="docs/report/source.csv",
    )
    assert feature_occurrence_intervals(feature) == ((100, 112), (300, 312))
    assert feature["time_start_bp"] == 100
    assert feature["time_end_bp"] == 312
    assert feature["sample_count"] == 3
    dated = feature["sample_chronologies"][0]["chronology"]
    assert dated["precision_posture"] == "sample_precise_interval"
    assert dated["evidence_class"] == "direct_numeric_sample_date"
    missing = feature["sample_chronologies"][2]
    assert missing["chronology"]["time_start_bp"] is None
    assert missing["chronology"]["time_end_bp"] is None
    assert missing["reference_epoch"] == "not_separately_declared"
    assert missing["calibration_status"] == "not_separately_declared"
    assert missing["model"] == "not_separately_declared"
    assert missing["chronology"]["original_text"] == "literal original source label"


@pytest.mark.parametrize(
    "kind",
    [
        "empty",
        "duplicate",
        "mixed_locality",
        "wrong_schema",
        "wrong_family",
        "fractional_age",
        "mismatched_endpoint",
        "mismatched_basis",
        "mismatched_label",
    ],
)
def test_source_parser_refuses_unowned_or_untyped_support(kind: str) -> None:
    rows = [_row("a", "100", "112")]
    if kind == "empty":
        rows = []
    elif kind == "duplicate":
        rows.append(dict(rows[0]))
    elif kind == "mixed_locality":
        rows.append(_row("b", "300", "312"))
        rows[1]["locality"] = "Another source locality"
    elif kind == "wrong_schema":
        rows[0]["schema_version"] = "unknown"
    elif kind == "wrong_family":
        rows[0]["source_family"] = "unadmitted"
    elif kind == "mismatched_endpoint":
        rows[0]["time_end_bp"] = "113"
    elif kind == "mismatched_basis":
        rows[0]["dating_basis"] = "bp_window"
    elif kind == "mismatched_label":
        rows[0]["time_label"] = "unsupported rewritten label"
    else:
        rows[0]["time_start_bp"] = "100.5"
    with pytest.raises(ValueError):
        feature_from_rows(rows, source_path="docs/report/source.csv")
