"""Publication buffers belong to the same verified input epoch as the decision."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path

import pytest

from tests.support.context_data.raa import REVIEW_INPUT_PATHS, write_authority_fixture


def test_snapshot_retains_verified_bytes_after_source_paths_change(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.raa.authority import (
        assess_raa_density_authority,
        capture_raa_authority_snapshot,
    )

    write_authority_fixture(tmp_path)
    raw = (tmp_path / REVIEW_INPUT_PATHS["normalized_density"]).read_bytes()
    snapshot = capture_raa_authority_snapshot(tmp_path)
    assert snapshot.decision.admitted
    assert snapshot.density_bytes == raw
    assert type(snapshot.metadata_bytes) is bytes
    receipts = {record.role: record for record in snapshot.input_receipts}
    assert len(receipts) == 11
    assert receipts["normalized_density"].sha256 == sha256(raw).hexdigest()
    assert receipts["normalized_density"].byte_count == len(raw)
    (tmp_path / REVIEW_INPUT_PATHS["normalized_density"]).write_bytes(raw + b" ")
    assert not assess_raa_density_authority(tmp_path).admitted
    assert snapshot.density_bytes == raw
    for target, field, value in (
        (snapshot, "density_bytes", b"substituted"),
        (receipts["normalized_density"], "sha256", "0" * 64),
    ):
        with pytest.raises(FrozenInstanceError):
            setattr(target, field, value)


def test_missing_proof_does_not_invent_verified_publication_buffers(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.raa.authority import (
        capture_raa_authority_snapshot,
    )

    snapshot = capture_raa_authority_snapshot(tmp_path)
    assert not snapshot.decision.admitted
    assert snapshot.metadata_bytes is None
    assert snapshot.density_bytes is None
    assert snapshot.input_receipts == ()
