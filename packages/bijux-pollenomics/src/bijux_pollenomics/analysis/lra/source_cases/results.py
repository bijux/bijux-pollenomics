"""Derived point vectors and supplied-design dispersion, without source SE claims."""

from __future__ import annotations

import csv
import io
from fractions import Fraction
from math import isfinite
from pathlib import Path
from typing import Any

from ....core.filesystem import BoundedInputTree
from ..uncertainty.statistics import summaries


def design_summaries(rows: list[dict[str, Any]], *, weighted: bool) -> dict[str, Any]:
    """Keep raw and per-case adjusted estimands separate through existing moments."""
    result = {}
    for kind in ("raw", "adjusted"):
        if weighted:
            transformed = []
            for row in sorted(rows, key=lambda v: v["case_id"]):
                weight = Fraction(row["mass"])
                transformed.append(
                    {
                        "bin_id": "fixed_support",
                        "status": row["status"],
                        "mass": {
                            "numerator": weight.numerator,
                            "denominator": weight.denominator,
                        },
                        "coordinates": row["coordinates"],
                        "values": row[kind + "_values"],
                    }
                )
            value = summaries(transformed, ["fixed_support"])["fixed_support"]
            value["summary_profile"] = "caller-design-conditional-point-dispersion.v1"
        else:
            value = {
                "requested_mass": None,
                "successful_mass": None,
                "failed_mass": None,
                "complete": all(row["status"] == "success" for row in rows),
                "coordinates": None,
                "mean": None,
                "population_covariance": None,
                "summary_profile": "unweighted-conditional-sensitivity.v1",
                "automatic_renormalization": False,
            }
        value.update(
            estimand=kind,
            empirical_uncertainty_claimed=False,
            source_standard_error=None,
            source_uncertainty_available=False,
        )
        result[kind] = value
    return result


def _table(directory: Path, name: str, limit: int) -> list[dict[str, str]]:
    path = directory / "numerical" / name
    with BoundedInputTree(
        path.parent, selected=path.name, max_bytes=limit, max_files=1
    ) as tree:
        return list(csv.DictReader(io.StringIO(tree.read(path).decode())))


def child_vectors(
    directory: Path, request: dict[str, Any], *, max_bytes: int
) -> dict[str, Any]:
    """Read authenticated private child tables without embedding source members."""
    regional = _table(directory, "regional_reveals/reconstruction.csv", max_bytes)
    raw = _table(directory, "local_love/aux_raw_cover_mean.csv", max_bytes)
    adjusted = _table(directory, "local_love/cover_mean.csv", max_bytes)
    if (
        len(regional) != 1
        or len(raw) != len(adjusted)
        or len(raw) != request["configuration"]["love"]["max_ring"]
    ):
        raise ValueError(
            "Derived child coordinate inventory differs from fixed support"
        )
    coords = [
        {
            "role": "regional",
            "taxon": taxon,
            "ring_mean_m": None,
            "unit": "fraction",
            "source_unit": "percent",
            "conversion": "divide_by_100",
        }
        for taxon in request["taxa"]
    ]
    raw_values = [
        float(regional[0][taxon + ".mean"]) / 100 for taxon in request["taxa"]
    ]
    adjusted_values = list(raw_values)
    for raw_row, adjusted_row in zip(raw, adjusted, strict=True):
        if float(raw_row["index"]) != float(adjusted_row["index"]):
            raise ValueError("Raw and adjusted ring inventories differ")
        for taxon in request["taxa"]:
            coords.append(
                {
                    "role": "local",
                    "taxon": taxon,
                    "ring_mean_m": float(raw_row["index"]),
                    "unit": "fraction",
                    "source_unit": "fraction",
                    "conversion": "identity",
                }
            )
            raw_values.append(float(raw_row[taxon]))
            adjusted_values.append(float(adjusted_row[taxon]))
    if not all(isfinite(v) for v in raw_values + adjusted_values):
        raise ValueError(
            "Conditional cases require finite derived cover; no missing-to-zero conversion"
        )
    return {
        "coordinates": coords,
        "raw_values": raw_values,
        "adjusted_values": adjusted_values,
    }
