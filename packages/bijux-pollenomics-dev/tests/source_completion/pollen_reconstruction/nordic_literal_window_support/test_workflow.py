"""Pin custody and source-epoch controls without opening real native counts."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.literal_window_support import (
    study,
)


def source_fixture(repository: Path) -> tuple[dict[str, Any], Path]:
    source = Path(__file__).resolve().parents[6]
    protocol = json.loads(
        (
            source
            / "reports/science/pollen-reconstruction/nordic-literal-window-support/protocol.json"
        ).read_text()
    )

    def store(relative: str, value: Any) -> dict[str, Any]:
        body = json.dumps(value).encode()
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        return {
            "path": relative,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }

    for core in protocol["cores"]:
        core["source"] = store(core["source"]["path"], {"rows": []})
    manifest = {
        "parts": [
            {
                "filename": Path(core["source"]["path"]).name,
                "downloaded_dataset_ids": [core["identity"]["dataset_id"]],
            }
            for core in protocol["cores"]
        ]
    }
    protocol["provenance"]["raw_manifest"] = store("manifest.json", manifest)
    baseline = {
        "input_artifacts": {
            "raw_archive": {
                "path": "data/neotoma/raw/neotoma_pollen_dataset_downloads",
                "manifest_sha256": protocol["provenance"]["raw_manifest"]["sha256"],
                "part_sha256": {
                    Path(core["source"]["path"]).name: core["source"]["sha256"]
                    for core in protocol["cores"]
                },
            }
        }
    }
    protocol["provenance"]["relational_baseline"] = store("baseline.json", baseline)
    policy = {
        "schema_version": "krageholm-regional-literal-panel-protocol.v1",
        "taxa": protocol["taxa"],
        "windows": protocol["windows"],
        **{key: "source-bound " + key for key in study.INHERITED},
    }
    protocol["provenance"]["literal_policy"] = store("policy.json", policy)
    path = repository / "protocol.json"
    path.write_text(json.dumps(protocol))
    return protocol, path


def test_contract_binds_exact_manifest_population_and_inherited_policy(
    tmp_path: Path,
) -> None:
    protocol, _ = source_fixture(tmp_path)
    expected = deepcopy(protocol)
    contract = study.load_contract(tmp_path, protocol)
    assert protocol == expected
    assert all(contract[key] == "source-bound " + key for key in study.INHERITED)
    manifest = protocol["provenance"]["raw_manifest"]
    (tmp_path / manifest["path"]).write_bytes(b"{}")
    with pytest.raises(ValueError, match="identity differs"):
        study.load_contract(tmp_path, protocol)


@pytest.mark.parametrize("damage", [None, "native_source", "code_epoch"])
def test_workflow_rechecks_native_sources_and_consumed_epoch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str | None
) -> None:
    protocol, path = source_fixture(tmp_path)
    (tmp_path / "artifacts").mkdir()
    output = tmp_path / "artifacts" / "source-support"
    calls: list[str] = []

    def project(
        native: dict[str, Any], core: dict[str, Any], contract: dict[str, Any]
    ) -> dict[str, Any]:
        assert native == {"rows": []}
        assert contract["suppression_semantics"] == "source-bound suppression_semantics"
        calls.append(core["key"])
        if damage == "native_source" and len(calls) == 1:
            (tmp_path / core["source"]["path"]).write_text('{"changed":true}')
        return {"key": core["key"], "engine_calls": 0}

    def state(*_: Any) -> dict[str, Any]:
        changed = damage == "code_epoch" and bool(calls)
        return {
            "head": "changed" if changed else "source",
            "index_sha256": "index",
            "python_files": {},
        }

    monkeypatch.setattr(study, "project", project)
    monkeypatch.setattr(study, "code_state", state)
    if damage is not None:
        with pytest.raises(ValueError, match="identity differs|changed"):
            study.produce(tmp_path, path, output)
        assert not (output / "result.json").exists()
    else:
        result = study.produce(tmp_path, path, output)
        assert calls == ["laihalampi", "dalmutladdo"]
        assert result["source_guards_passed"] is True
        assert result["sourcepins"] == [
            protocol["provenance"][key] for key in study.PROVENANCE
        ] + [core["source"] for core in protocol["cores"]]
        assert result["model_fits"] == result["engine_calls"] == 0
        assert set(result["products"]) == set(calls)
        for pin in result["products"].values():
            body = (output / pin["path"]).read_bytes()
            assert hashlib.sha256(body).hexdigest() == pin["sha256"]


def test_workflow_preserves_existing_output(tmp_path: Path) -> None:
    _, path = source_fixture(tmp_path)
    output = tmp_path / "artifacts" / "source-support"
    output.mkdir(parents=True)
    marker = output / "preserve.txt"
    marker.write_text("existing")
    with pytest.raises(ReportRebuildError, match="output must be absent"):
        study.produce(tmp_path, path, output)
    assert marker.read_text() == "existing"
