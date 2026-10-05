"""Reject invalid compact source/count shapes and escaping publication paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_conditional_love.producer import (
    publish,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_conditional_love.summary import (
    close,
    integer,
    matrix,
    vector,
)


@pytest.mark.parametrize("value", [-1, 0.5, True, None, float("nan"), float("inf")])
def test_literal_counts_refuse_fractional_nonfinite_and_boolean(value: object) -> None:
    with pytest.raises(ValueError, match="nonnegative integer"):
        integer(value)


@pytest.mark.parametrize(
    "a,b", [(float("nan"), 1.0), (1.0, float("inf")), (True, 1.0), (1.0, "1")]
)
def test_scalar_comparison_refuses_nonfinite_or_non_numeric(
    a: object, b: object
) -> None:
    with pytest.raises(ValueError):
        close(a, b)


@pytest.mark.parametrize("value", [[], [1.0], [1.0, 0.0, 0.0]])
def test_panel_vector_requires_exact_taxon_axis(value: list[float]) -> None:
    with pytest.raises(ValueError, match="two-taxon vector"):
        vector(value, [1.0, 0.0])


@pytest.mark.parametrize("value", [[], [[1.0, 0.0]], [[1.0], [0.0]]])
def test_covariance_requires_exact_panel_shape(value: list[list[float]]) -> None:
    with pytest.raises(ValueError, match="two-taxon"):
        matrix(value, [[1.0, 0.0], [0.0, 1.0]])


def test_signed_infeasible_values_are_not_clipped_by_comparison() -> None:
    vector(
        [1.0016539822067665, -0.001653982206766491],
        [1.0016539822067665, -0.001653982206766491],
    )
    with pytest.raises(ValueError, match="numerical comparison"):
        vector([1.0, 0.0], [1.0016539822067665, -0.001653982206766491])


@pytest.mark.parametrize("kind", ["traversal", "artifact-root", "outside"])
def test_destination_refuses_before_private_source_reads(
    tmp_path: Path, kind: str
) -> None:
    output = {
        "traversal": tmp_path / "artifacts/../outside",
        "artifact-root": tmp_path / "artifacts",
        "outside": tmp_path / "outside",
    }[kind]
    with pytest.raises(ReportRebuildError):
        publish(
            tmp_path,
            tmp_path / "unprovided-store",
            Path("unprovided-descriptor.json"),
            output,
        )
    assert not output.exists()
