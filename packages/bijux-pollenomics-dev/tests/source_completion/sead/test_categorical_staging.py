"""Usable categorical rows preserve native keys, nulls and relational identity."""

from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
    SEAD_GOVERNED_BUILD_ID,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
)
from bijux_pollenomics_dev.source_completion.sead import (
    categorical_staging as stage,
)
from bijux_pollenomics_dev.source_completion.sead import (
    categorical_values as consumer,
)

from .test_categorical_values import source

UUID = "3d50fd2b-c1b1-4a45-b8ad-70ed033919a0"


def rows() -> tuple[dict[str, Any], ...]:
    parent, component, observation = source()
    observation.update(observation_id="sead-observation:controlled", country_code="SE")
    observation["source_semantics"]["dataset_semantics_id"] = "sead-dataset:11"
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
    return (
        component,
        parent,
        observation,
        entity,
        {"site_id": 1, "site_uuid": UUID},
        {"value_type_item_id": 6, "value_type_id": 13, "name": "W"},
        {"value_class_id": 8, "value_type_id": 13, "name": "Waney edge"},
        {
            "value_type_id": 13,
            "name": "Waney edge",
            "base_type": "category",
            "unit_id": None,
        },
    )


def test_linked_item_never_fills_null_observed_value_or_changes_parent_text() -> None:
    arguments = rows()
    before = deepcopy(arguments)
    result = stage.project_row(*arguments)
    assert arguments == before
    assert result["analysis_categorical_value_id"] == 3
    assert result["component_id"] == "sead-analysis-categorical-value:3"
    assert result["analysis_value_id"] == 2 and result["site_uuid"] == UUID
    assert result["typed_value_json"] == result["is_variant_json"] == "null"
    assert (
        result["typed_value_state"]
        == result["typed_value_parse_state"]
        == "source_null"
    )
    assert result["value_type_item_id"] == 6 and result["item_name_json"] == '"W"'
    assert result["item_key_parse_state"] == "resolved_native_foreign_key"
    assert result["parent_value_json"] == '"source display"'
    assert result["parent_display_vs_item_name"] == "different"
    assert result["event_eligibility"] == "refused"
    assert result["source_unit_id"] is None


@pytest.mark.parametrize(
    "value,state",
    [
        (None, "source_null"),
        (False, "reported"),
        (0, "reported"),
        ("", "reported"),
        ("W?", "reported"),
    ],
)
def test_native_nullable_field_is_not_a_category_label_interpretation(
    value: object, state: str
) -> None:
    arguments = rows()
    arguments[0]["value"] = value
    arguments[0]["is_variant"] = False
    result = stage.project_row(*arguments)
    assert json.loads(result["typed_value_json"]) == value
    assert result["typed_value_state"] == state
    assert result["typed_value_parse_state"] == (
        "source_null" if value is None else "reported_uninterpreted"
    )
    assert (
        result["is_variant_json"] == "false"
        and result["is_variant_state"] == "reported"
    )


def test_missing_field_and_literal_null_are_distinct_without_imputation() -> None:
    arguments = rows()
    arguments[0].pop("value")
    result = stage.project_row(*arguments)
    assert result["typed_value_json"] == "" and result["typed_value_state"] == "missing"
    assert (
        result["is_variant_json"] == "null"
        and result["is_variant_state"] == "source_null"
    )


@pytest.mark.parametrize(
    "defect",
    [
        "bool_pk",
        "parent",
        "site",
        "uuid",
        "uuid_case",
        "entity",
        "dataset",
        "item",
        "class",
        "base_type",
    ],
)
def test_staged_keys_site_uuid_and_source_semantics_cannot_be_substituted(
    defect: str,
) -> None:
    arguments = rows()
    if defect == "bool_pk":
        arguments[0]["analysis_categorical_value_id"] = True
    elif defect == "parent":
        arguments[0]["analysis_value_id"] = 5
    elif defect == "site":
        arguments[3]["site_id"] = 2
    elif defect == "uuid":
        arguments[3]["site_uuid"] = "other"
    elif defect == "uuid_case":
        arguments[3]["site_uuid"] = UUID.upper()
    elif defect == "entity":
        arguments[3]["analysis_entity_id"] = 14
    elif defect == "dataset":
        arguments[3]["dataset_id"] = 12
    elif defect == "item":
        arguments[5]["value_type_item_id"] = 7
    elif defect == "class":
        arguments[6]["value_class_id"] = 9
    else:
        arguments[7]["base_type"] = "text"
    with pytest.raises(ValueError):
        stage.project_row(*arguments)


def test_csv_is_a_stable_component_table_with_explicit_duplicate_refusal() -> None:
    first = stage.project_row(*rows())
    second = dict(
        first,
        analysis_categorical_value_id=1,
        component_id="sead-analysis-categorical-value:1",
    )
    table = list(csv.DictReader(io.StringIO(stage.render_rows([first, second]))))
    assert [r["analysis_categorical_value_id"] for r in table] == ["1", "3"]
    assert table[0]["site_uuid"] == UUID and table[0]["typed_value_json"] == "null"
    with pytest.raises(ValueError, match="duplicate primary key"):
        stage.render_rows([first, first])


def controlled_source(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    component, parent, observation, entity, site, item, value_class, value_type = rows()
    tables = {
        "tbl_analysis_values": {2: parent},
        "tbl_analysis_categorical_values": {3: component},
        "tbl_value_type_items": {6: item},
        "tbl_value_classes": {8: value_class},
        "tbl_value_types": {13: value_type},
        "tbl_units": {},
        "tbl_sites": {1: site},
    }
    digests = {name: "digest-" + name for name in tables}
    observation["source_payload_sha256"] = digests["tbl_analysis_values"]
    files = [
        {"path": p, "sha256": "digest-" + p}
        for p in (
            "source_native_observations.json",
            "observations.json",
            "observation_relation_index.json",
            "entities.json",
        )
    ]
    shared = {
        "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "build_id": SEAD_GOVERNED_BUILD_ID,
        "acquisition_manifest_sha256": SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
        "parent_admission_sha256": SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
    }
    native = {
        **shared,
        "source_table_sha256": digests,
        "observation_table_counts": {"tbl_analysis_values": 1},
        "component_table_counts": {"tbl_analysis_categorical_values": 1},
        "partitioned_fields": {"observations": {"parts": [files[1]]}},
    }
    relations = {
        "source_table_sha256": digests,
        "partitioned_fields": {"entity_relations": {"parts": [files[3]]}},
    }
    documents = {
        "admission.json": shared,
        "manifest.json": {},
        "evidence_materialization_manifest.json": {
            **shared,
            "files": files,
            "observation_count": 1,
        },
        "source_native_observations.json": native,
        "observation_relation_index.json": relations,
    }
    state = {
        "tables": tables,
        "observations": [observation],
        "entities": [entity],
        "native": native,
    }
    monkeypatch.setattr(
        consumer, "governed_sead_evidence_root", lambda root: root / "normalized"
    )
    monkeypatch.setattr(
        consumer, "_read_object", lambda path, digest: documents[path.name]
    )
    monkeypatch.setattr(
        consumer, "_raw_table", lambda raw, admission, table, key, digest: tables[table]
    )
    monkeypatch.setattr(
        consumer,
        "_parts",
        lambda root, files, doc, field: iter(
            state["observations" if field == "observations" else "entities"]
        ),
    )
    return state


def test_optional_table_keeps_the_existing_lineage_report_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    controlled_source(monkeypatch)
    original = consumer.build_report(tmp_path)
    table: list[dict[str, Any]] = []
    extended = consumer.build_report(tmp_path, staging_rows=table)
    summary = extended.pop("typed_staging")
    assert summary["row_count"] == summary["distinct_component_primary_keys"] == 1
    assert summary["relationship_review_ledgers"] == {
        "duplicate_component_keys": [],
        "orphan_components": [],
        "missing_entity_parents": [],
        "missing_site_parents": [],
        "fan_out_parents": [],
    }
    assert (
        len(extended["source_readset_sha256"]) - len(original["source_readset_sha256"])
        == 3
    )
    extended["source_readset_sha256"] = original["source_readset_sha256"]
    assert extended == original
    assert table[0]["site_uuid"] == UUID and table[0]["typed_value_json"] == "null"


@pytest.mark.parametrize(
    "defect",
    [
        "duplicate_entity",
        "missing_entity",
        "missing_site",
        "orphan_component",
        "type_mismatch",
        "site_uuid",
    ],
)
def test_typed_consumer_refuses_orphans_duplicated_joins_and_native_identity_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    state = controlled_source(monkeypatch)
    if defect == "duplicate_entity":
        state["entities"].append(state["entities"][0])
    elif defect == "missing_entity":
        state["entities"].clear()
    elif defect == "missing_site":
        state["tables"]["tbl_sites"].clear()
    elif defect == "orphan_component":
        state["tables"]["tbl_analysis_categorical_values"][3]["analysis_value_id"] = 77
    elif defect == "type_mismatch":
        state["tables"]["tbl_value_type_items"][6]["value_type_id"] = 14
    else:
        state["entities"][0]["site_uuid"] = "other"
    with pytest.raises(ValueError):
        consumer.build_report(tmp_path, staging_rows=[])


def test_one_to_many_parent_relation_is_emitted_as_fan_out_not_collapsed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = controlled_source(monkeypatch)
    component = dict(
        state["tables"]["tbl_analysis_categorical_values"][3],
        analysis_categorical_value_id=4,
    )
    state["tables"]["tbl_analysis_categorical_values"][4] = component
    state["observations"][0]["source_components"][
        "tbl_analysis_categorical_values"
    ].append(component)
    state["native"]["component_table_counts"]["tbl_analysis_categorical_values"] = 2
    table: list[dict[str, Any]] = []
    report = consumer.build_report(tmp_path, staging_rows=table)
    assert len(table) == 2 and report["categorical_parent_count"] == 1
    assert report["typed_staging"]["relationship_review_ledgers"][
        "fan_out_parents"
    ] == [{"analysis_value_id": 2, "component_count": 2}]


@pytest.mark.parametrize("changed", [False, True])
def test_cli_writes_one_usable_table_only_after_raw_integrity_recheck(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed: bool
) -> None:
    data = tmp_path / "data"
    data.mkdir()
    path = data / "source.json"
    raw = b"controlled original source"
    path.write_bytes(raw)

    def build(
        root: Path, *, staging_rows: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        assert root == data and staging_rows == []
        staging_rows.append(stage.project_row(*rows()))
        if changed:
            path.write_bytes(b"changed")
        return {
            "typed_staging": {"parser_rule": stage.PARSER_RULE, "row_count": 1},
            "source_readset_sha256": {"source.json": hashlib.sha256(raw).hexdigest()},
        }

    monkeypatch.setattr(consumer, "build_report", build)
    report = tmp_path / "artifacts" / "categorical" / "report.json"
    csvfile = report.with_name("rows.csv")
    args = [
        "--repository",
        str(tmp_path),
        "--output",
        str(report),
        "--rows-output",
        str(csvfile),
    ]
    if changed:
        with pytest.raises(ValueError, match="changed before publication"):
            consumer.main(args)
        assert not report.exists() and not csvfile.exists()
    else:
        assert consumer.main(args) == 0
        actual = json.loads(report.read_text())
        records = list(csv.DictReader(io.StringIO(csvfile.read_text())))
        assert actual["typed_staging"]["rows_file"] == "rows.csv"
        assert len(records) == 1 and records[0]["typed_value_json"] == "null"


@pytest.mark.parametrize("defect", ["existing", "same", "other_directory", "symlink"])
def test_rows_destination_cannot_overwrite_or_escape_owned_unit(
    tmp_path: Path, defect: str
) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    report = root / "report.json"
    target = root / "rows.csv"
    if defect == "existing":
        target.write_text("user bytes")
    elif defect == "same":
        target = report
    elif defect == "other_directory":
        target = root / "sub" / "rows.csv"
    else:
        target.symlink_to(tmp_path / "outside.csv")
    with pytest.raises(ValueError):
        consumer.run(tmp_path, report, rows_output=target)
    assert not report.exists()
    if defect == "existing":
        assert target.read_text() == "user bytes"
