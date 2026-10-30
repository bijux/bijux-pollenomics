"""Bound true ring masses, then score a closed continuous-law prediction packet."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import inspect
import json
from pathlib import Path
import signal
import subprocess
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ...abborrtjarnen_ppe_dependence.sources import bound_files
from .. import radial_envelope, radial_envelope_workflow
from .coefficients import EPSILON
from .quadrature import IntegralResult
from .ring_bounds import RingCaseResult, coefficient_q_spreads, enclose_ring_population
from .ring_inputs import RingInputs, identity, read_ring_inputs
from .ring_predictions import prediction_contexts, score_closed, summarize
from .study import _peak_rss
from .study_inputs import OWNERS, decode_json, geometry_record, require


def source_guard(
    repository: Path, protocol_path: Path, pins: dict[str, Any]
) -> tuple[Any, ...]:
    """Freeze consumed maintained code, input bytes and the raw Git index."""
    files = {
        *Path(__file__).parent.rglob("*.py"),
        Path(radial_envelope.__file__),
        Path(radial_envelope_workflow.__file__),
        Path(inspect.getfile(bound_files)),
        Path(inspect.getfile(require_absent_artifact_output)),
        protocol_path,
    }
    names = sorted(str(p.resolve().relative_to(repository)) for p in files)
    git = ["git", "--no-optional-locks", "-C", str(repository)]
    head = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(
        [*git, "ls-files", "--error-unmatch", "--", *names],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*git, "diff", "--exit-code", head, "--", *names],
        check=True,
        capture_output=True,
    )
    index = Path(
        subprocess.check_output(
            [*git, "rev-parse", "--git-path", "index"], text=True
        ).strip()
    )
    if not index.is_absolute():
        index = repository / index
    inputs = []
    for name, pin in sorted(pins.items()):
        observed = identity((repository / name).read_bytes())
        require(observed == pin, "Pinned scientific input changed")
        inputs.append((name, observed["bytes"], observed["sha256"]))
    return (
        head,
        hashlib.sha256(index.read_bytes()).hexdigest(),
        tuple(
            (name, hashlib.sha256((repository / name).read_bytes()).hexdigest())
            for name in names
        ),
        tuple(inputs),
    )


def _integral(result: IntegralResult | None) -> dict[str, Any] | None:
    if result is None:
        return None
    return {
        "bounds": result.enclosure.encoded(),
        "status": result.status,
        "refusal": result.refusal,
        "quadrature_rule": result.rule,
        "leaves": [
            {
                "box": [[str(a), str(b)] for a, b in panel.box],
                "node_sum": panel.node_sum.encoded(),
                "error_radius": str(panel.error_radius),
                "directional_radii": [str(v) for v in panel.directional_radii],
                "quadrature_rule": panel.rule,
            }
            for panel in result.panels
        ],
    }


def case_record(
    inputs: RingInputs, index: int, result: RingCaseResult, work: Any
) -> dict[str, Any]:
    """Record one case's endpoint outcomes, bounds and charged work."""
    bounds = result.bounds
    values = (
        None
        if bounds is None
        else {"K": bounds.homogeneous, "B1": bounds.first, "B2": bounds.second}
    )
    row: dict[str, Any] = {
        "case_index": index,
        "core": OWNERS[index][0],
        "taxon": OWNERS[index][1],
        "geometry": geometry_record(inputs.geometries[index]),
        "edges_exact": [str(v) for v in inputs.edges[index]],
        "endpoints": [_integral(v) for v in result.endpoints],
        "endpoint_refusals": list(result.refusals),
        "backend_refusal": result.refusal,
        "coefficient_bounds": None
        if values is None
        else {k: v.encoded() for k, v in values.items()},
        "raw_endpoint_widths_pass": all(
            v is not None and v.enclosure.width <= Fraction(1, 10**10)
            for v in result.endpoints
        ),
        "all_final_widths_pass": values is not None
        and all(v.width <= EPSILON for v in values.values()),
        "positive_bounds_usable": values is not None
        and all(v.lower > 0 for v in values.values()),
        "work": {
            "attempted_panels": work.attempts,
            "reserved_node_evaluations": work.nodes,
            "completed_node_evaluations": work.completed_nodes,
            "derivative_boxes": work.derivative_boxes,
            "leaf_reservations": work.leaves,
        },
    }
    if "frontier" in inputs.protocol:
        spreads = None if bounds is None else coefficient_q_spreads(bounds)
        row["q_uncertainty_spreads_exact"] = (
            None if spreads is None else {k: str(v) for k, v in spreads.items()}
        )
        row["q_uncertainty_target_pass"] = (
            spreads is not None and max(spreads.values()) <= EPSILON / 16
        )
    return row


def _write(path: Path, value: Any, limit: int) -> dict[str, str | int]:
    raw = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()
    require(
        not path.exists() and len(raw) <= limit,
        "Fresh bounded scientific output required",
    )
    require(
        sum(p.stat().st_size for p in path.parent.iterdir()) + len(raw) <= 4_850_000,
        "Total scientific output byte cap exceeded",
    )
    path.write_bytes(raw)
    return {"path": path.name, **identity(raw)}


def run_study(repository: Path, protocol_path: Path, output: Path) -> dict[str, Any]:
    """Publish ring predictions and preserve every population refusal."""
    started = time.monotonic()
    repository, protocol_path = repository.resolve(), protocol_path.resolve()
    require(protocol_path.is_relative_to(repository), "Protocol escapes repository")
    destination = require_absent_artifact_output(repository, output)
    inputs = read_ring_inputs(repository, protocol_path)
    before = source_guard(repository, protocol_path, inputs.protocol["input_files"])
    destination.mkdir()
    protocol_pin = {
        "path": str(protocol_path.relative_to(repository)),
        **identity(protocol_path.read_bytes()),
    }
    population = enclose_ring_population(
        inputs.geometries,
        inputs.edges,
        wall_seconds=160,
        priority=inputs.protocol.get("frontier", {}).get("priority", "raw_width"),
    )
    require(
        len(population.results) == len(population.budgets) == 6, "Lost scientific case"
    )
    rows = [
        case_record(inputs, i, result, work)
        for i, (result, work) in enumerate(
            zip(population.results, population.budgets, strict=True)
        )
    ]
    proof_pin = _write(
        destination / "certificates.json",
        {"schema_version": "continuous-receiver-ring-certificates.v1", "cases": rows},
        4_000_000,
    )
    contexts = prediction_contexts(inputs.prediction, population.results)
    prediction = {
        "schema_version": "continuous-receiver-ring-predictions.v1",
        "source_commit": before[0],
        "source_prediction_commit": inputs.prediction["source_commit"],
        "protocol_file": protocol_pin,
        "certificate_file": proof_pin,
        "contexts": contexts,
    }
    prediction_path = destination / "prediction-ranges.json"
    prediction_pin = _write(prediction_path, prediction, 400_000)
    # Both proofs and all count-free prediction ranges are closed before
    # the scorer receives the already exposed target observation packet.
    old_scored = decode_json(inputs.scored_path.read_bytes())
    scores = score_closed(prediction_path, old_scored, inputs.prediction)
    summary = summarize(scores, old_scored)
    require(
        source_guard(repository, protocol_path, inputs.protocol["input_files"])
        == before,
        "Consumed source/input/index changed",
    )
    elapsed, peak = time.monotonic() - started, _peak_rss()
    counters_pass = all(
        r["work"]["attempted_panels"] <= 8191
        and r["work"]["completed_node_evaluations"]
        <= r["work"]["reserved_node_evaluations"]
        <= 73719
        and r["work"]["derivative_boxes"] <= r["work"]["attempted_panels"]
        and r["work"]["leaf_reservations"] <= 4096
        for r in rows
    )
    resource_pass = elapsed < 180 and peak <= 805306368 and counters_pass
    complete = all(
        all(v is not None for v in case.endpoints) and case.bounds is not None
        for case in population.results
    )
    result = {
        "schema_version": "continuous-receiver-ring-result.v1",
        "source_commit": before[0],
        "protocol_file": protocol_pin,
        "prediction_file": prediction_pin,
        "certificate_file": proof_pin,
        "source_guards_pass": True,
        "resource_guards_pass": resource_pass,
        "elapsed_seconds": elapsed,
        "integration_elapsed_seconds": population.elapsed_seconds,
        "peak_rss_bytes": peak,
        "status": "continuous_law_bounds"
        if resource_pass and complete
        else "refuse_incomplete"
        if resource_pass
        else "refuse_resources",
        "all_endpoint_partitions_complete": complete,
        "all_774_raw_endpoint_widths_pass": all(
            r["raw_endpoint_widths_pass"] for r in rows
        ),
        "all_18_coefficient_widths_pass": all(r["all_final_widths_pass"] for r in rows),
        "counts": {
            "cases": 6,
            "endpoint_slots": sum(len(r["endpoints"]) for r in rows),
            "contexts": len(contexts),
            "family_slots": len(scores),
        },
        "scores": scores,
        "summary": summary,
        "limits": "Ideal reused captured-A law; fixed source covers/PPE/static geometry. Coefficient EPS, endpoint precision, positive prediction support and score separation are separate decisions. No historical-A, field, measured vegetation or untouched acceptance.",
    }
    _write(destination / "result.json", result, 400_000)
    return result


def main() -> None:
    """Run the declared ring study and print its outcome summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    signal.alarm(180)
    result = run_study(args.repository, args.protocol, args.output)
    signal.alarm(0)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "status",
                    "counts",
                    "all_774_raw_endpoint_widths_pass",
                    "all_18_coefficient_widths_pass",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
