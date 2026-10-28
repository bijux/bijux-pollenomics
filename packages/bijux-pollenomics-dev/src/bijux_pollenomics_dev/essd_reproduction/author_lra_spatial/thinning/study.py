"""Freeze a geographic-thinning cohort's prescribed forecasts before scoring."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..inputs import decode, require
from ..products import check_sources, code_state, reopen, resources, write
from .inputs import load_inputs
from .outcomes import OutcomeReader
from .prediction import predict_context
from .scoring import retained_metrics, score_targets


def produce(
    repository: Path, archive: Path, protocol_path: Path, output: Path
) -> dict[str, Any]:
    """Use saved pair-specific fits for ten fresh nine-owner numerical closures."""
    started = time.monotonic()
    repository, archive = repository.resolve(strict=True), archive.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    raw_protocol = protocol_path.read_bytes()
    protocol = decode(raw_protocol)
    require(
        protocol["schema_version"] == "author-lra-geographic-thinning.v1"
        and protocol["cohort"]["size"] == 10
        and protocol["models"]["hellinger_scales_km"] == [20.0, 100.0],
        "Prospective ten-site prescribed sensitivity required",
    )
    state = code_state(repository)
    packet = load_inputs(repository, archive, protocol)
    require(
        len(packet["contexts"]) == 10
        and len(packet["retained_reference_predictions"]) == 40,
        "Ten new contexts and forty separately retained predictions required",
    )
    output.mkdir()
    maximum = protocol["limits"]["max_output_bytes"]
    predictions = [
        row
        for context in packet["contexts"]
        for row in predict_context(
            context, packet["taxa"], protocol["models"]["hellinger_scales_km"]
        )
    ]
    require(len(predictions) == 50, "Every prescribed prediction slot must remain")
    pins = {
        "inputs": write(output, "inputs.json", packet, maximum),
        "predictions": write(output, "predictions.json", predictions, maximum),
    }
    frozen_pin = write(
        output,
        "prediction-manifest.json",
        {
            "schema_version": "author-lra-thinning-prediction-freeze.v1",
            "files": dict(pins),
            "protocol_sha256": hashlib.sha256(raw_protocol).hexdigest(),
            "selection_status": "prescribed_unselected_scales_no_inner_selection",
            "scoring_observations_decoded": 0,
            "role": "Member accounting only; each new prediction retains its own nine-owner numerical closure. Previously exposed cached fits are not globally unread observations.",
        },
        maximum,
    )
    frozen = reopen(output, frozen_pin)
    require(frozen["files"] == pins, "Prediction member binding changed")
    closed = {name: reopen(output, pin) for name, pin in frozen["files"].items()}
    reader = OutcomeReader(archive, closed["inputs"], frozen_pin["sha256"])
    counts = {
        target: reader.read(target) for target in closed["inputs"]["cohort"]["selected"]
    }
    prior = retained_metrics(repository, protocol, closed["inputs"], counts)
    scores = score_targets(
        closed["inputs"], closed["predictions"], counts, prior, frozen_pin["sha256"]
    )
    pins["scores"] = write(output, "scores.json", scores, maximum)
    pins["outcome_access"] = write(
        output, "outcome-access.json", reader.accesses, maximum
    )
    require(len(reader.accesses) == 10, "Exactly ten scoring accesses required")
    check_sources(repository, archive, packet)
    require(
        protocol_path.read_bytes() == raw_protocol and code_state(repository) == state,
        "Consumed source, protocol, HEAD or index changed",
    )
    result = {
        "schema_version": "author-lra-thinning-result.v1",
        "status": "produced_awaiting_independent_verification",
        "source_commit": state["head"],
        "protocol_sha256": hashlib.sha256(raw_protocol).hexdigest(),
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "scientific_sources_checked": len(packet["sources"]),
        "source_guards_passed": True,
        "products": pins,
        "prediction_manifest": frozen_pin,
        "resources": resources(started, output, protocol["limits"]),
    }
    write(output, "result.json", result, maximum)
    resources(started, output, protocol["limits"])
    return result


def main() -> None:
    """Execute the source-bound point-only geographic-thinning comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "archive", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = produce(args.repository, args.archive, args.protocol, args.output)
    print(json.dumps({"status": result["status"], "resources": result["resources"]}))


if __name__ == "__main__":
    main()
