"""Bounded synthetic source custody and complete serialized producer controls."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.author_window_support import (
    study,
)

from .fixtures import protocol, saved_inputs


def setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, dict[str, Any], Path]:
    repository, originals = tmp_path / "repository", tmp_path / "originals"
    profile, path = saved_inputs(repository, originals)
    runner = repository / "owned-source-reader.py"
    runner.write_text("synthetic source-epoch witness")
    monkeypatch.setattr(study, "__file__", str(runner))
    monkeypatch.setattr(
        study,
        "code_state",
        lambda _: {"head": "f" * 40, "index_sha256": "e" * 64, "python_files": {}},
    )
    (repository / "artifacts").mkdir()
    return repository, originals, profile, path


def test_complete_synthetic_serialized_workflow_542_owners_42_windows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, originals, profile, path = setup(tmp_path, monkeypatch)
    output = repository / "artifacts" / "author-source-support"
    result = study.produce(repository, originals, path, output)
    assert result["source_guards_passed"] is True
    assert result["population"]["native_owner_count"] == 542
    assert sum(result["window_status_counts"].values()) == 42
    assert result["engine_calls"] == result["model_fits"] == 0
    assert (
        result["source_acquisition"] is result["scientific_or_field_admission"] is False
    )
    assert set(result["products"]) == {*study.CORE_KEYS, "parameters", "input_manifest"}
    assert {p.name for p in output.iterdir()} == {
        p["path"] for p in result["products"].values()
    } | {"result.json"}
    assert json.loads((output / "result.json").read_bytes()) == result
    for pin in result["products"].values():
        raw = (output / pin["path"]).read_bytes()
        assert (
            len(raw) == pin["bytes"]
            and hashlib.sha256(raw).hexdigest() == pin["sha256"]
        )
    cores = [
        json.loads((output / (key + ".json")).read_bytes()) for key in study.CORE_KEYS
    ]
    assert sum(len(c["samples"]) for c in cores) == 542
    assert len({c["physical_family"] for c in cores}) == 6
    assert cores[3]["physical_family"] == cores[4]["physical_family"]
    assert (
        cores[0]["chronology"]["selected_chronology_id"]
        == cores[0]["chronology"]["native_collection_default_reference"]
    )
    assert len(result["sourcepins"]) == 14
    assert (
        sum(p.stat().st_size for p in tmp_path.rglob("*") if p.is_file()) < 8 * 1024**2
    )
    assert (
        result["cores"]["abborrtjarnen"]["identity"] == profile["cores"][0]["identity"]
    )


@pytest.mark.parametrize(
    "kind",
    [
        "manifest",
        "native_membership",
        "chronology_reference",
        "metadata_country",
        "parameter_identity",
    ],
)
def test_contract_rejects_custody_or_relational_parent_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    repository, originals, profile, _ = setup(tmp_path, monkeypatch)
    key = (
        "raw_manifest"
        if kind in {"manifest", "native_membership"}
        else "chronology_metadata"
        if kind == "chronology_reference"
        else "collection_metadata"
        if kind == "metadata_country"
        else "author_parameter_binding"
    )
    pin = profile["provenance"][key]
    source = repository / pin["path"]
    data = json.loads(source.read_bytes())
    if kind == "manifest":
        source.write_bytes(b"{}")
    else:
        if kind == "native_membership":
            data["parts"][0]["downloaded_dataset_ids"].append(
                profile["cores"][1]["identity"]["dataset_id"]
            )
        elif kind == "chronology_reference":
            data["rows"][0]["selected_by_collection_unit_reference"] = False
        elif kind == "metadata_country":
            data["rows"][0]["country_code"] = "DK"
        else:
            data["inputs"][0]["sha256"] = "0" * 64
        body = json.dumps(data).encode()
        source.write_bytes(body)
        pin.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        if kind == "native_membership":
            baseline_pin = profile["provenance"]["relational_baseline"]
            baseline_path = repository / baseline_pin["path"]
            baseline = json.loads(baseline_path.read_bytes())
            baseline["input_artifacts"]["raw_archive"]["manifest_sha256"] = pin[
                "sha256"
            ]
            raw = json.dumps(baseline).encode()
            baseline_path.write_bytes(raw)
            baseline_pin.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    with pytest.raises(ValueError):
        study.load_contract(repository, originals, profile)


@pytest.mark.parametrize("damage", ["original", "native", "epoch"])
def test_post_projection_source_guards_fail_without_success_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    damage: str,
) -> None:
    repository, originals, profile, path = setup(tmp_path, monkeypatch)
    original_project = study.project
    calls = []

    def project(*args: Any, **kwargs: Any) -> dict[str, Any]:
        result = original_project(*args, **kwargs)
        calls.append(result["key"])
        if len(calls) == 7:
            if damage == "original":
                (originals / profile["author_sources"]["driver"]["path"]).write_bytes(
                    b"changed"
                )
            elif damage == "native":
                (repository / profile["cores"][0]["source"]["path"]).write_bytes(
                    b"changed"
                )
        return result

    monkeypatch.setattr(study, "project", project)
    if damage == "epoch":
        monkeypatch.setattr(
            study,
            "code_state",
            lambda _: {
                "head": "changed" if calls else "f" * 40,
                "index_sha256": "e" * 64,
                "python_files": {},
            },
        )
    output = repository / "artifacts" / "source-refusal"
    with pytest.raises(ValueError, match="identity differs|changed"):
        study.produce(repository, originals, path, output)
    assert len(calls) == 7 and not (output / "result.json").exists()
    assert (output / "parameters.json").exists()


def test_existing_output_and_symlinked_source_are_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, originals, profile, path = setup(tmp_path, monkeypatch)
    output = repository / "artifacts" / "existing"
    output.mkdir()
    (output / "keep").write_text("keep")
    with pytest.raises(ReportRebuildError, match="absent"):
        study.produce(repository, originals, path, output)
    assert (output / "keep").read_text() == "keep"
    pin = profile["author_sources"]["mean"]
    p = originals / pin["path"]
    real = p.with_suffix(".owned")
    p.rename(real)
    p.symlink_to(real)
    with pytest.raises(ValueError, match="alias refused"):
        study.load_contract(repository, originals, profile)


@pytest.mark.parametrize(
    "damage",
    ["owners", "country", "windows", "lookup", "model", "limit", "same_family"],
)
def test_exact_population_and_no_model_scope_cannot_change(damage: str) -> None:
    profile = deepcopy(protocol())
    if damage == "owners":
        profile["population"]["native_owner_count"] = 541
    elif damage == "country":
        profile["cores"][0]["country"] = "Unknown country"
    elif damage == "windows":
        profile["windows"][0][1] = 3199
    elif damage == "lookup":
        profile["author_lookup_contract"]["parameter_targets"] = 31.0
    elif damage == "model":
        profile["model_fits"] = True
    elif damage == "limit":
        profile["limits"]["producer_wall_seconds"] = 91
    else:
        profile["cores"][4]["physical_family"] = "unrelated"
    with pytest.raises(ValueError):
        study.validate_protocol(profile)
