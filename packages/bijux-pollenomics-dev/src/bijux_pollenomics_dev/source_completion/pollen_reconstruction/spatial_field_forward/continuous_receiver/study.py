"""Bounded six-owner continuous-response producer with closed-reference comparison."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import inspect
import json
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_lra.dispersal import kernels

from .. import radial_envelope
from .certificates import encoded_certificates
from .coefficients import EPSILON, PRODUCT_WIDTH, CoefficientResult
from .population import enclose_population
from .quadrature import SEVEN_NODE_RULE, ResourceRefusal
from .study_inputs import (
    INPUT_PATHS,
    LEGACY_ATOL,
    LEGACY_RTOL,
    RESOURCE_LIMITS,
    StudyCase,
    decode_json,
    geometry_record,
    prepare_inputs,
    read_inputs,
    require,
    validate_protocol,
)

PRODUCT_BYTE_LIMIT = 4_850_000
CERTIFICATE_BYTE_LIMIT = 4_500_000


@dataclass(frozen=True)
class SourceGuard:
    head: str
    index_digest: str
    consumed: tuple[tuple[str, str], ...]


def source_guard(repository: Path, protocol: Path) -> SourceGuard:
    """Internal source guards are not exported as a code-hash registry."""
    files = [
        *Path(__file__).parent.glob("*.py"),
        Path(radial_envelope.__file__),
        Path(inspect.getfile(kernels.gpm_values)),
        Path(inspect.getfile(require_absent_artifact_output)),
        protocol,
        *(repository / name for name in INPUT_PATHS),
    ]
    relative = sorted({str(path.resolve().relative_to(repository)) for path in files})
    git = ["git", "--no-optional-locks", "-C", str(repository)]
    head = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(
        [*git, "ls-files", "--error-unmatch", "--", *relative],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*git, "diff", "--exit-code", head, "--", *relative],
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
    return SourceGuard(
        head,
        hashlib.sha256(index.read_bytes()).hexdigest(),
        tuple(
            (name, hashlib.sha256((repository / name).read_bytes()).hexdigest())
            for name in relative
        ),
    )


def _write(path: Path, value: object) -> int:
    raw = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode("utf-8")
    require(not path.exists(), "Owned study output already exists")
    require(
        sum(member.stat().st_size for member in path.parent.iterdir()) + len(raw)
        <= PRODUCT_BYTE_LIMIT,
        "Product output exceeds its reserved total byte ceiling",
    )
    path.write_bytes(raw)
    return len(raw)


def _identity(path: Path, owner: Path) -> dict[str, str | int]:
    raw = path.read_bytes()
    return {
        "path": str(path.relative_to(owner)),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def compare_references(
    case: StudyCase, result: CoefficientResult
) -> list[dict[str, Any]]:
    bounds = {"K": result.homogeneous, "B1": result.first, "B2": result.second}
    rows = []
    for reference in case.references:
        interval = bounds[reference.target]
        maximum = max(
            abs(reference.value - interval.lower), abs(reference.value - interval.upper)
        )
        tolerance = LEGACY_ATOL + LEGACY_RTOL * abs(reference.value)
        rows.append(
            {
                "name": reference.name,
                "target": reference.target,
                "value_exact": str(reference.value),
                "bounds": interval.encoded(),
                "max_absolute_error_exact": str(maximum),
                "absolute_error_certified": maximum <= EPSILON,
                "correspondence_tolerance_exact": str(tolerance),
                "correspondence_pass": maximum <= tolerance,
            }
        )
    return rows


def _peak_rss() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def run_study(repository: Path, protocol_path: Path, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    repository = repository.resolve()
    protocol_path = protocol_path.resolve()
    require(
        protocol_path.is_relative_to(repository),
        "Study protocol escapes its repository",
    )
    destination = require_absent_artifact_output(repository, output)
    with protocol_path.open("rb") as stream:
        protocol_bytes = stream.read(1_000_001)
    require(
        len(protocol_bytes) <= 1_000_000, "Study protocol exceeds its metadata bound"
    )
    protocol = decode_json(protocol_bytes)
    validate_protocol(protocol)
    before = source_guard(repository, protocol_path)
    original_result, original_protocol = read_inputs(repository, protocol)
    selected = prepare_inputs(original_result, original_protocol, protocol)
    destination.mkdir()
    freeze = {
        "schema_version": "continuous-receiver-input-freeze.v1",
        "source_commit": before.head,
        "input_files": protocol["input_files"],
        "protocol_file": _identity(protocol_path, repository),
        "environment": selected.environment,
        "native_prefix": selected.native_prefix,
        "historical_A_authenticated": False,
        "law": "Ideal continuous exp(-captured_A*d^(1/8)); old floating arithmetic and q=745 truncation are separate numerical references.",
        "cases": [
            {
                "case_index": i,
                "core": case.core,
                "taxon": case.taxon,
                "anchor_order": case.anchor_order,
                "geometry": geometry_record(case.geometry),
            }
            for i, case in enumerate(selected.cases)
        ],
    }
    _write(destination / "input-freeze.json", freeze)
    # The mathematical solver receives no saved values, scores or source rows.
    population = enclose_population(
        selected.geometries,
        wall_seconds=160,
        max_leaves=4096,
        max_attempts=8191,
        max_nodes=73719,
        max_queue=4096,
    )
    require(
        len(population.results)
        == len(population.refusals)
        == len(population.budgets)
        == 6,
        "Numerical population omitted an owner",
    )
    complete: list[CoefficientResult] = []
    mapping = []
    for i, (case, result) in enumerate(
        zip(selected.cases, population.results, strict=True)
    ):
        if result is None:
            continue
        require(
            result.rule == SEVEN_NODE_RULE
            and result.conditioning is not None
            and result.conditioning.geometry == case.geometry,
            "Returned certificate has foreign geometry/rule ownership",
        )
        mapping.append(
            {
                "case_index": i,
                "core": case.core,
                "taxon": case.taxon,
                "certificate_index": len(complete),
            }
        )
        complete.append(result)
    certificate_closed = False
    certificate_refusal = None
    try:
        encoded = encoded_certificates(complete, maximum_bytes=CERTIFICATE_BYTE_LIMIT)
        (destination / "certificates.json").write_bytes(encoded)
        certificate_closed = True
    except ResourceRefusal as error:
        certificate_refusal = str(error)
    try:
        after = source_guard(repository, protocol_path)
        sources_pass = before == after
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        sources_pass = False
        certificate_refusal = f"source_guard:{type(error).__name__}"
    elapsed = time.monotonic() - started
    peak = _peak_rss()
    work = [
        {
            "attempted_panels": budget.attempts,
            "reserved_node_evaluations": budget.nodes,
            "completed_node_evaluations": budget.completed_nodes,
            "derivative_boxes": budget.derivative_boxes,
            "leaf_reservations": budget.leaves,
        }
        for budget in population.budgets
    ]
    counters_pass = (
        all(
            all(type(value) is int and value >= 0 for value in row.values())
            and row["completed_node_evaluations"]
            <= row["reserved_node_evaluations"]
            <= 73719
            and row["attempted_panels"] <= 8191
            and row["derivative_boxes"] <= 2 * row["attempted_panels"]
            and row["leaf_reservations"] <= 4096
            for row in work
        )
        and sum(row["attempted_panels"] for row in work) <= 49146
        and sum(row["reserved_node_evaluations"] for row in work) <= 442314
        and sum(row["leaf_reservations"] for row in work) <= 24576
    )
    resources_pass = elapsed < 180 and peak <= 805306368 and counters_pass
    proof_available = certificate_closed and sources_pass and resources_pass
    cases = []
    for i, (case, result, refusal) in enumerate(
        zip(selected.cases, population.results, population.refusals, strict=True)
    ):
        row: dict[str, Any] = {
            "case_index": i,
            "core": case.core,
            "taxon": case.taxon,
            "backend_refusal": refusal,
            "work": work[i],
            "complete_geometry_certificate": proof_available and result is not None,
            "backend_status": None,
            "math_bounds": None,
            "widths_exact": None,
            "all_final_widths_pass": False,
            "positive_bounds_usable": False,
            "local_integral_allocations_pass": False,
            "endpoint_product_allocations_pass": False,
            "local_allocations_pass": False,
            "references": None,
        }
        if result is not None:
            bounds = {"K": result.homogeneous, "B1": result.first, "B2": result.second}
            integral_allocations = all(
                integral.status == "certified_width" for integral in result.integrals
            )
            product_allocations = all(
                product.width <= PRODUCT_WIDTH for product in result.endpoint_products
            )
            row.update(
                {
                    "backend_status": result.status,
                    "math_bounds": {
                        name: interval.encoded() for name, interval in bounds.items()
                    },
                    "widths_exact": {
                        name: str(interval.width) for name, interval in bounds.items()
                    },
                    "all_final_widths_pass": proof_available
                    and all(interval.width <= EPSILON for interval in bounds.values()),
                    "positive_bounds_usable": proof_available
                    and all(interval.lower > 0 for interval in bounds.values()),
                    "local_integral_allocations_pass": integral_allocations,
                    "endpoint_product_allocations_pass": product_allocations,
                    "local_allocations_pass": integral_allocations
                    and product_allocations,
                }
            )
            # This is deliberately after the aggregate proof file has closed.
            if proof_available:
                row["references"] = compare_references(case, result)
        cases.append(row)
    all_complete = proof_available and all(
        result is not None for result in population.results
    )
    summary: dict[str, Any] = {
        "schema_version": "continuous-receiver-study-result.v1",
        "status": "all_coefficients_certified"
        if all_complete and all(row["all_final_widths_pass"] for row in cases)
        else "refuse_unresolved",
        "source_commit": before.head,
        "input_files": protocol["input_files"],
        "protocol_file": freeze["protocol_file"],
        "input_freeze": "input-freeze.json",
        "input_freeze_file": _identity(destination / "input-freeze.json", destination),
        "certificate_file": "certificates.json" if certificate_closed else None,
        "certificate_identity": _identity(
            destination / "certificates.json", destination
        )
        if certificate_closed
        else None,
        "certificate_cases": mapping if certificate_closed else [],
        "certificate_closed": certificate_closed,
        "certificate_refusal": certificate_refusal,
        "all_population_complete": all_complete,
        "source_guards_pass": sources_pass,
        "resource_guards_pass": resources_pass,
        "resource_limits": RESOURCE_LIMITS,
        "elapsed_seconds": elapsed,
        "integration_elapsed_seconds": population.elapsed_seconds,
        "peak_rss_bytes": peak,
        "cases": cases,
    }
    # Leave room for the root-owned time/terminal logs within the 5MB contract.
    summary_bytes = len(
        (
            json.dumps(summary, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode("utf-8")
    )
    # Include reference arithmetic and summary serialization in the owned
    # observation, rather than stopping the clock at integration.
    summary["elapsed_seconds"] = time.monotonic() - started
    summary["peak_rss_bytes"] = _peak_rss()
    if summary["elapsed_seconds"] >= 180 or summary["peak_rss_bytes"] > 805306368:
        summary.update(
            {
                "status": "refuse_unresolved",
                "resource_guards_pass": False,
                "all_population_complete": False,
            }
        )
        for row in cases:
            row.update(
                {
                    "complete_geometry_certificate": False,
                    "all_final_widths_pass": False,
                    "positive_bounds_usable": False,
                    "references": None,
                }
            )
    if (
        sum(path.stat().st_size for path in destination.iterdir()) + summary_bytes
        > PRODUCT_BYTE_LIMIT
    ):
        summary.update(
            {
                "status": "refuse_unresolved",
                "resource_guards_pass": False,
                "all_population_complete": False,
                "certificate_refusal": "total_product_byte_ceiling",
            }
        )
        for row in cases:
            row.update(
                {
                    "complete_geometry_certificate": False,
                    "all_final_widths_pass": False,
                    "positive_bounds_usable": False,
                    "references": None,
                }
            )
    _write(destination / "result.json", summary)
    require(
        sum(path.stat().st_size for path in destination.iterdir())
        <= PRODUCT_BYTE_LIMIT,
        "Product output exceeded reserved total byte ceiling",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    signal.alarm(180)
    result = run_study(arguments.repository, arguments.protocol, arguments.output)
    signal.alarm(0)
    print(
        json.dumps(
            {
                "status": result["status"],
                "cases": len(result["cases"]),
                "source_guards_pass": result["source_guards_pass"],
                "resource_guards_pass": result["resource_guards_pass"],
            }
        )
    )
    if not result["source_guards_pass"] or not result["resource_guards_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
