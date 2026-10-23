"""Source-shaped repeated support and independent derivative/covariance controls."""

from dataclasses import replace

import numpy as np
import pytest

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.joint_fixed_site_covariance import (
    ConditionalResultInput,
    CountSupport,
    JointFixedSiteCovariance,
    joint_fixed_site_covariance,
)


def observation(result_id="a", *, support=None, deposition=(1.0, 1.0)):
    return ConditionalResultInput(
        result_id,
        support or CountSupport(37925, 52082, 37160, 0, 100, "a" * 64),
        ("parameter-row/Betula", "parameter-row/Pinus"),
        np.array([30, 70]),
        np.array(deposition),
        np.array([True, True]),
    )


def evaluate(
    *rows,
    parameters=("parameter-row/Betula", "parameter-row/Pinus"),
    ppe=(1.0, 1.0),
    covariance=None,
    windows=True,
    units=True,
):
    return joint_fixed_site_covariance(
        tuple(rows),
        parameter_ids=parameters,
        ppe=np.array(ppe),
        ppe_covariance=np.diag([0.01, 0.04]) if covariance is None else covariance,
        assume_disjoint_window_count_independence=windows,
        assume_distinct_unit_count_independence=units,
    )


@pytest.mark.parametrize(
    "field", ["ppe", "ppe_covariance", "counts", "deposition", "taxon_measured"]
)
@pytest.mark.parametrize("unresolved", [True, False])
def test_fixed_site_masks_cannot_become_backing_counts_parameters_or_covariance(
    field: str, unresolved: bool
) -> None:
    item = observation()
    ppe = np.array([1.4, 2.3])
    covariance = np.array([[0.01, 0.005], [0.005, 0.04]])

    def calculate() -> JointFixedSiteCovariance:
        return joint_fixed_site_covariance(
            (item,),
            parameter_ids=item.parameter_ids,
            ppe=ppe,
            ppe_covariance=covariance,
            assume_disjoint_window_count_independence=True,
            assume_distinct_unit_count_independence=True,
        )

    expected = calculate()
    value = (
        ppe
        if field == "ppe"
        else covariance
        if field == "ppe_covariance"
        else getattr(item, field)
    )
    mask = np.zeros(value.shape, dtype=bool)
    mask.flat[0] = unresolved
    masked = np.ma.array(value, mask=mask)
    if field == "ppe":
        ppe = masked
    elif field == "ppe_covariance":
        covariance = masked
    else:
        if field == "counts":
            item = replace(item, counts=masked)
        elif field == "deposition":
            item = replace(item, deposition=masked)
        else:
            item = replace(item, taxon_measured=masked)
    if unresolved:
        with pytest.raises(ValidationError, match=field + " contains masked"):
            calculate()
    else:
        actual = calculate()
        for name in (
            "cover",
            "count_jacobian",
            "ppe_jacobian",
            "counting_covariance",
            "ppe_covariance",
            "total_covariance",
        ):
            np.testing.assert_array_equal(
                getattr(actual, name), getattr(expected, name)
            )


def test_identical_geometry_is_one_count_observation_and_zero_contrast():
    out = evaluate(observation(), observation("b"))
    assert out.distinct_count_supports == 1
    assert out.count_jacobian.shape == (4, 2)
    assert out.counting_covariance[0, 0] == pytest.approx(0.0021)
    assert out.ppe_covariance[0, 0] == pytest.approx(0.002205)
    np.testing.assert_allclose(
        out.total_covariance[:2, 2:], out.total_covariance[:2, :2]
    )
    contrast = np.concatenate([np.eye(2), -np.eye(2)], axis=1)
    np.testing.assert_allclose(
        contrast @ out.total_covariance @ contrast.T, 0, atol=1e-15
    )


def test_count_and_ppe_derivatives_match_independent_perturbation():
    item = observation(deposition=(2.0, 0.7))
    p = np.array([1.4, 2.3])
    out = evaluate(item, ppe=p)
    n = item.counts.astype(float)

    def closed(count, parameters):
        weights = count / (item.deposition * parameters)
        return weights / weights.sum()

    delta = 1e-5
    for column in range(2):
        perturbation = np.eye(2)[column] * delta
        dn = (closed(n + perturbation, p) - closed(n - perturbation, p)) / (2 * delta)
        dp = (closed(n, p + perturbation) - closed(n, p - perturbation)) / (2 * delta)
        np.testing.assert_allclose(
            out.count_jacobian[:, column], dn, rtol=2e-8, atol=1e-11
        )
        np.testing.assert_allclose(
            out.ppe_jacobian[:, column], dp, rtol=2e-8, atol=1e-11
        )
    np.testing.assert_allclose(np.ones(2) @ out.count_jacobian, 0, atol=1e-15)
    np.testing.assert_allclose(np.ones(2) @ out.ppe_jacobian, 0, atol=1e-15)


def test_disjoint_windows_share_ppe_but_not_declared_count_latents():
    a = observation()
    b = observation(
        "b",
        support=replace(
            a.support, younger_cal_bp=100, older_cal_bp=350, source_sha256="b" * 64
        ),
    )
    out = evaluate(a, b)
    assert out.distinct_count_supports == 2
    np.testing.assert_allclose(out.counting_covariance[:2, 2:], 0)
    np.testing.assert_allclose(out.ppe_covariance[:2, 2:], out.ppe_covariance[:2, :2])
    with pytest.raises(ValidationError, match="independence"):
        evaluate(a, b, windows=False)


def test_distinct_unit_count_independence_is_explicit():
    a = observation()
    b = observation(
        "b",
        support=replace(
            a.support,
            collection_unit_id=14989,
            dataset_id=20034,
            chronology_id=11601,
            source_sha256="b" * 64,
        ),
    )
    with pytest.raises(ValidationError, match="independence"):
        evaluate(a, b, units=False)
    out = evaluate(a, b)
    np.testing.assert_allclose(out.counting_covariance[:2, 2:], 0)
    assert out.ppe_covariance[0, 2] > 0


def test_asymmetric_geometry_and_global_parameter_permutation():
    rows = (observation(), observation("b", deposition=(2.0, 0.7)))
    out = evaluate(*rows)
    reordered = evaluate(
        *rows,
        parameters=("parameter-row/Pinus", "parameter-row/Betula"),
        covariance=np.diag([0.04, 0.01]),
    )
    np.testing.assert_allclose(
        out.total_covariance, reordered.total_covariance, atol=1e-15
    )
    assert np.linalg.eigvalsh(out.total_covariance).min() > -1e-15
    for section in out.result_slices:
        closure = np.zeros(4)
        closure[section] = 1
        np.testing.assert_allclose(closure @ out.total_covariance, 0, atol=1e-15)
    assert not out.total_covariance.flags.writeable


@pytest.mark.parametrize(
    "mutation",
    [
        "counts",
        "panel",
        "overlap",
        "chronology",
        "dataset",
        "digest",
        "mask",
        "fractional",
        "unknown_parameter",
        "nonpositive_k",
    ],
)
def test_unresolved_support_or_invalid_source_axes_refuse(mutation):
    a = observation()
    b = observation("b")
    if mutation == "counts":
        b = replace(b, counts=np.array([31, 69]))
    elif mutation == "panel":
        b = replace(b, parameter_ids=tuple(reversed(b.parameter_ids)))
    elif mutation == "overlap":
        b = replace(
            b, support=replace(b.support, older_cal_bp=120, source_sha256="b" * 64)
        )
    elif mutation == "chronology":
        b = replace(
            b, support=replace(b.support, chronology_id=37159, source_sha256="b" * 64)
        )
    elif mutation == "dataset":
        b = replace(
            b, support=replace(b.support, dataset_id=1234, source_sha256="b" * 64)
        )
    elif mutation == "digest":
        b = replace(b, support=replace(b.support, collection_unit_id=14989))
    elif mutation == "mask":
        b = replace(b, taxon_measured=np.array([True, False]))
    elif mutation == "fractional":
        b = replace(b, counts=np.array([30.5, 70]))
    elif mutation == "unknown_parameter":
        b = replace(b, parameter_ids=("unknown", b.parameter_ids[1]))
    elif mutation == "nonpositive_k":
        b = replace(b, deposition=np.array([0, 1]))
    with pytest.raises(ValidationError):
        evaluate(a, b)


@pytest.mark.parametrize(
    "covariance",
    [
        np.array([[0, 1e-20], [1e-20, 0]]),
        np.array([[1, 2], [2, 1]]),
        np.array([[1, 0], [0.1, 1]]),
    ],
)
def test_invalid_global_ppe_covariance_refuses(covariance):
    with pytest.raises(ValidationError):
        evaluate(observation(), covariance=covariance)
