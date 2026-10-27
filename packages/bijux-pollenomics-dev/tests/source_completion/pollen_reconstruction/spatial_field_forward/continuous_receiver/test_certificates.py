"""Complete-partition refusal and aggregate certificate size boundaries."""

from __future__ import annotations

from fractions import Fraction

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.certificates import (
    encoded_certificates,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.coefficients import (
    certify,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.kernel import (
    Geometry,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.spatial_field_forward.continuous_receiver.quadrature import (
    ResourceRefusal,
    WorkBudget,
)


def test_initial_four_domain_refusal_is_complete_and_byte_cap_is_aggregate() -> None:
    model = Geometry(
        Fraction(3, 5),
        Fraction(1),
        Fraction(17),
        (Fraction(4), Fraction(1)),
        (Fraction(-7), Fraction(3)),
    )
    result = certify(model, WorkBudget(max_attempts=4))
    assert result.status == "refuse_unresolved"
    assert len(result.integrals) == 4
    assert all(len(row.panels) == 1 for row in result.integrals)
    assert all(row.refusal == "attempt_or_node_ceiling" for row in result.integrals)
    assert result.homogeneous.width > Fraction(1, 10**9)
    assert result.second.lower == (result.homogeneous - result.first).lower
    one = encoded_certificates([result])
    assert encoded_certificates([result], maximum_bytes=len(one)) == one
    with pytest.raises(ResourceRefusal, match="byte_ceiling"):
        encoded_certificates([result, result], maximum_bytes=len(one))


def test_failure_before_first_closed_panel_does_not_return_a_partial_integral() -> None:
    model = Geometry(
        Fraction(3, 5),
        Fraction(1),
        Fraction(17),
        (Fraction(4), Fraction(1)),
        (Fraction(-7), Fraction(3)),
    )
    with pytest.raises(ResourceRefusal, match="ceiling"):
        certify(model, WorkBudget(max_nodes=1))
