"""Bounded source-free cost observation for a long-annulus Duffy response.

This executable is a synthetic feasibility control, not a real-case producer.
The input geometry is literal test data; no study packet or raw source is read.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import resource
import signal
import sys
import time

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward import (
    radial_envelope,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver import (
    arithmetic,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.certificates import (
    encoded_certificates,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.coefficients import (
    EPSILON,
    certify,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    SEVEN_NODE_RULE,
    SIMPSON_RULE,
    ResourceRefusal,
    WorkBudget,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.radial_partition import (
    DYADIC_RADIAL,
    WHOLE_ANNULUS,
)


def source_pins() -> dict[str, str]:
    """Hash the probe and receiver sources used for its execution record."""
    directory = Path(arithmetic.__file__).parent
    paths = [*directory.glob("*.py"), Path(radial_envelope.__file__), Path(__file__)]
    return {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(paths)
    }


def main() -> None:
    """Run the bounded source-free receiver probe and record its refusals."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--rule", choices=(SIMPSON_RULE, SEVEN_NODE_RULE), default=SIMPSON_RULE
    )
    parser.add_argument(
        "--partition", choices=(WHOLE_ANNULUS, DYADIC_RADIAL), default=WHOLE_ANNULUS
    )
    arguments = parser.parse_args()
    output: Path = arguments.output
    output.mkdir(parents=True, exist_ok=False)
    signal.alarm(60)
    started = time.monotonic()
    before = source_pins()
    model = Geometry(
        Fraction(3, 5),
        Fraction(1),
        Fraction(1025),
        (Fraction(137), Fraction(41)),
        (Fraction(-293), Fraction(107)),
    )
    # Leave finite time for serialization and terminal resource/source guards.
    budget = WorkBudget(wall_seconds=45)
    report: dict[str, object] = {
        "schema_version": "continuous-receiver-synthetic-feasibility.v1",
        "source_free": True,
        "actual_six_case_calculation": False,
        "new_fits_or_point_forecasts": 0,
        "geometry": {
            "A": str(model.coefficient),
            "R": str(model.receiver),
            "L": str(model.outer),
            "first": [str(value) for value in model.first],
            "second": [str(value) for value in model.second],
        },
        "target_full_width": str(EPSILON),
        "quadrature_rule": arguments.rule,
        "radial_partition": arguments.partition,
    }
    try:
        result = certify(
            model, budget, rule=arguments.rule, partition=arguments.partition
        )
        report.update(
            {
                "status": result.status,
                "complete_continuous_enclosure": True,
                "widths_exact": {
                    "K": str(result.homogeneous.width),
                    "B1": str(result.first.width),
                    "B2": str(result.second.width),
                },
                "widths_float_diagnostic": {
                    "K": float(result.homogeneous.width),
                    "B1": float(result.first.width),
                    "B2": float(result.second.width),
                },
                "integrals": [
                    {
                        "status": row.status,
                        "refusal": row.refusal,
                        "full_width": str(row.enclosure.width),
                        "leaves": len(row.panels),
                    }
                    for row in result.integrals
                ],
            }
        )
        encoded = encoded_certificates([result], maximum_bytes=950_000)
        (output / "certificate.json").write_bytes(encoded)
        report["certificate_bytes"] = len(encoded)
        report["certificate_sha256"] = hashlib.sha256(encoded).hexdigest()
    except ResourceRefusal as error:
        report.update(
            {
                "status": "refuse_unresolved",
                "refusal": str(error),
                "complete_continuous_enclosure": False,
                "coefficient_bounds_available": False,
            }
        )
    elapsed = time.monotonic() - started
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = rss if sys.platform == "darwin" else rss * 1024
    after = source_pins()
    report.update(
        {
            "elapsed_seconds": elapsed,
            "peak_rss_bytes": peak_bytes,
            "resources": {
                "wall_seconds_maximum": 60,
                "rss_bytes_maximum": 536870912,
                "total_output_bytes_maximum": 1048576,
            },
            "work": {
                "attempted_panels": budget.attempts,
                "reserved_node_evaluations": budget.nodes,
                "completed_node_evaluations": budget.completed_nodes,
                "derivative_boxes": budget.derivative_boxes,
                "leaf_reservations": budget.leaves,
            },
            "source_guards_pass": before == after,
            "resource_guards_pass": elapsed < 60 and peak_bytes <= 536870912,
        }
    )
    encoded_report = (
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    total = len(encoded_report) + sum(path.stat().st_size for path in output.iterdir())
    if total > 1048576:
        raise ResourceRefusal("synthetic_total_output_bytes")
    (output / "report.json").write_bytes(encoded_report)
    signal.alarm(0)
    print(
        json.dumps(
            {
                "status": report["status"],
                "elapsed_seconds": elapsed,
                "peak_rss_bytes": peak_bytes,
                "output_bytes": total,
            }
        )
    )
    if before != after or not report["resource_guards_pass"]:
        raise RuntimeError("Source or resource guard failed")


if __name__ == "__main__":
    main()
