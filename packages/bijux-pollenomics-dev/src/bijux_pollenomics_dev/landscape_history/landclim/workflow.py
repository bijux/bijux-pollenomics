"""Publish deterministic, source-bound Swedish-center model summaries."""

from __future__ import annotations

from collections import Counter
import csv
from dataclasses import asdict
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from bijux_pollenomics.reporting.modeled_context import contracts, metric_families

from .aggregation import BAND_COUNTS, POLICIES, WEIGHTINGS, aggregate
from .classification import (
    CLOSURE_TOLERANCE_PP,
    DEFINITIONS,
    METRIC_KEYS,
    classify_means,
)
from .inputs import SOURCE_PATHS, WINDOWS, CellWindow, load_cells

CALCULATION_FILES = (
    "__init__.py",
    "__main__.py",
    "classification.py",
    "inputs.py",
    "aggregation.py",
    "workflow.py",
)


def _pin(path: Path, label: str) -> dict[str, Any]:
    body = path.read_bytes()
    return {
        "path": label,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def _source_pins() -> list[dict[str, Any]]:
    prefix = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/landscape_history/landclim"
    own = [
        _pin(Path(__file__).parent / name, f"{prefix}/{name}")
        for name in CALCULATION_FILES
    ]
    dependencies = []
    for module in (contracts, metric_families):
        location = module.__file__
        if location is None:
            raise ValueError("Calculation dependency has no source-file identity")
        dependencies.append(
            _pin(
                Path(location),
                f"packages/bijux-pollenomics/src/bijux_pollenomics/reporting/modeled_context/{module.__name__.rsplit('.', 1)[-1]}.py",
            )
        )
    return own + dependencies


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _protocol() -> dict[str, Any]:
    return {
        "schema_version": "swedish-landscape-history-protocol.v1",
        "source_dataset": "10.1594/PANGAEA.937075",
        "evidence_role": "derived_published_model;not_independent_vegetation_validation",
        "selection": "26governed Swedish-center cells x25published windows; whole cells assigned by center, not Swedish land intersections",
        "units": "percentage_cover",
        "epoch": "BP1950",
        "band_counts": BAND_COUNTS,
        "latitude_extent": [55, 70],
        "band_rule": "Equal latitude width; south-inclusive/north-exclusive;70N included last; center assignment only",
        "weightings": WEIGHTINGS,
        "area_rule": "Full1degree spherical cell area at earth radius6371.0088km, proportional to cos(center latitude); represented grid support only",
        "policies": POLICIES,
        "available": "All eligible high/low cells in each published window; changing support is descriptive",
        "high_quality": "Only eligible source high-quality cells in each window",
        "fixed_recent": "Intersection of eligible grids across all8whole published windows0-3200BP; no values outside those windows",
        "recent_windows": WINDOWS[:8],
        "source_windows": WINDOWS,
        "primary_recent_display": "five bands;fixed_recent;area",
        "classification": DEFINITIONS,
        "closure_tolerance_percentage_points": CLOSURE_TOLERANCE_PP,
        "mean_rule": "Direct weighted sums with one common mask/weight per component; no clipping or renormalization",
        "cereal_ratio_rule": "Ratio of weighted cereals to weighted non-tree; null at zero denominator; not a mean of per-cell ratios",
        "uncertainty": "Cellwise minimum/maximum describe spatial variation. Only source OL/AL SE ranges retained, unpooled; no spatial/taxon covariance or joint draws available",
        "regional_confidence_intervals": False,
        "quality_counts": "coverage.high/low count eligible high/low rows; source_quality_counts include every raw quality row including invalid rows",
        "missing_rule": "All no_pollen_data rows excluded regardless native means; zero31taxon mass refused; true component zero retained",
        "time_rule": "Retain discrete source windows, including2700-3200BP whole; no interpolation or artificial100year information",
    }


def _write_cells(path: Path, cells: tuple[CellWindow, ...]) -> None:
    mean_keys = sorted({k for c in cells for k in c.estimates})
    error_keys = sorted({k for c in cells for k in c.standard_errors})
    fields = [
        "grid_id",
        "longitude",
        "latitude",
        "younger_bp",
        "older_bp",
        "quality",
        "status",
        "reason",
        *METRIC_KEYS,
        *(f"native_mean:{k}" for k in mean_keys),
        *(f"native_se:{k}" for k in error_keys),
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fields, lineterminator="\n")
        writer.writeheader()
        for c in cells:
            row = {
                k: v
                for k, v in asdict(c).items()
                if k not in ("estimates", "standard_errors")
            }
            if c.status == "eligible":
                row.update(classify_means(c.estimates))
            row.update({f"native_mean:{k}": v for k, v in c.estimates.items()})
            row.update({f"native_se:{k}": v for k, v in c.standard_errors.items()})
            writer.writerow(row)


def _write_trajectories(path: Path, rows: list[dict[str, Any]]) -> None:
    """Flatten parallel metric columns; preserve lists and coverage as compact JSON."""
    flattened = []
    for row in rows:
        flat = {
            key: (
                json.dumps(value, sort_keys=True, separators=(",", ":"))
                if isinstance(value, (dict, list))
                else value
            )
            for key, value in row.items()
            if key not in ("metrics", "source_standard_error_ranges")
        }
        for key, metric in row["metrics"].items():
            flat.update({f"{key}_{stat}": value for stat, value in metric.items()})
        for key, bounds in row["source_standard_error_ranges"].items():
            flat.update(
                {f"source_{key}_se_{stat}": value for stat, value in bounds.items()}
            )
        flattened.append(flat)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, list(flattened[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(flattened)


def run(repository: Path, output: Path) -> Path:
    """Write a new artifact tree after binding all inputs and calculation bytes."""
    repository, output = repository.resolve(), output.resolve()
    if not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Repository artifacts destination required")
    if output.exists():
        raise ValueError("Output destination must be absent")
    pins = [_pin(repository / name, name) for name in SOURCE_PATHS]
    source_pins = _source_pins()
    cells = load_cells(repository)
    rows = aggregate(cells)
    protocol = _protocol()
    output.mkdir(parents=True)
    _write_json(output / "protocol.json", protocol)
    _write_json(
        output / "trajectories.json",
        {
            "schema_version": "swedish-landscape-history-trajectories.v1",
            "definitions": DEFINITIONS,
            "rows": rows,
        },
    )
    _write_cells(output / "cells.csv", cells)
    _write_trajectories(output / "trajectories.csv", rows)
    if (
        pins != [_pin(repository / name, name) for name in SOURCE_PATHS]
        or source_pins != _source_pins()
    ):
        raise ValueError(
            "Consumed source or calculation bytes changed during execution"
        )
    git = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )
    packages: dict[str, str | None] = {}
    for name in ("bijux-pollenomics", "bijux-pollenomics-dev"):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    summary = {
        "schema_version": "swedish-landscape-history-result.v1",
        "status": "complete",
        "input_pins": pins,
        "calculation_source_pins": source_pins,
        "input_guard_count": len(pins),
        "calculation_guard_count": len(source_pins),
        "git_head": git.stdout.strip() if git.returncode == 0 else None,
        "runtime": {
            "executable": sys.executable,
            "python": sys.version,
            "packages": packages,
        },
        "arguments": {"repository": str(repository), "output": str(output)},
        "protocol": protocol,
        "cell_count": len(cells),
        "grid_count": len({c.grid_id for c in cells}),
        "source_window_count": len(WINDOWS),
        "trajectory_row_count": len(rows),
        "cell_status_counts": dict(Counter(c.status for c in cells)),
        "source_quality_counts": dict(Counter(c.quality for c in cells)),
        "refusals": [
            {
                "grid_id": c.grid_id,
                "younger_bp": c.younger_bp,
                "older_bp": c.older_bp,
                "quality": c.quality,
                "reason": c.reason,
            }
            for c in cells
            if c.status == "invalid"
        ],
        "products": [
            _pin(output / name, name)
            for name in (
                "protocol.json",
                "trajectories.json",
                "trajectories.csv",
                "cells.csv",
            )
        ],
    }
    _write_json(output / "summary.json", summary)
    return output
