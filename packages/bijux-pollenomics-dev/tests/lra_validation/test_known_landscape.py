"""Challenge the independent known-landscape generator and its claim boundary."""

from __future__ import annotations

import hashlib
import inspect
import json
import sys
from typing import cast

import pytest

from bijux_pollenomics_dev.lra_validation import (
    KNOWN_LANDSCAPE_PROFILE,
    KnownLandscapeError,
    build_known_landscape_report,
)
import bijux_pollenomics_dev.lra_validation.known_landscape as oracle

JsonObject = dict[str, object]


def _object(value: object) -> JsonObject:
    assert isinstance(value, dict)
    return cast(JsonObject, value)


def _cases(payload: JsonObject) -> dict[str, JsonObject]:
    values = cast(list[JsonObject], payload["cases"])
    return {cast(str, value["case_id"]): value for value in values}


@pytest.fixture(scope="module")
def payload() -> JsonObject:
    return build_known_landscape_report().payload()


def test_generator_is_deterministic_canonical_and_defensively_copied() -> None:
    first = build_known_landscape_report()
    second = build_known_landscape_report()
    assert first.canonical_bytes == second.canonical_bytes
    assert first.sha256 == hashlib.sha256(first.canonical_bytes).hexdigest()
    assert first.sha256 == second.sha256
    assert (
        first.canonical_bytes
        == json.dumps(
            first.payload(),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
    )
    changed = first.payload()
    changed["profile"] = "mutated"
    assert first.payload()["profile"] == KNOWN_LANDSCAPE_PROFILE


def test_oracle_has_no_production_forward_or_inverse_dependency(
    payload: JsonObject,
) -> None:
    source = inspect.getsource(oracle)
    assert "bijux_pollenomics_lra" not in source
    assert "bijux_pollenomics.analysis.lra" not in source
    simulator = _object(payload["simulator"])
    assert simulator["production_forward_imported"] is False
    assert simulator["production_inverse_imported"] is False
    assert simulator["cell_weight"] == ("area_m2 / (distance_m + basin_radius_m)^2")


def test_noise_free_homogeneous_and_heterogeneous_recovery_is_exact(
    payload: JsonObject,
) -> None:
    cases = _cases(payload)
    for case_id, kind in (
        ("homogeneous-noise-free", "homogeneous"),
        ("heterogeneous-noise-free", "heterogeneous"),
    ):
        case = cases[case_id]
        assert (case["status"], case["landscape_kind"]) == ("success", kind)
        assert case["cell_count"] == 9
        assert cast(float, case["vegetation_mae_fraction"]) <= 1e-15
        assert cast(
            dict[str, float], case["true_support_vegetation_fraction"]
        ) == pytest.approx(
            cast(dict[str, float], case["recovered_vegetation_fraction"]),
            abs=1e-15,
        )
    heterogeneous = cases["heterogeneous-noise-free"]
    rows = cast(list[JsonObject], heterogeneous["cells"])
    compositions = {
        tuple(cast(dict[str, float], row["vegetation_fraction"]).values())
        for row in rows
    }
    assert len(compositions) > 1


def test_noisy_and_sparse_cases_report_observation_coverage_denominators(
    payload: JsonObject,
) -> None:
    cases = _cases(payload)
    noisy = cases["heterogeneous-noisy"]
    sparse = cases["sparse-counts"]
    for case, effort in ((noisy, 200), (sparse, 12)):
        assert case["status"] == "success"
        assert case["counting_effort"] == effort
        assert case["requested_draws"] == 128
        assert case["generated_draws"] == 128
        assert case["refused_draws"] == 0
        assert case["coverage_denominator"] == 384
        assert 0.75 <= cast(float, case["coverage_fraction"]) <= 1.0
        rows = cast(list[JsonObject], case["draws"])
        assert len(rows) == 128
        assert all(
            sum(cast(dict[str, int], row["counts"]).values()) == effort for row in rows
        )
    assert cast(float, sparse["mean_interval_width_fraction"]) > cast(
        float, noisy["mean_interval_width_fraction"]
    )
    assert cast(float, sparse["mean_vegetation_mae_fraction"]) > cast(
        float, noisy["mean_vegetation_mae_fraction"]
    )


def test_ppe_and_fall_speed_misspecification_degrade_recovery(
    payload: JsonObject,
) -> None:
    cases = _cases(payload)
    reference = cast(
        float,
        cases["heterogeneous-noise-free"]["vegetation_mae_fraction"],
    )
    for case_id in ("misspecified-ppe", "misspecified-fall-speed"):
        case = cases[case_id]
        assert case["status"] == "success"
        assert case["expected_disposition"] == "expected_degradation"
        assert cast(float, case["vegetation_mae_fraction"]) > reference + 0.02


def test_missing_dominant_taxon_and_incomplete_support_refuse_explicitly(
    payload: JsonObject,
) -> None:
    cases = _cases(payload)
    missing = cases["missing-dominant-taxon"]
    assert missing["status"] == "refused"
    assert missing["requested_draws"] == 1
    assert missing["generated_draws"] == 0
    assert missing["refused_draws"] == 1
    row = cast(list[JsonObject], missing["draws"])[0]
    assert row["reason_code"] == "missing_dominant_taxon"
    assert None in cast(dict[str, int | None], row["counts"]).values()

    support = cases["incomplete-spatial-support"]
    assert support["status"] == "refused"
    assert support["reason_code"] == "incomplete_spatial_support"
    assert support["expected_disposition"] == "expected_refusal"


def test_variable_support_is_retained_and_changes_the_target(
    payload: JsonObject,
) -> None:
    cases = _cases(payload)
    narrow = cases["variable-support-narrow"]
    wide = cases["variable-support-wide"]
    assert (narrow["declared_support_m"], wide["declared_support_m"]) == (
        2_500.0,
        12_000.0,
    )
    assert (
        narrow["true_support_vegetation_fraction"]
        != wide["true_support_vegetation_fraction"]
    )
    assert narrow["expected_pollen_fraction"] != wide["expected_pollen_fraction"]


def test_denominators_and_nonclaims_are_complete(payload: JsonObject) -> None:
    denominators = _object(payload["denominators"])
    assert denominators == {
        "requested_cases": 10,
        "successful_cases": 8,
        "refused_cases": 2,
        "requested_noisy_draws": 257,
        "generated_noisy_draws": 256,
        "refused_noisy_draws": 1,
    }
    claims = _object(payload["claims"])
    assert claims == {
        "independent_synthetic_forward_generator": True,
        "production_lra_recovery_validated": False,
        "real_observations_used": False,
        "empirical_ecological_accuracy": False,
        "predictive_intervals_calibrated_for_real_data": False,
        "reviewed_acceptance_thresholds_supplied": False,
        "scientifically_approved": False,
        "scientific_acceptance": "not_evaluated",
    }


@pytest.mark.parametrize("seed", [-1, 1 << 64, True])
def test_invalid_seed_refuses(seed: int) -> None:
    with pytest.raises(KnownLandscapeError) as error:
        build_known_landscape_report(seed=seed)
    assert error.value.reason_code == "invalid_seed"


def test_seed_changes_only_stochastic_draws() -> None:
    first = _cases(build_known_landscape_report(seed=1).payload())
    second = _cases(build_known_landscape_report(seed=2).payload())
    assert first["heterogeneous-noise-free"] == second["heterogeneous-noise-free"]
    assert (
        first["heterogeneous-noisy"]["draws"] != second["heterogeneous-noisy"]["draws"]
    )


def test_transport_matched_profile_is_separate_and_preserves_original_bytes() -> None:
    # Python 3.11's float summation differs at the last bit from 3.12+.
    # Keep exact report pins for both interpreter profiles; neither changes
    # any counts, statuses or nonnumeric case fields.
    expected_sha256 = (
        "1bd4997dfe82490a05182ca2f211f8496a1c68312f8449ee39a5f140958ad551"
        if sys.version_info < (3, 12)
        else "c53291b9be045fef04334533a8a7f40f8811d7f49c809745522409db8b94aff8"
    )
    assert build_known_landscape_report().sha256 == expected_sha256
    first = oracle.build_transport_matched_report()
    assert (
        first.canonical_bytes == oracle.build_transport_matched_report().canonical_bytes
    )
    payload = first.payload()
    assert payload["profile"] == oracle.TRANSPORT_MATCHED_PROFILE
    assert payload["profile"] != KNOWN_LANDSCAPE_PROFILE
    assert payload["denominators"] == {
        "requested_cases": 2,
        "successful_cases": 2,
        "refused_cases": 0,
    }
    claims = _object(payload["claims"])
    assert claims["inverse_crime_control"] is True
    assert claims["empirical_ecological_accuracy"] is False
    assert claims["empirical_ppe_estimated"] is False
    assert claims["held_out_accuracy"] is False
    assert "bijux_pollenomics_lra" not in inspect.getsource(oracle)


def test_transport_matched_cases_exclude_inner_basin_and_recover_analytic_cover() -> (
    None
):
    cases = cast(
        list[JsonObject], oracle.build_transport_matched_report().payload()["cases"]
    )
    assert len(cases) == 2
    for case in cases:
        edges = cast(list[int], case["annulus_edges_m"])
        assert edges[0] == case["basin_diameter_m"]
        assert edges[-1] == case["region_cutoff_m"]
        assert edges == sorted(set(edges))
        factors = cast(dict[str, float], case["independent_deposition_factor"])
        assert all(factor > 0 for factor in factors.values())
        assert cast(float, case["analytical_true_ppe_mae_fraction"]) < 1e-15
        pollen = cast(dict[str, float], case["expected_pollen_fraction"])
        truth = cast(dict[str, float], case["true_support_vegetation_fraction"])
        misspecified = {
            taxon: pollen[taxon] / (factors[taxon] * ppe)
            for taxon, ppe in (
                ("broadleaf", 1.92),
                ("conifer", 1.2),
                ("open_land", 0.8),
            )
        }
        mass = sum(misspecified.values())
        wrong_mae = (
            sum(abs(misspecified[taxon] / mass - truth[taxon]) for taxon in truth) / 3
        )
        assert wrong_mae > 0.02
