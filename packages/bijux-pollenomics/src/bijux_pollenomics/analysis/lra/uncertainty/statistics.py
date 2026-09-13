"""Finite-law population summaries, separate from Monte Carlo and sampling SE."""

from __future__ import annotations

import csv
from fractions import Fraction
from math import fsum, isfinite
from pathlib import Path
from typing import Any

from .contracts import mass


def child_values(
    directory: Path, request: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[float]]:
    root = directory / "numerical"
    with (root / "regional_reveals/reconstruction.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        regional = list(csv.DictReader(stream))
    with (root / "local_love/cover_mean.csv").open(
        encoding="utf-8", newline=""
    ) as stream:
        local = list(csv.DictReader(stream))
    if len(regional) != 1:
        raise ValueError("Expected one regional output row")
    coordinates: list[dict[str, Any]] = []
    values: list[float] = []
    for taxon in request["taxa"]:
        coordinates.append(
            {
                "role": "regional",
                "taxon": taxon,
                "ring_mean_m": None,
                "unit": "fraction",
                "source_unit": "percent",
                "conversion": "divide_by_100",
            }
        )
        values.append(float(regional[0][taxon + ".mean"]) / 100)
    for item in local:
        for taxon in request["taxa"]:
            coordinates.append(
                {
                    "role": "local",
                    "taxon": taxon,
                    "ring_mean_m": float(item["index"]),
                    "unit": "fraction",
                    "source_unit": "fraction",
                    "conversion": "identity",
                }
            )
            values.append(float(item[taxon]))
    if not values or not all(isfinite(x) for x in values):
        raise ValueError(
            "Joint summaries require finite realized cover; no missing-to-zero conversion"
        )
    return coordinates, values


def summaries(rows: list[dict[str, Any]], bin_ids: list[str]) -> dict[str, Any]:
    result = {}
    for bin_id in sorted(bin_ids):
        selected = [row for row in rows if row["bin_id"] == bin_id]
        success = [row for row in selected if row["status"] == "success"]
        available = sum((mass(row["mass"]) for row in success), Fraction())
        base: dict[str, Any] = {
            "requested_mass": {"numerator": 1, "denominator": 1},
            "successful_mass": {
                "numerator": available.numerator,
                "denominator": available.denominator,
            },
            "failed_mass": {
                "numerator": (1 - available).numerator,
                "denominator": (1 - available).denominator,
            },
            "complete": len(success) == len(selected),
            "coordinates": None,
            "mean": None,
            "population_covariance": None,
            "covariance_unit": "fraction_squared",
            "intervals": None,
            "summary_profile": "supplied-finite-law-population-moments-v1",
            "monte_carlo_standard_error_claimed": False,
            "automatic_renormalization": False,
        }
        if len(success) == len(selected) and success:
            coordinates = success[0]["coordinates"]
            if any(row["coordinates"] != coordinates for row in success):
                raise ValueError(
                    "Joint output coordinate inventory differs across atoms"
                )
            weights = [float(mass(row["mass"])) for row in success]
            vectors = [row["values"] for row in success]
            means = [
                fsum(w * x[i] for w, x in zip(weights, vectors, strict=True))
                for i in range(len(coordinates))
            ]
            covariance = [
                [
                    fsum(
                        w * (x[i] - means[i]) * (x[j] - means[j])
                        for w, x in zip(weights, vectors, strict=True)
                    )
                    for j in range(len(coordinates))
                ]
                for i in range(len(coordinates))
            ]
            if not all(isfinite(v) for v in means) or not all(
                isfinite(v) for row in covariance for v in row
            ):
                raise ValueError("Finite-law moment arithmetic overflow")
            base.update(
                coordinates=coordinates, mean=means, population_covariance=covariance
            )
        result[bin_id] = base
    return result
