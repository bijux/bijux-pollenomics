"""Verify retained comparison scope without rerunning captured native vectors."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from bijux_pollenomics_dev.lra_validation.native_reference.annulus_capture import (
    AnnulusCapture,
)
from bijux_pollenomics_dev.lra_validation.native_reference.source_replay import (
    build_source_replay,
)
from bijux_pollenomics_dev.source_completion.method_certification.native_r_comparison import (
    _consumer_inputs,
)

ROOT = Path(__file__).resolve().parents[5]


@pytest.fixture
def reader() -> ModuleType:
    path = (
        ROOT
        / "docs/report/method-certification/current-r-oracle/verify_source_replay.py"
    )
    spec = importlib.util.spec_from_file_location("reader_source_replay", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(params=["annulus", "count-domain"])
def records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    reader: ModuleType,
    request: pytest.FixtureRequest,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    repository = tmp_path / "repository"
    policy_path = ROOT / "configs/ci/report-ownership.json"
    policy = json.loads(policy_path.read_text())
    owner = next(
        row
        for row in policy["owners"]
        if row["owner_id"] == "method-certification/current-r-oracle/report-products"
    )
    profile = request.param
    owner["producer_inputs"] = [
        name.replace("native-r-count-domain/", f"native-r-{profile}/")
        for name in owner["producer_inputs"]
    ]
    for name in owner["producer_paths"] + owner["producer_inputs"]:
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic declared consumer source\n")
    (repository / "configs/ci/report-ownership.json").write_text(
        json.dumps({"owners": [owner]})
    )
    capture = AnnulusCapture(
        repository / "capture",
        repository / "archives",
        "a" * 40,
        "b" * 64,
        (),
        {},
        {},
        {"clean_execution": False},
    )
    monkeypatch.setattr(
        reader, "validated_current_capture", lambda root, *, profile: capture
    )
    report = json.loads(
        (
            ROOT / "docs/report/method-certification/current-r-oracle/report.json"
        ).read_text()
    )
    # Use the retained fields as a serializer-shape fixture; no fresh native call.
    report["schema_version"] = "current-native-r-reference.1"
    replay = build_source_replay(report, capture.source_revision)
    scope = {
        "native_capture_profile": profile,
        "native_capture_source_revision": capture.source_revision,
        "native_capture_manifest_sha256": capture.manifest_sha256,
        "native_capture_source_context": capture.source_context,
        "fresh_R_executed_for_this_comparison": False,
        "current_python_expectations_regenerated_for_this_comparison": False,
        "consumer_inputs": _consumer_inputs(
            repository, capture.manifest_sha256, profile
        ),
        "native_source_acquisition": "retained_public_locked_archive_acquisition",
        "scope": "retained native R capture against original R vectors; current consumer code and data bytes are independently identified, protected captured science inputs match, and neither R nor Python expectations are newly executed",
    }
    report.pop("private_source_custody", None)
    replay.pop("source_revision")
    report["schema_version"] = "retained-native-r-comparison-report.v1"
    replay["schema_version"] = "retained-native-r-comparison-source-replay.v1"
    report.update(copy.deepcopy(scope))
    replay.update(copy.deepcopy(scope))
    return repository, report, replay


def test_retained_consumer_and_case_vector_identity(
    reader: ModuleType, records: tuple[Path, dict[str, Any], dict[str, Any]]
) -> None:
    repository, report, replay = records
    before = copy.deepcopy((report, replay))
    result = reader._require_retained_comparison(repository, report, replay)
    assert result.manifest_sha256 == "b" * 64
    assert (report, replay) == before
    assert len(report["consumer_inputs"]["code_sha256"]) == 98
    assert len(report["consumer_inputs"]["data_sha256"]) == 280
    assert replay["retained_numeric_csv"]["file_count"] == 97


@pytest.mark.parametrize(
    "mutation",
    [
        "fresh-r",
        "fresh-python",
        "false-is-int",
        "capture",
        "consumer",
        "case",
        "prospective",
        "paired",
        "csv",
        "head",
        "scope",
        "report-schema",
        "digest-map",
    ],
)
def test_scope_case_vector_corruptions_refuse(
    reader: ModuleType,
    records: tuple[Path, dict[str, Any], dict[str, Any]],
    mutation: str,
) -> None:
    repository, report, replay = records
    if mutation == "fresh-r":
        replay["fresh_R_executed_for_this_comparison"] = True
    elif mutation == "fresh-python":
        report["current_python_expectations_regenerated_for_this_comparison"] = True
    elif mutation == "false-is-int":
        report["fresh_R_executed_for_this_comparison"] = 0
    elif mutation == "capture":
        report["native_capture_manifest_sha256"] = "c" * 64
    elif mutation == "consumer":
        report["consumer_inputs"]["sha256"] = "c" * 64
    elif mutation == "case":
        replay["cases"]["core_passed"] = 42
    elif mutation == "prospective":
        report["new_core_cases"][-1]["id"] = report["new_core_cases"][0]["id"]
    elif mutation == "paired":
        report["original_R_to_current_R_cases"].pop()
    elif mutation == "csv":
        report["raw_results_sha256"].pop("oracle/C0000.csv")
    elif mutation == "head":
        replay["source_revision"] = "a" * 40
    elif mutation == "scope":
        report["scope"] = "fresh execution"
    elif mutation == "report-schema":
        report["schema_version"] = "current-native-r-reference.1"
    else:
        report["current_inputs_sha256"]["../outside"] = "a" * 64
    with pytest.raises(ValueError):
        reader._require_retained_comparison(repository, report, replay)


def test_consumer_physical_byte_drift_refuses(
    reader: ModuleType, records: tuple[Path, dict[str, Any], dict[str, Any]]
) -> None:
    repository, report, replay = records
    name = next(iter(report["consumer_inputs"]["code_sha256"]))
    (repository / name).write_text("changed consumer source")
    with pytest.raises(ValueError):
        reader._require_retained_comparison(repository, report, replay)


def test_mapped_schema_cannot_take_legacy_path(
    reader: ModuleType,
    records: tuple[Path, dict[str, Any], dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, report, replay = records
    replay["schema_version"] = "native-r-source-replay.v1"
    (tmp_path / "report.json").write_text(json.dumps(report))
    (tmp_path / "source-replay.json").write_text(json.dumps(replay))
    monkeypatch.setattr(reader, "HERE", tmp_path)
    monkeypatch.setattr(reader, "ROOT", repository)
    with pytest.raises(ValueError, match="schema"):
        reader.main()


def test_both_mapped_tags_reset_cannot_bypass_consumer_scope(
    reader: ModuleType,
    records: tuple[Path, dict[str, Any], dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, report, replay = records
    report["schema_version"] = "current-native-r-reference.1"
    replay["schema_version"] = "native-r-source-replay.v1"
    (tmp_path / "report.json").write_text(json.dumps(report))
    (tmp_path / "source-replay.json").write_text(json.dumps(replay))
    monkeypatch.setattr(reader, "HERE", tmp_path)
    monkeypatch.setattr(reader, "ROOT", repository)
    with pytest.raises(ValueError, match="schema"):
        reader.main()


@pytest.mark.parametrize("selected", ["report", "replay"])
def test_dirty_capture_false_is_not_integer_zero(
    reader: ModuleType,
    records: tuple[Path, dict[str, Any], dict[str, Any]],
    selected: str,
) -> None:
    repository, report, replay = records
    target = report if selected == "report" else replay
    target["native_capture_source_context"]["clean_execution"] = 0
    with pytest.raises(ValueError, match="dirty source context"):
        reader._require_retained_comparison(repository, report, replay)


@pytest.mark.parametrize("profile", [None, False, "unknown", ""])
def test_missing_or_invalid_native_capture_profile_refuses(
    reader: ModuleType,
    records: tuple[Path, dict[str, Any], dict[str, Any]],
    profile: object,
) -> None:
    repository, report, replay = records
    report["native_capture_profile"] = profile
    with pytest.raises(ValueError, match="profile"):
        reader._require_retained_comparison(repository, report, replay)


def test_report_and_replay_capture_profiles_must_agree(
    reader: ModuleType, records: tuple[Path, dict[str, Any], dict[str, Any]]
) -> None:
    repository, report, replay = records
    replay["native_capture_profile"] = (
        "count-domain" if report["native_capture_profile"] == "annulus" else "annulus"
    )
    with pytest.raises(ValueError, match="scope"):
        reader._require_retained_comparison(repository, report, replay)
