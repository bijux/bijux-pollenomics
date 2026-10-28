"""Shared native sample support and conditional multinomial derivative contracts."""

from dataclasses import replace
from typing import cast
import warnings

import numpy as np
import pytest

from bijux_pollenomics_lra import api
from bijux_pollenomics_lra.models.errors import ValidationError

AXIS = ("Betula", "Poaceae")


def sample(
    key: str = "a", *, counts: tuple[int, int] = (30, 70), sid: int = 1
) -> api.AliquotCountInput:
    return api.AliquotCountInput(
        key, 1, 2, sid, "a" * 64, AXIS, np.array(counts), np.ones(2, dtype=bool)
    )


def result(
    key: str = "x",
    members: tuple[str, ...] = ("a",),
    k: tuple[float, float] = (1.0, 1.0),
) -> api.AliquotResultInput:
    return api.AliquotResultInput(key, members, AXIS, np.array(k))


def evaluate(
    observations: tuple[api.AliquotCountInput, ...],
    results: tuple[api.AliquotResultInput, ...],
    *,
    independent: bool = True,
    count_ppe: bool = True,
) -> api.JointAliquotCovariance:
    return api.joint_aliquot_covariance(
        observations,
        results,
        parameter_ids=AXIS,
        ppe=np.array([1.4, 2.3]),
        ppe_covariance=np.diag([0.01, 0.04]),
        assume_distinct_aliquot_count_independence=independent,
        assume_count_ppe_independence=count_ppe,
    )


def test_reused_sample_identical_response_zero_contrast() -> None:
    out = evaluate((sample(),), (result(), result("y")))
    D = np.concatenate([-np.eye(2), np.eye(2)], axis=1)
    np.testing.assert_allclose(D @ out.total_covariance @ D.T, 0, atol=1e-18)
    assert out.distinct_count_observations == 1
    assert not out.cover.flags.writeable
    assert not out.total_covariance.flags.writeable


def test_shared_sample_with_different_factor_is_not_forced_to_zero() -> None:
    out = evaluate((sample(),), (result(), result("y", k=(2.0, 0.5))))
    assert abs(out.cover[0] - out.cover[2]) > 0.1
    D = np.concatenate([-np.eye(2), np.eye(2)], axis=1)
    assert (D @ out.total_covariance @ D.T)[0, 0] > 0


def test_disjoint_samples_share_ppe_only() -> None:
    out = evaluate((sample(), sample("b", sid=2)), (result(), result("y", ("b",))))
    np.testing.assert_array_equal(out.counting_covariance[:2, 2:], 0)
    assert out.ppe_covariance[0, 2] > 0


def test_one_aliquot_matches_existing_public_pooled_api() -> None:
    out = evaluate((sample(),), (result(),))
    old = api.joint_fixed_site_covariance(
        (
            api.ConditionalResultInput(
                "x",
                api.CountSupport(1, 2, 3, 0, 100, "a" * 64),
                AXIS,
                np.array([30, 70]),
                np.ones(2),
                np.ones(2, dtype=bool),
            ),
        ),
        parameter_ids=AXIS,
        ppe=np.array([1.4, 2.3]),
        ppe_covariance=np.diag([0.01, 0.04]),
        assume_disjoint_window_count_independence=False,
        assume_distinct_unit_count_independence=False,
    )
    for a, b in [
        (out.cover, old.cover),
        (out.counting_covariance, old.counting_covariance),
        (out.ppe_covariance, old.ppe_covariance),
        (out.count_jacobian, old.count_jacobian),
    ]:
        np.testing.assert_allclose(a, b, rtol=1e-13, atol=1e-18)


def test_quotient_derivatives_independent_finite_difference() -> None:
    out = evaluate(
        (sample(), sample("b", counts=(80, 20), sid=2)),
        (result(members=("a", "b"), k=(0.8, 1.7)),),
    )
    n = np.array([110.0, 90.0])
    p = np.array([1.4, 2.3])
    k = np.array([0.8, 1.7])
    delta = 1e-5

    def f(x: np.ndarray, y: np.ndarray) -> np.ndarray:
        w = x / (k * y)
        return np.asarray(w / w.sum(), dtype=float)

    for j in range(2):
        h = np.eye(2)[j] * delta
        np.testing.assert_allclose(
            out.count_jacobian[:, j],
            (f(n + h, p) - f(n - h, p)) / (2 * delta),
            rtol=2e-8,
            atol=1e-11,
        )
        np.testing.assert_allclose(
            out.ppe_jacobian[:, j],
            (f(n, p + h) - f(n, p - h)) / (2 * delta),
            rtol=2e-8,
            atol=1e-11,
        )
    np.testing.assert_allclose(out.count_jacobian[:, :2], out.count_jacobian[:, 2:])


def test_between_aliquot_composition_identity_and_order_invariance() -> None:
    observations = (sample(), sample("b", counts=(80, 20), sid=2))
    out = evaluate(observations, (result(members=("a", "b")),))
    n = np.array([110.0, 90.0])
    pooled = np.diag(n) - np.outer(n, n) / n.sum()
    within = sum(
        np.diag(x.counts) - np.outer(x.counts, x.counts) / x.counts.sum()
        for x in observations
    )
    between = sum(
        x.counts.sum()
        * np.outer(
            x.counts / x.counts.sum() - n / n.sum(),
            x.counts / x.counts.sum() - n / n.sum(),
        )
        for x in observations
    )
    np.testing.assert_allclose(pooled - within, between)
    assert np.linalg.eigvalsh(between).min() >= -1e-13
    J = out.count_jacobian[:, :2]
    assert (J @ pooled @ J.T)[0, 0] > out.counting_covariance[0, 0]
    reordered = evaluate(observations[::-1], (result(members=("b", "a")),))
    np.testing.assert_allclose(reordered.total_covariance, out.total_covariance)


@pytest.mark.parametrize("n", [(0, 70), (30, 0)])
def test_measured_zero_axis_has_finite_derivatives(n: tuple[int, int]) -> None:
    out = evaluate((sample(counts=n),), (result(),))
    assert np.isfinite(out.count_jacobian).all()
    np.testing.assert_array_equal(out.counting_covariance, 0)


@pytest.mark.parametrize("change", ["digest", "count", "key"])
def test_same_native_sample_cannot_be_aliased(change: str) -> None:
    b = replace(sample(), observation_id="b")
    if change == "digest":
        b = replace(b, source_sha256="b" * 64)
    if change == "count":
        b = replace(b, counts=np.array([31, 69]))
    if change == "key":
        b = replace(b, observation_id="a", native_sample_id=2)
    with pytest.raises(ValidationError):
        evaluate((sample(), b), (result(members=("a", "b")),))


@pytest.mark.parametrize("members", [("unknown",), ("a", "a"), ()])
def test_membership_refusals(members: tuple[str, ...]) -> None:
    with pytest.raises(ValidationError):
        evaluate((sample(),), (result(members=members),))


@pytest.mark.parametrize(
    "counts",
    [
        np.array([True, False]),
        np.array([0.5, 4]),
        np.array([-1, 4]),
        np.array([0, 0]),
        np.array([np.inf, 1]),
        np.array([2**53, 1]),
        np.array([1, 2, 3]),
    ],
)
def test_count_refusals(counts: np.ndarray) -> None:
    with pytest.raises(ValidationError):
        evaluate((replace(sample(), counts=counts),), (result(),))


def test_unmeasured_and_axis_and_unreferenced_refusals() -> None:
    for bad in [
        replace(sample(), taxon_measured=np.array([True, False])),
        replace(sample(), parameter_ids=AXIS[::-1]),
    ]:
        with pytest.raises(ValidationError):
            evaluate((bad,), (result(),))
    with pytest.raises(ValidationError):
        evaluate((sample(), sample("b", sid=2)), (result(),))


@pytest.mark.parametrize("independent,count_ppe", [(False, True), (True, False)])
def test_undeclared_independence_refuses(independent: bool, count_ppe: bool) -> None:
    with pytest.raises(ValidationError):
        evaluate((sample(),), (result(),), independent=independent, count_ppe=count_ppe)


@pytest.mark.parametrize(
    "k", [(0.0, 1.0), (-1.0, 1.0), (float("inf"), 1.0), (1e-320, 1.0)]
)
def test_correction_refusals(k: tuple[float, float]) -> None:
    with pytest.raises(ValidationError):
        evaluate((sample(),), (result(k=k),))


def test_invalid_ppe_covariance_refuses() -> None:
    with pytest.raises(ValidationError):
        api.joint_aliquot_covariance(
            (sample(),),
            (result(),),
            parameter_ids=AXIS,
            ppe=np.ones(2),
            ppe_covariance=np.array([[1.0, 2.0], [2.0, 1.0]]),
            assume_distinct_aliquot_count_independence=True,
            assume_count_ppe_independence=True,
        )


def test_native_sample_alias_across_units_refuses() -> None:
    with pytest.raises(ValidationError):
        evaluate(
            (sample(), replace(sample("b"), collection_unit_id=9)),
            (result(members=("a", "b")),),
        )


def test_mixed_boolean_list_is_not_accepted_after_integer_coercion() -> None:
    with pytest.raises(ValidationError, match="explicit numeric array"):
        evaluate((replace(sample(), counts=cast(np.ndarray, [True, 2])),), (result(),))


def test_finite_result_budget_refuses_before_matrix_allocation() -> None:
    with pytest.raises(ValidationError, match="budget"):
        evaluate((sample(),), tuple(result(str(i)) for i in range(257)))


@pytest.mark.parametrize(
    "case", ["corrected_sum", "zero_axis_derivative", "ppe_derivative", "covariance"]
)
def test_extreme_domain_refuses_under_strict_numpy_warning_policy(case: str) -> None:
    n = np.array([1, 1])
    k = np.ones(2)
    p = np.ones(2)
    covariance = np.eye(2)
    if case == "corrected_sum":
        k = np.array([1e-308, 1e-308])
    elif case == "zero_axis_derivative":
        n = np.array([0, 1])
        k = np.array([1e-308, 1e308])
    elif case == "ppe_derivative":
        p = np.array([5e-324, 5e-324])
        k = np.array([1e308, 1e308])
    else:
        p = np.array([1e-200, 1e-200])
        k = np.array([1e200, 1e200])
        covariance = np.eye(2) * 1e200
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        with np.errstate(all="raise"), pytest.raises(ValidationError):
            api.joint_aliquot_covariance(
                (replace(sample(), counts=n),),
                (replace(result(), deposition=k),),
                parameter_ids=AXIS,
                ppe=p,
                ppe_covariance=covariance,
                assume_distinct_aliquot_count_independence=True,
                assume_count_ppe_independence=True,
            )
