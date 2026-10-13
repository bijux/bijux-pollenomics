"""Evaluate two declared static basin geometries on one frozen native cohort."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Any, cast

import numpy as np

from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus
from bijux_pollenomics_lra.reconstruction.fixed_site_covariance import (
    fixed_site_cover_covariance,
)

JsonMap = dict[str, Any]
DOMAIN = Path(__file__).resolve().parent


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def point_window(value: object, edges: list[float]) -> int | None:
    if type(value) not in (int, float):
        raise ValueError("Source age is not a finite native number")
    number = cast(int | float, value)
    if not math.isfinite(number):
        raise ValueError("Source age is not a finite native number")
    if not edges[0] <= number < edges[-1]:
        return None
    return bisect_right(edges, number) - 1


def qualify(source_root: Path) -> tuple[JsonMap, JsonMap]:
    source_root = source_root.resolve(strict=True)
    protocol: JsonMap = read(DOMAIN / "protocol.json")
    custody: JsonMap = read(DOMAIN / "source-custody.json")
    for name, pin in custody.items():
        path = source_root / name
        if (
            path.is_symlink()
            or not path.is_file()
            or not path.resolve().is_relative_to(source_root)
        ):
            raise ValueError("Source custody requires regular exact files")
        body = path.read_bytes()
        if (
            len(body) != pin["bytes"]
            or hashlib.sha256(body).hexdigest() != pin["sha256"]
        ):
            raise ValueError("Source custody changed")
    native: JsonMap = read(source_root / "inputs/native-results.json")
    original: JsonMap = read(source_root / "inputs/protocol.json")
    samples: list[JsonMap] = read(
        source_root / "inputs/dataset-23013-sample-eligibility.json"
    )
    source_terminal: JsonMap = read(source_root / "inputs/source-terminal.json")
    terminal: JsonMap = read(source_root / "inputs/native-terminal.json")
    if not all(
        t["native_exit_code"] == 0 and t["status"] == "PASS"
        for t in (source_terminal, terminal)
    ):
        raise ValueError("Original source/science capture did not pass")
    source_pin = custody["inputs/dataset-23013-sample-eligibility.json"]
    if (
        source_terminal["product_files"]["dataset-23013-sample-eligibility.json"]
        != source_pin
    ):
        raise ValueError("Dataset capture is not original source-terminal output")
    if (
        terminal["product_files"]["physical-results.json"]
        != custody["inputs/native-results.json"]
    ):
        raise ValueError("Native results are not original native-terminal output")
    profile: JsonMap = next(
        p
        for p in native["single_dataset_profiles"]
        if p["selected_source_profile"]["native_dataset_id"] == 23013
        and p["selected_source_profile"]["native_chronology_id"] == 13366
    )
    selected: JsonMap = profile["selected_source_profile"]
    metadata = selected["static_workbook_radius_candidates"]
    if (
        len(metadata) != 1
        or metadata[0]["metadata_radius_m"] != 837.0
        or metadata[0]["metadata_sample_count"] != "96"
    ):
        raise ValueError("Workbook claims changed")
    edges: list[float] = [float(v) for v in original["age_window_edges_cal_bp"]]
    axis: list[str] = native["literal_axis"]
    if (
        axis != ["Betula", "Poaceae"]
        or original["diffusion_coefficient"] != 0.12
        or original["turbulence_parameter"] != 0.25
    ):
        raise ValueError("Declared transport or panel changed")
    bins: dict[int, list[JsonMap]] = {i: [] for i in range(25)}
    ledger: list[JsonMap] = []
    refusals: Counter[str] = Counter()
    for sample in samples:
        ages = [
            a
            for a in sample["typed_calibrated_source_ages"]
            if a["native_chronology_id"] == 13366
        ]
        reason: str | None = None
        index: int | None = None
        if len(ages) != 1:
            raise ValueError("Named age profile is missing or ambiguous")
        age: JsonMap = ages[0]
        point = age["source_point_age"]
        if age["source_age_type"] != "Calibrated radiocarbon years BP":
            raise ValueError("Named source age is not finite calibrated BP")
        index = point_window(point, edges)
        if index is None:
            reason = "source_point_outside_declared_windows"
        if age["window_index"] != index:
            raise ValueError(
                "Stored point-age bin differs from exact current selection"
            )
        panel: JsonMap = sample["strict_unique_literal_parameter_counts"]
        if not all(t in panel for t in axis):
            reason = "literal_panel_missing_or_ambiguous"
            index = None
        elif any(
            type(panel[t]["count"]) is not int or panel[t]["count"] < 0 for t in axis
        ):
            raise ValueError("Native count is not a nonnegative integer")
        elif sum(panel[t]["count"] for t in axis) == 0:
            reason = "explicit_allzero_panel"
            index = None
        if index is not None:
            bins[index].append(sample)
        else:
            assert reason is not None
            refusals[reason] += 1
        ledger.append(
            {
                "native_sample_id": sample["native_sample_id"],
                "native_analysis_unit_id": sample["native_analysis_unit_id"],
                "source_depth": sample["source_depth"],
                "source_age": age,
                "window_index": index,
                "refusal": reason,
            }
        )
    archived = {
        r["window_index"]: r
        for r in profile["conditional_results"]
        if r["physical_profile"] == "metadata_radius_wind_3"
    }
    if (
        len(samples) != 96
        or sum(len(v) for v in bins.values()) != 95
        or {i for i, v in bins.items() if v} != set(archived)
        or len(archived) != 24
    ):
        raise ValueError("Frozen source cohort or occupied domain changed")
    radii = {
        "workbook_static_circle": 837.0,
        "paper_area_declared_circle": math.sqrt(186 * 10000 / math.pi),
    }
    factors: dict[str, list[float]] = {}
    factor_records: list[JsonMap] = []
    for name, radius in radii.items():
        values: list[float] = []
        errors: list[float] = []
        for fall in native["fall_speed_m_s"]:
            response = circular_receiver_annulus(
                receiver_radius_m=radius,
                inner_radius_m=radius,
                outer_radius_m=100000.0,
                fall_speed_m_s=fall,
                diffusion_coefficient=0.12,
                turbulence_parameter=0.25,
                wind_speed_m_s=3.0,
            )
            values.append(response.factor)
            errors.append(response.estimated_absolute_error)
        factors[name] = values
        factor_records.append(
            {
                "scenario": name,
                "receiver_radius_m": radius,
                "deposition": values,
                "adaptive_nonrigorous_absolute_error_estimates": errors,
            }
        )
    ppe = np.asarray(native["ppe"], dtype=float)
    ppe_covariance = np.diag(np.square(np.asarray(native["ppe_SD"], dtype=float)))
    public_rows: list[JsonMap] = []
    private_counts: list[JsonMap] = []
    for index in range(25):
        group = bins[index]
        row: JsonMap = {
            "window_index": index,
            "younger_cal_bp": edges[index],
            "older_cal_bp_exclusive": edges[index + 1],
            "status": "paired_conditional_results"
            if group
            else "both_scenarios_refused_no_source_samples",
            "selected_native_sample_count": len(group),
            "scenarios": {},
            "alternative_minus_reference_cover": None,
            "paired_standard_error": None,
            "paired_uncertainty_scope": "No cross-geometry covariance or basin uncertainty model supplied",
        }
        if group:
            counts = [
                sum(
                    s["strict_unique_literal_parameter_counts"][t]["count"]
                    for s in group
                )
                for t in axis
            ]
            nisp = sum(s["reported_pollen_NISP"] for s in group)
            saved: JsonMap = archived[index]
            if (
                saved["source_support"]["counts"] != counts
                or saved["source_support"]["reported_source_pollen_NISP_sum"] != nisp
                or sorted(saved["source_support"]["native_sample_ids"])
                != sorted(s["native_sample_id"] for s in group)
            ):
                raise ValueError("Original native support differs")
            private_counts.append(
                {
                    "window_index": index,
                    "counts": counts,
                    "full_reported_source_NISP": nisp,
                }
            )
            for name in radii:
                result = fixed_site_cover_covariance(
                    np.asarray([counts]),
                    np.asarray([factors[name]]),
                    ppe,
                    ppe_covariance,
                    taxon_measured=np.ones((1, 2), dtype=bool),
                )
                row["scenarios"][name] = {
                    "conditional_panel_cover": result.cover.tolist(),
                    "conditional_standard_error": result.standard_error.tolist(),
                    "counting_covariance": result.counting_covariance.tolist(),
                    "shared_ppe_covariance": result.ppe_covariance.tolist(),
                    "total_conditional_covariance": result.total_covariance.tolist(),
                }
            baseline = row["scenarios"]["workbook_static_circle"][
                "conditional_panel_cover"
            ]
            if (
                max(
                    abs(a - b)
                    for a, b in zip(
                        baseline, saved["conditional_panel_cover"], strict=True
                    )
                )
                > 2e-8
            ):
                raise ValueError(
                    "Maintained baseline differs from retained native result"
                )
            row["alternative_minus_reference_cover"] = [
                a - b
                for a, b in zip(
                    row["scenarios"]["paper_area_declared_circle"][
                        "conditional_panel_cover"
                    ],
                    baseline,
                    strict=True,
                )
            ]
        public_rows.append(row)
    public: JsonMap = {
        "schema_version": "krageholm-static-geometry-sensitivity.v1",
        "native_dataset_id": 23013,
        "native_collection_unit_id": 16622,
        "native_chronology_id": 13366,
        "literal_axis": axis,
        "protocol": protocol,
        "source_pins": custody,
        "original_sample_count": 96,
        "selected_sample_count": 95,
        "source_sample_refusals": dict(refusals),
        "workbook_sample_claim": "96",
        "window_domain_count": 25,
        "paired_windows": 24,
        "refused_window_count": 1,
        "physical_factors": factor_records,
        "window_rows": public_rows,
        "maximum_absolute_paired_cover_difference": max(
            abs(v)
            for r in public_rows
            if r["alternative_minus_reference_cover"] is not None
            for v in r["alternative_minus_reference_cover"]
        ),
        "historical_basin_authenticated": False,
        "vegetation_accuracy_claimed": False,
        "paired_standard_error_admitted": False,
    }
    private: JsonMap = {"samples": ledger, "window_counts": private_counts}
    return public, private


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    public, private = qualify(args.source_root)
    args.output_root.mkdir(parents=True, exist_ok=False)
    for name, account in (
        ("geometry-sensitivity.json", public),
        ("private-source-support.json", private),
    ):
        with (args.output_root / name).open("x", encoding="utf-8") as stream:
            json.dump(account, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
