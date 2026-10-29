"""Protect complete fold evidence and freeze-before-score scientific admission."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
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


def test_new_scientific_capture_uses_every_governed_source_marker() -> None:
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
