"""Lossless AADR annotation-file source-row parsing."""

from __future__ import annotations

import csv
from hashlib import sha256
import io
from pathlib import Path

from .chronology import prepare_aadr_chronology_evidence
from .coordinates import parse_aadr_coordinates
from .date_methods import classify_aadr_date_method
from .models import (
    AadrSourceFile,
    AadrSourceRow,
    AadrSourceTable,
)

_FIELD_PREFIXES: dict[str, tuple[str, ...]] = {
    "genetic_id": ("Genetic ID",),
    "latitude": ("Latitude", "Lat."),
    "longitude": ("Longitude", "Long."),
    "date_method": ("Method for Determining Date",),
    "date_mean_bp": ("Date mean in BP",),
    "date_stddev_bp": ("Date standard deviation in BP",),
    "full_date": ("Full Date",),
}


def load_aadr_source_table(
    path: Path,
    *,
    source_release: str,
    dataset_name: str,
    expected_sha256: str | None = None,
) -> AadrSourceTable:
    """Load every AADR data row and bind it to the exact source-file digest."""
    path = Path(path)
    source_bytes = path.read_bytes()
    source_sha256 = sha256(source_bytes).hexdigest()
    if expected_sha256 is not None and source_sha256 != expected_sha256:
        raise ValueError(
            "AADR source digest mismatch: "
            f"expected {expected_sha256}, observed {source_sha256}"
        )
    source = AadrSourceFile(
        source_path=str(path),
        source_release=source_release,
        dataset_name=dataset_name,
        source_sha256=source_sha256,
        source_byte_count=len(source_bytes),
    )
    text = source_bytes.decode("utf-8-sig")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter="\t")
    try:
        column_names = tuple(next(reader))
    except StopIteration as error:
        raise ValueError("AADR source file is empty") from error
    if not column_names or not any(column_names):
        raise ValueError("AADR source header is empty")
    field_indexes = {
        key: _find_column_index(column_names, prefixes)
        for key, prefixes in _FIELD_PREFIXES.items()
    }
    rows: list[AadrSourceRow] = []
    previous_line_end = reader.line_num
    for source_record_number, parsed_tokens in enumerate(reader, start=1):
        line_start = previous_line_end + 1
        line_end = reader.line_num
        previous_line_end = line_end
        raw_tokens = tuple(parsed_tokens)
        rows.append(
            AadrSourceRow(
                source=source,
                source_record_number=source_record_number,
                source_line_start=line_start,
                source_line_end=line_end,
                column_names=column_names,
                raw_tokens=raw_tokens,
                genetic_id_raw=_selected_value(raw_tokens, field_indexes, "genetic_id"),
                coordinates=parse_aadr_coordinates(
                    _selected_value(raw_tokens, field_indexes, "latitude"),
                    _selected_value(raw_tokens, field_indexes, "longitude"),
                ),
                chronology=prepare_aadr_chronology_evidence(
                    date_method=classify_aadr_date_method(
                        _selected_value(raw_tokens, field_indexes, "date_method")
                    ),
                    date_mean_bp_raw=_selected_value(
                        raw_tokens, field_indexes, "date_mean_bp"
                    ),
                    date_stddev_bp_raw=_selected_value(
                        raw_tokens, field_indexes, "date_stddev_bp"
                    ),
                    full_date_raw=_selected_value(
                        raw_tokens, field_indexes, "full_date"
                    ),
                ),
            )
        )
    return AadrSourceTable(source=source, column_names=column_names, rows=tuple(rows))


def _find_column_index(
    column_names: tuple[str, ...], prefixes: tuple[str, ...]
) -> int | None:
    casefolded_prefixes = tuple(prefix.casefold() for prefix in prefixes)
    matches = tuple(
        index
        for index, column_name in enumerate(column_names)
        if any(
            column_name.casefold() == prefix
            or column_name.casefold().startswith(prefix)
            for prefix in casefolded_prefixes
        )
    )
    if len(matches) > 1:
        raise ValueError(f"AADR source columns are ambiguous for {prefixes!r}")
    return matches[0] if matches else None


def _raw_value(raw_tokens: tuple[str, ...], index: int | None) -> str:
    if index is None or index >= len(raw_tokens):
        return ""
    return raw_tokens[index]


def _selected_value(
    raw_tokens: tuple[str, ...],
    field_indexes: dict[str, int | None],
    field_name: str,
) -> str:
    return _raw_value(raw_tokens, field_indexes[field_name])


__all__ = ["load_aadr_source_table"]
