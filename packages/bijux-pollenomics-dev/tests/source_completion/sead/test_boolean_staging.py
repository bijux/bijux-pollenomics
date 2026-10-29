"""Native flags, declared types and parent display remain distinct preparation facts."""

from __future__ import annotations

from copy import deepcopy
import csv
import io
import json
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.sead import boolean_staging as stage

UUID = "3d50fd2b-c1b1-4a45-b8ad-70ed033919a0"


def sources() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[int, dict[str, Any]],
]:
    """One exact source relation with independently reported display and flag."""
    component = {
        "analysis_boolean_value_id": 3,
        "analysis_value_id": 2,
        "value": False,
        "qualifier": "nära",
    }
    parent = {
        "analysis_value_id": 2,
        "analysis_entity_id": 13,
        "value_class_id": 8,
        "analysis_value": "Not dated",
        "boolean_value": False,
    }
    entity = {
        "entity_relation_id": "sead-analysis-entity:13",
        "analysis_entity_id": 13,
        "site_id": 1,
        "site_uuid": UUID,
        "country_code": "SE",
        "dataset_id": 11,
        "sample_group_id": 4,
        "physical_sample_id": 7,
    }
    observation = {
        "observation_id": "sead-observation:controlled",
        "country_code": "SE",
        "source_table": "tbl_analysis_values",
        "source_record_id": "2",
        "entity_relation_id": "sead-analysis-entity:13",
        "source_payload_sha256": "parent-digest",
        "source_row": deepcopy(parent),
        "source_value_field": "analysis_value",
        "source_value": "Not dated",
        "source_value_state": "reported",
        "source_components": {"tbl_analysis_boolean_values": [deepcopy(component)]},
        "source_semantics": {
            "dataset_semantics_id": "sead-dataset:11",
            "value_semantics_id": "sead-value-class:8",
            "source_unit_id": None,
            "unit_status": "not_exposed_by_relation",
        },
        "chronology_link": {
            "entity_relation_id": "sead-analysis-entity:13",
            "selection_rule": "same_analysis_entity_only",
            "eligible_claim_count": 0,
            "claim_count": 1,
            "status": "direct_analysis_entity_context_only",
        },
        "event_eligibility": "refused",
        "event_refusal_reason_codes": ["source_classification_not_accepted"],
    }
    return (
        component,
        parent,
        observation,
        entity,
        {"site_id": 1, "site_uuid": UUID},
        {"value_class_id": 8, "value_type_id": 3, "name": "Native class"},
        {
            "value_type_id": 3,
            "name": "Boolean",
            "base_type": "boolean",
            "unit_id": None,
        },
        {},
    )


def test_native_false_does_not_become_missing_or_interpreted_display() -> None:
    args = sources()
    before = deepcopy(args)
    row = stage.project_row(*args)
    assert args == before
    assert row["component_id"] == "sead-analysis-boolean-value:3"
    assert row["typed_value_json"] == "false"
    assert row["typed_value_state"] == "reported"
    assert row["typed_value_parse_state"] == "false"
    assert row["parent_value_json"] == '"Not dated"'
    assert row["qualifier_json"] == '"nära"'
    assert row["parent_boolean_comparison"] == "equal_native_boolean"
    assert row["site_uuid"] == UUID
    assert row["event_eligibility"] == "refused" and row["eligible_claim_count"] == 0


@pytest.mark.parametrize(
    "value,parsed", [(True, "true"), (False, "false"), (None, "source_null")]
)
def test_native_boolean_and_source_null_have_exact_states(
    value: object, parsed: str
) -> None:
    args = sources()
    args[0]["value"] = value
    row = stage.project_row(*args)
    assert json.loads(row["typed_value_json"]) is value
    assert row["typed_value_parse_state"] == parsed
    assert row["typed_value_state"] == ("source_null" if value is None else "reported")


@pytest.mark.parametrize("value", [0, 1, 0.0, 1.0, "true", "false", "", [], {}])
def test_integer_text_and_container_substitutions_refuse(value: object) -> None:
    args = sources()
    args[0]["value"] = value
    with pytest.raises(ValueError, match="parse_failed"):
        stage.project_row(*args)


def test_missing_null_and_unreported_parent_are_never_imputed() -> None:
    args = sources()
    args[0].pop("value")
    args[0]["qualifier"] = None
    args[1].pop("boolean_value")
    args[1].pop("analysis_value")
    row = stage.project_row(*args)
    assert row["typed_value_json"] == "" and row["typed_value_parse_state"] == "missing"
    assert row["qualifier_json"] == "null" and row["qualifier_state"] == "source_null"
    assert row["parent_value_state"] == row["parent_boolean_value_state"] == "missing"
    assert row["parent_boolean_comparison"] == "not_both_reported"


def test_native_integer_declaration_does_not_recast_boolean_storage() -> None:
    args = sources()
    args[5]["value_type_id"] = 1
    args[6].update(value_type_id=1, name="Count", base_type="integer")
    row = stage.project_row(*args)
    assert (
        row["value_type_base_type"] == "integer" and row["value_type_name"] == "Count"
    )
    assert row["typed_value_json"] == "false"
    assert row["storage_vs_declared_base_type"] == "boolean_storage_other_declaration"


def test_parent_native_flag_difference_is_preserved_without_repair() -> None:
    args = sources()
    args[1]["boolean_value"] = True
    row = stage.project_row(*args)
    assert (
        row["typed_value_json"] == "false"
        and row["parent_boolean_value_json"] == "true"
    )
    assert row["parent_boolean_comparison"] == "different_native_boolean"
    args[1]["boolean_value"] = 1
    with pytest.raises(ValueError, match="parse_failed"):
        stage.project_row(*args)


@pytest.mark.parametrize(
    "defect",
    [
        "bool_pk",
        "parent",
        "site",
        "uuid_case",
        "entity",
        "dataset",
        "type",
        "unit",
        "chronology",
        "eligible",
    ],
)
def test_exact_native_relations_and_refusals_cannot_be_replaced(defect: str) -> None:
    args = sources()
    if defect == "bool_pk":
        args[0]["analysis_boolean_value_id"] = True
    if defect == "parent":
        args[0]["analysis_value_id"] = 99
    if defect == "site":
        args[4]["site_id"] = 99
    if defect == "uuid_case":
        args[3]["site_uuid"] = UUID.upper()
    if defect == "entity":
        args[3]["entity_relation_id"] = "sead-analysis-entity:013"
    if defect == "dataset":
        args[2]["source_semantics"]["dataset_semantics_id"] = "sead-dataset:99"
    if defect == "type":
        args[6]["value_type_id"] = 99
    if defect == "unit":
        args[6]["unit_id"] = 4
    if defect == "chronology":
        args[2]["chronology_link"]["eligible_claim_count"] = True
    if defect == "eligible":
        args[2]["event_eligibility"] = "eligible"
    with pytest.raises(ValueError, match="staging"):
        stage.project_row(*args)


def test_linked_units_remain_native_and_do_not_imply_ecological_admission() -> None:
    args = sources()
    args[6]["unit_id"] = 4
    args[7][4] = {"unit_id": 4, "unit_name": "native unit"}
    args[2]["source_semantics"].update(
        source_unit_id=4, unit_status="source_native_linked"
    )
    row = stage.project_row(*args)
    assert row["source_unit_id"] == 4 and row["source_unit_name"] == "native unit"
    assert row["event_eligibility"] == "refused"


def test_writer_preserves_fanout_and_csv_values_without_merging_rows() -> None:
    stream = io.StringIO()
    writer = stage.BooleanStagingWriter(stream)
    row = stage.project_row(*sources())
    writer.append(row)
    writer.append(
        {
            **row,
            "analysis_boolean_value_id": 4,
            "component_id": "sead-analysis-boolean-value:4",
        }
    )
    rows = list(csv.DictReader(io.StringIO(stream.getvalue())))
    assert len(rows) == 2 and rows[0]["site_uuid"] == UUID
    assert json.loads(rows[0]["qualifier_json"]) == "nära"
    account = writer.account()
    assert account["row_count"] == account["distinct_component_primary_keys"] == 2
    assert account["distinct_parent_primary_keys"] == 1
    assert account["relationship_review_ledgers"]["fan_out_parents"] == [
        {"analysis_value_id": 2, "component_count": 2}
    ]
    with pytest.raises(ValueError, match="duplicate"):
        writer.append(row)


def test_csv_byte_limit_refuses_before_oversized_row_is_written(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = io.StringIO()
    writer = stage.BooleanStagingWriter(stream)
    header = stream.getvalue()
    monkeypatch.setattr(stage, "MAX_CSV_BYTES", len(header.encode()))
    with pytest.raises(ValueError, match="sixteen MiB"):
        writer.append(stage.project_row(*sources()))
    assert stream.getvalue() == header and writer.account()["row_count"] == 0
