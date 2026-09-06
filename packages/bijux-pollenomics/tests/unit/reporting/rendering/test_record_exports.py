"""Portable newline behavior for report CSV exports."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics.reporting.rendering import record_exports


@pytest.mark.parametrize(
    ("writer", "fields", "record"),
    (
        (
            record_exports.write_samples_csv,
            record_exports.SAMPLE_EXPORT_FIELDS,
            SimpleNamespace(datasets=("source-a",), accession_lineage=("id-a",)),
        ),
        (
            record_exports.write_localities_csv,
            record_exports.LOCALITY_EXPORT_FIELDS,
            SimpleNamespace(datasets=("source-a",), sample_ids=("sample-a",)),
        ),
    ),
)
def test_csv_exports_use_repository_native_line_endings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    writer: Any,
    fields: tuple[str, ...],
    record: SimpleNamespace,
) -> None:
    serializer_name = (
        "serialize_sample_record"
        if writer is record_exports.write_samples_csv
        else "serialize_locality_summary"
    )
    monkeypatch.setattr(
        record_exports,
        serializer_name,
        lambda _record: dict.fromkeys(fields, ""),
    )
    output_path = tmp_path / "records.csv"

    writer(output_path, (record,))

    payload = output_path.read_bytes()
    assert payload.endswith(b"\n")
    assert b"\r\n" not in payload
    assert payload.count(b"\n") == 2
