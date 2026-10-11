"""Native boolean type, parent lineage and nonpromotion invariants."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.sead.boolean_values import (
    _boolean_state,
    _reconcile_component,
    run,
)


@pytest.mark.parametrize("value", [0, 1, "true", "false", 1.0])
def test_integer_and_text_substitutions_are_not_native_booleans(value: object) -> None:
    with pytest.raises(ValueError, match="bool or source null"):
        _boolean_state(value)


def test_source_false_and_null_have_distinct_states() -> None:
    assert _boolean_state(True) == "true"
    assert _boolean_state(False) == "false"
    assert _boolean_state(None) == "source_null"


@pytest.mark.parametrize("value", [True, False, None])
def test_parent_display_is_preserved_without_boolean_coercion(value: object) -> None:
    parent = {
        "analysis_value_id": 2,
        "analysis_entity_id": 17,
        "analysis_value": "source display",
    }
    component = {"analysis_boolean_value_id": 1, "analysis_value_id": 2, "value": value}
    observation: dict[str, object] = {
        "source_table": "tbl_analysis_values",
        "source_record_id": "2",
        "entity_relation_id": "sead-analysis-entity:17",
        "source_payload_sha256": "parent-digest",
        "source_row": parent.copy(),
        "source_value_field": "analysis_value",
        "source_value": "source display",
        "source_value_state": "reported",
        "source_components": {"tbl_analysis_boolean_values": [component.copy()]},
        "event_eligibility": "refused",
        "event_refusal_reason_codes": ["source_classification_not_accepted"],
    }
    _reconcile_component(observation, parent, [component], "parent-digest")
    changed = copy.deepcopy(observation)
    components = changed["source_components"]
    assert isinstance(components, dict)
    boolean_rows = components["tbl_analysis_boolean_values"]
    assert isinstance(boolean_rows, list)
    boolean_row = boolean_rows[0]
    assert isinstance(boolean_row, dict)
    boolean_row["value"] = 1 if value else 0
    with pytest.raises(ValueError, match="boolean components differ"):
        _reconcile_component(changed, parent, [component], "parent-digest")
    changed = {**observation, "source_value": True}
    with pytest.raises(ValueError, match="parent observation differs"):
        _reconcile_component(changed, parent, [component], "parent-digest")
    changed = {**observation, "event_eligibility": "eligible"}
    with pytest.raises(ValueError, match="source refusal changed"):
        _reconcile_component(changed, parent, [component], "parent-digest")


def test_boolean_parent_entity_relation_must_match_raw_parent() -> None:
    parent = {
        "analysis_value_id": 2,
        "analysis_entity_id": 17,
        "analysis_value": "source display",
    }
    component = {"analysis_boolean_value_id": 1, "analysis_value_id": 2, "value": True}
    observation = {
        "source_table": "tbl_analysis_values",
        "source_record_id": "2",
        "entity_relation_id": "sead-analysis-entity:17",
        "source_payload_sha256": "parent-digest",
        "source_row": parent.copy(),
        "source_value_field": "analysis_value",
        "source_value": "source display",
        "source_value_state": "reported",
        "source_components": {"tbl_analysis_boolean_values": [component.copy()]},
        "event_eligibility": "refused",
        "event_refusal_reason_codes": ["source_classification_not_accepted"],
    }
    _reconcile_component(observation, parent, [component], "parent-digest")
    for relation in ("sead-analysis-entity:999", "sead-analysis-entity:017", None):
        with pytest.raises(ValueError, match="parent observation differs"):
            _reconcile_component(
                {**observation, "entity_relation_id": relation},
                parent,
                [component],
                "parent-digest",
            )
    for entity_id in (True, 0, -17, "17"):
        with pytest.raises(ValueError, match="parent entity key is invalid"):
            _reconcile_component(
                observation,
                {**parent, "analysis_entity_id": entity_id},
                [component],
                "parent-digest",
            )


def test_report_destination_cannot_overwrite_or_escape(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    existing = artifacts / "report.json"
    existing.write_bytes(b"user bytes")
    with pytest.raises(ValueError, match="already exists"):
        run(tmp_path, existing)
    assert existing.read_bytes() == b"user bytes"
    with pytest.raises(ValueError, match="artifact file"):
        run(tmp_path, tmp_path / "report.json")
    link = artifacts / "linked"
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="artifact file"):
        run(tmp_path, link / "report.json")
