"""Reconstruct wider conditional panels from exact native counts and hypotheses."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from bijux_pollenomics_lra.api import fixed_site_cover_covariance
from bijux_pollenomics_lra.dispersal.receiver_annulus import circular_receiver_annulus

from ..swedish_static_basin.reconstruction import parameter_vectors, validate_protocol
from ..swedish_static_basin.sources import NativeSourceRecord, read_bound, sha256
from .comparison import compare_cases
from .mapping import scenario_input, source_to_parameter_map
from .sources import DECLARATION, PROTOCOL, load_scope


def reconstruct(
    repository: Path, candidate: str
) -> tuple[NativeSourceRecord, NativeSourceRecord]:
    """Reconstruct declared conditional panels without admitting source masks as complete."""
    authority_before = {
        relative: sha256(repository / relative) for relative in (DECLARATION, PROTOCOL)
    }
    producer_before = {p.name: sha256(p) for p in Path(__file__).parent.glob("*.py")}
    scenario, physical, datasets, basins, identities = load_scope(repository, candidate)
    edges = validate_protocol(physical)
    with (
        repository / "data/landclim/raw/landclim_ii_taxa_pft_ppe_fsp_values.csv"
    ).open(newline="") as stream:
        parameters = {
            r["Plant taxa/Pollen-morphological types"]: r
            for r in csv.DictReader(stream)
        }
    if len(parameters) != 31:
        raise ValueError("public parameter source must have31 unique rows")
    outputs = []
    audit_support = {}
    source_parent_child_pairs = (
        ("Betula", "Betula pubescens"),
        ("Betula", "Betula nana"),
        ("Pinus", "Pinus sylvestris"),
        ("Picea", "Picea abies"),
        ("Fagus", "Fagus sylvatica"),
        ("Corylus", "Corylus avellana"),
        ("Calluna", "Calluna vulgaris"),
        ("Fraxinus", "Fraxinus excelsior"),
        ("Tilia", "Tilia cordata"),
        ("Poaceae", "Poaceae undiff. (<40 µm)"),
        ("Poaceae", "Poaceae undiff. (>40 µm)"),
    )
    for core in physical["cores"]:
        code, did, chron = (
            core["metadata_code"],
            core["native_dataset_id"],
            core["chronology_id"],
        )
        samples = [
            {
                "native_sample_id": s["sample_id"],
                "native_analysis_unit_id": s["analysis_unit_id"],
                "depth": s["depth"],
                "source_ages": s["ages"],
                "counts": s["counts"],
                "reported_pollen_NISP_sum": s["reported_all_pollen_NISP_sum"],
            }
            for s in datasets[did]["samples"]
        ]
        metadata = basins[code]
        radius = float(metadata["fields"]["siteradius"])
        assert metadata["fields"]["siteType"] == "lake"
        names = {name for sample in samples for name in sample["counts"]}
        expected = scenario["native_source_population"][str(did)]
        assert (
            sum(s["reported_pollen_NISP_sum"] for s in samples)
            == expected["all_native_pollen_NISP_sum"]
        )
        assert len(samples) == expected["native_samples"] and len(
            {s["native_sample_id"] for s in samples}
        ) == len(samples)
        # Cache only immutable physical responses shared by explicitly declared alternatives.
        cache = {}
        for transfer in scenario["profiles"]:
            native_support = {}
            rules = [
                {"source": s, "target": t}
                for s, t in transfer["nonliteral_mappings"].items()
            ]
            mapping = source_to_parameter_map(names, set(parameters), rules)
            taxa = sorted(set(mapping.values()))
            assert taxa
            ppe, deviation, fall_values = parameter_vectors(repository, taxa)
            sd = deviation.tolist()
            fall = fall_values.tolist()
            cov = np.diag(deviation**2)
            grouped: dict[
                int,
                list[tuple[NativeSourceRecord, NativeSourceRecord, NativeSourceRecord]],
            ] = {}
            exclusions: Counter[str] = Counter()
            for sample in samples:
                ages = [
                    a
                    for a in sample["source_ages"]
                    if a["chronologyid"] == chron
                    and a["agetype"] == "Calibrated radiocarbon years BP"
                ]
                if len(ages) != 1:
                    exclusions["named_calibrated_chronology_missing_or_ambiguous"] += 1
                    continue
                age = ages[0]["age"]
                if (
                    isinstance(age, bool)
                    or not isinstance(age, (float, int))
                    or not math.isfinite(age)
                    or not edges[0] <= age < edges[-1]
                ):
                    exclusions["point_age_outside_declared_windows"] += 1
                    continue
                predicted = scenario_input(
                    sample,
                    mapping,
                    taxa,
                    sparse_zero_hypothesis=True,
                    mutually_exclusive_partition_hypothesis=True,
                    ambiguous_parent_child_pairs=source_parent_child_pairs,
                )
                index = int(np.searchsorted(edges, age, side="right") - 1)
                grouped.setdefault(index, []).append((sample, ages[0], predicted))
            deposition = {}
            response = []
            for transport in physical["profiles"]:
                values = []
                for name, speed in zip(taxa, fall, strict=True):
                    key = (name, transport["id"])
                    if key not in cache:
                        cache[key] = circular_receiver_annulus(
                            receiver_radius_m=radius * transport["radius_multiplier"],
                            inner_radius_m=radius * transport["radius_multiplier"],
                            outer_radius_m=physical["regional_extent_m"],
                            fall_speed_m_s=speed,
                            diffusion_coefficient=physical["diffusion_coefficient"],
                            turbulence_parameter=physical["turbulence_parameter"],
                            wind_speed_m_s=transport["wind_speed_m_s"],
                        )
                    values.append(cache[key])
                deposition[transport["id"]] = np.asarray([[v.factor for v in values]])
                response.append(
                    {
                        "profile": transport["id"],
                        "factors": deposition[transport["id"]].tolist(),
                        "estimated_absolute_error": [
                            v.estimated_absolute_error for v in values
                        ],
                        "rigorous_error_bound": False,
                    }
                )
            windows = []
            accepted_samples = 0
            accepted_windows = 0
            refused_zero_windows = 0
            for index, group in sorted(grouped.items()):
                counts = np.asarray(
                    [
                        [
                            sum(pred["counts"][i] for _, _, pred in group)
                            for i in range(len(taxa))
                        ]
                    ],
                    dtype=np.int64,
                )
                if counts.sum() == 0:
                    exclusions["hypothesized_parameter_panel_total_zero"] += len(group)
                    refused_zero_windows += 1
                    continue
                full = sum(pred["reported_all_pollen_NISP"] for _, _, pred in group)
                residual = sum(
                    pred["unparameterized_reported_pollen_NISP"] for _, _, pred in group
                )
                assert int(counts.sum()) + residual == full
                support = {
                    "source_sample_ids": [s["native_sample_id"] for s, _, _ in group],
                    "selected_source_name_axis": group[0][2][
                        "selected_source_name_axis"
                    ],
                    "actual_selected_source_name_presence": [
                        p["actual_selected_source_name_presence"] for _, _, p in group
                    ],
                    "any_source_label_present_on_parameter_axis": [
                        p["any_source_label_present_on_parameter_axis"]
                        for _, _, p in group
                    ],
                    "all_contributing_source_labels_present_on_parameter_axis": [
                        p["all_contributing_source_labels_present_on_parameter_axis"]
                        for _, _, p in group
                    ],
                    "hypothesized_complete_parameter_mask": [
                        pred["hypothesized_complete_input"] for _, _, pred in group
                    ],
                }
                support_key = f"{code}/{transfer['id']}/window-{index}"
                native_support[support_key] = support
                accepted_samples += len(group)
                accepted_windows += 1
                metadata_window = {
                    "younger_cal_bp": float(edges[index]),
                    "older_cal_bp_exclusive": float(edges[index + 1]),
                    "native_sample_count": len(group),
                    "raw_age_bounds_missing": sum(
                        a.get("ageolder") is None and a.get("ageyounger") is None
                        for _, a, _ in group
                    ),
                    "assumed_zero_source_cells": sum(
                        p["assumed_zero_source_cells"] for _, _, p in group
                    ),
                    "assumed_zero_parameter_cells": sum(
                        p["assumed_zero_parameter_cells"] for _, _, p in group
                    ),
                    "actual_explicit_zero_rows": sum(
                        p["actual_explicit_zero_rows"] for _, _, p in group
                    ),
                    "actual_source_target_presence_counts": [
                        sum(
                            p["any_source_label_present_on_parameter_axis"][i]
                            for _, _, p in group
                        )
                        for i in range(len(taxa))
                    ],
                    "source_support_key": support_key,
                    "source_support_sha256": hashlib.sha256(
                        json.dumps(
                            support, sort_keys=True, separators=(",", ":")
                        ).encode()
                    ).hexdigest(),
                    "hypothesized_panel_counts": counts.tolist(),
                    "panel_NISP_sum": int(counts.sum()),
                    "reported_all_pollen_NISP_sum": full,
                    "unparameterized_reported_NISP_sum": residual,
                    "retained_reported_pollen_mass_fraction": float(counts.sum())
                    / full,
                    "source_measurement_complete_claimed": False,
                    "model_mask_interpretation": "Complete mathematical input conditioned on declared sparse-zero/partition hypotheses; not the actual source presence mask",
                    "direct_hypothesized_panel_fraction": (
                        counts[0] / counts.sum()
                    ).tolist(),
                }
                baseline = None
                for transport in physical["profiles"]:
                    k = deposition[transport["id"]]
                    # This mask describes hypothesis-conditioned completeness, never observed source support.
                    assumed_mask = np.asarray(
                        [
                            [
                                all(
                                    p["hypothesized_complete_input"][i]
                                    for _, _, p in group
                                )
                                for i in range(len(taxa))
                            ]
                        ],
                        dtype=bool,
                    )
                    result = fixed_site_cover_covariance(
                        counts, k, ppe, cov, taxon_measured=assumed_mask
                    )
                    independent = counts[0] / (k[0] * ppe)
                    independent /= independent.sum()
                    assert np.allclose(
                        result.cover, independent, atol=1e-14, rtol=1e-12
                    )
                    assert np.allclose(
                        result.total_covariance,
                        result.counting_covariance + result.ppe_covariance,
                        atol=1e-14,
                        rtol=1e-12,
                    )
                    assert (
                        np.isfinite(result.total_covariance).all()
                        and np.all(result.cover >= 0)
                        and abs(result.cover.sum() - 1) < 1e-12
                    )
                    windows.append(
                        {
                            **metadata_window,
                            "transport_profile": transport["id"],
                            "conditional_cover": result.cover.tolist(),
                            "conditional_standard_error": result.standard_error.tolist(),
                            "counting_covariance": result.counting_covariance.tolist(),
                            "assumed_ppe_covariance": result.ppe_covariance.tolist(),
                            "total_conditional_covariance": result.total_covariance.tolist(),
                        }
                    )
                    if transport["id"] == "metadata_radius_wind_3":
                        baseline = result
                assert baseline is not None
                zero = fixed_site_cover_covariance(
                    counts,
                    deposition["metadata_radius_wind_3"],
                    ppe,
                    np.zeros_like(cov),
                    taxon_measured=assumed_mask,
                )
                assert np.allclose(
                    zero.counting_covariance,
                    baseline.counting_covariance,
                    atol=1e-14,
                    rtol=1e-12,
                )
                windows.append(
                    {
                        **metadata_window,
                        "transport_profile": "metadata_radius_wind_3_zero_ppe_uncertainty",
                        "conditional_cover": zero.cover.tolist(),
                        "conditional_standard_error": zero.standard_error.tolist(),
                    }
                )
            assert accepted_samples + sum(exclusions.values()) == len(samples)
            assert len(windows) == (len(physical["profiles"]) + 1) * accepted_windows
            case = {
                "refused_zero_panel_window_count": refused_zero_windows,
                "core": code,
                "native_dataset_id": did,
                "chronology_id": chron,
                "metadata_static_radius_m": radius,
                "metadata_area_m2": math.pi * radius**2,
                "scenario": transfer["id"],
                "parameter_taxa": taxa,
                "parameter_ppe": ppe.tolist(),
                "parameter_sd": sd,
                "parameter_fall_speed_m_s": fall,
                "source_to_parameter_map": mapping,
                "source_rows_remain_source_names_not_accepted_taxonomy": True,
                "native_samples": len(samples),
                "included_native_samples": accepted_samples,
                "exclusions_by_reason": dict(exclusions),
                "occupied_windows": accepted_windows,
                "response": response,
                "results": windows,
            }
            audit_support.update(native_support)
            support_body = json.dumps(
                native_support,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode()
            case["local_actual_source_support_sha256"] = hashlib.sha256(
                support_body
            ).hexdigest()
            case["local_actual_source_support_key_count"] = len(native_support)
            # Retain actual per-sample source masks in a separate local audit capsule; public output carries aggregate support and digest.
            compact: list[NativeSourceRecord] = []
            for row in windows:
                scope = {
                    k: v
                    for k, v in row.items()
                    if k
                    not in {
                        "transport_profile",
                        "conditional_cover",
                        "conditional_standard_error",
                        "counting_covariance",
                        "assumed_ppe_covariance",
                        "total_conditional_covariance",
                    }
                }
                numerical = {
                    k: v
                    for k, v in row.items()
                    if k
                    in {
                        "transport_profile",
                        "conditional_cover",
                        "conditional_standard_error",
                    }
                    or row["transport_profile"] == "metadata_radius_wind_3"
                    and k
                    in {
                        "counting_covariance",
                        "assumed_ppe_covariance",
                        "total_conditional_covariance",
                    }
                }
                key = (row["younger_cal_bp"], row["older_cal_bp_exclusive"])
                if (
                    compact
                    and (
                        compact[-1]["younger_cal_bp"],
                        compact[-1]["older_cal_bp_exclusive"],
                    )
                    == key
                ):
                    compact[-1]["numerical_profiles"].append(numerical)
                else:
                    compact.append({**scope, "numerical_profiles": [numerical]})
            case["results"] = compact
            case["covariance_output_scope"] = (
                "Full baseline conditional covariance; remaining physical sensitivities and zero-PPE control retain actual point/SE outputs. Original local capture retains all physical-profile covariance matrices."
            )
            outputs.append(case)
            print(
                code,
                transfer["id"],
                len(taxa),
                "taxa",
                accepted_samples,
                "samples",
                accepted_windows,
                "windows",
                flush=True,
            )
    adjacent = []
    for code in ["ABB", "BOKE", "BUS", "TIB"]:
        cases = [
            next(
                case
                for case in outputs
                if case["core"] == code and case["scenario"] == profile["id"]
            )
            for profile in scenario["profiles"]
        ]
        expanded = []
        for case in cases:
            baseline_windows = [
                {
                    **{k: v for k, v in row.items() if k != "numerical_profiles"},
                    **next(
                        p
                        for p in row["numerical_profiles"]
                        if p["transport_profile"] == "metadata_radius_wind_3"
                    ),
                }
                for row in case["results"]
            ]
            expanded.append({**case, "results": baseline_windows})
        for left, right in [(expanded[1], expanded[2]), (expanded[2], expanded[3])]:
            adjacent.append(compare_cases(left, right))
    for name, identity in identities.items():
        read_bound(repository, name, identity)
    if authority_before != {
        relative: sha256(repository / relative) for relative in authority_before
    } or producer_before != {
        p.name: sha256(p) for p in Path(__file__).parent.glob("*.py")
    }:
        raise ValueError("transfer source/control authority changed during computation")
    report = {
        "schema_version": "swedish-parameter-transfer-maintained-producer.v1",
        "producer_source_candidate": candidate,
        "producer_source_sha256": producer_before,
        "source_files": identities,
        "source_declaration_sha256": authority_before[DECLARATION],
        "scenario_protocol_sha256": authority_before[PROTOCOL],
        "candidate_binding_scope": "Declared exact source base plus finite producer overlay; immutable external execution receipt establishes actual source custody, not a SHA argument alone.",
        "scenario_protocol": scenario,
        "physical_protocol": physical,
        "cases": outputs,
        "adjacent_profile_comparisons": adjacent,
        "estimator_denominator": "Mapped-panel NISP under declared sparse/partition/PPE-transfer hypotheses; residual pollen mass is retained, not inverted to full land cover.",
        "zero_SE_scope": "Boundary plug-in delta SE at observed or imputed zero does not prove absence or uncertainty coverage; conditional delta SE is not an absence interval.",
        "parent_child_guard_scope": "Finite selected source-name pairs, without authenticated complete native higher-taxon/synonym graph.",
        "historical_reproduction_claimed": False,
        "accepted_taxonomy_mapping_claimed": False,
        "observed_sparse_zero_claimed": False,
        "complete31_measurement_claimed": False,
        "vegetation_accuracy_claimed": False,
        "nativeR_numerical_parity_claimed": False,
        "raw_source_redistribution_authorized": False,
    }
    return report, audit_support
