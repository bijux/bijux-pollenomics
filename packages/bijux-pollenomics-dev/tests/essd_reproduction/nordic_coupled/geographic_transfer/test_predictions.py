"""Cached-fit-only nominal correspondence, refusal inheritance and Hellinger flow."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import math
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.geographic_transfer import (
    predictions,
)


def bind(candidate: dict[str, Any]) -> None:
    """Keep synthetic scientific identities coherent after deliberate input changes."""
    allowed = candidate["cached_fit"]["allowed_inputs"]
    allowed["case"] = deepcopy(candidate["case"])
    allowed["ppe"]["samples_sha256"] = hashlib.sha256(
        np.asarray(candidate["ppe_samples"], dtype="<f8").tobytes(order="C")
    ).hexdigest()
    candidate["scientific_refs"]["allowed_inputs"] = deepcopy(allowed)


def candidate(*, replicates: int = 4, defined: int = 3) -> dict[str, Any]:
    """Create source-compatible array axes with independently known nominal values."""
    assert 0 <= defined <= replicates
    case = {
        "case_id": "synthetic-case",
        "target_id": "held-out",
        "regional_owner_id": "regional",
        "local_owners": [
            {
                "owner_id": owner,
                "local_k": [[1.0, 1.0], [2.0, 2.0]],
                "regional_k": [[1.0, 1.0], [2.0, 2.0]],
            }
            for owner in ("local-far", "local-near")
        ],
        "regional_deposition": [1.0, 1.0],
        "forward_local_k": [[2.0, 1.0], [1.0, 4.0]],
        "forward_regional_k": [0.5, 0.25],
        "terrestrial_fraction": [0.5, 0.25],
        "distances_km": [40.0, 20.0],
        "selected_ring_index": 1,
    }
    ppe = [[2.0 + 0.25 * (i % 3), 3.0 + 0.25 * (i % 2)] for i in range(replicates)]
    allowed = {
        "case": deepcopy(case),
        "count_owners": [
            {
                "owner_id": owner,
                "counts": [3, 2],
                "stream_index": [0] * 8,
                "samples_sha256": "c" * 64,
            }
            for owner in ("regional", "local-far", "local-near")
        ],
        "ppe": {
            "seed": 20261027,
            "replicates": replicates,
            "means": [2.0, 3.0],
            "sds": [0.1, 0.1],
            "samples_sha256": "",
        },
    }
    source_mask = [i < defined for i in range(replicates)]
    signed = []
    local_refusals = []
    for i, valid in enumerate(source_mask):
        far = [0.1 * (i % 4), 1 - 0.1 * (i % 4)] if valid else [-0.25, 1.25]
        near = [1 - 0.1 * (i % 3), 0.1 * (i % 3)]
        signed.append([[[-1.0, 2.0], far], [[None, None], near]])
        local_refusals.append(
            [None, None] if valid else ["local_selected_cover_out_of_bounds", None]
        )
    cached = {
        "schema_version": "krageholm-predictive-ensemble.case.v1",
        "case_id": case["case_id"],
        "target_id": case["target_id"],
        "axis": list(predictions.AXIS),
        "replicates": replicates,
        "allowed_inputs": allowed,
        "regional_cover": [[0.4, 0.6] for _ in range(replicates)],
        "regional_refusals": [None] * replicates,
        "local_signed_cover": signed,
        "local_ring_refusals": [
            [[None, None], ["local_engine_nonfinite", None]] for _ in range(replicates)
        ],
        "local_refusals": local_refusals,
        "methods": {
            method: {
                "valid_mask": list(source_mask),
                "refusals": [
                    None if valid else "required_local_predictor_undefined"
                    for valid in source_mask
                ],
            }
            for method in predictions.METHODS
        },
    }
    references = []
    for method, cover in zip(
        predictions.METHODS, ([0.5, 0.5], [1.0, 0.0], [0.8, 0.2]), strict=True
    ):
        # Independent equation: local=(2.5*c0,4.5*c1), regional=(.4,.45).
        masses = [0.4 + 2.5 * cover[0], 0.45 + 4.5 * cover[1]]
        references.append(
            {
                "case_id": case["case_id"],
                "method": method,
                "vegetation_fraction": list(cover),
                "pollen_fraction": [value / sum(masses) for value in masses],
                "regional_cover": [0.4, 0.6],
                "prediction_manifest_sha256": "d" * 64,
            }
        )
    nominal = {
        "local_covers_by_ring": [[[-1.0, 2.0], [0.0, 1.0]], [[None, None], [1.0, 0.0]]],
        "regional_cover": [0.4, 0.6],
        "ppe": [2.0, 3.0],
        "reference_predictions": references,
    }
    pin = {"path": "source/member.json", "bytes": 1, "sha256": "a" * 64}
    refs = {
        "allowed_inputs": deepcopy(allowed),
        "nominal_fits": [
            {
                "owner_id": owner,
                "native_manifest": dict(pin),
                "request": dict(pin),
                "cover_csv": dict(pin),
                "regional_csv": dict(pin),
            }
            for owner in ("local-far", "local-near")
        ],
    }
    result = {
        "case": case,
        "cached_fit": cached,
        "ppe_samples": ppe,
        "nominal": nominal,
        "scientific_refs": refs,
    }
    bind(result)
    return result


def test_nominal_handoff_compares_all_three_saved_point_methods() -> None:
    source = candidate()
    before = deepcopy(source)
    facts = predictions.check_nominal_handoff(source)
    assert facts["passed"] is True
    assert (
        facts["cover_comparisons"]
        == facts["pollen_comparisons"]
        == facts["forward_calls"]
        == 3
    )
    assert facts["absolute_tolerance"] == 1e-12
    assert facts["maximum_cover_absolute_error"] < 1e-15
    assert facts["maximum_pollen_absolute_error"] < 1e-15
    assert facts["failures"] == []
    assert source == before


@pytest.mark.parametrize(
    "change", ["reference_cover", "reference_pollen", "wrong_local_k"]
)
def test_nominal_handoff_retains_every_mismatch(change: str) -> None:
    source = candidate()
    if change.startswith("reference"):
        field = (
            "vegetation_fraction" if change == "reference_cover" else "pollen_fraction"
        )
        for row in source["nominal"]["reference_predictions"]:
            row[field] = [0.1, 0.9]
    else:
        source["case"]["forward_local_k"][0][0] *= 2
        bind(source)
    facts = predictions.check_nominal_handoff(source)
    assert facts["passed"] is False
    assert facts["forward_calls"] == facts["pollen_comparisons"] == 3
    assert len(facts["failures"]) == 3


@pytest.mark.parametrize("scale", [20.0, 100.0])
def test_known_gaussian_hellinger_and_forward_ppe_once(scale: float) -> None:
    source = candidate()
    row = predictions.predict_candidate(source, length_scale_km=scale)
    ratio = math.exp(-(40**2 - 20**2) / (2 * scale**2))
    far, near = ratio / (1 + ratio), 1 / (1 + ratio)
    expected_cover = [near**2 / (far**2 + near**2), far**2 / (far**2 + near**2)]
    assert row["weights"] == pytest.approx(
        {"local-far": far, "local-near": near}, abs=1e-15
    )
    assert row["nominal"]["cover"] == pytest.approx(expected_cover, abs=1e-15)
    assert row["ensemble"]["cover"][0] == pytest.approx(expected_cover, abs=1e-15)
    masses = [0.4 + 2.5 * expected_cover[0], 0.45 + 4.5 * expected_cover[1]]
    assert row["ensemble"]["pollen"][0] == pytest.approx(
        [value / sum(masses) for value in masses], abs=1e-15
    )
    wrong = [0.8 + 2.5 * expected_cover[0], 1.35 + 4.5 * expected_cover[1]]
    assert row["ensemble"]["pollen"][0] != pytest.approx(
        [value / sum(wrong) for value in wrong], abs=1e-6
    )
    assert row["selection_status"] == "unselected_fixed_sensitivity"


def test_exact_orthogonal_mean_is_not_an_arithmetic_mean() -> None:
    source = candidate()
    result = predictions._spatial(
        [[1.0, 0.0], [0.0, 1.0]],
        [0.4, 0.6],
        [2.0, 3.0],
        source["case"],
        ["local-far", "local-near"],
        {"local-far": 0.25, "local-near": 0.75},
    )
    assert result["status"] == "predicted"
    assert result["cover"] == pytest.approx([0.1, 0.9], abs=1e-15)
    assert result["cover"] != [0.25, 0.75]


def test_inherited_undefined_rows_are_never_rescued() -> None:
    source = candidate()
    before = deepcopy(source)
    row = predictions.predict_candidate(source, length_scale_km=20.0)
    ensemble = row["ensemble"]
    assert ensemble["source_valid_mask"] == [True, True, True, False]
    assert ensemble["valid_mask"] == ensemble["source_valid_mask"]
    assert ensemble["cover"][-1] == ensemble["pollen"][-1] == [None, None]
    assert ensemble["refusals"][-1] == {
        "kind": "inherited_source_undefined",
        "regional_refusal": None,
        "local_refusals": ["local_selected_cover_out_of_bounds", None],
        "method_refusals": dict.fromkeys(
            predictions.METHODS, "required_local_predictor_undefined"
        ),
    }
    assert ensemble["inherited_undefined_replicates"] == 1
    assert ensemble["additional_refusals"] == 0
    assert row["pollen_summary"]["unconditional_status"] == "refused_undefined_mass"
    assert source == before


def test_full_source_population_is_derived_not_forced() -> None:
    source = candidate(replicates=1024, defined=860)
    row = predictions.predict_candidate(source, length_scale_km=100.0)
    assert row["replicates"] == 1024
    assert (
        row["ensemble"]["source_defined_replicates"]
        == sum(row["ensemble"]["valid_mask"])
        == 860
    )
    assert row["ensemble"]["inherited_undefined_replicates"] == 164
    assert row["pollen_summary"]["undefined_mass"] == 164 / 1024
    assert (
        predictions.predict_candidate(candidate(defined=2), length_scale_km=100.0)[
            "ensemble"
        ]["source_defined_replicates"]
        == 2
    )


def test_ring_zero_and_unrelated_data_do_not_enter_prediction_or_digest() -> None:
    source = candidate()
    expected = predictions.predict_candidate(source, length_scale_km=20.0)
    for row in source["cached_fit"]["local_signed_cover"]:
        row[0][0], row[1][0] = [None, None], [-200.0, 201.0]
    for row in source["cached_fit"]["local_ring_refusals"]:
        row[0][0], row[1][0] = "local_engine_nonfinite", None
    source["nominal"]["local_covers_by_ring"][0][0] = [-1000.0, 1001.0]
    source["held_labels"] = [10**9, 0]
    source["unrelated_bank"] = {"held-out": [0, 10**9], "sha256": "f" * 64}
    source["cached_fit"]["methods"]["nearest_site"]["pollen"] = [[0.0, 1.0]] * 4
    assert predictions.predict_candidate(source, length_scale_km=20.0) == expected


@pytest.mark.parametrize(
    "mutation",
    [
        "mask_disagreement",
        "mask_type",
        "ppe_identity",
        "case_owner",
        "extra_count_owner",
        "global_reference",
        "selected_refusal",
        "missing_draw",
        "case_header",
        "schema_header",
    ],
)
def test_inconsistent_source_metadata_is_not_a_new_numerical_refusal(
    mutation: str,
) -> None:
    source = candidate()
    if mutation == "mask_disagreement":
        source["cached_fit"]["methods"]["nearest_site"]["valid_mask"][0] = False
        source["cached_fit"]["methods"]["nearest_site"]["refusals"][0] = (
            "source_refused"
        )
    elif mutation == "mask_type":
        source["cached_fit"]["methods"]["nearest_site"]["valid_mask"][0] = 1
    elif mutation == "ppe_identity":
        source["ppe_samples"][0][0] += 0.1
    elif mutation == "case_owner":
        source["case"]["local_owners"][0]["owner_id"] = source["case"]["target_id"]
    elif mutation == "extra_count_owner":
        source["scientific_refs"]["allowed_inputs"]["count_owners"].append(
            {"owner_id": "held-out"}
        )
    elif mutation == "global_reference":
        source["scientific_refs"]["whole_bank_sha256"] = "a" * 64
    elif mutation == "selected_refusal":
        source["cached_fit"]["local_ring_refusals"][0][0][1] = "local_engine_refused"
    elif mutation == "missing_draw":
        source["cached_fit"]["local_signed_cover"].pop()
    elif mutation == "case_header":
        source["case"]["case_id"] = 1
    else:
        source["cached_fit"]["schema_version"] = "foreign"
    with pytest.raises(ValueError):
        predictions.predict_candidate(source, length_scale_km=20.0)


def test_additional_weight_refusals_do_not_rescue_source_undefined() -> None:
    source = candidate()
    source["case"]["distances_km"] = [0.0, 1e308]
    bind(source)
    row = predictions.predict_candidate(source, length_scale_km=20.0)
    assert row["weights"] is None
    assert row["nominal"]["status"] == "refused"
    assert row["ensemble"]["additional_refusals"] == 3
    assert row["ensemble"]["valid_mask"] == [False] * 4
    assert row["ensemble"]["refusals"][0]["reason"] == "hellinger_weight_underflow"
    assert row["ensemble"]["refusals"][-1]["kind"] == "inherited_source_undefined"
    assert (
        row["pollen_summary"]["conditional"]["status"]
        == "unavailable_no_defined_replicates"
    )


def test_supported_component_underflow_is_an_additional_refusal() -> None:
    source = candidate()
    source["cached_fit"]["local_signed_cover"][0][0][1] = [1.0, 5e-324]
    source["cached_fit"]["local_signed_cover"][0][1][1] = [1.0, 0.0]
    row = predictions.predict_candidate(source, length_scale_km=20.0)
    assert row["ensemble"]["additional_refusals"] == 1
    assert row["ensemble"]["valid_mask"] == [False, True, True, False]
    assert row["ensemble"]["refusals"][0]["reason"] == "hellinger_composition_underflow"


def test_native_forward_domain_refusals_remain_typed() -> None:
    source = candidate()
    source["case"]["forward_local_k"] = [[0.0, 0.0], [0.0, 0.0]]
    source["case"]["forward_regional_k"] = [0.0, 0.0]
    bind(source)
    assert predictions.check_nominal_handoff(source)["passed"] is False
    row = predictions.predict_candidate(source, length_scale_km=100.0)
    assert row["nominal"]["refusal"]["reason"] == "forward_engine_refused"
    assert row["ensemble"]["additional_refusals"] == 3
    assert all(
        item["reason"] == "forward_engine_refused"
        for item in row["ensemble"]["refusals"][:3]
    )


def test_shared_zero_and_known_conditional_moments() -> None:
    source = candidate(replicates=3, defined=2)
    for i, value in enumerate(([1.0, 0.0], [0.0, 1.0])):
        for local in source["cached_fit"]["local_signed_cover"][i]:
            local[1] = list(value)
        source["cached_fit"]["regional_cover"][i] = list(value)
    row = predictions.predict_candidate(source, length_scale_km=100.0)
    assert (
        row["ensemble"]["cover"]
        == row["ensemble"]["pollen"]
        == [[1.0, 0.0], [0.0, 1.0], [None, None]]
    )
    summary = row["cover_summary"]
    assert summary["undefined_replicates"] == 1
    assert summary["unconditional_status"] == "refused_undefined_mass"
    conditional = summary["conditional"]
    assert conditional["mean"] == [0.5, 0.5]
    assert conditional["covariance"] == [[0.25, -0.25], [-0.25, 0.25]]
    assert conditional["mean_mcse"] == [0.5, 0.5]
    assert conditional["empirical_quantiles"]["0.5"] == [0.5, 0.5]


def test_joint_owner_permutation_preserves_numerical_predictions() -> None:
    source = candidate()
    original = predictions.predict_candidate(source, length_scale_km=20.0)
    source["case"]["local_owners"].reverse()
    source["case"]["distances_km"].reverse()
    source["nominal"]["local_covers_by_ring"].reverse()
    source["scientific_refs"]["nominal_fits"].reverse()
    for field in ("local_signed_cover", "local_refusals", "local_ring_refusals"):
        for row in source["cached_fit"][field]:
            row.reverse()
    allowed = source["cached_fit"]["allowed_inputs"]
    allowed["count_owners"][1:] = reversed(allowed["count_owners"][1:])
    bind(source)
    changed = predictions.predict_candidate(source, length_scale_km=20.0)
    assert changed["weights"] == original["weights"]
    for field in ("cover", "pollen", "valid_mask", "source_valid_mask"):
        assert changed["ensemble"][field] == original["ensemble"][field]
    assert changed["pollen_summary"] == original["pollen_summary"]
    assert changed["ensemble"]["refusals"][-1]["local_refusals"] == list(
        reversed(original["ensemble"]["refusals"][-1]["local_refusals"])
    )


def test_joint_taxon_value_permutation_preserves_forward_algebra() -> None:
    source = candidate()
    original = predictions.predict_candidate(source, length_scale_km=100.0)
    source["case"]["regional_deposition"].reverse()
    source["case"]["forward_regional_k"].reverse()
    for row in source["case"]["forward_local_k"]:
        row.reverse()
    for local in source["case"]["local_owners"]:
        for field in ("local_k", "regional_k"):
            for row in local[field]:
                row.reverse()
    for rows in source["nominal"]["local_covers_by_ring"]:
        for row in rows:
            row.reverse()
    source["nominal"]["regional_cover"].reverse()
    source["nominal"]["ppe"].reverse()
    for row in source["nominal"]["reference_predictions"]:
        for field in ("regional_cover", "vegetation_fraction", "pollen_fraction"):
            row[field].reverse()
    for row in source["cached_fit"]["regional_cover"]:
        row.reverse()
    for row in source["cached_fit"]["local_signed_cover"]:
        for local in row:
            for ring in local:
                ring.reverse()
    for row in source["ppe_samples"]:
        row.reverse()
    for field in ("means", "sds"):
        source["cached_fit"]["allowed_inputs"]["ppe"][field].reverse()
    for row in source["cached_fit"]["allowed_inputs"]["count_owners"]:
        row["counts"].reverse()
    bind(source)
    assert predictions.check_nominal_handoff(source)["passed"] is True
    changed = predictions.predict_candidate(source, length_scale_km=100.0)
    assert changed["ensemble"]["valid_mask"] == original["ensemble"]["valid_mask"]
    for field in ("cover", "pollen"):
        for left, right in zip(
            changed["ensemble"][field], original["ensemble"][field], strict=True
        ):
            if right[0] is None:
                assert left == [None, None]
            else:
                assert left == pytest.approx(list(reversed(right)), abs=1e-15)


def test_single_replicate_keeps_mcse_unavailable() -> None:
    row = predictions.predict_candidate(
        candidate(replicates=1, defined=1), length_scale_km=20.0
    )
    assert row["ensemble"]["source_defined_replicates"] == 1
    assert row["pollen_summary"]["unconditional_status"] == "defined"
    assert row["pollen_summary"]["conditional"]["mean_mcse"] is None
    assert (
        row["pollen_summary"]["conditional"]["mean_mcse_status"]
        == "unavailable_fewer_than_two_defined"
    )


def test_no_fit_kernel_or_random_generator_is_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty import (
        draws,
    )
    from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.predictive_uncertainty import (
        predictions as original,
    )

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Cached-fit projection cannot refit or regenerate draws")

    for name in ("REVEALS", "lov", "predict_case"):
        monkeypatch.setattr(original, name, forbidden)
    monkeypatch.setattr(draws, "generate_draw_bank", forbidden)
    source = candidate()
    assert predictions.check_nominal_handoff(source)["passed"] is True
    assert (
        predictions.predict_candidate(source, length_scale_km=20.0)["ensemble"][
            "source_defined_replicates"
        ]
        == 3
    )


def test_profiles_are_fixed_unselected_and_not_point_aliases() -> None:
    source = candidate()
    first = predictions.predict_candidate(source, length_scale_km=20.0)
    second = predictions.predict_candidate(source, length_scale_km=100.0)
    assert first["weights"] != second["weights"]
    assert first["scientific_input_sha256"] != second["scientific_input_sha256"]
    assert (
        first["nominal"]["cover"]
        != source["nominal"]["reference_predictions"][0]["vegetation_fraction"]
    )
    assert (
        first["ensemble"]["source_valid_mask"]
        == second["ensemble"]["source_valid_mask"]
    )
    with pytest.raises(ValueError, match="unselected fixed"):
        predictions.predict_candidate(source, length_scale_km=50.0)
