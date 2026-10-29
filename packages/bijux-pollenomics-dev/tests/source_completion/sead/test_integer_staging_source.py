"""Source joins and CLI publication preserve native integer preparation scope."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
import csv
import importlib.util
import io
import json
from pathlib import Path
import runpy
import sys
from typing import Any

import pytest

from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_ACQUISITION_MANIFEST_SHA256,
    SEAD_GOVERNED_BUILD_ID,
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_PARENT_ADMISSION_SHA256,
)
from bijux_pollenomics_dev.source_completion import sead_analysis_integer_values as core
from bijux_pollenomics_dev.source_completion.sead import integer_values as adapter

from .test_integer_staging import UUID, sources


def install_source(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    integer, parent, observation, entity, site, value_class, value_type, unit = (
        sources()
    )
    tables = {
        "tbl_analysis_integer_values": [integer],
        "tbl_analysis_values": [parent],
        "tbl_value_classes": [value_class],
        "tbl_value_types": [value_type],
        "tbl_sites": [site],
        "tbl_units": [unit],
    }
    keys = {
        "tbl_analysis_integer_values": "analysis_integer_value_id",
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
    manifest = {
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
    }
    docs = {
        "evidence_materialization_manifest.json": manifest,
        "admission.json": {**identity, "run_id": SEAD_GOVERNED_EVIDENCE_RUN_ID},
        "source_native_observations.json": {"source_table_sha256": digests},
        "observation_relation_index.json": {
            "source_table_sha256": digests,
            "source_table_counts": {name: len(rows) for name, rows in tables.items()},
        },
    }
    calls: list[str] = []

    def raw(
        _root: Path, _admission: object, name: str, key: str, digest: str
    ) -> dict[int, dict[str, Any]]:
        assert key == keys[name] and digest == digests[name]
        calls.append(name)
        return {row[key]: deepcopy(row) for row in tables[name]}

    semantic = {
        "value_class": value_class,
        "source_value_type": value_type,
        "value_semantics_id": "sead-value-class:12",
        "source_unit": unit,
    }
    parts = {
        "observations": [observation],
        "entity_relations": [entity],
        "value_semantics": [semantic],
    }
    monkeypatch.setattr(
        core, "governed_sead_evidence_root", lambda root: root / "normalized"
    )
    monkeypatch.setattr(
        core, "_read_object", lambda path, _digest: deepcopy(docs[path.name])
    )
    monkeypatch.setattr(core, "_raw_table", raw)
    monkeypatch.setattr(
        core, "_parts", lambda _root, _files, _doc, field: iter(deepcopy(parts[field]))
    )
    return calls


def test_optional_stream_reuses_single_source_scan_and_preserves_default_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = install_source(monkeypatch)
    original = core.build_report(Path("controlled-data"))
    assert (
        "typed_staging" not in original
        and original["public_consumer"]["typed_component_exposed"] is False
    )
    assert len(calls) == len(set(calls)) == 4
    calls.clear()
    stream = io.StringIO()
    current = core.build_report(Path("controlled-data"), staging_stream=stream)
    summary = current.pop("typed_staging")
    assert current == original
    assert len(calls) == len(set(calls)) == 6
    assert summary["row_count"] == summary["distinct_component_primary_keys"] == 1
    assert list(csv.DictReader(io.StringIO(stream.getvalue())))[0]["site_uuid"] == UUID


@pytest.mark.parametrize("bad", ["outside", "report", "not_csv", "sibling"])
def test_cli_refuses_unsafe_csv_without_running_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, bad: str
) -> None:
    data = tmp_path / "data"
    data.mkdir()
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    output = artifacts / "integer-values"
    rows = {
        "outside": tmp_path / "values.csv",
        "report": output / "report.json",
        "not_csv": output / "values.json",
        "sibling": artifacts / "values.csv",
    }[bad]
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "integer",
            "--data-root",
            str(data),
            "--output",
            str(output),
            "--rows-output",
            str(rows),
        ],
    )
    with pytest.raises(ValueError, match="CSV"):
        core.main()
    assert not output.exists()


def test_cli_passes_optional_rows_to_existing_producer_and_restores_arguments(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from types import SimpleNamespace

    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda _name: SimpleNamespace(origin=str(tmp_path / adapter.CORE_PATH)),
    )
    calls: list[list[str]] = []
    monkeypatch.setattr(
        runpy,
        "run_module",
        lambda *_args, **_kwargs: calls.append(list(sys.argv)),
    )
    original = sys.argv
    output = tmp_path / "artifacts/integer-values"
    adapter.main(
        [
            "--repository",
            str(tmp_path),
            "--output",
            str(output),
            "--rows-output",
            str(output / "values.csv"),
        ]
    )
    assert calls[0][-2:] == ["--rows-output", str(output / "values.csv")]
    assert sys.argv is original


@pytest.mark.parametrize(
    "broken", ["orphan_component", "missing_entity", "missing_site", "foreign_unit"]
)
def test_producer_refuses_broken_source_relations_before_qualified_report(
    monkeypatch: pytest.MonkeyPatch, broken: str
) -> None:
    install_source(monkeypatch)
    original_raw: Callable[..., dict[int, dict[str, Any]]] = vars(core)["_raw_table"]
    original_parts = vars(core)["_parts"]

    def raw(*args: Any, **kwargs: Any) -> dict[int, dict[str, Any]]:
        result = original_raw(*args, **kwargs)
        if broken == "orphan_component" and args[2] == "tbl_analysis_integer_values":
            result[3]["analysis_value_id"] = 999
        if broken == "missing_site" and args[2] == "tbl_sites":
            result[1]["site_id"] = 999
            result = {999: result[1]}
        return result

    def parts(*args: Any, **kwargs: Any) -> Any:
        rows = list(original_parts(*args, **kwargs))
        if broken == "missing_entity" and args[3] == "entity_relations":
            return iter(())
        if broken == "foreign_unit" and args[3] == "value_semantics":
            rows[0]["source_unit"]["unit_name"] = "different source unit"
        return iter(rows)

    monkeypatch.setattr(core, "_raw_table", raw)
    monkeypatch.setattr(core, "_parts", parts)
    with pytest.raises(
        ValueError, match="parent keys|entity relation|site parent|unit relation"
    ):
        core.build_report(Path("controlled-data"), staging_stream=io.StringIO())


def test_optional_cli_writes_one_streamed_csv_and_existing_report_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    install_source(monkeypatch)
    data = tmp_path / "data"
    data.mkdir()
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    output = artifacts / "integer-values"
    rows = output / "values.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "integer",
            "--data-root",
            str(data),
            "--output",
            str(output),
            "--rows-output",
            str(rows),
        ],
    )
    core.main()
    assert {path.name for path in output.iterdir()} == {"values.csv", "report.json"}
    report = json.loads((output / "report.json").read_text())
    assert report["typed_staging"]["rows_file"] == "values.csv"
    assert report["typed_staging"]["csv_byte_count"] == rows.stat().st_size
    assert report["public_consumer"]["typed_component_exposed"] is False
    assert report["event_admission_status"] == "refused"
    with rows.open(newline="") as stream:
        parsed = list(csv.DictReader(stream))
    assert len(parsed) == 1 and parsed[0]["site_uuid"] == UUID
    with pytest.raises(ValueError, match="already exists"):
        core.main()
