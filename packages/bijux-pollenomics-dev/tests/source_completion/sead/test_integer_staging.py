"""Native integer preparation preserves individual values and source relations."""

from __future__ import annotations

from copy import deepcopy
import csv
import io
import json
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion import sead_analysis_integer_values as core
from bijux_pollenomics_dev.source_completion.sead import integer_staging as stage

UUID = "3d50fd2b-c1b1-4a45-b8ad-70ed033919a0"


def sources(
    value: object = -1500, display: object = "-1500"
) -> tuple[dict[str, Any], ...]:
    integer = {
        "analysis_integer_value_id": 3,
        "analysis_value_id": 2,
        "value": value,
        "qualifier": None,
        "is_variant": False,
    }
    parent = {
        "analysis_value_id": 2,
        "analysis_entity_id": 13,
        "value_class_id": 12,
        "analysis_value": display,
    }
    entity = {
        "entity_relation_id": "sead-analysis-entity:13",
        "analysis_entity_id": 13,
        "site_id": 1,
        "site_uuid": UUID,
        "country_code": "SE",
        "sample_group_id": 4,
        "physical_sample_id": 7,
        "dataset_id": 11,
    }
    site = {"site_id": 1, "site_uuid": UUID}
    value_class = {
        "value_class_id": 12,
        "value_type_id": 6,
        "name": "Inferred growth year ≥",
    }
    value_type = {"value_type_id": 6, "name": "Year", "unit_id": 8}
    unit = {"unit_id": 8, "unit_name": "AD"}
    observation = {
        "observation_id": "sead-observation:controlled",
        "source_table": "tbl_analysis_values",
        "source_record_id": "2",
        "source_payload_sha256": "parent-digest",
        "source_row": parent.copy(),
        "source_value_field": "analysis_value",
        "source_value": display,
        "source_value_state": "source_null" if display is None else "reported",
        "source_components": {"tbl_analysis_integer_values": [integer.copy()]},
        "entity_relation_id": entity["entity_relation_id"],
        "country_code": "SE",
        "event_eligibility": "refused",
        "event_refusal_reason_codes": ["source_classification_not_accepted"],
        "source_semantics": {
            "dataset_semantics_id": "sead-dataset:11",
            "value_semantics_id": "sead-value-class:12",
            "source_unit_id": 8,
            "unit_status": "source_native_linked",
        },
        "chronology_link": {
            "status": "direct_analysis_entity_context_only",
            "eligible_claim_count": 0,
        },
    }
    return integer, parent, observation, entity, site, value_class, value_type, unit


def project(arguments: tuple[dict[str, Any], ...]) -> dict[str, Any]:
    integer, parent, observation, entity, site, value_class, value_type, unit = (
        arguments
    )
    return stage.project_row(
        integer,
        parent,
        observation,
        entity,
        site,
        value_class,
        value_type,
        core._value_states(integer, parent),
        unit,
    )


def test_signed_values_and_native_units_do_not_become_selected_dates() -> None:
    arguments = sources()
    before = deepcopy(arguments)
    row = project(arguments)
    assert arguments == before
    assert row["typed_value_json"] == row["parent_numeric_value"] == "-1500"
    assert (
        row["site_uuid"] == UUID
        and row["component_id"] == "sead-analysis-integer-value:3"
    )
    assert row["parent_value_json"] == '"-1500"'
    assert row["source_unit_id"] == 8 and row["source_unit_name"] == "AD"
    assert row["unit_status"] == "source_native_linked"
    assert row["event_eligibility"] == "refused"
    assert row["chronology_link_status"] == "direct_analysis_entity_context_only"
    assert row["qualifier_json"] == "null" and row["is_variant_json"] == "false"


@pytest.mark.parametrize("display", ["<5", "~30", "~ 30", "NaN", "Infinity", ""])
def test_qualified_or_nonfinite_display_never_overwrites_native_integer(
    display: str,
) -> None:
    row = project(sources(5, display))
    assert row["typed_value_json"] == "5"
    assert json.loads(row["parent_value_json"]) == display
    assert row["parent_parse_state"] == "parse_failed"
    assert (
        row["value_comparison"] == "not_comparable"
        and row["parent_numeric_value"] == ""
    )


@pytest.mark.parametrize(
    "value,display",
    [
        (1402787, "1402786.9999999995"),
        (8123376, "8123376.000000006"),
        (7135442, "7135441.9999999935"),
        (7687001, "7687001.000000004"),
        (2810528, "2810528.0000000005"),
    ],
)
def test_five_original_precision_differences_remain_exact(
    value: int, display: str
) -> None:
    row = project(sources(value, display))
    assert row["typed_value_json"] == str(value)
    assert row["parent_numeric_value"] == display
    assert row["value_comparison"] == "numeric_difference"


def test_source_null_and_missing_flags_stay_distinct() -> None:
    arguments = sources(None, None)
    del arguments[0]["qualifier"]
    arguments[0]["is_variant"] = None
    arguments[2]["source_components"]["tbl_analysis_integer_values"] = [
        arguments[0].copy()
    ]
    row = project(arguments)
    assert (
        row["typed_value_json"]
        == row["parent_value_json"]
        == row["is_variant_json"]
        == "null"
    )
    assert (
        row["typed_value_state"]
        == row["parent_value_state"]
        == row["is_variant_state"]
        == "source_null"
    )
    assert row["qualifier_json"] == "" and row["qualifier_state"] == "missing"
    assert row["parent_parse_state"] == "source_null"
    assert (
        row["parent_numeric_value"] == ""
        and row["value_comparison"] == "not_comparable"
    )


@pytest.mark.parametrize("field", ["value", "analysis_value"])
def test_missing_required_values_refuse_instead_of_becoming_null(field: str) -> None:
    arguments = sources()
    del arguments[0 if field == "value" else 1][field]
    with pytest.raises(ValueError, match="source value is missing"):
        project(arguments)


@pytest.mark.parametrize("value", [True, False, 1.0, "1"])
def test_native_typed_integer_cannot_be_coerced(value: object) -> None:
    with pytest.raises(ValueError, match="typed integer"):
        project(sources(value, "1"))


@pytest.mark.parametrize(
    "mutation",
    [
        "foreign_uuid",
        "uppercase_uuid",
        "entity",
        "parent",
        "class",
        "dataset",
        "boolean_key",
        "unit",
        "refusal",
        "boolean_alias",
    ],
)
def test_foreign_identity_or_native_type_substitution_refuses(mutation: str) -> None:
    arguments = sources()
    integer, _, observation, entity, site, value_class, _, unit = arguments
    if mutation == "foreign_uuid":
        site["site_uuid"] = "7d559aea-e1ac-4df2-aea2-df1d03a9f44a"
    elif mutation == "uppercase_uuid":
        site["site_uuid"] = entity["site_uuid"] = UUID.upper()
    elif mutation == "entity":
        entity["analysis_entity_id"] = 14
    elif mutation == "parent":
        integer["analysis_value_id"] = 10
    elif mutation == "class":
        value_class["value_class_id"] = 18
    elif mutation == "dataset":
        entity["dataset_id"] = 12
    elif mutation == "boolean_key":
        site["site_id"] = True
    elif mutation == "unit":
        unit["unit_id"] = 9
    elif mutation == "refusal":
        observation["event_eligibility"] = "eligible"
    else:
        integer["is_variant"] = 0  # Python False == 0 cannot authenticate source types.
    with pytest.raises(ValueError, match="UUID|key|relation|unit|source or refusal"):
        project(arguments)


def test_uninterpreted_native_flags_survive_csv_without_full_raw_row_copies() -> None:
    arguments = sources(5, "5")
    arguments[0]["qualifier"] = "source qualifier, unclassified\nline"
    arguments[0]["is_variant"] = "native flag"
    arguments[2]["source_components"]["tbl_analysis_integer_values"] = [
        arguments[0].copy()
    ]
    stream = io.StringIO(newline="")
    writer = stage.IntegerStagingWriter(stream)
    writer.write_row(project(arguments))
    rows = list(csv.DictReader(io.StringIO(stream.getvalue())))
    assert len(rows) == 1
    assert json.loads(rows[0]["qualifier_json"]) == arguments[0]["qualifier"]
    assert json.loads(rows[0]["is_variant_json"]) == "native flag"
    assert rows[0]["site_uuid"] == UUID
    assert not any(
        "source_row" in name or "sha256" in name or "parser" in name
        for name in stage.CSV_FIELDS
    )
    summary = writer.summary(
        1, {"tbl_sites": "site-digest", "tbl_units": "unit-digest"}
    )
    assert summary["csv_byte_count"] == len(stream.getvalue().encode())
    assert summary["relationship_review_ledgers"] == {
        "duplicate_component_keys": [],
        "orphan_components": [],
        "missing_entity_parents": [],
        "missing_site_parents": [],
        "fan_out_parents": [],
    }


@pytest.mark.parametrize("duplicate", ["component", "parent"])
def test_stream_refuses_duplicate_and_fan_out_rows(duplicate: str) -> None:
    writer = stage.IntegerStagingWriter(io.StringIO())
    row = project(sources())
    writer.write_row(row)
    if duplicate == "parent":
        row["analysis_integer_value_id"] = 4
    with pytest.raises(ValueError, match="duplicate|fan-out"):
        writer.write_row(row)


def test_output_budget_stops_before_publishing_an_over_budget_row(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stream = io.StringIO()
    writer = stage.IntegerStagingWriter(stream)
    before = stream.getvalue()
    monkeypatch.setattr(stage, "MAX_CSV_BYTES", writer.byte_count + 2)
    with pytest.raises(ValueError, match="32 MiB"):
        writer.write_row(project(sources()))
    assert stream.getvalue() == before and not writer.identities
