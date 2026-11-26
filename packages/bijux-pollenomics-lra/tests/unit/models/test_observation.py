"""Observation result identity and returned-data mutation isolation."""

from dataclasses import replace

import pytest

from bijux_pollenomics_lra import ValidationError, sample_pollen_observations


def test_stale_result_bytes_and_hash_refuse() -> None:
    result = sample_pollen_observations(
        {"a": 1.0},
        effort=10,
        repeats=2,
        seed=0,
        coverage=0.9,
        prediction_sha256="a" * 64,
        effort_evidence_sha256="b" * 64,
    )
    with pytest.raises(ValidationError):
        replace(result, result_sha256="0" * 64)
    with pytest.raises(ValidationError):
        replace(
            result,
            canonical_result_json=result.canonical_result_json.replace(
                '"effort":10', '"effort":11'
            ),
        )
    output = result.as_dict()
    output["counts"][0][0] = 0
    assert result.as_dict()["counts"] == [[10], [10]]


@pytest.mark.parametrize(
    "kind",
    ["empty", "draw_count", "negative", "effort", "missing_taxon", "claimed_coverage"],
)
def test_rehashed_incomplete_or_incompatible_result_refuses(kind: str) -> None:
    from bijux_pollenomics_lra import PollenObservationDraws
    from bijux_pollenomics_lra.provenance.identity import canonical_json, sha256_object

    payload = sample_pollen_observations(
        {"a": 1.0},
        effort=10,
        repeats=2,
        seed=0,
        coverage=0.9,
        prediction_sha256="a" * 64,
        effort_evidence_sha256="b" * 64,
    ).as_dict()
    if kind == "empty":
        payload = {
            "schema_version": payload["schema_version"],
            "profile": payload["profile"],
        }
    elif kind == "draw_count":
        payload["counts"].pop()
    elif kind == "negative":
        payload["counts"][0][0] = -1
    elif kind == "effort":
        payload["counts"][0][0] = 11
    elif kind == "missing_taxon":
        payload["marginal_predictive_intervals"] = {}
    else:
        payload["empirical_coverage_verified"] = True
    with pytest.raises(ValidationError):
        PollenObservationDraws(canonical_json(payload), sha256_object(payload))


@pytest.mark.parametrize(
    "kind", ["boolean_fraction", "closure", "rng", "note", "version", "boundary_bool"]
)
def test_rehashed_profile_and_field_types_refuse(kind: str) -> None:
    from bijux_pollenomics_lra import PollenObservationDraws
    from bijux_pollenomics_lra.provenance.identity import canonical_json, sha256_object

    payload = sample_pollen_observations(
        {"a": 0.0, "b": 1.0},
        effort=10,
        repeats=2,
        seed=0,
        coverage=0.9,
        prediction_sha256="a" * 64,
        effort_evidence_sha256="b" * 64,
    ).as_dict()
    if kind == "boolean_fraction":
        payload["marginal_predictive_intervals"]["a"]["lower_fraction"] = False
    elif kind == "closure":
        payload["declaration"]["closure_profile"] = "unreviewed-closure"
    elif kind == "rng":
        payload["declaration"]["rng"] = "unknown-generator"
    elif kind == "note":
        payload["sampling_probability_note"] = {"unexpected": True}
    elif kind == "boundary_bool":
        payload["numerical_boundary_separation"] = False
    else:
        payload["declaration"]["engine_version"] = {"unexpected": True}
    identity = sha256_object(payload["declaration"])
    payload["declaration_sha256"] = identity
    payload["draw_ids"] = [f"{identity}:{i}" for i in range(2)]
    with pytest.raises(ValidationError):
        PollenObservationDraws(canonical_json(payload), sha256_object(payload))


@pytest.mark.parametrize("kind", ["impossible_count", "effective_probability"])
def test_rehashed_declared_probability_contradictions_refuse(kind: str) -> None:
    from bijux_pollenomics_lra import PollenObservationDraws
    from bijux_pollenomics_lra.provenance.identity import canonical_json, sha256_object

    payload = sample_pollen_observations(
        {"a": 0.0, "b": 1.0},
        effort=7,
        repeats=2,
        seed=0,
        coverage=0.9,
        prediction_sha256="a" * 64,
        effort_evidence_sha256="b" * 64,
    ).as_dict()
    if kind == "impossible_count":
        payload["counts"][0] = [1, 6]
    else:
        payload["declaration"]["effective_pollen_fraction"] = {"a": 0.5, "b": 0.5}
    identity = sha256_object(payload["declaration"])
    payload["declaration_sha256"] = identity
    payload["draw_ids"] = [f"{identity}:{i}" for i in range(2)]
    with pytest.raises(ValidationError):
        PollenObservationDraws(canonical_json(payload), sha256_object(payload))


@pytest.mark.parametrize(
    "probability,effort", [(0.0, 7), (1.0, 7), (0.5, 7), (0.5, 300)]
)
def test_rehashed_wrong_equal_tail_interval_refuses(
    probability: float, effort: int
) -> None:
    from bijux_pollenomics_lra import PollenObservationDraws
    from bijux_pollenomics_lra.provenance.identity import canonical_json, sha256_object

    payload = sample_pollen_observations(
        {"a": probability, "b": 1 - probability},
        effort=effort,
        repeats=2,
        seed=0,
        coverage=0.9,
        prediction_sha256="a" * 64,
        effort_evidence_sha256="b" * 64,
    ).as_dict()
    bounds = payload["marginal_predictive_intervals"]["a"]
    bounds.update(
        lower_count=0, upper_count=effort, lower_fraction=0.0, upper_fraction=1.0
    )
    with pytest.raises(ValidationError):
        PollenObservationDraws(
            canonical_json(payload), sha256_object(payload)
        ).validate_predictive_intervals()


def test_large_support_refuses_unavailable_recorded_scipy_version() -> None:
    from bijux_pollenomics_lra import PollenObservationDraws
    from bijux_pollenomics_lra.provenance.identity import canonical_json, sha256_object

    payload = sample_pollen_observations(
        {"a": 0.5, "b": 0.5},
        effort=300,
        repeats=2,
        seed=0,
        coverage=0.9,
        prediction_sha256="a" * 64,
        effort_evidence_sha256="b" * 64,
    ).as_dict()
    payload["declaration"]["scipy_version"] = "0.0-unavailable"
    identity = sha256_object(payload["declaration"])
    payload["declaration_sha256"] = identity
    payload["draw_ids"] = [f"{identity}:{i}" for i in range(2)]
    with pytest.raises(ValidationError):
        PollenObservationDraws(
            canonical_json(payload), sha256_object(payload)
        ).validate_predictive_intervals()


def test_small_support_exact_threshold_matches_independent_cdf_at_ties() -> None:
    from fractions import Fraction

    import numpy as np

    from bijux_pollenomics_lra.models.observation_intervals import _exact_cdf_at_least
    from bijux_pollenomics_lra.workflows.observation import _exact_cdf

    for n in (1, 2, 7, 12):
        for p in (0.0, 0.125, 0.5, 0.875, 1.0, 5e-324):
            for k in range(-1, n + 1):
                cdf = _exact_cdf(k, n, p)
                tie = float(cdf)
                for q in (
                    0.0,
                    np.nextafter(tie, 0.0),
                    tie,
                    np.nextafter(tie, 1.0),
                    1.0,
                ):
                    q = float(q)
                    assert _exact_cdf_at_least(k, n, p, q) == (
                        cdf >= Fraction.from_float(q)
                    )


def test_small_support_does_not_require_recorded_scipy_version() -> None:
    from bijux_pollenomics_lra import PollenObservationDraws
    from bijux_pollenomics_lra.provenance.identity import canonical_json, sha256_object

    payload = sample_pollen_observations(
        {"a": 0.5, "b": 0.5},
        effort=7,
        repeats=2,
        seed=0,
        coverage=0.9,
        prediction_sha256="a" * 64,
        effort_evidence_sha256="b" * 64,
    ).as_dict()
    payload["declaration"]["scipy_version"] = "0.0-unavailable"
    identity = sha256_object(payload["declaration"])
    payload["declaration_sha256"] = identity
    payload["draw_ids"] = [f"{identity}:{i}" for i in range(2)]
    saved = PollenObservationDraws(canonical_json(payload), sha256_object(payload))
    saved.validate_predictive_intervals()
    assert saved.as_dict() == payload


def test_large_support_degenerate_does_not_need_scipy_replay() -> None:
    from bijux_pollenomics_lra import PollenObservationDraws
    from bijux_pollenomics_lra.provenance.identity import canonical_json, sha256_object

    payload = sample_pollen_observations(
        {"a": 0.0, "b": 1.0},
        effort=300,
        repeats=2,
        seed=0,
        coverage=0.9,
        prediction_sha256="a" * 64,
        effort_evidence_sha256="b" * 64,
    ).as_dict()
    payload["declaration"]["scipy_version"] = "0.0-unavailable"
    identity = sha256_object(payload["declaration"])
    payload["declaration_sha256"] = identity
    payload["draw_ids"] = [f"{identity}:{i}" for i in range(2)]
    saved = PollenObservationDraws(canonical_json(payload), sha256_object(payload))
    saved.validate_predictive_intervals()


def test_small_support_threshold_matches_random_exact_cdf() -> None:
    from fractions import Fraction

    import numpy as np

    from bijux_pollenomics_lra.models.observation_intervals import _exact_cdf_at_least
    from bijux_pollenomics_lra.workflows.observation import _exact_cdf

    generator = np.random.default_rng(71)
    for _ in range(100):
        n = int(generator.integers(1, 50))
        k = int(generator.integers(-1, n + 1))
        p = float(generator.random())
        q = float(generator.random())
        assert _exact_cdf_at_least(k, n, p, q) == (
            _exact_cdf(k, n, p) >= Fraction.from_float(q)
        )
