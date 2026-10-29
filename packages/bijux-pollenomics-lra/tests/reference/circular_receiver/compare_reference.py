"""Compare three saved circle-overlap R factors with fresh maintained quadrature."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import stat
from typing import Any, Protocol

ABSOLUTE_TOLERANCE = 1e-8
MAX_DIAGNOSTIC_BYTES = 65_536
MAX_REPORT_BYTES = 65_536
CASES = (
    ("inner_ring", 81.0, 500.0),
    ("outer_ring", 500.0, 1000.0),
    ("combined_annulus", 81.0, 1000.0),
)
COLUMNS = (
    "factor",
    "raw_factor",
    "estimated_absolute_error",
    "tail_mass_bound",
    "method",
    "coefficient_from_parameters",
    "exponent",
    "absolute_tolerance",
    "relative_tolerance",
    "quadrature_limit",
    "subdivisions_used",
    "case",
)


class Response(Protocol):
    @property
    def factor(self) -> float: ...

    @property
    def estimated_absolute_error(self) -> float: ...


Evaluator = Callable[..., Response]


def _finite(value: str, name: str) -> float:
    if not re.fullmatch(
        r"[-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][-+]?[0-9]+)?", value
    ):
        raise ValueError(f"Invalid R numeric field {name}")
    try:
        number = float(value)
    except (ValueError, TypeError) as error:
        raise ValueError(f"Invalid R numeric field {name}") from error
    if not math.isfinite(number):
        raise ValueError(f"Nonfinite R numeric field {name}")
    return number


def _identity(value: str, length: int) -> str:
    if not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
        raise ValueError("Expected a lowercase hexadecimal source identity")
    return value


def _physical_path(path: Path) -> Path:
    """Reject traversal and linked ancestors without resolving them away."""
    if ".." in path.parts:
        raise ValueError("Reference paths cannot traverse parent directories")
    absolute = path.absolute()
    for parent in reversed(absolute.parents):
        if not stat.S_ISDIR(parent.lstat().st_mode):
            raise ValueError("Reference paths require physical directory ancestors")
    return absolute


def _output_path(root: Path, path: Path) -> Path:
    owned = _physical_path(root)
    if not stat.S_ISDIR(owned.lstat().st_mode):
        raise ValueError("Output root must be a physical directory")
    output = _physical_path(path)
    if not output.is_relative_to(owned):
        raise ValueError("Comparison output must stay inside its explicit output root")
    if output.exists() or output.is_symlink():
        raise ValueError("Comparison output must be absent")
    return output


def read_diagnostics(
    path: Path, checksum: str
) -> tuple[list[dict[str, Any]], dict[str, object]]:
    """Authenticate one bounded regular TSV buffer before interpreting any values."""
    _identity(checksum, 64)
    path = _physical_path(path)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as source:
        metadata = os.fstat(source.fileno())
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size > MAX_DIAGNOSTIC_BYTES
        ):
            raise ValueError("R diagnostics must be a bounded regular file")
        body = source.read(MAX_DIAGNOSTIC_BYTES + 1)
    if len(body) > MAX_DIAGNOSTIC_BYTES or hashlib.sha256(body).hexdigest() != checksum:
        raise ValueError("R diagnostics byte identity changed")
    reader = csv.DictReader(
        io.StringIO(body.decode("utf-8"), newline=""), delimiter="\t", strict=True
    )
    if reader.fieldnames != list(COLUMNS):
        raise ValueError("R diagnostics columns differ from the declared producer")
    rows = list(reader)
    if len(rows) != len(CASES) or [row.get("case") for row in rows] != [
        case[0] for case in CASES
    ]:
        raise ValueError(
            "R diagnostics require the exact ordered three-case population"
        )
    parsed: list[dict[str, Any]] = []
    coefficient = 4 * 0.03 / (0.25 * 3 * math.sqrt(math.pi) * 0.12)
    for row in rows:
        if set(row) != set(COLUMNS) or any(value is None for value in row.values()):
            raise ValueError("R diagnostics row shape is invalid")
        numeric = {
            key: _finite(row[key], key)
            for key in COLUMNS
            if key not in {"case", "method"}
        }
        if (
            row["method"] != "displacement_circle_overlap_one_dimensional"
            or not 0 <= numeric["factor"] <= 1
            or not -1e-11 <= numeric["raw_factor"] <= 1 + 1e-11
            or numeric["estimated_absolute_error"] < 0
            or numeric["tail_mass_bound"] != 0
            or numeric["absolute_tolerance"] != 1e-11
            or numeric["relative_tolerance"] != 1e-10
            or numeric["quadrature_limit"] != 1000
            or numeric["exponent"] != 0.125
            or not math.isclose(
                numeric["coefficient_from_parameters"], coefficient, rel_tol=1e-12
            )
            or not numeric["subdivisions_used"].is_integer()
            or not 3 <= numeric["subdivisions_used"] <= 3000
            or not math.isclose(
                numeric["factor"],
                min(1, max(0, numeric["raw_factor"])),
                rel_tol=0,
                abs_tol=1e-14,
            )
        ):
            raise ValueError("R diagnostics violate the frozen numerical profile")
        parsed.append({"case": row["case"], "method": row["method"], **numeric})
    return parsed, {
        "path": str(path.absolute()),
        "sha256": checksum,
        "bytes": len(body),
    }


def _compare(
    rows: list[dict[str, Any]], evaluator: Evaluator
) -> list[dict[str, object]]:
    comparisons: list[dict[str, object]] = []
    for row, (case, inner, outer) in zip(rows, CASES, strict=True):
        parameters = {
            "receiver_radius_m": 80.0,
            "inner_radius_m": inner,
            "outer_radius_m": outer,
            "fall_speed_m_s": 0.03,
            "diffusion_coefficient": 0.12,
            "turbulence_parameter": 0.25,
            "wind_speed_m_s": 3.0,
            "absolute_tolerance": 1e-9,
            "relative_tolerance": 1e-8,
            "quadrature_limit": 100,
        }
        response = evaluator(**parameters)
        factor, estimate = response.factor, response.estimated_absolute_error
        if (
            isinstance(factor, bool)
            or isinstance(estimate, bool)
            or not math.isfinite(factor)
            or not 0 <= factor <= 1
            or not math.isfinite(estimate)
            or estimate < 0
        ):
            raise ValueError("Maintained Python response is invalid")
        difference = abs(factor - row["factor"])
        comparisons.append(
            {
                "case": case,
                "parameters": parameters,
                "r": row,
                "python_factor": factor,
                "python_estimated_absolute_error": estimate,
                "absolute_difference": difference,
                "raw_factor_absolute_difference": abs(factor - row["raw_factor"]),
                "within_absolute_tolerance": difference <= ABSOLUTE_TOLERANCE,
            }
        )
    return comparisons


def _load_evaluator() -> tuple[Evaluator, list[dict[str, object]]]:
    # The explicit numerical command imports the qualified engine; TSV tests do not.
    from bijux_pollenomics_lra.dispersal import kernels, receiver_annulus

    sources: list[dict[str, object]] = []
    for module in (receiver_annulus, kernels):
        if module.__file__ is None:
            raise RuntimeError("Maintained operator source has no physical identity")
        path = Path(module.__file__).resolve(strict=True)
        body = path.read_bytes()
        sources.append(
            {
                "path": str(path),
                "sha256": hashlib.sha256(body).hexdigest(),
                "bytes": len(body),
            }
        )
    return receiver_annulus.circular_receiver_annulus, sources


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnostics", type=Path, required=True)
    parser.add_argument("--diagnostics-sha256", required=True)
    parser.add_argument("--r-source-epoch", required=True)
    parser.add_argument("--python-source-epoch", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    r_epoch = _identity(args.r_source_epoch, 40)
    python_epoch = _identity(args.python_source_epoch, 40)
    output = _output_path(args.output_root, args.output)
    rows, source = read_diagnostics(args.diagnostics, args.diagnostics_sha256)
    evaluator, python_sources = _load_evaluator()
    comparisons = _compare(rows, evaluator)
    passed = all(row["within_absolute_tolerance"] for row in comparisons)
    report = {
        "schema_version": "circular-receiver-reference-comparison.v1",
        "r_source_epoch": r_epoch,
        "python_source_epoch": python_epoch,
        "r_diagnostics": source,
        "python_operator_sources": python_sources,
        "comparison_count": len(comparisons),
        "absolute_tolerance": ABSOLUTE_TOLERANCE,
        "all_within_absolute_tolerance": passed,
        "comparisons": comparisons,
        "scope": "Three controlled same-formula scalar comparisons; nonrigorous numerical error estimates, no historical-author, field, covariance or calibrated-uncertainty claim.",
    }
    body = (
        json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()
    if len(body) > MAX_REPORT_BYTES:
        raise ValueError("Comparison report exceeds its byte budget")
    with output.open("xb") as target:
        target.write(body)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
