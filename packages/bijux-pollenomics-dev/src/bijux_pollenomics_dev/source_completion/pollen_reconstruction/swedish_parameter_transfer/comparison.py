"""Compare conditional cover on explicit flat target axes and shared windows."""

import math


def baseline_rows(case):
    axis = case["parameter_taxa"]
    if not axis or len(set(axis)) != len(axis):
        raise ValueError("Parameter axis must be nonempty and unique")
    rows = {}
    for row in case["results"]:
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
        key = (row["younger_cal_bp"], row["older_cal_bp_exclusive"])
        if key in rows:
            raise ValueError("Duplicate baseline age window")
        rows[key] = row
    return rows


def compare_cases(left, right):
    if left["core"] != right["core"]:
        raise ValueError("Adjacent alternatives must refer to the same native core")
    lrows, rrows = baseline_rows(left), baseline_rows(right)
    laxis, raxis = left["parameter_taxa"], right["parameter_taxa"]
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
