"""Exact mass, status and full-moment projection."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.uncertainty.contracts import JointLRAPlan
from bijux_pollenomics.reporting.lra_products.joint.downloads import (
    capture_joint_product,
)
from bijux_pollenomics.reporting.lra_products.joint.projection import (
    project_joint_product,
)

from .support import FixtureState, joint_fixture


@pytest.mark.parametrize(
    "state,counts,masses",
    [
        ("complete", (4, 0, 0), ((1, 1), (0, 1), (0, 1))),
        ("refused", (3, 1, 0), ((3, 4), (1, 4), (0, 1))),
        ("interrupted", (1, 0, 3), ((1, 4), (0, 1), (3, 4))),
    ],
)
def test_exact_status_partitions_and_null_moments(
    tmp_path: Path,
    state: FixtureState,
    counts: tuple[int, int, int],
    masses: tuple[tuple[int, int], tuple[int, int], tuple[int, int]],
) -> None:
    product, checksum = joint_fixture(tmp_path, state=state)
    manifest, files = capture_joint_product(product, checksum)
    plan = JointLRAPlan(files["plan.json"].decode("utf-8")).payload()
    projected = project_joint_product(manifest, plan, product_manifest_sha256=checksum)
    band = projected["bins"][0]
    assert band["counts"] == {
        "requested": 4,
        "successful": counts[0],
        "refused": counts[1],
        "not_run": counts[2],
    }
    for status, expected in zip(
        ("successful", "refused", "not_run"), masses, strict=True
    ):
        assert (
            band["masses"][status]["numerator"],
            band["masses"][status]["denominator"],
        ) == expected
    assert band["masses"]["requested"]["text"] == "1/1"
    assert len(projected["draw_bin_ledger"]) == 4
    assert all(
        row["retained_row"] == manifest["rows"][index]
        for index, row in enumerate(projected["draw_bin_ledger"])
    )
    if state == "complete":
        assert len(projected["means"]) == 4
        assert len(projected["covariance"]) == 16
        assert any(row["value"] < 0 for row in projected["covariance"])
        assert any(row["value"] > 0 for row in projected["covariance"])
        assert any(row["value"] == 0 for row in projected["covariance"])
        assert projected["means"][0]["coordinate"]["ring_mean_m"] is None
    else:
        assert band["mean"] is None and band["population_covariance"] is None
        assert projected["means"] == [] and projected["covariance"] == []


def test_ordered_covariance_keeps_cross_role_pairs(tmp_path: Path) -> None:
    product, checksum = joint_fixture(tmp_path)
    manifest, files = capture_joint_product(product, checksum)
    projection = project_joint_product(
        manifest,
        JointLRAPlan(files["plan.json"].decode("utf-8")).payload(),
        product_manifest_sha256=checksum,
    )
    assert [
        (row["row_index"], row["column_index"]) for row in projection["covariance"]
    ] == [(row, column) for row in range(4) for column in range(4)]
    cross = next(
        row
        for row in projection["covariance"]
        if row["row_coordinate"]["role"] == "regional"
        and row["column_coordinate"]["role"] == "local"
    )
    assert cross["unit"] == "fraction_squared"
    assert "population_covariance" in cross["source_pointer"]
