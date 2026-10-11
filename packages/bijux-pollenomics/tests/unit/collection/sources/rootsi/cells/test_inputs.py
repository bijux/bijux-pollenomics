"""Exact source and path refusal counterexamples."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics.collection.sources.rootsi.cells.inputs import (
    RETAINED_INVENTORY_SHA256,
    bind_capture,
    member_name,
    output_path,
    read_bytes,
    verify_capture,
)

from .support import capture_fixture


@pytest.mark.parametrize(
    "value",
    [
        "../x.xls",
        "/x.xls",
        "rootsi//x.xls",
        "rootsi/./x.xls",
        "rootsi/x.xls\x00",
        "rootsi\\x.xls",
        "rootsi/x.xlsx",
        True,
    ],
)
def test_member_refuses_unsafe_or_untyped_name(value: object) -> None:
    """Never sanitize source member identity into a different accepted value."""
    with pytest.raises(IntakeRefusal):
        member_name(value)


def test_member_case_and_unicode_preserved() -> None:
    """No basename/casefold merge is performed."""
    assert member_name("rootsi/Åge.xls") == "rootsi/Åge.xls"


def test_arbitrary_inventory_pin_cannot_impersonate_real_capture(
    tmp_path: Path,
) -> None:
    """Even an honestly rehashed alternate inventory fails public capture admission."""
    capture = capture_fixture(tmp_path)
    with pytest.raises(IntakeRefusal, match="unrecognized_capture"):
        bind_capture(
            inventory_path=capture.inventory_path,
            expected_inventory_sha256=capture.inventory_sha256,
            workbook_files={
                item.archive_member: item.path for item in capture.workbooks
            },
            scope="selected_workbooks",
        )
    with pytest.raises(IntakeRefusal, match="input_digest_mismatch"):
        bind_capture(
            inventory_path=capture.inventory_path,
            expected_inventory_sha256=RETAINED_INVENTORY_SHA256,
            workbook_files={},
            scope="complete_retained_capture",
        )


def test_mutation_and_source_directory_overlap_refuse(tmp_path: Path) -> None:
    """Reject lexical containment before creating a stage in source storage."""
    capture = capture_fixture(tmp_path)
    verify_capture(capture)
    bridge = tmp_path / "bridge"
    bridge.mkdir()
    with pytest.raises(IntakeRefusal, match="unsafe_output"):
        output_path(bridge / ".." / "raw" / "nested", capture)
    with pytest.raises(IntakeRefusal, match="unsafe_output"):
        output_path(tmp_path, capture)
    source = capture.workbooks[0].path
    source.write_bytes(source.read_bytes() + b"changed")
    with pytest.raises(IntakeRefusal, match="input_digest_mismatch"):
        verify_capture(capture)


def test_symlink_even_before_dot_normalization_refuses(tmp_path: Path) -> None:
    """A hidden symlink component cannot disappear via lexical normalization."""
    capture = capture_fixture(tmp_path)
    link = tmp_path / "alias"
    link.symlink_to(capture.inventory_path.parent, target_is_directory=True)
    with pytest.raises(IntakeRefusal, match="symlink_path"):
        output_path(link / ".." / "out", capture)
    alias_file = tmp_path / "file"
    alias_file.symlink_to(capture.inventory_path)
    with pytest.raises(IntakeRefusal, match="symlink_path"):
        read_bytes(
            alias_file, hashlib.sha256(capture.inventory_path.read_bytes()).hexdigest()
        )
