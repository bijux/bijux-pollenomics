"""Atomic retained-report lifecycle and identity checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.lra_products.contracts import digest
from bijux_pollenomics.reporting.lra_products.joint.api import (
    JointLRAPresentation,
    LRAPresentationRefusal,
    render_joint_lra_report,
)

from .support import FixtureState, joint_fixture


def test_atomic_report_receipt_and_deterministic_membership(tmp_path: Path) -> None:
    product, checksum = joint_fixture(tmp_path / "fixture")
    first = render_joint_lra_report(
        product, expected_manifest_sha256=checksum, destination=tmp_path / "report"
    )
    assert isinstance(first, JointLRAPresentation)
    assert first.product_status == "complete" and not first.interrupted
    assert first.bin_count == 1 and first.requested_draw_bins == 4
    assert first.successful_draw_bins == 4
    manifest = json.loads((first.directory / "manifest.json").read_bytes())
    assert (
        digest((first.directory / "manifest.json").read_bytes())
        == first.manifest_sha256
    )
    assert manifest["publication_authorized"] is False
    assert all(
        digest((first.directory / member).read_bytes()) == sha256
        for member, sha256 in manifest["files"].items()
    )
    assert manifest["capabilities"] == {
        "geometry": False,
        "map": False,
        "publication": False,
        "scientific_acceptance": False,
        "empirical_coverage": False,
        "intervals": False,
        "renormalization": False,
        "numerical_recomputation": False,
    }
    second = render_joint_lra_report(
        product, expected_manifest_sha256=checksum, destination=tmp_path / "again"
    )
    assert second.manifest_sha256 == first.manifest_sha256


def test_existing_nested_and_ancestor_destinations_refuse(tmp_path: Path) -> None:
    product, checksum = joint_fixture(tmp_path / "fixture")
    destination = tmp_path / "report"
    render_joint_lra_report(
        product, expected_manifest_sha256=checksum, destination=destination
    )
    before = (destination / "manifest.json").read_bytes()
    with pytest.raises(LRAPresentationRefusal, match="presentation_output_exists"):
        render_joint_lra_report(
            product, expected_manifest_sha256=checksum, destination=destination
        )
    assert (destination / "manifest.json").read_bytes() == before
    with pytest.raises(LRAPresentationRefusal, match="invalid_presentation_output"):
        render_joint_lra_report(
            product,
            expected_manifest_sha256=checksum,
            destination=product / "nested",
        )
    with pytest.raises(LRAPresentationRefusal, match="invalid_presentation_output"):
        render_joint_lra_report(
            product,
            expected_manifest_sha256=checksum,
            destination=product.parent,
        )


def test_external_pin_and_source_mutation_refuse_before_publication(
    tmp_path: Path,
) -> None:
    product, checksum = joint_fixture(tmp_path / "fixture")
    with pytest.raises(LRAPresentationRefusal, match="changed_presentation_input"):
        render_joint_lra_report(
            product,
            expected_manifest_sha256="0" * 64,
            destination=tmp_path / "bad-pin",
        )
    assert not (tmp_path / "bad-pin").exists()
    (product / "plan.json").write_text("changed", encoding="utf-8")
    with pytest.raises(LRAPresentationRefusal):
        render_joint_lra_report(
            product,
            expected_manifest_sha256=checksum,
            destination=tmp_path / "changed",
        )
    assert not (tmp_path / "changed").exists()


def test_incomplete_and_interrupted_receipts_are_not_promoted(tmp_path: Path) -> None:
    cases: tuple[tuple[FixtureState, int, int], ...] = (
        ("refused", 1, 0),
        ("interrupted", 0, 3),
    )
    for state, refused, not_run in cases:
        root = tmp_path / state
        product, checksum = joint_fixture(root / "fixture", state=state)
        report = render_joint_lra_report(
            product,
            expected_manifest_sha256=checksum,
            destination=root / "report",
        )
        assert report.product_status == "incomplete"
        assert report.refused_draw_bins == refused
        assert report.not_run_draw_bins == not_run
        assert report.interrupted is (state == "interrupted")
