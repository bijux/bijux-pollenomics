"""Freeze geography-admitted cached-fit spatial ensembles before scoring."""

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
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.inputs import decode
from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    code_state,
    reopen,
    resources,
    write,
)

from .geometry import admit_targets, require
from .inputs import check_sources, load_inputs
from .observations import ObservationReader
from .predictions import check_nominal_handoff, predict_candidate
from .scoring import score_candidate


def produce(repository: Path, protocol_path: Path, output: Path) -> dict[str, Any]:
    """Apply both block and numeric-source gates before new Hellinger forecasts."""
    started = time.monotonic()
    repository = repository.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    raw_protocol = protocol_path.read_bytes()
    protocol = decode(raw_protocol)
    require(
        protocol["model"]["scales_km"] == [20.0, 100.0],
        "Two fixed unselected scales required",
    )
    state = code_state(repository)
    packet = load_inputs(repository, protocol)
    admission = admit_targets(packet, protocol["geography"])
    candidates = {row["case"]["case_id"]: row for row in packet["candidate_cases"]}
    output.mkdir()
    maximum = protocol["limits"]["max_output_bytes"]
    pins = {
        "inputs": write(output, "inputs.json", packet, maximum),
        "admission": write(output, "admission.json", admission, maximum),
    }
    nominal = []
    for role in admission["roles"]:
        if role["status"] == "admitted":
            require(
                role["case_id"] in candidates,
                "Admitted role lacks an unchanged source-case projection",
            )
            candidate = candidates[role["case_id"]]
            required = [
                candidate["case"]["regional_owner_id"],
                *(row["owner_id"] for row in candidate["case"]["local_owners"]),
            ]
            require(
                required == role["required_source_owner_ids"]
                and candidate["case"]["target_id"] == role["target_id"],
                "Admitted full source set differs from numerical candidate",
            )
            nominal.append(check_nominal_handoff(candidate))
    pins["nominal_handoff"] = write(output, "nominal-handoff.json", nominal, maximum)
    require(
        all(row["passed"] for row in nominal),
        "Nominal source correspondence failed before new forecasts",
    )
    predicted = []
    for role in admission["roles"]:
        for scale in protocol["model"]["scales_km"]:
            predicted.append(
                {
                    "case_id": role["case_id"],
                    "target_id": role["target_id"],
                    "length_scale_km": scale,
                    "admission_status": role["status"],
                    "prediction": predict_candidate(
                        candidates[role["case_id"]], length_scale_km=scale
                    )
                    if role["status"] == "admitted"
                    else None,
                    "refusal": None if role["status"] == "admitted" else role["reason"],
                }
            )
    require(
        len(predicted) == 6, "All three target roles and two sensitivities required"
    )
    pins["predictions"] = write(output, "predictions.json", predicted, maximum)
    freeze_pin = write(
        output,
        "prediction-manifest.json",
        {
            "schema_version": "krageholm-geographic-transfer-freeze.v1",
            "files": dict(pins),
            "scoring_roles_opened": 0,
            "scope": "Whole-file accounting only; original exposed sources are not globally unread. Each candidate retains its target-free source parents.",
        },
        maximum,
    )
    frozen = reopen(output, freeze_pin)
    require(
        frozen["files"] == pins and frozen["scoring_roles_opened"] == 0,
        "New prediction freeze bindings changed",
    )
    closed = {key: reopen(output, pin) for key, pin in frozen["files"].items()}
    closed_candidates = {
        row["case"]["case_id"]: row for row in closed["inputs"]["candidate_cases"]
    }
    reader = ObservationReader(
        repository, closed["inputs"], closed["admission"], freeze_pin["sha256"]
    )
    observations = {}
    for role in closed["admission"]["roles"]:
        if role["status"] == "admitted":
            observations[role["target_id"]] = reader.read(role["target_id"])
    scores = []
    for row in closed["predictions"]:
        if row["prediction"] is None:
            scores.append(
                {
                    "case_id": row["case_id"],
                    "target_id": row["target_id"],
                    "length_scale_km": row["length_scale_km"],
                    "status": "not_executed_geographic_refusal",
                    "reason": row["refusal"],
                }
            )
        else:
            scores.append(
                {
                    "status": "evaluated_admitted_observation",
                    **score_candidate(
                        closed_candidates[row["case_id"]],
                        row["prediction"],
                        observations[row["target_id"]],
                    ),
                }
            )
    pins["scores"] = write(output, "scores.json", scores, maximum)
    pins["observation_access"] = write(
        output, "observation-access.json", reader.accesses, maximum
    )
    check_sources(repository, packet)
    require(
        protocol_path.read_bytes() == raw_protocol and code_state(repository) == state,
        "Consumed source, protocol, HEAD or index changed",
    )
    result = {
        "schema_version": "krageholm-geographic-transfer-result.v1",
        "status": "produced_awaiting_independent_verification",
        "source_commit": state["head"],
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "protocol_sha256": hashlib.sha256(raw_protocol).hexdigest(),
        "prediction_manifest": freeze_pin,
        "products": pins,
        "source_guards_passed": True,
        "resources": resources(started, output, protocol["limits"]),
    }
    write(output, "result.json", result, maximum)
    resources(started, output, protocol["limits"])
    return result


def main() -> None:
    """Run one declared source-reusing geographic ensemble consumer."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = produce(args.repository, args.protocol, args.output)
    print(json.dumps({"status": result["status"], "resources": result["resources"]}))


if __name__ == "__main__":
    main()
