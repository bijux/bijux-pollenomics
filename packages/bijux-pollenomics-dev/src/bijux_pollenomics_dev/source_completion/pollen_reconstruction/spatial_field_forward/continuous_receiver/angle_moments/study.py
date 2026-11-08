"""One fixed-input six-owner coefficient study; native A is never recaptured."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import signal
import time
from typing import Any

from ..coefficients import EPSILON
from ..verification.contracts import OWNERS, RESOURCE_LIMITS
from . import METHOD
from .certificates import encoded_certificates
from .inputs import identity, read_inputs, require
from .population import enclose_population
from .transport import (
    check_terminal,
    environment,
    fresh_output,
    source_guard,
    write_json,
)


def _deadline(_number: int, _frame: object) -> None:
    raise TimeoutError("Original 180-second process ceiling reached")


def run_study(root: Path, protocol: Path, output: Path) -> dict[str, Any]:
    """Keep all cases and source/resource facts, including every precision refusal."""
    started = time.monotonic()
    root, protocol, output = root.resolve(), protocol.resolve(), output.absolute()
    require(protocol.is_relative_to(root), "Scientific protocol escaped source owner")
    destination = fresh_output(root, output)
    report: dict[str, Any] = {
        "schema_version": "continuous-receiver-angle-moments-result.v1",
        "method": METHOD,
        "status": "failed",
        "native_prefix_recaptured": False,
        "cases": [
            {
                "case_index": i,
                "core": core,
                "taxon": taxon,
                "complete": False,
                "status": "not_certified",
            }
            for i, (core, taxon) in enumerate(OWNERS)
        ],
    }
    previous = signal.signal(signal.SIGALRM, _deadline)
    signal.setitimer(signal.ITIMER_REAL, 180)
    try:
        inputs = read_inputs(root, protocol)
        runtime = environment(root)
        before = source_guard(root, inputs)
        write_json(
            destination,
            "execution-context.json",
            {
                "source": asdict(before),
                "inputs": inputs.identities,
                "environment": runtime,
                "resources": RESOURCE_LIMITS,
                "method": METHOD,
                "law_capture_source_commit": inputs.freeze["source_commit"],
                "law": inputs.protocol["law"],
                "scope": inputs.protocol["limits"],
            },
        )
        population = enclose_population(inputs.geometries)
        complete = [value for value in population.results if value is not None]
        rows = []
        certificate_index = 0
        for index, (frozen, result, refusal, budget) in enumerate(
            zip(
                inputs.freeze["cases"],
                population.results,
                population.refusals,
                population.budgets,
                strict=True,
            )
        ):
            row: dict[str, Any] = {
                "case_index": index,
                "core": frozen["core"],
                "taxon": frozen["taxon"],
                "geometry": frozen["geometry"],
                "complete": result is not None,
                "backend_refusal": refusal,
                "work": {
                    "attempted_panels": budget.attempts,
                    "reserved_node_evaluations": budget.nodes,
                    "completed_node_evaluations": budget.completed_nodes,
                    "derivative_boxes": budget.derivative_boxes,
                    "leaf_reservations": budget.leaves,
                },
            }
            if result is None:
                row["status"] = "initial_coverage_incomplete_or_not_executed"
            else:
                coefficients = (result.homogeneous, result.first, result.second)
                row.update(
                    certificate_index=certificate_index,
                    status=result.status,
                    coefficient_bounds={
                        name: value.encoded()
                        for name, value in zip(
                            ("K", "B1", "B2"), coefficients, strict=True
                        )
                    },
                    widths={
                        name: str(value.width)
                        for name, value in zip(
                            ("K", "B1", "B2"), coefficients, strict=True
                        )
                    },
                    width_pass=[value.width <= EPSILON for value in coefficients],
                    positive_bounds=[value.lower > 0 for value in coefficients],
                    saved_leaves=sum(len(value.panels) for value in result.integrals),
                    complete_domains=len(result.integrals),
                    q_bound=str(result.partition.contraction.q_bound),
                    global_series_remainder_radius=str(
                        result.partition.contraction.remainder_radius
                    ),
                )
                certificate_index += 1
            rows.append(row)
        report.update(
            source_commit=before.head,
            input_identities=inputs.identities,
            resource_limits=RESOURCE_LIMITS,
            integration_elapsed_seconds=population.elapsed_seconds,
            cooperative_work_deadline_reached=any(
                value and "wall_seconds" in value for value in population.refusals
            ),
            cases=rows,
            complete_cases=len(complete),
            certified_widths=sum(sum(row.get("width_pass", [])) for row in rows),
            positive_bounds=sum(sum(row.get("positive_bounds", [])) for row in rows),
            independent_precision="not_yet_evaluated",
            saved_native_reference_diagnostics="historical results retained; not re-evaluated",
            scope="Same retained captured-A law; no target inspection, native recapture, source admission, refit, prediction, score or field claim",
        )
        raw = encoded_certificates(complete, maximum_bytes=4_500_000)
        (destination / "certificates.json").write_bytes(raw)
        report["certificate_identity"] = identity(raw)
        terminal = check_terminal(root, protocol, before, inputs, started, destination)
        passes = len(complete) == 6 and all(
            all(row.get("width_pass", [])) and all(row.get("positive_bounds", []))
            for row in rows
        )
        report.update(
            terminal=terminal,
            status="producer_precision_usable" if passes else "refuse_unresolved",
        )
    except Exception as error:
        report["error"] = str(error)
        report["elapsed_seconds_at_failure"] = time.monotonic() - started
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        write_json(destination, "result.json", report)
    return report


def main() -> None:
    """Run the explicitly selected committed protocol into a fresh artifact owner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_study(args.repository, args.protocol, args.output)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "status",
                    "source_commit",
                    "complete_cases",
                    "certified_widths",
                    "positive_bounds",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
