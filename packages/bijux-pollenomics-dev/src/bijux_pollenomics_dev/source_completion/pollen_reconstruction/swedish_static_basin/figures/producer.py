"""Project retained aggregate model outputs into the declared figure CSV axis."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from ..sources import FAMILY, read_bound, sha256

DECLARATION = FAMILY / "inputs/figure-source-identities.json"
FIELDS = [
    "core",
    "taxon",
    "younger_cal_bp",
    "older_cal_bp_exclusive",
    "window_midpoint_cal_bp",
    "direct_panel_pollen_percent",
    "corrected_panel_cover_percent",
    "conditional_standard_error_pp",
]


def _record(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("Figure captured records must be objects")
    return value


def _array(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("Figure captured population must be an array")
    return value


def _finite_number(value: object) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError("Figure requires finite numerical cells")
    return value


def _vector(value: object, size: int) -> list[float]:
    values = [_finite_number(cell) for cell in _array(value)]
    if len(values) != size or any(cell < 0 for cell in values):
        raise ValueError("Figure requires finite flat values on the target axis")
    return values


def projection(report: dict[str, object]) -> bytes:
    """Require the literal captured axis before projecting aggregate figure rows."""
    rows = []
    for raw_core in _array(report["cores"]):
        core = _record(raw_core)
        axis = []
        for token in _array(core["parameter_taxa"]):
            if not isinstance(token, str):
                raise ValueError("Figure target labels must be literal strings")
            axis.append(token)
        if not axis or len(axis) != len(set(axis)):
            raise ValueError("Figure target axis must be nonempty and unique")
        code = core["metadata_code"]
        if not isinstance(code, str):
            raise ValueError("Figure core identity must be a literal string")
        seen: set[tuple[float, float]] = set()
        for raw_result in _array(core["results"]):
            result = _record(raw_result)
            if result["profile"] != "metadata_radius_wind_3":
                continue
            bounds = (
                _finite_number(result["younger_cal_bp"]),
                _finite_number(result["older_cal_bp_exclusive"]),
            )
            if bounds[0] >= bounds[1] or bounds in seen:
                raise ValueError(
                    "Figure windows must be unique positive finite intervals"
                )
            seen.add(bounds)
            values = [
                _vector(result[key], len(axis))
                for key in ("direct_pollen_panel_fraction", "cover", "standard_error")
            ]
            if any(abs(sum(v) - 1) > 1e-10 for v in values[:2]):
                raise ValueError("Figure fractions must close on the declared panel")
            for index, taxon in enumerate(axis):
                rows.append(
                    dict(
                        zip(
                            FIELDS,
                            [
                                code,
                                taxon,
                                *bounds,
                                sum(bounds) / 2,
                                100 * values[0][index],
                                100 * values[1][index],
                                100 * values[2][index],
                            ],
                            strict=True,
                        )
                    )
                )
    if not rows:
        raise ValueError("Figure baseline output has no supported rows")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def publish(repository: Path, source_root: Path, output: Path) -> dict[str, object]:
    """Publish the declared aggregate figure projection from authenticated source bytes."""
    repository = repository.absolute()
    source_root = source_root.absolute()
    if (
        source_root.resolve() != source_root
        or not (source_root / "pyproject.toml").is_file()
    ):
        raise ValueError("Figure source root must be a contained product checkout")
    output = require_absent_artifact_output(repository, output)
    declaration = source_root / DECLARATION
    if declaration.resolve() != declaration or not declaration.is_file():
        raise ValueError("Figure source declaration must be contained and regular")
    declaration_before = sha256(declaration)
    identities = json.loads(declaration.read_bytes())["source_files"]
    if set(identities) != {str(FAMILY / "report.json")}:
        raise ValueError(
            "Figure projection consumes exactly one declared aggregate numerical report"
        )
    relative = str(FAMILY / "report.json")
    body = read_bound(source_root, relative, identities[relative])
    report = json.loads(body)
    controls = {p.name: sha256(p) for p in Path(__file__).parent.glob("*.py")}
    csv_body = projection(report)
    stage = Path(tempfile.mkdtemp(prefix=".swedish-panel-figure-", dir=output.parent))
    published = False
    try:
        products = stage / "source-products"
        products.mkdir()
        (products / "panel-comparison.csv").write_bytes(csv_body)
        read_bound(source_root, relative, identities[relative])
        if sha256(declaration) != declaration_before or controls != {
            p.name: sha256(p) for p in Path(__file__).parent.glob("*.py")
        }:
            raise ValueError(
                "Figure input/control authority changed before publication"
            )
        require_absent_artifact_output(repository, output)
        os.replace(products, output)
        published = True
    finally:
        if published:
            shutil.rmtree(stage)
    capture = {
        "source_report": relative,
        "source_report_sha256": hashlib.sha256(body).hexdigest(),
        "source_producer_candidate": report["producer_candidate"],
        "projection_controls_sha256": controls,
        "figure_declaration_sha256": declaration_before,
        "csv_sha256": hashlib.sha256(csv_body).hexdigest(),
        "scope": "Aggregate baseline projection only. No physical/R execution, source-mask admission, new measured data or new scientific claim.",
    }
    print(json.dumps(capture), flush=True)
    return capture


def main(argv: list[str] | None = None) -> int:
    """Parse the source-bound figure projection command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    publish(args.repository, args.source_root or args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
