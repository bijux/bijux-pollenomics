"""Finite authority inputs retain one byte identity through source reconciliation."""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import os
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.raa import assess_raa_density_authority
from tests.support.context_data.raa import REVIEW_INPUT_PATHS, write_authority_fixture


def test_input_receipt_hashes_the_exact_buffer_used_for_decode(tmp_path: Path) -> None:
    from bijux_pollenomics.collection.sources.raa.authority_inputs import (
        RaaAuthorityInputs,
    )

    write_authority_fixture(tmp_path)
    path = tmp_path / REVIEW_INPUT_PATHS["raw_inventory"]
    raw = path.read_bytes() + b"\n  "
    path.write_bytes(raw)
    with RaaAuthorityInputs(tmp_path) as inputs:
        assert inputs.load_object("raw_inventory")["numberMatched"] == 2
        assert inputs.receipt("raw_inventory") == {
            "path": REVIEW_INPUT_PATHS["raw_inventory"],
            "sha256": sha256(raw).hexdigest(),
            "byte_count": len(raw),
        }
        inputs.validate()


@pytest.mark.parametrize(
    "problem", ["missing_ledger", "oversized_raw", "oversized_review"]
)
def test_every_slot_is_preflighted_before_any_body_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, problem: str
) -> None:
    from bijux_pollenomics.core.filesystem import BoundedInputTree

    write_authority_fixture(tmp_path)
    if problem == "missing_ledger":
        (tmp_path / REVIEW_INPUT_PATHS["membership_ledger"]).unlink()
    else:
        path = tmp_path / (
            REVIEW_INPUT_PATHS["raw_inventory"]
            if problem == "oversized_raw"
            else "raa/review/spatiotemporal_review.json"
        )
        os.truncate(
            path, (256 * 1024 * 1024 if problem == "oversized_raw" else 256 * 1024) + 1
        )

    def refuse_read(*_args: object, **_kwargs: object) -> bytes:
        raise AssertionError("authority opened a body before complete preflight")

    monkeypatch.setattr(BoundedInputTree, "read", refuse_read)
    decision = assess_raa_density_authority(tmp_path)
    assert not decision.admitted
    assert (
        "missing_density_membership"
        if problem == "missing_ledger"
        else "authority_input_resource_budget_exceeded"
    ) in decision.reason_codes


@pytest.mark.parametrize(
    "role",
    ["raw_inventory", "normalized_density", "sweden_boundary", "scientific_review"],
)
def test_input_seals_reject_drift_after_the_first_read(
    tmp_path: Path, role: str
) -> None:
    from bijux_pollenomics.collection.sources.raa.authority_inputs import (
        INPUT_PATHS,
        RaaAuthorityInputs,
    )

    write_authority_fixture(tmp_path)
    with RaaAuthorityInputs(tmp_path) as inputs:
        raw = inputs.read(role)
        (tmp_path / INPUT_PATHS[role]).write_bytes(raw + b" ")
        with pytest.raises(ValueError):
            inputs.validate()


def test_unknown_roles_and_boundary_paths_cannot_open_arbitrary_files(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.raa.authority_inputs import (
        RaaAuthorityInputs,
    )

    write_authority_fixture(tmp_path)
    with RaaAuthorityInputs(tmp_path) as inputs:
        with pytest.raises(ValueError, match="literal|role"):
            inputs.read("arbitrary")
        with pytest.raises(ValueError, match="literal|boundary"):
            inputs.boundary_reader(tmp_path / "outside.json")


def test_a_closed_input_operation_cannot_reuse_an_authenticated_buffer(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.raa.authority_inputs import (
        RaaAuthorityInputs,
    )

    write_authority_fixture(tmp_path)
    inputs = RaaAuthorityInputs(tmp_path)
    with inputs:
        inputs.read("raw_inventory")
    with pytest.raises(ValueError, match="active|closed|operation"):
        inputs.read("raw_inventory")


def test_an_input_operation_cannot_be_reentered_with_stale_receipts(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.raa.authority_inputs import (
        RaaAuthorityInputs,
    )

    write_authority_fixture(tmp_path)
    inputs = RaaAuthorityInputs(tmp_path)
    with inputs:
        inputs.read("raw_inventory")
    with pytest.raises(ValueError, match="operation"), inputs:
        pass


@pytest.mark.parametrize(
    "role", ["raw_inventory", "sweden_boundary", "scientific_review"]
)
def test_public_authority_rechecks_inputs_after_ledger_recomputation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, role: str
) -> None:
    from bijux_pollenomics.collection.sources.raa import authority
    from bijux_pollenomics.collection.sources.raa.authority_inputs import INPUT_PATHS

    write_authority_fixture(tmp_path)
    from bijux_pollenomics.collection.sources.raa.density_membership import (
        DensityMembership,
        build_raa_density_membership,
    )

    def drifting_membership(
        *,
        feature_inventory: Mapping[str, object],
        sweden_boundary: Mapping[str, object],
    ) -> DensityMembership:
        result = build_raa_density_membership(
            feature_inventory=feature_inventory, sweden_boundary=sweden_boundary
        )
        path = tmp_path / INPUT_PATHS[role]
        path.write_bytes(path.read_bytes() + b" ")
        return result

    monkeypatch.setattr(authority, "build_raa_density_membership", drifting_membership)
    decision = assess_raa_density_authority(tmp_path)
    assert not decision.admitted
    assert "authority_input_changed" in decision.reason_codes
