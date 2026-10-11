"""Source continuity and refusal checks for SEAD integer analysis values."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.sead_analysis_integer_values import (
    _reconcile_component,
    _value_states,
    build_report,
)


def test_integer_parent_display_text_keeps_its_own_parse_state() -> None:
    assert _value_states({"value": 30}, {"analysis_value": "~ 30"}) == (
        "reported",
        "parse_failed",
        "not_comparable",
    )
    assert _value_states(
        {"value": 1_402_787}, {"analysis_value": "1402786.9999999995"}
    ) == (
        "reported",
        "parsed_numeric",
        "numeric_difference",
    )
    assert _value_states({"value": None}, {"analysis_value": None}) == (
        "source_null",
        "source_null",
        "not_comparable",
    )
    with pytest.raises(ValueError, match="typed integer"):
        _value_states({"value": True}, {"analysis_value": "1"})


def test_changed_component_parent_and_refusal_are_rejected() -> None:
    integer = {"analysis_integer_value_id": 1, "analysis_value_id": 2, "value": 3}
    parent = {"analysis_value_id": 2, "analysis_value": "3"}
    observation = {
        "source_table": "tbl_analysis_values",
        "source_record_id": "2",
        "source_payload_sha256": "parent-digest",
        "source_row": parent.copy(),
        "source_value_field": "analysis_value",
        "source_value": "3",
        "source_value_state": "reported",
        "source_components": {"tbl_analysis_integer_values": [integer.copy()]},
        "event_eligibility": "refused",
        "event_refusal_reason_codes": ["source_classification_not_accepted"],
    }
    _reconcile_component(observation, integer, parent, "parent-digest")
    with pytest.raises(ValueError, match="integer component differs"):
        _reconcile_component(
            observation, {**integer, "value": 4}, parent, "parent-digest"
        )
    with pytest.raises(ValueError, match="parent observation differs"):
        _reconcile_component(
            observation, integer, {**parent, "analysis_value": "4"}, "parent-digest"
        )
    observation["event_eligibility"] = "eligible"
    with pytest.raises(ValueError, match="source refusal changed"):
        _reconcile_component(observation, integer, parent, "parent-digest")


def test_governed_integer_lineage_reconciles_every_source_component() -> None:
    repository = Path(__file__).resolve().parents[4]
    report = build_report(repository / "data")
    assert (
        report["integer_value_count"] == report["parent_analysis_value_count"] == 24_701
    )
    assert report["source_observation_denominator"] == 177_763
    assert sum(item["row_count"] for item in report["value_classes"]) == 24_701
    assert report["value_comparison_counts"] == {
        "not_comparable": 1763,
        "numeric_difference": 5,
        "numeric_equal": 22933,
    }
    assert report["value_state_counts"] == {
        "parent:reported": 24701,
        "parent_parse:parse_failed": 1763,
        "parent_parse:parsed_numeric": 22938,
        "typed:reported": 24701,
    }
    assert report["chronology_role_counts"] == {
        "inferred_growth_year_bound": 4430,
        "other_source_count": 10763,
        "tree_age_bound": 4757,
        "tree_ring_count": 4751,
    }
    assert {
        item["analysis_integer_value_id"] for item in report["nonmatching_values"]
    } == {
        25786,
        25787,
        25788,
        25789,
        25790,
    }
    assert report["eligible_event_count"] == 0
    assert report["event_admission_status"] == "refused"
