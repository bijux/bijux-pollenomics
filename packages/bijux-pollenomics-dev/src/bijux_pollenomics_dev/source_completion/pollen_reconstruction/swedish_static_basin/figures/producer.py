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


def projection(report: dict) -> bytes:
    rows = []
    for core in report["cores"]:
        axis = core["parameter_taxa"]
        if not axis or len(axis) != len(set(axis)):
            raise ValueError("Figure target axis must be nonempty and unique")
        seen = set()
        for result in core["results"]:
            if result["profile"] != "metadata_radius_wind_3":
                continue
            bounds = (result["younger_cal_bp"], result["older_cal_bp_exclusive"])
            if (
                any(not math.isfinite(v) for v in bounds)
                or bounds[0] >= bounds[1]
                or bounds in seen
            ):
                raise ValueError(
                    "Figure windows must be unique positive finite intervals"
                )
            seen.add(bounds)
            values = [
                result["direct_pollen_panel_fraction"],
                result["cover"],
                result["standard_error"],
            ]
            if any(
                len(v) != len(axis)
                or any(
                    isinstance(x, bool)
                    or not isinstance(x, (int, float))
                    or not math.isfinite(x)
                    or x < 0
                    for x in v
                )
                for v in values
            ):
                raise ValueError(
                    "Figure requires finite flat values on the target axis"
                )
            if any(abs(sum(v) - 1) > 1e-10 for v in values[:2]):
                raise ValueError("Figure fractions must close on the declared panel")
            for index, taxon in enumerate(axis):
                rows.append(
                    dict(
                        zip(
                            FIELDS,
                            [
                                core["metadata_code"],
                                taxon,
                                *bounds,
                                sum(bounds) / 2,
                                100 * values[0][index],
                                100 * values[1][index],
                                100 * values[2][index],
                            ],
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


def publish(repository: Path, source_root: Path, output: Path) -> dict:
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    publish(args.repository, args.source_root or args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
