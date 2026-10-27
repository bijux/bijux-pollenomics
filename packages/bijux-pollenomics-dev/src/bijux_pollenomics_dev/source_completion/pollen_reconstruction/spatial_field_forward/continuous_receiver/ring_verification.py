"""Observe closed true-ring proofs with independent source and numerical algebra."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import time
from typing import Any

from .ring_inputs import BASE, CAPTURE, RADIAL_PROTOCOL
from .ring_study import source_guard
from .study import _peak_rss
from .verification.contracts import Clock, VerificationError, identity, parse, require
from .verification.ring_predictions import audit
from .verification.ring_sources import bind_raw_inputs
from .verification.study import _owned


def _bound_output(path: Path, pin: object) -> bytes:
    raw = path.read_bytes()
    require(
        isinstance(pin, dict)
        and set(pin) == {"path", "bytes", "sha256"}
        and pin.get("path") == path.name
        and {k: v for k, v in pin.items() if k != "path"} == identity(raw),
        "Closed scientific output identity differs",
    )
    return raw


def run_verification(
    repository: Path, protocol_path: Path, study_output: Path, output: Path
) -> dict[str, Any]:
    started = time.monotonic()
    repository = repository.resolve()
    protocol_path = _owned(repository, protocol_path)
    study_output = _owned(repository, study_output)
    output = _owned(repository, output)
    require(
        not output.exists()
        and output.is_relative_to(repository / "artifacts")
        and study_output.is_relative_to(repository / "artifacts"),
        "Fresh owned observer output required",
    )
    require(
        protocol_path.stat().st_size <= 100_000, "Protocol metadata byte cap exceeded"
    )
    protocol = parse(protocol_path.read_bytes())
    raw_inputs = {}
    for name in protocol["input_files"]:
        path = _owned(repository, Path(name))
        require(path.stat().st_size <= 1_000_000, "Scientific input byte cap exceeded")
        raw_inputs[name] = path.read_bytes()
    parsed = bind_raw_inputs(protocol, raw_inputs)
    before = source_guard(repository, protocol_path, protocol["input_files"])
    expected = {"certificates.json", "prediction-ranges.json", "result.json"}
    members = list(study_output.iterdir())
    require(
        {p.name for p in members} == expected
        and all(p.is_file() and not p.is_symlink() for p in members)
        and sum(p.stat().st_size for p in members) <= 4_850_000,
        "Scientific output population or byte bound differs",
    )
    snapshot = {p.name: identity(p.read_bytes()) for p in members}
    result = parse((study_output / "result.json").read_bytes())
    prediction = parse(
        _bound_output(
            study_output / "prediction-ranges.json", result["prediction_file"]
        )
    )
    certificate_raw = _bound_output(
        study_output / "certificates.json", result["certificate_file"]
    )
    require(
        prediction["certificate_file"] == result["certificate_file"]
        and result["source_commit"] == prediction["source_commit"] == before[0]
        and result["protocol_file"]
        == prediction["protocol_file"]
        == {
            "path": str(protocol_path.relative_to(repository)),
            **identity(protocol_path.read_bytes()),
        },
        "Closed source/protocol ownership differs",
    )
    certificates = parse(certificate_raw)
    radial = parsed[RADIAL_PROTOCOL]
    clock = Clock()
    try:
        checked = audit(
            protocol=protocol,
            public_source=parsed[BASE + "result.json"],
            original_protocol=parsed[BASE + "protocol.json"],
            capture_freeze=parsed[CAPTURE],
            original_prediction=parsed[radial["source_prediction"]],
            original_scored=parsed[radial["source_result"]],
            certificates=certificates,
            prediction_packet=prediction,
            result=result,
            clock=clock,
        )
    except (
        VerificationError,
        ValueError,
        ArithmeticError,
        KeyError,
        TypeError,
        IndexError,
    ) as error:
        checked = {
            "status": "failed",
            "accounting_verified": False,
            "reason": f"{type(error).__name__}: {error}",
            "current_case": clock.current_case,
            "current_domain": clock.current_domain,
            "completed_leaf_replays": clock.completed_leaves,
        }
    require(
        source_guard(repository, protocol_path, protocol["input_files"]) == before
        and snapshot
        == {p.name: identity(p.read_bytes()) for p in study_output.iterdir()},
        "Source/input/index or closed scientific output changed during observation",
    )
    elapsed, peak = time.monotonic() - started, _peak_rss()
    require(
        elapsed < 180 and peak <= 805306368, "Independent final resource cap exceeded"
    )
    checked.update(
        {
            "schema_version": "continuous-receiver-ring-independent-check.v1",
            "producer_source_commit": before[0],
            "observer_source_commit": before[0],
            "study_result_identity": snapshot["result.json"],
            "elapsed_seconds": elapsed,
            "peak_rss_bytes": peak,
        }
    )
    raw = (
        json.dumps(checked, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()
    require(len(raw) <= 4_850_000, "Independent output byte ceiling exceeded")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    return checked


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--study-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    signal.alarm(180)
    checked = run_verification(
        args.repository, args.protocol, args.study_output, args.output
    )
    signal.alarm(0)
    print(json.dumps({k: checked[k] for k in ("status", "accounting_verified")}))
    if checked["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
