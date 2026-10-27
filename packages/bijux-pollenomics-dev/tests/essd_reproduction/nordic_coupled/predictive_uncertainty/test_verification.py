"""Manual equations and negative controls for the predictive-law observer."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as Q
import hashlib
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.verification import (
    algebra as observer,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty.verification import (
    audit,
    summaries,
)


def test_regional_rounds_both_percent_components_without_inventing_a_complement() -> (
    None
):
    assert observer.regional_cover([3, 1], [2, 1], [1, 1]) == (Q(3, 5), Q(2, 5))
    assert observer.rounded_percent(Q(12345, 10000)) == 1.234
    assert observer.rounded_percent(Q(12355, 10000)) == 1.236


def test_signed_love_retains_negative_first_ring_and_positive_final_ring() -> None:
    regional = (Q(1, 2), Q(1, 2))
    first = observer.signed_local([1, 3], [1, 1], regional, [1, 1], [4, 0])
    final = observer.signed_local([1, 3], [1, 1], regional, [2, 2], [1, 1])
    assert first == (Q(-5, 4), Q(9, 4))
    assert not observer.admitted(first)
    assert final == (Q(1, 8), Q(7, 8))
    assert observer.admitted(final)


def test_spatial_ties_zero_distances_and_fixed_two_predictor_requirement() -> None:
    assert observer.weights("training_mean", [1, 2]) == (Q(1, 2), Q(1, 2))
    assert observer.weights("nearest_site", [4, 4]) == (Q(1, 2), Q(1, 2))
    assert observer.weights("inverse_distance_squared", [1, 2]) == (Q(4, 5), Q(1, 5))
    assert observer.weights("inverse_distance_squared", [0, 2]) == (Q(1), Q(0))
    with pytest.raises(ValueError, match="both local"):
        observer.interpolated([(Q(1, 2), Q(1, 2)), (Q(-1), Q(2))], [Q(1), Q(0)])


def test_full_forward_includes_shared_ppe_and_regional_outer_contribution() -> None:
    value = observer.forward_pollen(
        [Q(1, 4), Q(3, 4)],
        [Q(1, 2), Q(1, 2)],
        [2, 1],
        [[1, 2], [3, 4]],
        [1, 1],
        [5, 6],
    )
    # The four-ring unnormalized amounts are 2*(1+5/2) and 9/2+3.
    assert value == (Q(14, 29), Q(15, 29))


def test_owner_stream_is_metadata_only_and_perturbing_target_cannot_shift_training() -> (
    None
):
    ppe, baseline = observer.replay_draws(
        {"regional": [7, 3], "local-a": [2, 8], "target": [4, 6]},
        [2, 1],
        [0.2, 0.1],
        replicates=12,
        seed=123,
    )
    altered_ppe, altered = observer.replay_draws(
        {"target": [9000, 1], "local-a": [2, 8], "regional": [7, 3]},
        [2, 1],
        [0.2, 0.1],
        replicates=12,
        seed=123,
    )
    assert ppe == altered_ppe
    assert baseline["regional"] == altered["regional"]
    assert baseline["local-a"] == altered["local-a"]
    assert baseline["target"] != altered["target"]
    assert all(sum(row) == 10 for row in baseline["target"])


def test_whole_vector_rejection_matches_literal_shared_library_stream() -> None:
    ppe, _ = observer.replay_draws(
        {"owner": [1, 2]}, [-1, 1], [1, 1], replicates=8, seed=7
    )
    generator = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence(7, spawn_key=(1,)))
    )
    expected: list[list[float]] = []
    rejected = 0
    while len(expected) < 8:
        first, second = generator.normal([-1, 1], [1, 1])
        if first >= 0 and second >= 0:
            expected.append([float(first), float(second)])
        else:
            rejected += 1
    assert rejected > 0
    assert ppe == expected


@pytest.mark.parametrize("bad", [[True, 1], [-1, 2], [1.0, 2], [0, 0]])
def test_multinomial_native_integer_and_positive_total_roles(bad: list[object]) -> None:
    with pytest.raises(ValueError):
        observer.replay_draws({"owner": bad}, [2, 1], [0, 0], replicates=1, seed=1)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, "1"])
def test_numeric_contract_excludes_nonfinite_bool_and_text(bad: object) -> None:
    with pytest.raises(ValueError):
        observer.finite(bad)


def test_all_field_comparison_keeps_masks_nulls_integer_types_and_extra_fields_strict() -> (
    None
):
    expected = {"mask": [True, False], "count": 2, "rows": [[0.25, 0.75], None]}
    observer.compare(expected, expected)
    for broken in (
        {**expected, "mask": [1, False]},
        {**expected, "count": 2.0},
        {**expected, "rows": [[0.3, 0.7], None]},
        {**expected, "extra": None},
    ):
        with pytest.raises(ValueError):
            observer.compare(broken, expected)


def test_conditional_moments_keep_undefined_mass_and_simplex_covariance() -> None:
    result = summaries.ensemble_summary(
        [[0.0, 1.0], [None, None], [1.0, 0.0]], [True, False, True]
    )
    assert result["undefined_mass"] == 1 / 3
    assert result["unconditional_status"] == "refused_undefined_mass"
    conditional = result["conditional"]
    assert conditional["mean"] == [0.5, 0.5]
    assert conditional["covariance"] == [[0.25, -0.25], [-0.25, 0.25]]
    assert all(sum(row) == 0 for row in conditional["covariance"])
    assert conditional["mean_mcse"] == [0.5, 0.5]
    assert conditional["empirical_quantiles"] == {
        "0.025": [0.025, 0.025],
        "0.5": [0.5, 0.5],
        "0.975": [0.975, 0.975],
    }


def test_zero_and_one_defined_rows_do_not_claim_zero_mc_error() -> None:
    empty = summaries.ensemble_summary([[None, None]], [False])
    assert empty["conditional"]["mean"] is None
    assert empty["conditional"]["mean_mcse"] is None
    one = summaries.ensemble_summary([[0.25, 0.75]], [True])
    assert one["conditional"]["covariance"] == [[0.0, 0.0], [0.0, 0.0]]
    assert one["conditional"]["mean_mcse"] is None
    assert (
        one["conditional"]["mean_mcse_status"] == "unavailable_fewer_than_two_defined"
    )


def test_quantiles_use_ordered_linear_interpolation_not_normal_coverage() -> None:
    assert summaries.linear_quantile([2, 0, 10, 4], 0.5) == 3
    assert summaries.linear_quantile([2, 0, 10, 4], 0.025) == pytest.approx(0.15)


def constant_summary(values: list[float]) -> dict[str, Any]:
    """Literal moments for a constant 1024-row ensemble, independent of the oracle."""
    return {
        "total_replicates": 1024,
        "defined_replicates": 1024,
        "undefined_replicates": 0,
        "undefined_mass": 0.0,
        "unconditional_status": "defined",
        "conditional": {
            "status": "defined",
            "mean": values,
            "covariance": [[0.0] * len(values) for _ in values],
            "sd": [0.0] * len(values),
            "empirical_quantiles": dict.fromkeys(("0.025", "0.5", "0.975"), values),
            "mean_mcse": [0.0] * len(values),
            "mean_mcse_status": "estimated_iid_conditional_expectation",
        },
        "covariance_divisor": "defined_replicates",
        "quantile_method": "linear",
        "mcse_scope": "IID conditional working-law expectation, not exact finite-ensemble mean error or field uncertainty",
    }


def complete_packets() -> tuple[dict[str, Any], ...]:
    """All pollen is taxon one: every closed prediction is analytically [1,0]."""
    windows = [f"cal-bp-{a}-{a + 500}" for a in range(2700, 5700, 500)]
    units = {
        "BOKE": (54001, 39241),
        "BUS": (53995, 39238),
        "SOLSOE83": (4446, 4304),
        "KRAGMJNY": (23013, 16622),
    }

    def owner(core: str, window: str) -> str:
        dataset, collection = units[core]
        return f"neotoma-{dataset}-{collection}-{window}"

    sampling = {
        "replicates": 1024,
        "seed": 20261027,
        "taxa": ["Betula", "Ulmus"],
        "ppe_means": [5.106, 1.27],
        "ppe_sds": [0.303, 0.05],
        "bit_generator": "PCG64",
        "count_stream": "SeedSequence(seed, spawn_key=(0, *eight_big_endian_uint32_words_of_SHA256_UTF8_owner_id))",
        "ppe_stream": "SeedSequence(seed, spawn_key=(1,))",
    }
    population: dict[str, Any] = dict(
        zip(
            [
                "original_folds",
                "original_method_dispositions",
                "active_folds",
                "propagated_method_slots",
                "original_refused_slots_retained",
                "draw_owner_count",
                "other_metadata_owner_count",
            ],
            [18, 54, 3, 9, 45, 4, 20],
            strict=True,
        )
    )
    population["active_window_cal_bp"] = [2700, 3200]
    inputs: dict[str, Any] = {
        "protocol": {
            "schema_version": "krageholm-predictive-uncertainty.v1",
            "sampling": sampling,
            "population": population,
            "numerical_checks": {
                "no_clipping_or_single_predictor_fallback": True,
                "nominal_prediction_absolute_tolerance": 1e-12,
                "independent_absolute_tolerance": 1e-13,
                "independent_relative_tolerance": 1e-10,
            },
            "summaries": {
                "conditional_population_covariance_ddof": 0,
                "quantile_probabilities": [0.025, 0.5, 0.975],
                "quantile_method": "linear",
            },
        },
        "owners": [],
        "cases": [],
        "folds": [],
        "dispositions": [],
        "nominal_predictions": [],
        "source_files": [],
        "accounting": {
            "sampling": deepcopy(sampling),
            "owner_lineage": {},
            "all_source_fingerprints_role": "accounting_only_not_fold_scientific_ancestry",
        },
    }
    for window in windows:
        for core in units:
            identity = owner(core, window)
            inputs["owners"].append({"owner_id": identity, "counts": [1, 0]})
            inputs["accounting"]["owner_lineage"][identity] = {
                "core": core,
                "raw": {
                    "path": f"artifacts/synthetic/{window}/{core}.json",
                    "bytes": 20,
                    "sha256": "b" * 64,
                },
                "panel_N": 1,
                "projection": {"projected_panel_N": 1},
            }
        for core in ("BOKE", "BUS", "SOLSOE83"):
            target, regional = owner(core, window), owner("KRAGMJNY", window)
            locals_ = sorted(
                owner(c, window) for c in ("BOKE", "BUS", "SOLSOE83") if c != core
            )
            fold_id, case_id = "fold-" + core, window + ":fold-" + core
            status = "predicted" if window == windows[0] else "refused"
            dispositions = [
                {"bin": window, "fold_id": fold_id, "method": method, "status": status}
                for method in observer.METHODS
            ]
            inputs["dispositions"].extend(dispositions)
            inputs["folds"].append(
                {
                    "case_id": case_id,
                    "bin": window,
                    "fold_id": fold_id,
                    "target_id": target,
                    "regional_owner_id": regional,
                    "local_owner_ids": locals_,
                    "nominal_status": status,
                    "nominal_refusal": None
                    if status == "predicted"
                    else [{"status": "refused"}] * 3,
                    "scientific_count_refs": [
                        inputs["accounting"]["owner_lineage"][identity]["raw"]
                        for identity in [regional, *locals_]
                    ],
                    "target_geometry_ref": {"path": core + "-geometry.json"},
                }
            )
            if status == "predicted":
                inputs["cases"].append(
                    {
                        "case_id": case_id,
                        "target_id": target,
                        "regional_owner_id": regional,
                        "local_owners": [
                            {
                                "owner_id": identity,
                                "local_k": [[1.0, 1.0]] * 2,
                                "regional_k": [[0.25, 0.25]] * 2,
                            }
                            for identity in locals_
                        ],
                        "regional_deposition": [1.0, 1.0],
                        "forward_local_k": [[1.0, 1.0]] * 2,
                        "forward_regional_k": [2.0, 2.0],
                        "terrestrial_fraction": [1.0, 1.0],
                        "distances_km": [1.0, 2.0],
                        "selected_ring_index": 1,
                    }
                )
                inputs["nominal_predictions"].extend(
                    {
                        "case_id": case_id,
                        "method": method,
                        "pollen_fraction": [1.0, 0.0],
                        "vegetation_fraction": [1.0, 0.0],
                        "regional_cover": [1.0, 0.0],
                        "prediction_manifest_sha256": "c" * 64,
                    }
                    for method in observer.METHODS
                )
    active = sorted(owner(core, windows[0]) for core in units)
    inputs["accounting"]["active_draw_owner_ids"] = active
    rng = np.random.Generator(
        np.random.PCG64(np.random.SeedSequence(20261027, spawn_key=(1,)))
    )
    # These means/SDs make negative normal draws practically absent, but retain the literal rule.
    ppe: list[list[float]] = []
    while len(ppe) < 1024:
        row = rng.normal([5.106, 1.27], [0.303, 0.05])
        if min(row) >= 0:
            ppe.append(row.tolist())
    count_hash = hashlib.sha256(
        np.array([[1, 0]] * 1024, dtype="<i8").tobytes()
    ).hexdigest()
    ppe_hash = hashlib.sha256(np.array(ppe, dtype="<f8").tobytes()).hexdigest()
    bank: dict[str, Any] = {
        "replicates": 1024,
        "seed": 20261027,
        "ppe_means": [5.106, 1.27],
        "ppe_sds": [0.303, 0.05],
        "ppe": ppe,
        "owners": [],
    }
    for identity in active:
        digest = hashlib.sha256(identity.encode()).digest()
        bank["owners"].append(
            {
                "owner_id": identity,
                "stream_index": [
                    int.from_bytes(digest[i : i + 4], "big") for i in range(0, 32, 4)
                ],
                "counts": [1, 0],
                "samples": [[1, 0]] * 1024,
            }
        )
    predictions: dict[str, Any] = {
        "schema_version": "krageholm-predictive-ensemble.v1",
        "cases": [],
        "original_dispositions": deepcopy(inputs["dispositions"]),
        "nominal_predictions": [],
    }
    for case in inputs["cases"]:
        ids = [
            case["regional_owner_id"],
            *(r["owner_id"] for r in case["local_owners"]),
        ]
        input_identity = {
            "case": deepcopy(case),
            "count_owners": [
                {
                    "owner_id": value,
                    "counts": [1, 0],
                    "stream_index": next(
                        r["stream_index"]
                        for r in bank["owners"]
                        if r["owner_id"] == value
                    ),
                    "samples_sha256": count_hash,
                }
                for value in ids
            ],
            "ppe": {
                "seed": 20261027,
                "replicates": 1024,
                "means": [5.106, 1.27],
                "sds": [0.303, 0.05],
                "samples_sha256": ppe_hash,
            },
        }
        methods = {}
        for method, spatial in zip(
            observer.METHODS, [[0.5, 0.5], [1.0, 0.0], [0.8, 0.2]], strict=True
        ):
            methods[method] = {
                "weights": spatial,
                "cover": [[1.0, 0.0]] * 1024,
                "pollen": [[1.0, 0.0]] * 1024,
                "direct_pollen": [[1.0, 0.0]] * 1024,
                "physical_minus_direct": [[0.0, 0.0]] * 1024,
                "valid_mask": [True] * 1024,
                "refusals": [None] * 1024,
                "summary": constant_summary([1.0, 0.0]),
                "direct_summary": constant_summary([1.0, 0.0]),
                "matched_difference_summary": constant_summary([0.0, 0.0]),
            }
        predictions["cases"].append(
            {
                "schema_version": "krageholm-predictive-ensemble.case.v1",
                "case_id": case["case_id"],
                "target_id": case["target_id"],
                "axis": ["Betula", "Ulmus"],
                "replicates": 1024,
                "allowed_inputs": input_identity,
                "regional_cover": [[1.0, 0.0]] * 1024,
                "regional_refusals": [None] * 1024,
                "local_signed_cover": [[[[1.0, 0.0]] * 2] * 2] * 1024,
                "local_ring_refusals": [[[None, None], [None, None]]] * 1024,
                "local_refusals": [[None, None]] * 1024,
                "methods": methods,
            }
        )
        predictions["nominal_predictions"].extend(
            {
                "case_id": case["case_id"],
                "target_id": case["target_id"],
                "method": method,
                "pollen_fraction": [1.0, 0.0],
                "vegetation_fraction": [1.0, 0.0],
                "reference_prediction_manifest_sha256": "c" * 64,
            }
            for method in observer.METHODS
        )

    def matched(values: list[float], *, all_direct: bool = True) -> dict[str, Any]:
        result = {
            "physical": constant_summary(values),
            "direct_on_physical_defined": constant_summary(values),
            "physical_minus_direct": constant_summary([0.0] * len(values)),
        }
        if all_direct:
            result["direct_all_replicates"] = constant_summary(values)
        return result

    case_ids = sorted(row["case_id"] for row in inputs["cases"])
    summary = {
        "schema_version": "coupled-pollen-bootstrap-summary.v1",
        "joint_predictions": {
            method: {"case_ids": case_ids, **matched([1.0, 0.0] * 3)}
            for method in observer.METHODS
        },
        "score_diagnostics": {
            "observed": [
                {
                    "case_id": row["case_id"],
                    "target_id": row["target_id"],
                    "counts": [1, 0],
                    "counts_source_reference": inputs["accounting"]["owner_lineage"][
                        row["target_id"]
                    ]["raw"],
                    "pollen_fraction": [1.0, 0.0],
                }
                for row in inputs["cases"]
            ],
            "cases": [
                {"case_id": case_id, "method": method, **matched([0.0] * 3)}
                for case_id in case_ids
                for method in observer.METHODS
            ],
            "aggregate": {
                method: {"case_ids": case_ids, **matched([0.0] * 3, all_direct=False)}
                for method in observer.METHODS
            },
        },
        "outcome_access": {
            "prediction_manifest_sha256": "d" * 64,
            "readback_verified": True,
            "scope": "previously exposed; postfreeze diagnostic only",
        },
    }
    return inputs, bank, predictions, summary


def test_complete_literal_packet_verifies_all_1024_rows_and_preserves_54_slots() -> (
    None
):
    result = audit(*complete_packets())
    assert result["replicate_method_slots_verified"] == 9216
    assert result["retained_nominal_refusals"] == 45
    assert result["joint_defined_replicates"] == dict.fromkeys(observer.METHODS, 1024)


@pytest.mark.parametrize(
    "defect",
    [
        "missing_fold",
        "active_old_refusal",
        "target_training",
        "global_bank_ancestry",
        "wrong_seed",
        "wrong_nominal",
        "wrong_count_mass",
        "wrong_mask",
        "missing_last_draw",
        "wrong_mcse",
        "wrong_observed_reference",
        "pre_freeze_outcome",
    ],
)
def test_complete_audit_refuses_population_lineage_law_draw_and_summary_tampering(
    defect: str,
) -> None:
    inputs, bank, predictions, summary = complete_packets()
    if defect == "missing_fold":
        inputs["folds"].pop()
    elif defect == "active_old_refusal":
        inputs["dispositions"][-1]["status"] = "predicted"
    elif defect == "target_training":
        inputs["cases"][0]["local_owners"][0]["owner_id"] = inputs["cases"][0][
            "target_id"
        ]
    elif defect == "global_bank_ancestry":
        predictions["cases"][0]["allowed_inputs"]["bank_sha256"] = "e" * 64
    elif defect == "wrong_seed":
        bank["seed"] += 1
    elif defect == "wrong_nominal":
        predictions["nominal_predictions"][0]["pollen_fraction"] = [0.9, 0.1]
    elif defect == "wrong_count_mass":
        bank["owners"][0]["samples"] = [[2, 0]] * 1024
    elif defect == "wrong_mask":
        predictions["cases"][0]["methods"]["training_mean"]["valid_mask"][1023] = False
    elif defect == "missing_last_draw":
        predictions["cases"][0]["regional_cover"].pop()
    elif defect == "wrong_mcse":
        summary["joint_predictions"]["training_mean"]["physical"]["conditional"][
            "mean_mcse"
        ][0] = 0.5
    elif defect == "wrong_observed_reference":
        summary["score_diagnostics"]["observed"][0]["counts_source_reference"] = {
            "path": "foreign"
        }
    else:
        summary["outcome_access"]["readback_verified"] = False
    with pytest.raises(ValueError):
        audit(inputs, bank, predictions, summary)


def single_case() -> tuple[dict[str, Any], dict[str, Any]]:
    inputs, bank, _, _ = complete_packets()
    case = inputs["cases"][0]
    bank["replicates"] = 1
    bank["ppe"] = [[1.0, 1.0]]
    for row in bank["owners"]:
        row["counts"] = [1, 1]
        row["samples"] = [[1, 1]]
    second = case["local_owners"][1]["owner_id"]
    next(row for row in bank["owners"] if row["owner_id"] == second)["samples"] = [
        [1, 3]
    ]
    return case, bank


def test_final_ring_selection_preserves_an_unselected_negative_ring() -> None:
    case, bank = single_case()
    case["local_owners"][1]["regional_k"][0] = [4.0, 0.01]
    result = observer.case_arrays(case, bank)
    assert result["local_signed_cover"][0][1][0][0] < 0
    assert result["local_signed_cover"][0][1][1][0] > 0
    assert all(value["valid_mask"] == [True] for value in result["methods"].values())


def test_invalid_zero_weight_predictor_refuses_all_methods_without_fallback() -> None:
    case, bank = single_case()
    case["local_owners"][1]["regional_k"][1] = [4.0, 0.01]
    result = observer.case_arrays(case, bank)
    assert result["methods"]["nearest_site"]["weights"] == [1.0, 0.0]
    for method in result["methods"].values():
        assert method["valid_mask"] == [False]
        assert method["refusals"] == ["required_local_predictor_undefined"]
        assert method["pollen"] == [[None, None]]
        assert method["direct_summary"]["defined_replicates"] == 1
        assert method["summary"]["unconditional_status"] == "refused_undefined_mass"


def test_retained_zero_ppe_refuses_math_without_resampling_counts_or_direct_baseline() -> (
    None
):
    case, bank = single_case()
    bank["ppe"] = [[0.0, 1.0]]
    result = observer.case_arrays(case, bank)
    assert result["regional_refusals"] == ["ppe_nonpositive"]
    assert result["local_ring_refusals"] == [[["regional_undefined"] * 2] * 2]
    assert all(value["valid_mask"] == [False] for value in result["methods"].values())
    assert all(
        value["direct_summary"]["defined_replicates"] == 1
        for value in result["methods"].values()
    )


def test_global_event_is_intersection_not_pairwise_available_covariance() -> None:
    cases = []
    observed = []
    for case_id, mask in zip(
        ("a", "b", "c"), ([True, False], [False, True], [True, True]), strict=True
    ):
        pollen = [[0.5, 0.5] if keep else [None, None] for keep in mask]
        cases.append(
            {
                "case_id": case_id,
                "replicates": 2,
                "methods": {
                    method: {
                        "pollen": pollen,
                        "direct_pollen": [[0.5, 0.5]] * 2,
                        "valid_mask": mask,
                    }
                    for method in observer.METHODS
                },
            }
        )
        observed.append({"case_id": case_id, "pollen_fraction": [0.5, 0.5]})
    result = summaries.reference_summaries(cases, observed, {})
    for method in observer.METHODS:
        assert (
            result["joint_predictions"][method]["physical"]["defined_replicates"] == 0
        )
        assert (
            result["joint_predictions"][method]["direct_all_replicates"][
                "defined_replicates"
            ]
            == 2
        )
        assert (
            result["score_diagnostics"]["aggregate"][method]["physical"][
                "defined_replicates"
            ]
            == 0
        )
        assert (
            result["score_diagnostics"]["aggregate"][method]["physical"]["conditional"][
                "covariance"
            ]
            is None
        )
