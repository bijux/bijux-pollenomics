"""Source-bound publication of components on frozen regional support."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from .. import workflow as base_workflow
from ..classification import CLOSURE_TOLERANCE_PP
from ..inputs import SOURCE_PATHS, load_cells
from .analysis import DEFINITIONS, METRICS, derive_rows
from .inputs import BASE_CSV, BASE_PATHS, BASE_SHA256, read_base_rows

CALCULATION_FILES = (
    "__init__.py",
    "__main__.py",
    "inputs.py",
    "analysis.py",
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
    prefix = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/landscape_history/landclim/indicators"
    return base_workflow._source_pins() + [
        _pin(Path(__file__).parent / name, f"{prefix}/{name}")
        for name in CALCULATION_FILES
    ]


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    flattened = []
    for row in rows:
        flat = {
            key: (
                json.dumps(value, sort_keys=True, separators=(",", ":"))
                if isinstance(value, (dict, list))
                else value
            )
            for key, value in row.items()
            if key != "metrics"
        }
        for key, stats in row["metrics"].items():
            flat.update({f"{key}_{stat}": value for stat, value in stats.items()})
        flattened.append(flat)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, list(flattened[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(flattened)


def run(repository: Path, output: Path) -> Path:
    """Refuse changed baseline bytes and preserve all frozen cohorts and gaps."""
    repository, output = repository.resolve(), output.resolve()
    if not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Repository artifacts destination required")
    if output.exists():
        raise ValueError("Output destination must be absent")
    baseline_pin = _pin(repository / BASE_CSV, BASE_CSV)
    if baseline_pin["sha256"] != BASE_SHA256:
        raise ValueError("Frozen baseline identity changed")
    pins = [_pin(repository / name, name) for name in (*SOURCE_PATHS, *BASE_PATHS)]
    source_pins = _source_pins()
    cells = load_cells(repository)
    rows = derive_rows(cells, read_base_rows(repository / BASE_CSV))
    protocol = {
        "schema_version": "swedish-agricultural-indicators-protocol.v1",
        "evidence_role": "components_of_published_modeled_vegetation;not_independent_validation",
        "baseline_csv": BASE_CSV,
        "baseline_sha256": BASE_SHA256,
        "cohort_rule": "Exact2250baseline band/window/policy/weighting rows; selected IDs, eligibility, counts and weights checked without changing cohorts",
        "source_support": "26Swedish-center one-degree grids x25published windows;650cell/windows, whole cells not Swedish polygon intersections",
        "primary_display": "five bands;fixed_recent;area;full eight windows0-3200BP; four/six bands and available/high_quality/equal diagnostics retained",
        "epoch": "BP1950",
        "units": "percentage_cover",
        "definitions": DEFINITIONS,
        "metrics": METRICS,
        "statistics": "Direct weighted component means plus individual-cell minimum/maximum on the same mask. Total extrema are computed directly; never sums of component extrema",
        "source_guards": "Per-cell31taxon closure and nonnegativity, Cerealia.t+Secale=AL, source OL subset identity; source OL, total cereals and seven-herb mean/min/max agree with all frozen baseline statistics",
        "absolute_tolerance_percentage_points": CLOSURE_TOLERANCE_PP,
        "missing_rule": "Baseline missing and policy-excluded rows remain null; true modeled zero remains numeric zero; zero-mass and no-data refusals unchanged",
        "uncertainty": "No new uncertainty law, standard-error aggregation, covariance or confidence interval. Ranges describe spatial variation of selected source cells",
        "new_reconstruction": False,
        "regional_confidence_intervals": False,
    }
    output.mkdir(parents=True)
    _write_json(output / "protocol.json", protocol)
    _write_json(
        output / "trajectories.json",
        {
            "schema_version": "swedish-agricultural-indicators-trajectories.v1",
            "definitions": DEFINITIONS,
            "rows": rows,
        },
    )
    _write_csv(output / "trajectories.csv", rows)
    if (
        pins != [_pin(repository / name, name) for name in (*SOURCE_PATHS, *BASE_PATHS)]
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
    summary = {
        "schema_version": "swedish-agricultural-indicators-result.v1",
        "status": "complete",
        "git_head": git.stdout.strip() if git.returncode == 0 else None,
        "runtime": {"executable": sys.executable, "python": sys.version},
        "arguments": {"repository": str(repository), "output": str(output)},
        "input_pins": pins,
        "calculation_source_pins": source_pins,
        "input_guard_count": len(pins),
        "calculation_guard_count": len(source_pins),
        "protocol": protocol,
        "cell_count": len(cells),
        "cell_status_counts": dict(Counter(c.status for c in cells)),
        "source_quality_counts": dict(Counter(c.quality for c in cells)),
        "trajectory_row_count": len(rows),
        "metric_count": len(METRICS),
        "baseline_statistics_verified": len(rows) * 3 * 3,
        "products": [
            _pin(output / name, name)
            for name in ("protocol.json", "trajectories.json", "trajectories.csv")
        ],
    }
    _write_json(output / "summary.json", summary)
    return output
