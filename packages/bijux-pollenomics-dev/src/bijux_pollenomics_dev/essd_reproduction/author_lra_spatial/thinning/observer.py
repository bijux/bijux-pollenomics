"""Independently reopen source joins, prescribed forecasts and matched scores."""

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
from ..products import check_sources, code_state, file_sha, reopen, resources, write
from .verification import audit_inputs, audit_predictions, audit_scores


def observe(
    repository: Path,
    archive: Path,
    protocol_path: Path,
    products: Path,
    output: Path,
) -> dict[str, Any]:
    """Qualify the new consumer without replaying old forecasts or basin fits."""
    started = time.monotonic()
    repository, archive = repository.resolve(strict=True), archive.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    raw_protocol = protocol_path.read_bytes()
    protocol = decode(raw_protocol)
    state = code_state(repository)
    result = decode((products / "result.json").read_bytes())
    require(
        result["schema_version"] == "author-lra-thinning-result.v1"
        and result["source_commit"] == state["head"]
        and result["index_sha256"] == state["index_sha256"]
        and result["python_files_checked"] == len(state["python_files"])
        and result["protocol_sha256"] == hashlib.sha256(raw_protocol).hexdigest()
        and result["source_guards_passed"] is True,
        "Original producer source or protocol identity differs",
    )
    pins = result["products"]
    require(
        set(pins) == {"inputs", "predictions", "scores", "outcome_access"},
        "Closed complete producer product inventory required",
    )
    frozen = reopen(products, result["prediction_manifest"])
    require(
        frozen["schema_version"] == "author-lra-thinning-prediction-freeze.v1"
        and frozen["files"] == {key: pins[key] for key in ("inputs", "predictions")}
        and frozen["protocol_sha256"] == result["protocol_sha256"]
        and frozen["selection_status"]
        == "prescribed_unselected_scales_no_inner_selection"
        and frozen["scoring_observations_decoded"] == 0,
        "Prescribed prediction readback changed",
    )
    closed = {name: reopen(products, pin) for name, pin in pins.items()}
    counts, source_facts = audit_inputs(repository, archive, protocol, closed["inputs"])
    require(
        all(
            row["retained_full15_metrics"]
            == source_facts["retained_reference_metrics"][row["target"]]
            for row in closed["scores"]["targets"]
        ),
        "A retained metric was recomputed, reassigned or changed",
    )
    numerical_facts = audit_predictions(
        closed["inputs"], closed["predictions"], protocol
    )
    require(
        closed["scores"]["prediction_freeze_sha256"]
        == result["prediction_manifest"]["sha256"]
        and all(
            row["prediction_freeze_sha256"] == result["prediction_manifest"]["sha256"]
            for row in closed["outcome_access"]
        ),
        "Scoring access is not bound to the closed prediction members",
    )
    scoring_facts = audit_scores(
        closed["inputs"],
        closed["predictions"],
        closed["scores"],
        closed["outcome_access"],
        counts,
        protocol,
    )
    check_sources(repository, archive, closed["inputs"])
    require(
        protocol_path.read_bytes() == raw_protocol and code_state(repository) == state,
        "Consumed code, protocol, HEAD or index changed during observation",
    )
    for pin in pins.values():
        reopen(products, pin)
    reopen(products, result["prediction_manifest"])
    output.mkdir()
    facts = {
        "schema_version": "author-lra-thinning-verification.v1",
        "status": "verified",
        "source_commit": state["head"],
        "protocol_sha256": hashlib.sha256(raw_protocol).hexdigest(),
        "producer_result_sha256": file_sha(products / "result.json"),
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "source_guards_passed": True,
        "sources": {
            key: value
            for key, value in source_facts.items()
            if key != "retained_reference_metrics"
        },
        "numerical_predictions": numerical_facts,
        "scoring": scoring_facts,
        "resources": resources(started, output, protocol["limits"], observer=True),
    }
    write(output, "verification.json", facts, protocol["limits"]["max_output_bytes"])
    resources(started, output, protocol["limits"], observer=True)
    return facts


def main() -> None:
    """Observe one declared new thinning result using independent arithmetic."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "archive", "protocol", "products", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = observe(
        args.repository, args.archive, args.protocol, args.products, args.output
    )
    print(json.dumps({"status": result["status"], "resources": result["resources"]}))


if __name__ == "__main__":
    main()
