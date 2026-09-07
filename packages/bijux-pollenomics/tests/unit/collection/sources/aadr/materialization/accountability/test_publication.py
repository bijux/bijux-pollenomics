"""Atomic publication tests for compact AADR accountability receipts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.aadr.materialization.accountability import (
    build_aadr_source_accountability_receipt,
    canonical_aadr_source_accountability_bytes,
    write_aadr_source_accountability_receipt,
)
from bijux_pollenomics.collection.sources.aadr.materialization.accountability import (
    publication,
)

from .support import reconciliation, release_manifest_identity


def test_canonical_receipt_bytes_and_atomic_writer_are_deterministic(
    tmp_path: Path,
) -> None:
    receipt = build_aadr_source_accountability_receipt(
        reconciliation(tmp_path / "inputs"),
        release_manifest=release_manifest_identity(),
    )
    output = tmp_path / "review" / "aadr_v66_source_accountability.json"

    expected = canonical_aadr_source_accountability_bytes(receipt)
    first = write_aadr_source_accountability_receipt(output, receipt)
    second = write_aadr_source_accountability_receipt(output, receipt)

    assert first == second == expected == output.read_bytes()
    assert expected.endswith(b"\n")
    assert json.loads(expected) == receipt
    assert not tuple(output.parent.glob("*.writing"))


def test_atomic_writer_preserves_existing_receipt_when_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = build_aadr_source_accountability_receipt(
        reconciliation(tmp_path / "inputs"),
        release_manifest=release_manifest_identity(),
    )
    output = tmp_path / "review" / "aadr_v66_source_accountability.json"
    output.parent.mkdir()
    original = b"existing governed receipt\n"
    output.write_bytes(original)

    def fail_replace(_source: object, _destination: object) -> None:
        raise OSError("injected atomic replacement failure")

    monkeypatch.setattr(publication, "_replace_file", fail_replace)

    with pytest.raises(OSError, match="injected atomic replacement failure"):
        write_aadr_source_accountability_receipt(output, receipt)

    assert output.read_bytes() == original
    assert not tuple(output.parent.glob("*.writing"))


def test_atomic_writer_refuses_symlink_destination(tmp_path: Path) -> None:
    receipt = build_aadr_source_accountability_receipt(
        reconciliation(tmp_path / "inputs"),
        release_manifest=release_manifest_identity(),
    )
    target = tmp_path / "target.json"
    target.write_text("do not replace", encoding="utf-8")
    output = tmp_path / "receipt.json"
    output.symlink_to(target)

    with pytest.raises(ValueError, match="cannot use a symlink"):
        write_aadr_source_accountability_receipt(output, receipt)

    assert target.read_text(encoding="utf-8") == "do not replace"
