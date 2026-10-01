"""Source continuity and refusal checks for SEAD numerical analysis values."""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.sead_analysis_numerical_values import (
    _read_object,
    _reconcile_component,
    _value_states,
    build_report,
)


def test_source_precision_is_preserved_without_replacing_parent_text() -> None:
    numerical = {"value": 3.90122}
    parent = {"analysis_value": "3.9012199999999995"}

    assert _value_states(numerical, parent) == (
        "reported",
        "reported",
        "parsed_numeric",
        "precision_difference",
    )
    assert parent["analysis_value"] == "3.9012199999999995"
    assert _value_states({"value": None}, {"analysis_value": "bad"}) == (
        "source_null",
        "reported",
        "parse_failed",
        "not_comparable",
    )


def test_changed_raw_component_and_parent_are_refused() -> None:
    numerical = {"analysis_numerical_value_id": 1, "analysis_value_id": 2, "value": 1.5}
    parent = {"analysis_value_id": 2, "analysis_value": "1.5"}
    observation = {
        "source_table": "tbl_analysis_values",
        "source_record_id": "2",
        "source_payload_sha256": "parent-digest",
        "source_row": parent.copy(),
        "source_value_field": "analysis_value",
        "source_value": "1.5",
        "source_value_state": "reported",
        "source_components": {"tbl_analysis_numerical_values": [numerical.copy()]},
        "event_eligibility": "refused",
        "event_refusal_reason_codes": ["source_classification_not_accepted"],
    }
    _reconcile_component(observation, numerical, parent, "parent-digest")

    with pytest.raises(ValueError, match="numerical component differs"):
        _reconcile_component(
            observation, {**numerical, "value": 2.5}, parent, "parent-digest"
        )
    with pytest.raises(ValueError, match="parent observation differs"):
        _reconcile_component(
            observation, numerical, {**parent, "analysis_value": "2"}, "parent-digest"
        )
    observation["event_eligibility"] = "eligible"
    with pytest.raises(ValueError, match="source refusal changed"):
        _reconcile_component(observation, numerical, parent, "parent-digest")


def test_digest_reader_refuses_changed_raw_bytes(tmp_path: Path) -> None:
    path = tmp_path / "source.json"
    original = b'{"rows": []}'
    path.write_bytes(original + b" ")

    with pytest.raises(ValueError, match="source digest differs"):
        _read_object(path, hashlib.sha256(original).hexdigest())


def test_governed_numerical_export_reconciles_all_source_rows() -> None:
    repository = Path(__file__).resolve().parents[4]
    report, text = build_report(repository / "data")
    rows = list(csv.DictReader(io.StringIO(text)))

    assert report["numerical_value_count"] == len(rows) == 60
    assert report["parent_analysis_value_count"] == 60
    assert report["source_observation_denominator"] == 177763
    assert report["value_comparison_counts"] == {
        "numeric_equal": 43,
        "precision_difference": 17,
    }
    assert report["eligible_event_count"] == 0
    assert report["value_class_count"] == 9
    assert report["value_type_count"] == 2
    assert {item["source_unit_id"] for item in report["value_classes"]} == {None}
    assert sum(item["row_count"] for item in report["value_classes"]) == 60
    assert {row["event_eligibility"] for row in rows} == {"refused"}
    assert {row["value_type_name"] for row in rows} == {"Measurement", "Percentage"}
    assert {row["value_type_unit_id"] for row in rows} == {""}
    assert len({row["analysis_numerical_value_id"] for row in rows}) == 60
    assert len({row["analysis_value_id"] for row in rows}) == 60
    assert len({row["physical_sample_id"] for row in rows}) == 5
    assert len({row["dataset_id"] for row in rows}) == 10
    assert {row["site_id"] for row in rows} == {"6486"}
    assert report["values_csv_sha256"] == hashlib.sha256(text.encode()).hexdigest()
