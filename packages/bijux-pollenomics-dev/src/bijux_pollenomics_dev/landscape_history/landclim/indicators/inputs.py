"""Read the frozen regional cohorts without changing the original calculation."""

from __future__ import annotations

import csv
import json
from math import isfinite
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict, cast

from ..aggregation import BAND_COUNTS, POLICIES, WEIGHTINGS
from ..inputs import WINDOWS

BASE_CSV = "reports/science/swedish-landscape-history/trajectories.csv"
BASE_SHA256 = "17299c41e317053eb3a2a3e68640f0e083b1c34023aed61f017deeff6b207750"
BASE_PATHS = (
    BASE_CSV,
    "reports/science/swedish-landscape-history/protocol.json",
    "reports/science/swedish-landscape-history/independent-check.json",
)
BASE_METRICS = ("source_OL", "cereals", "non_cereal_herbs")
STATS: tuple[Literal["mean", "minimum", "maximum"], ...] = (
    "mean",
    "minimum",
    "maximum",
)


class Statistics(TypedDict):
    """Mean and observed cell extrema, with unavailable values explicit."""

    mean: float | None
    minimum: float | None
    maximum: float | None


class BaseRow(TypedDict):
    """The typed identity and support retained from one frozen trajectory row."""

    band_count: int
    band_index: int
    south_latitude: float
    north_latitude: float
    younger_bp: int
    older_bp: int
    source_window: str
    policy: str
    weighting: str
    count: int
    grid_ids: list[str]
    status: str
    reason: str
    coverage: dict[str, int]
    metrics: dict[str, Statistics]
    excluded_grid_ids: NotRequired[list[str]]
    high_quality_grid_ids: NotRequired[list[str]]
    low_quality_grid_ids: NotRequired[list[str]]
    invalid_grid_ids: NotRequired[list[str]]
    no_data_grid_ids: NotRequired[list[str]]
    source_quality_counts: NotRequired[dict[str, int]]
    total_area_km2: NotRequired[float]
    selected_area_km2: NotRequired[float]
    area_weight_denominator_km2: NotRequired[float]
    eligible_area_fraction: NotRequired[float | None]
    selected_area_fraction: NotRequired[float | None]
    weight_denominator: NotRequired[float]


INTEGER_FIELDS = ("band_count", "band_index", "younger_bp", "older_bp", "count")
FLOAT_FIELDS = (
    "south_latitude",
    "north_latitude",
    "total_area_km2",
    "selected_area_km2",
    "area_weight_denominator_km2",
    "eligible_area_fraction",
    "selected_area_fraction",
    "weight_denominator",
)
JSON_FIELDS = (
    "grid_ids",
    "excluded_grid_ids",
    "high_quality_grid_ids",
    "low_quality_grid_ids",
    "invalid_grid_ids",
    "no_data_grid_ids",
    "coverage",
    "source_quality_counts",
)
STRING_FIELDS = ("source_window", "policy", "weighting", "status", "reason")


def _number(token: str) -> float | None:
    if token == "":
        return None
    value = float(token)
    if not isfinite(value):
        raise ValueError("Nonfinite baseline number")
    return value


def read_base_rows(path: Path) -> list[BaseRow]:
    """Parse all2250 frozen cohorts, preserving nulls, support IDs and weights."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows: list[BaseRow] = []
        for raw in reader:
            parsed: dict[str, Any] = {key: int(raw[key]) for key in INTEGER_FIELDS}
            parsed.update({key: _number(raw[key]) for key in FLOAT_FIELDS})
            parsed.update({key: raw[key] for key in STRING_FIELDS})
            for key in JSON_FIELDS:
                value = json.loads(raw[key])
                if key.endswith("ids"):
                    if not isinstance(value, list) or any(
                        not isinstance(v, str) for v in value
                    ):
                        raise ValueError("Invalid baseline grid IDs")
                elif not isinstance(value, dict) or any(
                    type(v) is not int or v < 0 for v in value.values()
                ):
                    raise ValueError("Invalid baseline coverage")
                parsed[key] = value
            parsed["metrics"] = {
                metric: {stat: _number(raw[f"{metric}_{stat}"]) for stat in STATS}
                for metric in BASE_METRICS
            }
            rows.append(cast(BaseRow, parsed))
    expected = {
        (n, i, a, b, policy, weighting)
        for n in BAND_COUNTS
        for i in range(n)
        for a, b in WINDOWS
        for policy in POLICIES
        for weighting in WEIGHTINGS
    }
    identities = [
        (
            r["band_count"],
            r["band_index"],
            r["younger_bp"],
            r["older_bp"],
            r["policy"],
            r["weighting"],
        )
        for r in rows
    ]
    if len(rows) != len(expected) or set(identities) != expected:
        raise ValueError("Complete unique2250-row baseline inventory required")
    return rows
