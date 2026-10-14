"""Evaluate declared fixed-radius wind scenarios with shared source count/PPE covariance."""

from __future__ import annotations

import argparse
from bisect import bisect_right
from dataclasses import replace
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np

from bijux_pollenomics_lra import api
from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus

JsonMap = dict[str, Any]


def require(condition: object) -> None:
    """Keep source and numerical guards active under optimized Python execution."""
    if not condition:
        raise ValueError("Krageholm wind source or numerical contract changed")


DOMAIN = Path(__file__).resolve().parent


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def verify_sources(source_root: Path, custody: JsonMap) -> None:
    """Keep selected source identities exact without granting source-use authority."""
    if (
        any(p.is_symlink() for p in (source_root, *source_root.parents))
        or not source_root.is_dir()
    ):
        raise ValueError("Source root must be a regular directory")
    for relative, pin in custody.items():
        native = PurePosixPath(relative)
        if native.is_absolute() or ".." in native.parts:
            raise ValueError("Unsafe source member")
        path = source_root / relative
        if (
            any(p.is_symlink() for p in (path, *path.parents))
            or not path.is_file()
            or (not path.resolve().is_relative_to(source_root.resolve()))
        ):
            raise ValueError("Source member must be a regular contained file")
        body = path.read_bytes()
        if (
            len(body) != pin["bytes"]
            or hashlib.sha256(body).hexdigest() != pin["sha256"]
        ):
            raise ValueError("Source custody changed")


def qualify(source_root: Path, output_root: Path) -> JsonMap:
    """Evaluate fixed-source conditional contrasts, retaining every refusal slot."""
    source_root = source_root.absolute()
    custody: JsonMap = read(DOMAIN / "wind-source-custody.json")
    verify_sources(source_root, custody)
    source_root = source_root.resolve(strict=True)
    if (
        output_root.exists()
        or output_root.is_symlink()
        or output_root.resolve().is_relative_to(source_root)
        or any(p.is_symlink() for p in output_root.parents)
    ):
        raise ValueError("Output must be absent and separate from source")
    protocol = read(DOMAIN / "wind-protocol.json")
    old = read(source_root / "native/geometry-sensitivity.json")
    native = read(source_root / "inputs/native-results.json")
    samples = read(source_root / "inputs/dataset-23013-sample-eligibility.json")
    selection = read(source_root / "inputs/protocol.json")
    for terminal_name in ["source-terminal.json", "native-terminal.json"]:
        t = read(source_root / "inputs" / terminal_name)
        require(t["native_exit_code"] == 0 and t["status"] == "PASS")
    for name, pin in old["source_pins"].items():
        path = source_root / name
        body = path.read_bytes()
        require(
            len(body) == pin["bytes"]
            and hashlib.sha256(body).hexdigest() == pin["sha256"]
        )
    require(
        api.joint_fixed_site_covariance.__module__
        == "bijux_pollenomics_lra.reconstruction.joint_fixed_site_covariance"
    )
    require(native["literal_axis"] == protocol["literal_axis"] == ["Betula", "Poaceae"])
    require(
        native["ppe"] == protocol["ppe"]
        and native["ppe_SD"] == protocol["ppe_sd_input_magnitudes"]
    )
    require(
        old["native_dataset_id"] == 23013
        and old["native_collection_unit_id"] == 16622
        and (old["native_chronology_id"] == 13366)
    )
    require(
        old["original_sample_count"] == 96
        and old["selected_sample_count"] == 95
        and (old["paired_windows"] == 24)
    )
    prior_terminal = read(source_root / "terminal.json")
    require(
        prior_terminal["native_exit_code"] == 0 and prior_terminal["status"] == "passed"
    )
    for name in [
        "native/geometry-sensitivity.json",
        "native/private-source-support.json",
        "comparison/independent-audit.json",
    ]:
        body = (source_root / name).read_bytes()
        pin = prior_terminal["outputs"][name]
        require(
            len(body) == pin["bytes"]
            and hashlib.sha256(body).hexdigest() == pin["sha256"]
        )
    axis = protocol["literal_axis"]
    scenarios = [row["id"] for row in protocol["wind_scenarios"]]
    require(scenarios == ["nominal_wind_3", "slow_wind_1_5", "fast_wind_6"])
    edges = selection["age_window_edges_cal_bp"]
    bins: dict[int, list[JsonMap]] = {i: [] for i in range(25)}
    refused: list[int] = []
    for sample in samples:
        ages = [
            x
            for x in sample["typed_calibrated_source_ages"]
            if x["native_chronology_id"] == 13366
        ]
        require(
            len(ages) == 1
            and ages[0]["source_age_type"] == "Calibrated radiocarbon years BP"
        )
        age = ages[0]["source_point_age"]
        w = bisect_right(edges, age) - 1 if edges[0] <= age < edges[-1] else None
        require(ages[0]["window_index"] == w)
        counts = sample["strict_unique_literal_parameter_counts"]
        require(
            all(
                t in counts
                and type(counts[t]["count"]) is int
                and (counts[t]["count"] >= 0)
                for t in axis
            )
        )
        require(sum(counts[t]["count"] for t in axis) > 0)
        if w is None:
            refused.append(sample["native_sample_id"])
        else:
            bins[w].append(sample)
    require(
        len(samples) == 96
        and sum(map(len, bins.values())) == 95
        and (len(refused) == 1)
    )
    baseline = next(
        x for x in old["physical_factors"] if x["scenario"] == "workbook_static_circle"
    )
    require(baseline["receiver_radius_m"] == protocol["receiver_radius_m"] == 837.0)
    require(
        protocol["inner_radius_m"] == 837.0 and protocol["outer_radius_m"] == 100000.0
    )
    require(
        protocol["diffusion_coefficient"] == 0.12
        and protocol["turbulence_parameter"] == 0.25
    )
    prior_physics = read(source_root / "comparison/independent-audit.json")
    baseline_checks = [
        r
        for r in prior_physics["physical_factor_checks"]
        if r["scenario"] == "workbook_static_circle"
    ]
    require(len(baseline_checks) == 2)
    require(
        all(
            row["maintained_factor"] == baseline["deposition"][row["taxon_index"]]
            for row in baseline_checks
        )
    )
    factors = {"nominal_wind_3": baseline["deposition"]}
    physical_rows = [
        {
            "scenario": "nominal_wind_3",
            "wind_speed_m_s": 3.0,
            "deposition": baseline["deposition"],
            "native_factor_execution_repeated": False,
            "authority": "Exact retained source-bound workbook_static_circle factors and prior independent lens comparison.",
        }
    ]
    physical = protocol["physical_tolerances"]
    for scenario in protocol["wind_scenarios"][1:]:
        values, estimates = [], []
        for fall in native["fall_speed_m_s"]:
            result = circular_receiver_annulus(
                receiver_radius_m=837.0,
                inner_radius_m=837.0,
                outer_radius_m=100000.0,
                fall_speed_m_s=fall,
                diffusion_coefficient=0.12,
                turbulence_parameter=0.25,
                wind_speed_m_s=scenario["wind_speed_m_s"],
                absolute_tolerance=physical["maintained_absolute"],
                relative_tolerance=physical["maintained_relative"],
                quadrature_limit=physical["maintained_subdivision_limit"],
            )
            require(0 < result.factor < 1)
            values.append(result.factor)
            estimates.append(result.estimated_absolute_error)
        factors[scenario["id"]] = values
        physical_rows.append(
            {
                "scenario": scenario["id"],
                "wind_speed_m_s": scenario["wind_speed_m_s"],
                "deposition": values,
                "adaptive_nonrigorous_absolute_error_estimates": estimates,
                "native_factor_execution_repeated": True,
                "authority": "New analyst-declared fixed-wind scenario; no estimated historical wind.",
            }
        )
    require(set(factors) == set(scenarios))
    ppeprofile = digest(
        {
            "native_snapshot": hashlib.sha256(
                (source_root / "inputs/native-results.json").read_bytes()
            ).hexdigest(),
            "axis": axis,
            "ppe": native["ppe"],
            "sd": native["ppe_SD"],
            "transport_scope": "same retained literal PPE profile across declared fixed winds",
        }
    )
    params = tuple(f"krageholm:{t}:{ppeprofile}" for t in axis)
    ppe = np.asarray(native["ppe"])
    cp = np.diag(np.square(np.asarray(native["ppe_SD"])))
    results: list[api.ConditionalResultInput] = []
    contexts: list[JsonMap] = []
    windows: list[JsonMap] = []
    samplepin = hashlib.sha256(
        (source_root / "inputs/dataset-23013-sample-eligibility.json").read_bytes()
    ).hexdigest()
    profile = next(
        x
        for x in native["single_dataset_profiles"]
        if x["selected_source_profile"]["native_dataset_id"] == 23013
        and x["selected_source_profile"]["native_chronology_id"] == 13366
    )
    saved = {
        x["window_index"]: x
        for x in profile["conditional_results"]
        if x["physical_profile"] == "metadata_radius_wind_3"
    }
    for w, group in bins.items():
        oldrow = old["window_rows"][w]
        require(oldrow["window_index"] == w)
        if not group:
            require(oldrow["status"] == "both_scenarios_refused_no_source_samples")
            windows.append(
                {
                    "window_index": w,
                    "status": "refused_no_source_samples",
                    "paired_standard_error": None,
                }
            )
            continue
        counts = [
            sum(x["strict_unique_literal_parameter_counts"][t]["count"] for x in group)
            for t in axis
        ]
        ids = sorted(x["native_sample_id"] for x in group)
        require(
            counts == saved[w]["source_support"]["counts"]
            and ids == sorted(saved[w]["source_support"]["native_sample_ids"])
        )
        support = digest(
            {
                "sample_capture_sha256": samplepin,
                "dataset": 23013,
                "unit": 16622,
                "chronology": 13366,
                "younger": edges[w],
                "older_exclusive": edges[w + 1],
                "native_sample_ids": ids,
                "literal_axis": axis,
                "counts": counts,
            }
        )
        bound = api.CountSupport(16622, 23013, 13366, edges[w], edges[w + 1], support)
        for scenario in scenarios:
            results.append(
                api.ConditionalResultInput(
                    f"{scenario}:window:{w}",
                    bound,
                    params,
                    np.asarray(counts),
                    np.asarray(factors[scenario]),
                    np.ones(2, dtype=bool),
                )
            )
            contexts.append(
                {
                    "window_index": w,
                    "scenario": scenario,
                    "counts": counts,
                    "deposition": factors[scenario],
                    "source_sha256": support,
                    "selected_native_sample_count": len(ids),
                }
            )
        windows.append(
            {
                "window_index": w,
                "status": "paired_conditional_results",
                "result_indices": [
                    len(results) - 3,
                    len(results) - 2,
                    len(results) - 1,
                ],
            }
        )

    def evaluate(
        rows: list[api.ConditionalResultInput], disjoint: bool = True
    ) -> api.JointFixedSiteCovariance:
        return api.joint_fixed_site_covariance(
            tuple(rows),
            parameter_ids=params,
            ppe=ppe,
            ppe_covariance=cp,
            assume_disjoint_window_count_independence=disjoint,
            assume_distinct_unit_count_independence=False,
        )

    joint = evaluate(results)
    require(
        len(joint.cover) == 144
        and joint.distinct_count_supports == 24
        and (joint.profile == "reveals-joint-fixed-site-delta-covariance")
    )
    L = np.zeros((96, 144))
    occupied = [row for row in windows if row["status"] == "paired_conditional_results"]
    contrast_contexts = []
    for window_number, row in enumerate(occupied):
        baseline_index, slow_index, fast_index = row["result_indices"]
        baseline_slice = joint.result_slices[baseline_index]
        prior = old["window_rows"][row["window_index"]]["scenarios"][
            "workbook_static_circle"
        ]
        for actual, key in [
            (joint.cover[baseline_slice], "conditional_panel_cover"),
            (
                joint.counting_covariance[baseline_slice, baseline_slice],
                "counting_covariance",
            ),
            (
                joint.ppe_covariance[baseline_slice, baseline_slice],
                "shared_ppe_covariance",
            ),
            (
                joint.total_covariance[baseline_slice, baseline_slice],
                "total_conditional_covariance",
            ),
        ]:
            require(
                np.max(np.abs(actual - np.asarray(prior[key])))
                <= protocol["absolute_tolerance"]
            )
        row["scenarios"] = {}
        for scenario, index in zip(scenarios, row["result_indices"], strict=True):
            selected_slice = joint.result_slices[index]
            row["scenarios"][scenario] = {
                "conditional_panel_cover": joint.cover[selected_slice].tolist(),
                "conditional_standard_error": np.sqrt(
                    np.maximum(
                        np.diag(joint.total_covariance[selected_slice, selected_slice]),
                        0,
                    )
                ).tolist(),
            }
        for alternative_number, index in enumerate([slow_index, fast_index]):
            offset = 4 * window_number + 2 * alternative_number
            L[offset : offset + 2, baseline_slice] = -np.eye(2)
            L[offset : offset + 2, joint.result_slices[index]] = np.eye(2)
            for taxon in range(2):
                contrast_contexts.append(
                    {
                        "window_index": row["window_index"],
                        "scenario": scenarios[alternative_number + 1],
                        "taxon_index": taxon,
                        "baseline_result_index": baseline_index,
                        "alternative_result_index": index,
                    }
                )
    contrasts = {
        name: L @ getattr(joint, field) @ L.T
        for name, field in [
            ("counting", "counting_covariance"),
            ("ppe", "ppe_covariance"),
            ("total", "total_covariance"),
        ]
    }
    require(
        all(
            np.diag(matrix).min() >= -protocol["absolute_tolerance"]
            for matrix in contrasts.values()
        )
    )
    contrastcover = L @ joint.cover
    for window_number, row in enumerate(occupied):
        row["contrasts"] = {}
        baseline_index = row["result_indices"][0]
        baseline_slice = joint.result_slices[baseline_index]
        for alternative_number, index in enumerate(row["result_indices"][1:]):
            offset = 4 * window_number + 2 * alternative_number
            block = slice(offset, offset + 2)
            selected_slice = joint.result_slices[index]
            row["contrasts"][scenarios[alternative_number + 1]] = {
                "alternative_minus_nominal_cover": contrastcover[block].tolist(),
                "conditional_paired_standard_error": np.sqrt(
                    np.maximum(np.diag(contrasts["total"])[block], 0)
                ).tolist(),
                "independence_counterfactual_standard_error": np.sqrt(
                    np.diag(joint.total_covariance[baseline_slice, baseline_slice])
                    + np.diag(joint.total_covariance[selected_slice, selected_slice])
                ).tolist(),
                **{
                    name + "_paired_covariance": matrix[block, block].tolist()
                    for name, matrix in contrasts.items()
                },
            }
    negative: list[JsonMap] = []
    first, second = (results[0], results[1])
    controls: dict[str, tuple[list[api.ConditionalResultInput], bool]] = {
        "same_support_changed_counts": (
            [first, replace(second, counts=second.counts + np.array([1, 0]))],
            True,
        ),
        "same_support_different_panel": (
            [first, replace(second, parameter_ids=params[::-1])],
            True,
        ),
        "different_support_reused_digest": (
            [
                first,
                replace(
                    second,
                    support=replace(
                        second.support, older_cal_bp=second.support.older_cal_bp + 1
                    ),
                ),
            ],
            True,
        ),
        "overlapping_same_unit_windows": (
            [
                first,
                replace(
                    second,
                    support=replace(
                        second.support,
                        younger_cal_bp=first.support.younger_cal_bp + 1,
                        source_sha256="d" * 64,
                    ),
                ),
            ],
            True,
        ),
        "alternate_chronology_same_unit": (
            [
                first,
                replace(
                    second,
                    support=replace(
                        second.support, chronology_id=13367, source_sha256="e" * 64
                    ),
                ),
            ],
            True,
        ),
        "disjoint_count_independence_undeclared": ([first, results[3]], False),
        "foreign_parameter_identity": (
            [replace(first, parameter_ids=("foreign", params[1]))],
            True,
        ),
        "unmeasured_axis": (
            [replace(first, taxon_measured=np.array([True, False]))],
            True,
        ),
        "noninteger_counts": (
            [replace(first, counts=first.counts + np.array([0.25, 0]))],
            True,
        ),
        "zero_panel_total": ([replace(first, counts=np.zeros(2))], True),
    }
    for name, (rows, disjoint) in controls.items():
        try:
            evaluate(rows, disjoint)
        except api.ValidationError as exc:
            negative.append({"control": name, "status": "refused", "reason": str(exc)})
        else:
            raise AssertionError(name + " was accepted")
    for name, wind in [
        ("zero_wind_refused", 0.0),
        ("negative_wind_refused", -1.0),
        ("nonfinite_wind_refused", float("nan")),
    ]:
        try:
            circular_receiver_annulus(
                receiver_radius_m=837.0,
                inner_radius_m=837.0,
                outer_radius_m=100000.0,
                fall_speed_m_s=0.024,
                diffusion_coefficient=0.12,
                turbulence_parameter=0.25,
                wind_speed_m_s=wind,
            )
        except api.ValidationError as error:
            negative.append(
                {"control": name, "status": "refused", "reason": str(error)}
            )
        else:
            raise AssertionError(name + " was accepted")
    require({row["control"] for row in negative} == set(protocol["negative_controls"]))
    out = output_root
    out.mkdir(parents=True, exist_ok=False)
    private = {
        "contexts": contexts,
        "parameter_ids": params,
        "ppe": ppe.tolist(),
        "ppe_covariance": cp.tolist(),
        "cover": joint.cover.tolist(),
        "count_jacobian": joint.count_jacobian.tolist(),
        "ppe_jacobian": joint.ppe_jacobian.tolist(),
        "counting_covariance": joint.counting_covariance.tolist(),
        "ppe_covariance_output": joint.ppe_covariance.tolist(),
        "total_covariance": joint.total_covariance.tolist(),
        "contrast_cover": contrastcover.tolist(),
        "contrast_covariance": {k: v.tolist() for k, v in contrasts.items()},
        "contrast_matrix": L.tolist(),
        "contrast_contexts": contrast_contexts,
    }
    (out / "joint-matrices.json").write_text(
        json.dumps(private, indent=2, allow_nan=False) + "\n"
    )
    public = {
        "schema_version": "krageholm-fixed-radius-wind-sensitivity.v1",
        "native_dataset_id": 23013,
        "native_collection_unit_id": 16622,
        "native_chronology_id": 13366,
        "profile": joint.profile,
        "protocol_sha256": hashlib.sha256(
            (DOMAIN / "wind-protocol.json").read_bytes()
        ).hexdigest(),
        "original_samples": 96,
        "selected_samples": 95,
        "window_domain_count": 25,
        "paired_windows": 24,
        "refused_windows": 1,
        "conditional_result_vectors": 72,
        "result_axes": 144,
        "distinct_count_supports": joint.distinct_count_supports,
        "shared_literal_parameter_axes": 2,
        "nominal_marginals_match_previous_configuration": True,
        "wind_scenarios": protocol["wind_scenarios"],
        "physical_factors": physical_rows,
        "new_response_tuples": 4,
        "retained_nominal_response_tuples": 2,
        "wind_uncertainty_distribution_supplied": False,
        "historical_wind_estimated": False,
        "contrast_axes": 96,
        "window_rows": windows,
        "negative_controls": negative,
        "ppe_covariance_authority": protocol["ppe_covariance_authority"],
        "geometry_uncertainty_distribution_supplied": False,
        "chronology_joint_posterior_supplied": False,
        "empirical_interval_coverage_claimed": False,
        "historical_basin_authenticated": False,
        "scientific_admission": False,
        "source_rights_admission": False,
        "global_shared_ppe_cross_window_covariance_retained": True,
        "full_count_covariance_reuses_same_source_between_wind_scenarios": True,
    }
    (out / "report.json").write_text(
        json.dumps(public, indent=2, allow_nan=False) + "\n"
    )
    origins = {
        name: str(Path(module.__file__).resolve())
        for name, module in __import__("sys").modules.items()
        if name.startswith("bijux_pollenomics_lra")
        and getattr(module, "__file__", None)
    }
    (out / "actual-module-origins.json").write_text(
        json.dumps(origins, indent=2) + "\n"
    )
    verify_sources(source_root, custody)
    return public


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    result = qualify(args.source_root, args.output_root)
    print(
        json.dumps(
            {
                "paired_windows": result["paired_windows"],
                "refused_windows": result["refused_windows"],
                "scientific_admission": False,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
