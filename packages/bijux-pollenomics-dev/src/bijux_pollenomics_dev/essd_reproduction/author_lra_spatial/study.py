"""Freeze zero-compatible spatial candidates before fold-local selection."""

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

from .evaluation import score_outer, select_scales
from .inputs import decode, load_inputs, require
from .nominal import check_nominal
from .outcomes import OutcomeReader
from .prediction import predict_context
from .products import check_sources, code_state, reopen, resources, write


def produce(
    repository: Path, archive: Path, protocol_path: Path, output: Path
) -> dict[str, Any]:
    """Execute one declared point-model study, retaining every eligible/refused row."""
    started = time.monotonic()
    repository, archive = repository.resolve(strict=True), archive.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    protocol_raw = protocol_path.read_bytes()
    protocol = decode(protocol_raw)
    require(
        protocol["scales_km"] == [20.0, 100.0],
        "Two prospectively declared scales required",
    )
    state = code_state(repository)
    packet = load_inputs(repository, archive, protocol)
    output.mkdir()
    maximum = protocol["limits"]["max_output_bytes"]
    nominal = check_nominal(packet)
    nominal_pin = write(output, "nominal.json", nominal, maximum)
    require(
        nominal["passed"],
        "Nominal correspondence failed; no new spatial predictions permitted",
    )
    candidates = [
        predict_context(context, packet["taxa"], scale)
        for context in packet["contexts"]
        for scale in protocol["scales_km"]
    ]
    require(len(candidates) == 450, "Complete 450-candidate population required")
    pins = {
        "inputs": write(output, "inputs.json", packet, maximum),
        "candidates": write(output, "candidates.json", candidates, maximum),
        "nominal": nominal_pin,
    }
    frozen_pin = write(
        output,
        "prediction-manifest.json",
        {
            "schema_version": "author-spatial-prediction-freeze.v1",
            "files": dict(pins),
            "role": "Whole-file accounting only; each row retains fold-local scientific ancestry.",
            "outcomes_decoded": 0,
        },
        maximum,
    )
    frozen = reopen(output, frozen_pin)
    require(frozen["files"] == pins, "Prediction member bindings changed")
    closed = {name: reopen(output, pin) for name, pin in frozen["files"].items()}
    reader = OutcomeReader(archive, closed["inputs"], protocol, frozen_pin["sha256"])
    inner_scores, choices = select_scales(
        closed["inputs"], closed["candidates"], reader
    )
    selection_pins = {
        "inner_scores": write(output, "inner-scores.json", inner_scores, maximum),
        "choices": write(output, "choices.json", choices, maximum),
    }
    selection_pin = write(
        output,
        "selection-manifest.json",
        {
            "schema_version": "author-spatial-selection-freeze.v1",
            "files": selection_pins,
            "prediction_manifest": frozen_pin,
            "role": "Accounting only; a choice uses its own fourteen training outcomes. Other folds may have exposed the same physical outcome.",
        },
        maximum,
    )
    selection = reopen(output, selection_pin)
    require(
        selection["files"] == selection_pins
        and selection["prediction_manifest"] == frozen_pin,
        "Selection member bindings changed",
    )
    for pin in selection_pins.values():
        reopen(output, pin)
    reader.selection_freeze = selection_pin["sha256"]
    outer = score_outer(
        closed["inputs"], reopen(output, selection_pins["choices"]), reader
    )
    pins.update(selection_pins)
    pins["outer_scores"] = write(output, "outer-scores.json", outer, maximum)
    pins["outcome_access"] = write(
        output, "outcome-access.json", reader.accesses, maximum
    )
    check_sources(repository, archive, packet)
    require(
        protocol_path.read_bytes() == protocol_raw and code_state(repository) == state,
        "Consumed code, protocol, HEAD or index changed",
    )
    result = {
        "schema_version": "author-spatial-result.v1",
        "status": "produced_awaiting_independent_verification",
        "source_commit": state["head"],
        "protocol_sha256": hashlib.sha256(protocol_raw).hexdigest(),
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "scientific_sources_checked": len(packet["sources"]),
        "source_guards_passed": True,
        "products": pins,
        "prediction_manifest": frozen_pin,
        "selection_manifest": selection_pin,
        "resources": resources(started, output, protocol["limits"]),
    }
    write(output, "result.json", result, maximum)
    resources(started, output, protocol["limits"])
    return result


def main() -> None:
    """Run the explicit source-bound declared spatial study."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "archive", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = produce(args.repository, args.archive, args.protocol, args.output)
    print(json.dumps({"status": result["status"], "resources": result["resources"]}))


if __name__ == "__main__":
    main()
