"""Replay deterministic analytical LOVE across the bundled ring geometry."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import warnings

import numpy as np

from bijux_pollenomics_lra.reconstruction.analytical import LOVEr
from bijux_pollenomics_lra.resources.examples import load_love_example


INPUTS = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/data/LOVEexamplePollen.json",
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/data/LOVEexampleParams.json",
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/data/LOVEexampleRings.json",
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/analytical.py",
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/inputs.py",
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/dispersal/kernels.py",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    local, regional, parameters, rings = load_love_example()
    parameters = {**parameters, "error": False}
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="All-NaN slice encountered")
        result = LOVEr(
            local,
            regional,
            parameters,
            rings,
            10,
            repeats=2,
            stochastic=False,
            return_samples=True,
        )
    values = result["Mean"].to_numpy(dtype=float)
    valid = result["valid_ring"].to_numpy(dtype=bool)
    assert values.shape == (10, 10) and valid.sum() == 3
    assert np.isnan(values[~valid]).all() and np.isfinite(values[valid]).all()
    assert np.array_equal(result["samples"][0], result["samples"][1], equal_nan=True)
    rows: list[dict[str, object]] = []
    for index in range(10):
        for taxon, value in zip(result["Mean"].columns, values[index], strict=True):
            rows.append(
                {
                    "ring": index + 1,
                    "inner": float(rings["inner"].iloc[index]),
                    "outer": float(rings["outer"].iloc[index]),
                    "mean_radius": float(rings["mean"].iloc[index]),
                    "valid": str(bool(valid[index])).lower(),
                    "taxon": taxon,
                    "cover_fraction": "" if np.isnan(value) else format(value, ".17g"),
                }
            )
    with (output / "ring-cover.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    admitted = values[valid]
    report = {
        "schema_version": "analytical-love-ring-sensitivity.1",
        "profile": "disqover-0.9.14-source-compatible-deterministic",
        "status": "passed",
        "input_sha256": {
            name: hashlib.sha256((repository / name).read_bytes()).hexdigest()
            for name in INPUTS
        },
        "ring_count": len(valid),
        "valid_ring_count": int(valid.sum()),
        "valid_mean_radii": [
            float(x) for x in rings["mean"].to_numpy()[: len(valid)][valid]
        ],
        "taxon_count": admitted.shape[1],
        "negative_cells": int((admitted < 0).sum()),
        "above_one_cells": int((admitted > 1).sum()),
        "min_cover_fraction": float(admitted.min()),
        "max_cover_fraction": float(admitted.max()),
        "largest_taxon_ring_span": float(np.ptp(admitted, axis=0).max()),
        "ring_cover_sha256": hashlib.sha256(
            (output / "ring-cover.csv").read_bytes()
        ).hexdigest(),
        "r_parity_case": "C0023",
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
