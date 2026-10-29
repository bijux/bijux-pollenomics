"""Optional Boolean preparation reuses admitted source joins and default account."""

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
from bijux_pollenomics_dev.source_completion.sead import boolean_values as consumer

from .test_boolean_staging import UUID, sources


def install_source(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    component, parent, observation, entity, site, value_class, value_type, _ = sources()
    tables = {
        "tbl_analysis_boolean_values": {3: component},
        "tbl_analysis_values": {2: parent},
        "tbl_value_classes": {8: value_class},
        "tbl_value_types": {3: value_type},
        "tbl_sites": {1: site},
        "tbl_units": {},
    }
    keys = {
        "tbl_analysis_boolean_values": "analysis_boolean_value_id",
        "tbl_analysis_values": "analysis_value_id",
        "tbl_value_classes": "value_class_id",
        "tbl_value_types": "value_type_id",
        "tbl_sites": "site_id",
        "tbl_units": "unit_id",
    }
    digests = {
        name: "parent-digest" if name == "tbl_analysis_values" else name + "-digest"
        for name in tables
    }
    identity = {
        "build_id": SEAD_GOVERNED_BUILD_ID,
        "parent_admission_sha256": SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
        "acquisition_manifest_sha256": SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
    }
    native = {
        **identity,
        "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
        "source_table_sha256": digests,
        "observation_table_counts": {"tbl_analysis_values": 1},
        "component_table_counts": {"tbl_analysis_boolean_values": 1},
        "partitioned_fields": {
            "observations": {"parts": [{"path": "obs.json", "sha256": "obs-digest"}]}
        },
    }
    relations = {
        "source_table_sha256": digests,
        "partitioned_fields": {
            "entity_relations": {
                "parts": [{"path": "entities.json", "sha256": "entities-digest"}]
            }
        },
    }
    docs = {
        "evidence_materialization_manifest.json": {
            **identity,
            "source_run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID,
            "observation_count": 1,
            "files": [
                {"path": name, "sha256": name + "-digest"}
                for name in [
                    "source_native_observations.json",
                    "observation_relation_index.json",
                ]
            ],
        },
        "admission.json": {**identity, "run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID},
        "manifest.json": {},
        "source_native_observations.json": native,
        "observation_relation_index.json": relations,
    }
    parts = {"observations": [observation], "entity_relations": [entity]}
    calls: list[str] = []

    def raw(
        _root: Path, _admission: object, name: str, key: str, digest: str
    ) -> dict[int, dict[str, Any]]:
        assert key == keys[name] and digest == digests[name]
        calls.append(name)
        return deepcopy(tables[name])

    monkeypatch.setattr(
        consumer, "governed_sead_evidence_root", lambda root: root / "normalized"
    )
    monkeypatch.setattr(
        consumer, "_read_object", lambda path, _digest: deepcopy(docs[path.name])
    )
    monkeypatch.setattr(consumer, "_raw_table", raw)
    monkeypatch.setattr(
        consumer,
        "_parts",
        lambda _root, _files, _doc, field: iter(deepcopy(parts[field])),
    )
    return tables, parts, calls


def test_optional_rows_preserve_every_default_report_field_and_readset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, _, calls = install_source(monkeypatch)
    old = consumer.build_report(Path("controlled-data"))
    assert len(calls) == 2 and "typed_staging" not in old
    assert old["boolean_value_states"] == {"false": 1}
    assert old["value_groups"] == [
        {
            "value_class_id": 8,
            "boolean_state": "false",
            "parent_value": "Not dated",
            "row_count": 1,
        }
    ]
    calls.clear()
    stream = io.StringIO()
    current = consumer.build_report(Path("controlled-data"), staging_stream=stream)
    summary = current.pop("typed_staging")
    assert len(calls) == len(set(calls)) == 6
    assert (
        len(current["source_readset_sha256"]) == len(old["source_readset_sha256"]) + 6
    )
    current["source_readset_sha256"] = old["source_readset_sha256"]
    assert current == old
    assert summary["row_count"] == 1
    assert list(csv.DictReader(io.StringIO(stream.getvalue())))[0]["site_uuid"] == UUID


@pytest.mark.parametrize(
    "defect",
    [
        "orphan",
        "missing_entity",
        "duplicate_entity",
        "missing_site",
        "missing_class",
        "missing_type",
        "changed_component",
        "bad_uuid",
    ],
)
def test_optional_source_join_refuses_broken_relations(
    monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    tables, parts, _ = install_source(monkeypatch)
    if defect == "orphan":
        tables["tbl_analysis_boolean_values"][3]["analysis_value_id"] = 99
    if defect == "missing_entity":
        parts["entity_relations"].clear()
    if defect == "duplicate_entity":
        parts["entity_relations"].append(deepcopy(parts["entity_relations"][0]))
    if defect == "missing_site":
        tables["tbl_sites"].clear()
    if defect == "missing_class":
        tables["tbl_value_classes"].clear()
    if defect == "missing_type":
        tables["tbl_value_types"].clear()
    if defect == "changed_component":
        parts["observations"][0]["source_components"]["tbl_analysis_boolean_values"][0][
            "value"
        ] = 0
    if defect == "bad_uuid":
        parts["entity_relations"][0]["site_uuid"] = UUID.upper()
    with pytest.raises(ValueError, match="parent|component|entity|relation"):
        consumer.build_report(Path("controlled-data"), staging_stream=io.StringIO())


def test_absent_component_value_is_explicit_in_optional_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tables, parts, _ = install_source(monkeypatch)
    tables["tbl_analysis_boolean_values"][3].pop("value")
    parts["observations"][0]["source_components"]["tbl_analysis_boolean_values"][0].pop(
        "value"
    )
    stream = io.StringIO()
    report = consumer.build_report(Path("controlled-data"), staging_stream=stream)
    assert report["boolean_value_states"] == {"missing": 1}
    row = list(csv.DictReader(io.StringIO(stream.getvalue())))[0]
    assert row["typed_value_json"] == "" and row["typed_value_parse_state"] == "missing"


@pytest.mark.parametrize(
    "bad", ["same", "outside", "different_parent", "non_csv", "existing", "symlink"]
)
def test_writer_refuses_unsafe_rows_before_source_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, bad: str
) -> None:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    output = artifacts / "report.json"
    rows = artifacts / "values.csv"
    if bad == "same":
        rows = output
    if bad == "outside":
        rows = tmp_path / "values.csv"
    if bad == "different_parent":
        rows = artifacts / "other/values.csv"
    if bad == "non_csv":
        rows = artifacts / "values.json"
    if bad == "existing":
        rows.write_text("user data")
    if bad == "symlink":
        rows.symlink_to(tmp_path / "source.csv")
    monkeypatch.setattr(
        consumer, "build_report", lambda *_args, **_kwargs: pytest.fail("source read")
    )
    with pytest.raises(ValueError, match="CSV|already exists"):
        consumer.run(tmp_path, output, rows_output=rows)
    assert not output.exists()
    if bad == "existing":
        assert rows.read_text() == "user data"


def test_cli_writes_only_two_outputs_and_rechecks_source_integrity(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = tmp_path / "data/raw.json"
    source.parent.mkdir()
    source.write_bytes(b"raw bytes")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()

    def report(_root: Path, *, staging_stream: Any = None) -> dict[str, Any]:
        assert staging_stream is not None
        staging_stream.write("native,data\n")
        return {
            "source_readset_sha256": {"raw.json": digest},
            "typed_staging": {"row_count": 1},
        }

    monkeypatch.setattr(consumer, "build_report", report)
    output = tmp_path / "artifacts/report.json"
    rows = output.with_name("values.csv")
    assert (
        consumer.main(
            [
                "--repository",
                str(tmp_path),
                "--output",
                str(output),
                "--rows-output",
                str(rows),
            ]
        )
        == 0
    )
    assert rows.read_text() == "native,data\n"
    assert json.loads(output.read_text())["typed_staging"]["rows_file"] == "values.csv"
    assert {p.name for p in output.parent.iterdir()} == {"report.json", "values.csv"}
    source.write_bytes(b"changed raw bytes")
    failed = tmp_path / "artifacts/changed/report.json"
    with pytest.raises(ValueError, match="changed before publication"):
        consumer.run(tmp_path, failed, rows_output=failed.with_name("values.csv"))
    assert not failed.exists() and not failed.with_name("values.csv").exists()
