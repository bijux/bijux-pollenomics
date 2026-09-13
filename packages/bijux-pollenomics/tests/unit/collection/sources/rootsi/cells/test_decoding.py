"""Public decoder protocol, optional import and complete-position behavior."""

from __future__ import annotations

import importlib
from importlib.metadata import PackageNotFoundError
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics.collection.sources.rootsi.cells import decoding

from .support import SyntheticParser, SyntheticSheet, capture_fixture


def test_every_position_and_empty_sheet_retained(tmp_path: Path) -> None:
    """Typed values, source text, signed zero and empty sheets are not filtered."""
    capture = capture_fixture(tmp_path)
    decoder = SyntheticParser()
    records = list(
        decoding.workbook_records(capture.workbooks[0], capture.archive_sha256, decoder)
    )
    assert [kind for kind, _ in records].count("cell") == 11
    sheets = [row for kind, row in records if kind == "sheet"]
    assert len(sheets) == 2 and sheets[1]["rectangle_positions"] == 0
    cells = [row for kind, row in records if kind == "cell"]
    assert cells[1]["decoded_value"] == "  rå \U0001f33f "
    assert cells[2]["binary64_hex"] != cells[3]["binary64_hex"]
    assert cells[6]["cell_type"] == 3 and cells[6]["decoded_value"] == 42000.5
    assert decoder.book.released


def test_duplicate_sheet_name_refuses_and_releases(tmp_path: Path) -> None:
    """Sheet ordinal does not excuse an ambiguous source sheet name."""
    capture = capture_fixture(tmp_path)
    decoder = SyntheticParser()
    decoder.book.pages.append(SyntheticSheet("empty", []))
    with pytest.raises(IntakeRefusal, match="invalid_sheet_name"):
        list(
            decoding.workbook_records(
                capture.workbooks[0], capture.archive_sha256, decoder
            )
        )
    assert decoder.book.released


def test_missing_optional_parser_is_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing distribution metadata refuses rather than selecting another reader."""

    def missing(name: str) -> str:
        raise PackageNotFoundError(name)

    monkeypatch.setattr(decoding, "version", missing)
    with pytest.raises(IntakeRefusal, match="optional_parser_unavailable"):
        decoding.parser()


def test_unsupported_parser_version_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    """No unrecorded parser upgrade is silently admitted."""
    monkeypatch.setattr(decoding, "version", lambda name: "999.0")
    monkeypatch.setattr(importlib, "import_module", lambda name: object())
    with pytest.raises(IntakeRefusal, match="unsupported_parser_version"):
        decoding.parser()
