"""Protect complete fold evidence and freeze-before-score scientific admission."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import runpy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import query
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    author_love_starts as prior,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.author_development import (
    admission,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.optimizer_inputs import (
    withheld_fold as subject,
)

ROOT = Path(__file__).resolve().parents[7]


def _bundle() -> tuple[dict[str, bytes], dict[str, dict[str, Any]], dict[str, Any]]:
    authority = json.loads((ROOT / admission.AUTHORITY).read_bytes())
    protocol = json.loads((ROOT / admission.PREFIX / "protocol.json").read_bytes())
    bodies, pins = {}, {}
    for role, row in authority["products"].items():
        bodies[role] = (ROOT / admission.PREFIX / row["name"]).read_bytes()
        pins[role] = dict(row["original_reference"])
    for role, previous in (("prior_report", "report"), ("prior_trials", "trials")):
        reference = protocol["prior_evidence"][previous]
        bodies[role] = (ROOT / reference["path"]).read_bytes()
        pins[role] = dict(reference)
    bodies["baseline"] = (ROOT / prior.BASELINE).read_bytes()
    pins["baseline"] = {
        "path": prior.BASELINE,
        "sha256": prior.BASELINE_SHA256,
        "bytes": len(bodies["baseline"]),
    }
    if "prediction_freeze" in bodies:
        pins["outcome"] = dict(protocol["outcome"])
        bodies["outcome"] = (
            ROOT / admission.INPUT_PREFIX / pins["outcome"]["path"]
        ).read_bytes()
    return bodies, pins, protocol


def _replace(
    role: str, value: Any, bodies: dict[str, bytes], pins: dict[str, dict[str, Any]]
) -> None:
    raw = (json.dumps(value, sort_keys=True) + "\n").encode()
    bodies[role] = raw
    pins[role] = {
        **pins[role],
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def _changed_training(
    bodies: dict[str, bytes], pins: dict[str, dict[str, Any]], value: dict[str, Any]
) -> None:
    _replace("training", value, bodies, pins)
    report = json.loads(bodies["report"])
    report["training"] = dict(pins["training"])
    _replace("report", report, bodies, pins)


def test_retained_scientific_fold_is_admitted_without_refitting() -> None:
    bodies, pins, protocol = _bundle()
    result = subject.validate_saved_outputs(bodies, pins, protocol)
    assert result["new_lifecycle_events"] == 1408
    assert result["reused_lifecycle_events"] == 256


def test_missing_training_predictor_cannot_be_hidden_by_new_hashes() -> None:
    bodies, pins, protocol = _bundle()
    training = json.loads(bodies["training"])
    training["training"].pop()
    _changed_training(bodies, pins, training)
    with pytest.raises(ReportRebuildError):
        subject.validate_saved_outputs(bodies, pins, protocol)


def test_omitted_training_attempt_cannot_reduce_the_denominator() -> None:
    bodies, pins, protocol = _bundle()
    training = json.loads(bodies["training"])
    failed = next(
        (
            index
            for index, row in enumerate(training["new_attempts"])
            if not row["accepted"]
        ),
        0,
    )
    training["new_attempts"].pop(failed)
    _changed_training(bodies, pins, training)
    with pytest.raises(ReportRebuildError, match="attempt denominator"):
        subject.validate_saved_outputs(bodies, pins, protocol)


def test_changed_prediction_bytes_are_refused_before_outcome_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bodies, pins, protocol = _bundle()
    if "prediction_freeze" not in bodies:
        pytest.skip("Retained training refusal has no target prediction")
    target = bodies["outcome"]
    original = subject._decode

    def guard(raw: bytes) -> Any:
        assert raw != target, "Target decoding preceded prediction admission"
        return original(raw)

    monkeypatch.setattr(subject, "_decode", guard)
    bodies["prediction_freeze"] += b" "
    with pytest.raises(ReportRebuildError):
        subject.validate_saved_outputs(bodies, pins, protocol)


def test_changed_score_is_refused_by_independent_count_arithmetic() -> None:
    bodies, pins, protocol = _bundle()
    if "prediction_freeze" not in bodies:
        pytest.skip("Retained training refusal has no target score")
    report = json.loads(bodies["report"])
    report["scores"][0]["total_variation"] += 0.1
    _replace("report", report, bodies, pins)
    with pytest.raises(ReportRebuildError, match="descriptive metrics"):
        subject.validate_saved_outputs(bodies, pins, protocol)


def test_empty_governed_source_marker_is_distinct_from_missing_source(
    tmp_path: Path,
) -> None:
    path = tmp_path / "py.typed"
    path.write_bytes(b"")
    digest = hashlib.sha256(b"").hexdigest()
    assert admission._read(tmp_path, path.name, digest, 0) == b""
    with pytest.raises(ReportRebuildError):
        admission._read(tmp_path, path.name, "0" * 64, 0)
    with pytest.raises((ReportRebuildError, OSError, ValueError)):
        admission._read(tmp_path, "missing.py", digest, 0)


def test_retained_scientific_capture_authenticates_original_governed_sources() -> None:
    from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

    authority = json.loads((ROOT / admission.AUTHORITY).read_bytes())
    entries = {}
    for row in authority["products"].values():
        name = admission.PREFIX + row["name"]
        raw = (ROOT / name).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        entries[name] = InventoryEntry(name, "file", len(raw), digest, digest)
    owners = json.loads((ROOT / "configs/ci/report-ownership.json").read_bytes())[
        "owners"
    ]
    accepted, result = admission.validated_author_development_capture(
        ROOT, entries, owners
    )
    assert len(accepted) == 5 and result["attempts"] == 832
    assert result["executed_source_candidate"] == admission.ORIGINAL_SOURCE_REVISION
    assert result["source_authentication_role"] == "original_execution_only"
    assert result["current_source_or_numerical_reuse_claimed"] is False


@pytest.mark.parametrize(
    "case",
    [
        "missing",
        "extra",
        "duplicate",
        "unlisted",
        "changed_pin",
        "negative_size",
        "changed_git_bytes",
        "linked_git_source",
        "changed_generated_bytes",
    ],
)
def test_original_source_authentication_refuses_changed_contract(
    monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    sources = deepcopy(_bundle()[2]["source_pins"])
    if case == "missing":
        sources.pop()
    elif case == "extra":
        sources.append(dict(sources[0]))
    elif case == "duplicate":
        sources[-1] = dict(sources[0])
    elif case == "unlisted":
        sources[0]["path"] = "packages/unlisted/source.py"
    elif case == "changed_pin":
        sources[0]["sha256"] = "0" * 64
    elif case == "negative_size":
        sources[0]["bytes"] = -1
    elif case == "changed_generated_bytes":
        monkeypatch.setattr(admission, "read_source_path", lambda *args: b"changed")
    else:
        original = query

        def changed_query(*args: Any, **kwargs: Any) -> bytes:
            raw = original(*args, **kwargs)
            if case == "changed_git_bytes" and args[1][:2] == ["cat-file", "blob"]:
                return bytes([raw[0] ^ 1]) + raw[1:]
            if case == "linked_git_source" and args[1][0] == "ls-tree":
                return b"120000" + raw[6:]
            return raw

        monkeypatch.setattr(admission, "query", changed_query)
    with pytest.raises(ReportRebuildError):
        admission._validate_original_sources(ROOT, sources)


@pytest.mark.parametrize(
    "source_name",
    [
        "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra_validation/metrics.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/__init__.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/models/validation.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/analytical.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/inputs.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/regional.py",
    ],
)
def test_live_replay_refuses_changed_original_computational_input_before_fitting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, source_name: str
) -> None:
    replay = runpy.run_path(str(ROOT / admission.PREFIX / "replay.py"))
    protocol = deepcopy(_bundle()[2])
    protocol["source_pins"] = [
        row for row in protocol["source_pins"] if row["path"] == source_name
    ]
    assert len(protocol["source_pins"]) == 1

    def refuse_execution(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Numerical execution preceded source admission")

    monkeypatch.setattr(runpy, "run_path", refuse_execution)
    with pytest.raises(ValueError, match="Declared computational source changed"):
        replay["run"](ROOT, tmp_path / "prepared", protocol, tmp_path / "output")
    assert not (tmp_path / "output").exists()
