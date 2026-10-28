"""Read back source-bound spatial predictions with independent numerical audits."""

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

from .audit import audit_predictions
from .inputs import decode, require
from .products import check_sources, code_state, reopen, resources, write
from .readback import audit_evaluation
from .source_audit import bind_sources


def observe(
    repository: Path, archive: Path, protocol_path: Path, products: Path, output: Path
) -> dict[str, Any]:
    """Authenticate both freezes before independently opening scoring outcomes."""
    started = time.monotonic()
    repository, archive = repository.resolve(strict=True), archive.resolve(strict=True)
    products = products.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    protocol_raw = protocol_path.read_bytes()
    protocol = decode(protocol_raw)
    state = code_state(repository)
    result_raw = (products / "result.json").read_bytes()
    result = decode(result_raw)
    require(
        result["protocol_sha256"] == hashlib.sha256(protocol_raw).hexdigest(),
        "Producer protocol identity differs",
    )
    require(
        result["source_commit"] == state["head"]
        and result["index_sha256"] == state["index_sha256"]
        and result["source_guards_passed"] is True,
        "Producer source epoch differs",
    )
    frozen = reopen(products, result["prediction_manifest"])
    selected = reopen(products, result["selection_manifest"])
    pins = result["products"]
    require(
        frozen["schema_version"] == "author-spatial-prediction-freeze.v1"
        and frozen["outcomes_decoded"] == 0
        and frozen["files"]
        == {key: pins[key] for key in ("inputs", "candidates", "nominal")}
        and selected["schema_version"] == "author-spatial-selection-freeze.v1"
        and selected["files"] == {key: pins[key] for key in ("inner_scores", "choices")}
        and selected["prediction_manifest"] == result["prediction_manifest"],
        "Prediction/selection membership or phase order changed",
    )
    closed = {key: reopen(products, pin) for key, pin in pins.items()}
    require(
        closed["nominal"]["passed"] is True
        and closed["nominal"]["reference_baselines"] == 675
        and closed["nominal"]["failures"] == [],
        "Nominal handoff failed",
    )
    counts, source_facts = bind_sources(repository, archive, protocol, closed["inputs"])
    numerical = audit_predictions(
        closed["inputs"],
        closed["candidates"],
        atol=protocol["comparison_tolerances"]["absolute"],
        rtol=protocol["comparison_tolerances"]["relative"],
    )
    evaluation = audit_evaluation(
        closed["inputs"],
        closed["candidates"],
        closed["inner_scores"],
        closed["choices"],
        closed["outer_scores"],
        closed["outcome_access"],
        counts,
        prediction_freeze_sha256=result["prediction_manifest"]["sha256"],
        selection_freeze_sha256=result["selection_manifest"]["sha256"],
    )
    check_sources(repository, archive, closed["inputs"])
    require(
        protocol_path.read_bytes() == protocol_raw
        and (products / "result.json").read_bytes() == result_raw
        and code_state(repository) == state,
        "Source or producer result changed during independent readback",
    )
    for pin in (
        *pins.values(),
        result["prediction_manifest"],
        result["selection_manifest"],
    ):
        reopen(products, pin)
    output.mkdir()
    facts = {
        "schema_version": "author-spatial-independent-readback.v1",
        "status": "verified",
        "source_commit": state["head"],
        "index_sha256": state["index_sha256"],
        "python_files_checked": len(state["python_files"]),
        "source_guards_passed": True,
        "sources": source_facts,
        "numerical_predictions": numerical,
        "selection_and_scoring": evaluation,
        "resources": resources(started, output, protocol["limits"], observer=True),
        "scope": "Previously exposed conditional point model; independent computational verification supplies no qualified human endorsement or field validation.",
    }
    write(output, "verification.json", facts, protocol["limits"]["max_output_bytes"])
    resources(started, output, protocol["limits"], observer=True)
    return facts


def main() -> None:
    """Run one independently audited retained-product readback."""
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
