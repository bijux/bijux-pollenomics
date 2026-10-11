"""Standalone report visibility and escaping boundaries."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.analysis.lra.uncertainty.contracts import JointLRAPlan
from bijux_pollenomics.reporting.lra_products.joint.downloads import (
    capture_joint_product,
)
from bijux_pollenomics.reporting.lra_products.joint.projection import (
    project_joint_product,
)
from bijux_pollenomics.reporting.lra_products.joint.rendering import render_report

from .support import FixtureState, joint_fixture


def _html(
    root: Path, *, state: FixtureState = "complete", bin_id: str = "target"
) -> str:
    product, checksum = joint_fixture(root, state=state, bin_id=bin_id)
    manifest, files = capture_joint_product(product, checksum)
    projection = project_joint_product(
        manifest,
        JointLRAPlan(files["plan.json"].decode("utf-8")).payload(),
        product_manifest_sha256=checksum,
    )
    return render_report(projection, manifest)


def test_complete_report_displays_full_covariance_and_claim_boundaries(
    tmp_path: Path,
) -> None:
    html = _html(tmp_path)
    assert html.startswith("<!doctype html>")
    assert "Full ordered population covariance" in html
    assert "fraction_squared" in html
    assert "ring=null" in html and "ring=100.0 m" in html
    assert "Scientific acceptance is not evaluated" in html
    assert "no geometry, map, posterior, empirical coverage" in html
    assert "covariance.csv" in html and "draw-bin-ledger.csv" in html


def test_incomplete_and_interrupted_states_remain_visible(tmp_path: Path) -> None:
    html = _html(tmp_path, state="interrupted")
    assert "Status: incomplete" in html
    assert "Product interrupted: True" in html
    assert "mean and covariance remain null" in html
    assert "Successful subsets were not renormalized" in html
    assert "3/4" in html and "not_run" in html
    assert "not run" in html.lower()


def test_untrusted_labels_are_escaped(tmp_path: Path) -> None:
    html = _html(tmp_path, bin_id="<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
