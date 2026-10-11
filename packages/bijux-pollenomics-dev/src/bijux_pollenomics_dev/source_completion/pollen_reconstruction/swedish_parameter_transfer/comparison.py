"""Compare conditional cover on explicit flat target axes and shared windows."""

from collections.abc import Mapping
import math
from typing import TypedDict


class _BaselineWindow(TypedDict):
    conditional_cover: list[int | float]
    panel_NISP_sum: object
    retained_reported_pollen_mass_fraction: object


def _taxa(case: Mapping[str, object]) -> list[str]:
    axis = case["parameter_taxa"]
    if not isinstance(axis, list) or any(not isinstance(taxon, str) for taxon in axis):
        raise ValueError("Parameter axis must contain flat target names")
    return axis


def baseline_rows(
    case: Mapping[str, object],
) -> dict[tuple[float, float], _BaselineWindow]:
    """Select the declared baseline windows while retaining their original fields."""
    axis = _taxa(case)
    if not axis or len(set(axis)) != len(axis):
        raise ValueError("Parameter axis must be nonempty and unique")
    rows: dict[tuple[float, float], _BaselineWindow] = {}
    results = case["results"]
    if not isinstance(results, list):
        raise ValueError("Conditional results must contain window objects")
    for row in results:
        if not isinstance(row, dict):
            raise ValueError("Conditional results must contain window objects")
        if row["transport_profile"] != "metadata_radius_wind_3":
            continue
        vector = row["conditional_cover"]
        if (
            not isinstance(vector, list)
            or len(vector) != len(axis)
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in vector
            )
        ):
            raise ValueError(
                "Conditional cover must be a finite flat vector on its parameter axis"
            )
        lower, upper = row["younger_cal_bp"], row["older_cal_bp_exclusive"]
        if not isinstance(lower, (int, float)) or not isinstance(upper, (int, float)):
            raise ValueError("Conditional window boundaries must be numeric")
        key = (lower, upper)
        if key in rows:
            raise ValueError("Duplicate baseline age window")
        rows[key] = {
            "conditional_cover": vector,
            "panel_NISP_sum": row["panel_NISP_sum"],
            "retained_reported_pollen_mass_fraction": row[
                "retained_reported_pollen_mass_fraction"
            ],
        }
    return rows


def compare_cases(
    left: Mapping[str, object], right: Mapping[str, object]
) -> dict[str, object]:
    """Compare adjacent conditional panels on their shared captured windows."""
    if left["core"] != right["core"]:
        raise ValueError("Adjacent alternatives must refer to the same native core")
    lrows, rrows = baseline_rows(left), baseline_rows(right)
    laxis, raxis = _taxa(left), _taxa(right)
    common = sorted(set(laxis) & set(raxis))
    differences = []
    for key in sorted(set(lrows) & set(rrows)):
        lr, rr = lrows[key], rrows[key]
        values = {
            taxon: 100
            * (
                rr["conditional_cover"][raxis.index(taxon)]
                - lr["conditional_cover"][laxis.index(taxon)]
            )
            for taxon in common
        }
        differences.append(
            {
                "younger_cal_bp": key[0],
                "older_cal_bp_exclusive": key[1],
                "common_target_difference_percentage_points": values,
                "left_panel_NISP_sum": lr["panel_NISP_sum"],
                "right_panel_NISP_sum": rr["panel_NISP_sum"],
                "left_retained_pollen_mass_fraction": lr[
                    "retained_reported_pollen_mass_fraction"
                ],
                "right_retained_pollen_mass_fraction": rr[
                    "retained_reported_pollen_mass_fraction"
                ],
            }
        )
    return {
        "core": left["core"],
        "left": left["scenario"],
        "right": right["scenario"],
        "left_parameter_axis": laxis,
        "right_parameter_axis": raxis,
        "left_only_windows": [list(key) for key in sorted(set(lrows) - set(rrows))],
        "right_only_windows": [list(key) for key in sorted(set(rrows) - set(lrows))],
        "scope": (
            "Adjacent alternatives isolate added dwarf-birch versus large-grass-PPE "
            "hypothesis; target/panel-denominator changes remain explicit, "
            "no measured land-cover effect claimed"
        ),
        "windows": differences,
    }
