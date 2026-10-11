"""Publication and replay orchestration with owned synthetic decoder fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics.collection.sources.rootsi.cells import (
    publication,
    read_rootsi_cell_review,
)
from bijux_pollenomics.collection.sources.rootsi.cells.reading import replay_bundle
from bijux_pollenomics.core import owned_tree

from .support import SyntheticParser, capture_fixture, synthetic_capture_authority


def test_deterministic_complete_review_and_owned_result(tmp_path: Path) -> None:
    """All kinds and empty sheets survive; returned accounting is an owned copy."""
    capture = capture_fixture(tmp_path)
    first = publication.publish(capture, tmp_path / "first", SyntheticParser())
    second = publication.publish(capture, tmp_path / "second", SyntheticParser())
    assert first.manifest_sha256 == second.manifest_sha256
    with synthetic_capture_authority(capture):
        retained = read_rootsi_cell_review(
            first.directory, expected_manifest_sha256=first.manifest_sha256
        )
    assert retained.accounting["rectangle_positions"] == 11
    assert retained.accounting["empty_sheets"] == 1
    assert retained.accounting["scientifically_admitted_observations"] == 0
    changed = retained.accounting
    changed["scientifically_admitted_observations"] = 1
    assert retained.accounting["scientifically_admitted_observations"] == 0
    with synthetic_capture_authority(capture):
        replay_bundle(retained, capture, SyntheticParser())


def test_existing_destination_and_actual_publish_race(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The OS no-replace operation preserves a competing empty directory."""
    capture = capture_fixture(tmp_path)
    output = tmp_path / "review"
    original = owned_tree.publish_new_output_tree

    def compete(*, final_output_root: Path, staging_output_root: Path) -> None:
        final_output_root.mkdir()
        original(
            final_output_root=final_output_root, staging_output_root=staging_output_root
        )

    monkeypatch.setattr(owned_tree, "publish_new_output_tree", compete)
    with pytest.raises(FileExistsError):
        publication.publish(capture, output, SyntheticParser())
    assert output.is_dir() and list(output.iterdir()) == []
    assert len(list(tmp_path.glob(".review.pending-*"))) == 1
    with pytest.raises(IntakeRefusal, match="output_exists"):
        publication.publish(capture, output, SyntheticParser())


def test_source_mutation_leaves_no_published_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A changed file after decoding cannot be attributed to the earlier pin."""
    capture = capture_fixture(tmp_path)
    decoder = SyntheticParser()
    original = decoder.book.release_resources

    def mutate() -> None:
        original()
        capture.workbooks[0].path.write_bytes(b"changed")

    monkeypatch.setattr(decoder.book, "release_resources", mutate)
    with pytest.raises(IntakeRefusal, match="input_digest_mismatch"):
        publication.publish(capture, tmp_path / "review", decoder)
    assert not (tmp_path / "review").exists()
