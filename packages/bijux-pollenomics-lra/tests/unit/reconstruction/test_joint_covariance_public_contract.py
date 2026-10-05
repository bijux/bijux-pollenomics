"""Public joint-covariance facade and malformed identity refusals."""

from dataclasses import replace

import numpy as np
import pytest

from bijux_pollenomics_lra import api
from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction import (
    joint_fixed_site_covariance as implementation,
)


def source():
    return implementation.ConditionalResultInput(
        "case:window",
        implementation.CountSupport(37925, 52082, 37160, 0, 100, "a" * 64),
        ("Betula:literal-row", "Pinus:literal-row"),
        np.array([30, 70]),
        np.array([1.0, 1.0]),
        np.array([True, True]),
    )


def evaluate(rows, parameters=("Betula:literal-row", "Pinus:literal-row")):
    return api.joint_fixed_site_covariance(
        rows,
        parameter_ids=parameters,
        ppe=np.array([1.0, 1.0]),
        ppe_covariance=np.diag([0.01, 0.04]),
        assume_disjoint_window_count_independence=True,
        assume_distinct_unit_count_independence=True,
    )


def test_public_facade_binds_actual_joint_implementation():
    for name in (
        "CountSupport",
        "ConditionalResultInput",
        "JointFixedSiteCovariance",
        "joint_fixed_site_covariance",
    ):
        assert getattr(api, name) is getattr(implementation, name)
        assert name in api.__all__
    result = evaluate((source(),))
    assert isinstance(result, api.JointFixedSiteCovariance)
    assert result.profile == implementation.PROFILE
    np.testing.assert_allclose(result.cover, [0.3, 0.7])


def test_extension_descriptor_declares_conditional_joint_capability():
    assert (
        "lra.reveals.multisite.joint-fixed-site-delta-covariance"
        in api.extension_descriptor()["capabilities"]
    )


def test_caller_parameter_list_cannot_change_returned_axis():
    parameters = ["Betula:literal-row", "Pinus:literal-row"]
    result = evaluate((source(),), parameters)
    parameters.reverse()
    assert result.parameter_ids == ("Betula:literal-row", "Pinus:literal-row")


def test_reused_count_support_accepts_equivalent_sequence_axes():
    first = source()
    second = replace(
        first,
        result_id="geometry-alternative:window",
        parameter_ids=list(first.parameter_ids),
    )
    result = evaluate((first, second))
    assert result.distinct_count_supports == 1
    np.testing.assert_allclose(result.cover[:2], result.cover[2:])
    np.testing.assert_allclose(
        result.counting_covariance[:2, :2], result.counting_covariance[:2, 2:]
    )


@pytest.mark.parametrize("foreign", [object(), {"result_id": "foreign"}, None])
def test_foreign_result_refuses_before_attribute_access(foreign):
    with pytest.raises(ValidationError, match="identities"):
        evaluate((foreign,))


@pytest.mark.parametrize("identifier", ["", 123, []])
def test_malformed_result_identifier_refuses_before_hashing(identifier):
    with pytest.raises(ValidationError, match="identities"):
        evaluate((replace(source(), result_id=identifier),))


@pytest.mark.parametrize("parameters", [None, ("valid", []), ("",)])
def test_malformed_global_parameter_identity_refuses(parameters):
    with pytest.raises(ValidationError, match="identities"):
        evaluate((source(),), parameters)


@pytest.mark.parametrize("parameters", [None, ("valid", [])])
def test_malformed_local_parameter_identity_refuses(parameters):
    with pytest.raises(ValidationError, match="axis"):
        evaluate((replace(source(), parameter_ids=parameters),))
