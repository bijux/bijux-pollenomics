"""Source-native SEAD analysis-value component closure and refusal checks."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.sead import (
    analysis_value_components as core,
)


def _fixture() -> tuple[
    dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]
]:
    tables: dict[str, list[dict[str, Any]]] = {name: [] for name in core.TABLE_KEYS}
    tables["tbl_sites"] = [{"site_id": 1, "site_uuid": "site-uuid"}]
    tables["tbl_sample_groups"] = [{"sample_group_id": 2, "site_id": 1}]
    tables["tbl_physical_samples"] = [{"physical_sample_id": 3, "sample_group_id": 2}]
    tables["tbl_analysis_entities"] = [
        {"analysis_entity_id": 4, "physical_sample_id": 3}
    ]
    tables["tbl_analysis_values"] = [
        {
            "analysis_value_id": 5,
            "analysis_entity_id": 4,
            "value_class_id": 6,
            "analysis_value": "12",
        },
        {
            "analysis_value_id": 7,
            "analysis_entity_id": 4,
            "value_class_id": 6,
            "analysis_value": "native text",
        },
    ]
    tables["tbl_analysis_integer_values"] = [
        {"analysis_integer_value_id": 8, "analysis_value_id": 5, "value": 12}
    ]
    tables["tbl_value_classes"] = [
        {"value_class_id": 6, "value_type_id": 9, "name": "Source class"}
    ]
    tables["tbl_value_types"] = [
        {"value_type_id": 9, "unit_id": None, "name": "Source type"}
    ]
    decisions = [
        {
            "site_id": 1,
            "site_uuid": "site-uuid",
            "governed_country_code": "SE",
            "decision": {
                "decision_status": "assigned",
                "decision_method": "strict_boundary_containment",
            },
        }
    ]
    observations = []
    for parent in tables["tbl_analysis_values"]:
        parent_id = parent["analysis_value_id"]
        observations.append(
            {
                "source_table": "tbl_analysis_values",
                "source_record_id": str(parent_id),
                "source_payload_sha256": "parent-digest",
                "source_row": copy.deepcopy(parent),
                "source_value": parent["analysis_value"],
                "source_value_state": "reported",
                "source_components": {
                    table: copy.deepcopy(tables[table])
                    if parent_id == 5 and table == "tbl_analysis_integer_values"
                    else []
                    for table in core.KINDS
                },
                "entity_relation_id": "sead-analysis-entity:4",
                "country_code": "SE",
                "source_semantics": {
                    "value_semantics_id": "sead-value-class:6",
                    "source_unit_id": None,
                    "unit_status": "not_exposed_by_relation",
                },
                "event_eligibility": "refused",
                "event_refusal_reason_codes": ["source_classification_not_accepted"],
            }
        )
    return tables, decisions, observations


def test_typed_and_untyped_parents_close_without_measure_inference() -> None:
    tables, decisions, observations = _fixture()
    rows, summary, total = core._source_rows(
        tables, decisions, observations, "parent-digest"
    )
    assert total == 2
    assert summary["parent_count"] == 2
    assert summary["typed_parent_count"] == 1
    assert summary["untyped_parent_count"] == 1
    assert summary["component_counts"] == {"integer": 1, "untyped_source_text": 1}
    assert {(row["component_kind"], row["parent_count"]) for row in rows} == {
        ("integer", 1),
        ("untyped_source_text", 1),
    }
    assert {row["source_unit_id"] for row in rows} == {None}
    assert {row["country_code"] for row in rows} == {"SE"}


@pytest.mark.parametrize(
    "change", ["overlap", "orphan", "duplicate_key", "boolean_key"]
)
def test_component_relation_refuses_invalid_keys(change: str) -> None:
    tables, decisions, observations = _fixture()
    if change == "overlap":
        tables["tbl_analysis_boolean_values"] = [
            {"analysis_boolean_value_id": 1, "analysis_value_id": 5, "value": True}
        ]
    elif change == "orphan":
        tables["tbl_analysis_integer_values"][0]["analysis_value_id"] = 999
    elif change == "duplicate_key":
        tables["tbl_analysis_integer_values"].append(
            copy.deepcopy(tables["tbl_analysis_integer_values"][0])
        )
    else:
        tables["tbl_analysis_integer_values"][0]["analysis_value_id"] = True
    with pytest.raises(ValueError, match="component|duplicate|invalid"):
        core._source_rows(tables, decisions, observations, "parent-digest")


@pytest.mark.parametrize(
    "change",
    [
        "missing_parent",
        "duplicate_parent",
        "component_substitution",
        "country",
        "unit",
        "event",
    ],
)
def test_parent_and_source_semantics_refuse_drift(change: str) -> None:
    tables, decisions, observations = _fixture()
    if change == "missing_parent":
        observations.pop()
    elif change == "duplicate_parent":
        observations.append(copy.deepcopy(observations[0]))
    elif change == "component_substitution":
        observations[0]["source_components"]["tbl_analysis_integer_values"][0][
            "value"
        ] = True
    elif change == "country":
        observations[0]["country_code"] = "DK"
    elif change == "unit":
        observations[0]["source_semantics"]["unit_status"] = "source_native_linked"
    else:
        observations[0]["event_eligibility"] = "eligible"
    with pytest.raises(ValueError, match="population|repeats|component|lineage"):
        core._source_rows(tables, decisions, observations, "parent-digest")


def test_linked_native_unit_is_not_transformed() -> None:
    tables, decisions, observations = _fixture()
    tables["tbl_value_types"][0]["unit_id"] = 10
    tables["tbl_units"] = [{"unit_id": 10, "unit_name": "native source unit"}]
    for observation in observations:
        observation["source_semantics"]["source_unit_id"] = 10
        observation["source_semantics"]["unit_status"] = "source_native_linked"
    rows, summary, _ = core._source_rows(
        tables, decisions, observations, "parent-digest"
    )
    assert summary["unit_status_counts"] == {"source_native_linked": 2}
    assert {row["source_unit_name"] for row in rows} == {"native source unit"}
    observations[0]["source_semantics"]["source_unit_id"] = 10.0
    with pytest.raises(ValueError, match="lineage"):
        core._source_rows(tables, decisions, observations, "parent-digest")


def test_absent_artifact_boundary_refuses_existing_or_escape(tmp_path: Path) -> None:
    (tmp_path / "artifacts").mkdir()
    outside = tmp_path / "outside"
    with pytest.raises(RuntimeError, match="artifact"):
        core.run(tmp_path, outside)
    existing = tmp_path / "artifacts" / "existing"
    existing.write_text("user bytes")
    with pytest.raises(RuntimeError, match="absent"):
        core.run(tmp_path, existing)
    assert existing.read_text() == "user bytes"


def test_source_change_before_publication_leaves_destination_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "artifacts").mkdir()
    source = tmp_path / "input.json"
    expected = hashlib.sha256(b"original").hexdigest()
    source.write_bytes(b"changed")
    report: dict[str, Any] = {"source_readset_sha256": {"input.json": expected}}
    monkeypatch.setattr(core, "build_report", lambda _repository: (report, b"rows\n"))
    output = tmp_path / "artifacts" / "products"
    with pytest.raises(ValueError, match="changed before publication"):
        core.run(tmp_path, output)
    assert not output.exists()
    assert not output.with_name("products.stage").exists()
