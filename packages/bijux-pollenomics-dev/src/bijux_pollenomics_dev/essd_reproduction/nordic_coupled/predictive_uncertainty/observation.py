"""Independently bind sources and audit closed coupled-pollen bootstrap products."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .products import (
    StudyError,
    _git_state,
    _loaded_code,
    _pin,
    _read_product,
    _resource_check,
    _source_check,
    _write,
)
from .verification import audit
from .verification.sources import bind_sources


def verify(
    repository: Path, protocol_path: Path, study_output: Path, output: Path
) -> dict[str, Any]:
    """Use independent source bindings and scalar algebra on closed products."""
    started = time.monotonic()
    repository = repository.resolve(strict=True)
    state = _git_state(repository)
    code = _loaded_code(repository)
    output = require_absent_artifact_output(repository, output)
    study_output = study_output.resolve(strict=True)
    if not study_output.is_relative_to(repository / "artifacts"):
        raise StudyError("An artifact study directory is required")
    result = json.loads((study_output / "result.json").read_bytes())
    if (
        result.get("schema_version") != "coupled-pollen-bootstrap-result.v1"
        or result.get("status") != "produced_awaiting_independent_verification"
        or result.get("source_guards_passed") is not True
        or result.get("source_commit") != state[0]
        or set(result["products"]) != {"inputs", "draws", "predictions", "summary"}
    ):
        raise StudyError("Independent producer/source epoch differs")
    protocol_raw = protocol_path.read_bytes()
    protocol = json.loads(protocol_raw)
    protocol_pin = _pin(protocol_path.resolve(strict=True), repository)
    if protocol_pin != result["protocol"]:
        raise StudyError("Independent protocol identity differs")
    packets = {
        key: _read_product(study_output, result["products"][key])
        for key in ("inputs", "draws", "predictions", "summary")
    }
    manifest = _read_product(study_output, result["prediction_manifest"])
    if manifest["files"] != {
        key: result["products"][key] for key in ("inputs", "draws", "predictions")
    }:
        raise StudyError("Prediction freeze member bindings differ")
    if (
        packets["inputs"]["protocol"] != protocol
        or packets["summary"]["outcome_access"]["prediction_manifest_sha256"]
        != result["prediction_manifest"]["sha256"]
    ):
        raise StudyError("Independent source/outcome access binding differs")
    source_observation = bind_sources(repository, packets["inputs"])
    observation = audit(
        packets["inputs"], packets["draws"], packets["predictions"], packets["summary"]
    )
    report = {
        "schema_version": "coupled-pollen-bootstrap-verification.v1",
        "source_commit": result["source_commit"],
        "source_observation": source_observation,
        "numerical_observation": observation,
    }
    _source_check(repository, packets["inputs"])
    if (
        protocol_path.read_bytes() != protocol_raw
        or _git_state(repository) != state
        or any(path.read_bytes() != raw for path, raw in code.items())
    ):
        raise StudyError("Independent consumed source, HEAD or index changed")
    report["resources"] = _resource_check(
        started, output.parent, protocol["limits"], wall_key="observer_wall_seconds"
    )
    _write(output, report, protocol["limits"]["max_output_bytes"])
    _resource_check(
        started, output.parent, protocol["limits"], wall_key="observer_wall_seconds"
    )
    return report


def main() -> None:
    """Observe closed products without importing the numerical producer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--study-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.repository, args.protocol, args.study_output, args.output)
    print(
        json.dumps(
            {
                "status": "independently_observed",
                "source_commit": result["source_commit"],
            }
        )
    )


if __name__ == "__main__":
    main()
