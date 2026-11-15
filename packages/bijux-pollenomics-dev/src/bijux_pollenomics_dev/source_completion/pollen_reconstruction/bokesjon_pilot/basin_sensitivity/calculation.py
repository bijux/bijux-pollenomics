"""Execute the public host boundary; every profile recomputes native coefficients."""

from __future__ import annotations

import csv
from math import isfinite
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra.api import read_lra_product, run_lra_request


def pair_table(path: Path) -> tuple[list[float], list[list[float]]]:
    """Read the complete verified two-ring, two-taxon numerical table."""
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["index", "Betula", "Ulmus"]:
            raise ValueError("Native ring/taxon axes differ")
        rows = list(reader)
    indices = [float(row["index"]) for row in rows]
    values = [[float(row[taxon]) for taxon in ("Betula", "Ulmus")] for row in rows]
    if len(rows) != 2 or not all(
        isfinite(x) for x in indices + [v for row in values for v in row]
    ):
        raise ValueError("Two finite native ring rows required")
    return indices, values


def extract(directory: Path) -> dict[str, Any]:
    """Retain raw and transformed cover alongside the newly computed kernels."""
    root = directory / "numerical"
    indices, signed = pair_table(root / "local_love/aux_raw_cover_mean.csv")
    clipped_indices, clipped = pair_table(root / "local_love/cover_mean.csv")
    local_indices, kloc = pair_table(root / "local_love/aux_Kloc.csv")
    regional_indices, kreg = pair_table(root / "local_love/aux_Kreg.csv")
    if not indices == clipped_indices == local_indices == regional_indices:
        raise ValueError("Native ring axes do not match")
    with (root / "regional_reveals/reconstruction.csv").open(newline="") as stream:
        regional = list(csv.DictReader(stream))
    if len(regional) != 1:
        raise ValueError("One deterministic regional background required")
    return {
        "ring_midpoints_m": indices,
        "signed_cover": signed,
        "clipped_cover": clipped,
        "Kloc": kloc,
        "Kreg": kreg,
        "regional_cover_percent": [
            float(regional[0][taxon + ".mean"]) for taxon in ("Betula", "Ulmus")
        ],
    }


def calculate(
    request: dict[str, Any], input_root: Path, output: Path
) -> dict[str, Any]:
    """Run a fresh source-compatible LRA request and authenticate its saved outputs."""
    product = run_lra_request(request, input_root=input_root, destination=output)
    read_lra_product(
        product.directory, expected_manifest_sha256=product.manifest_sha256
    )
    return {
        "status": "generated",
        "product_directory": str(product.directory),
        "manifest_sha256": product.manifest_sha256,
        **extract(product.directory),
    }
