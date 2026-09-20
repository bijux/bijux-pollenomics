"""Source-row capture layered on the established LandClim CSV parsers."""

from __future__ import annotations

from collections.abc import Mapping
import csv
from dataclasses import dataclass
from io import TextIOWrapper
from zipfile import ZipFile

from ..catalog import time_window_from_tw_filename
from ..time_windows.landclim_ii_rows import (
    _LandClimIIStandardErrors,
    _published_headers,
    _published_identity,
    _require_exact_tokens,
)
from ..time_windows.values import _required_numeric_mapping
from .contracts import LandClimPublishedInventoryRefusal


@dataclass(frozen=True, slots=True)
class _SourceRow:
    member_name: str
    source_row: int
    cell_id: str
    cell_id_token: str
    longitude_token: str
    latitude_token: str
    longitude_float: float | None
    latitude_float: float | None
    value_tokens: tuple[str, ...]
    parsed_values: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class _SourceTable:
    headers_by_window: Mapping[str, tuple[str, ...]]
    variables_by_window: Mapping[str, tuple[str, ...]]
    rows: Mapping[tuple[str, str], _SourceRow]


def _read_source_table(
    archive: ZipFile,
    *,
    prefix: str,
    value_kind: str,
    require_nonnegative: bool,
) -> _SourceTable:
    headers_by_window: dict[str, tuple[str, ...]] = {}
    variables_by_window: dict[str, tuple[str, ...]] = {}
    rows: dict[tuple[str, str], _SourceRow] = {}
    for member_name in sorted(archive.namelist()):
        if not member_name.startswith(prefix) or not member_name.endswith(".csv"):
            continue
        time_window = time_window_from_tw_filename(member_name)
        if time_window in headers_by_window:
            raise LandClimPublishedInventoryRefusal(
                f"LandClim {value_kind} members repeat {time_window}"
            )
        with archive.open(member_name) as handle:
            reader = csv.DictReader(TextIOWrapper(handle, encoding="utf-8"))
            headers, variables = _published_headers(reader.fieldnames, member_name)
            headers_by_window[time_window] = headers
            variables_by_window[time_window] = variables
            for source_row, row in enumerate(reader, start=2):
                _require_exact_tokens(row, headers, member_name=member_name)
                cell_id, longitude, latitude = _published_identity(
                    row, member_name=member_name
                )
                key = (time_window, cell_id)
                if key in rows:
                    raise LandClimPublishedInventoryRefusal(
                        f"LandClim {value_kind} rows repeat {key}"
                    )
                parsed = _required_numeric_mapping(
                    row,
                    variables=variables,
                    dataset_id="937075",
                    record_id=f"{cell_id}:{time_window}",
                    value_kind=value_kind,
                    require_nonnegative=require_nonnegative,
                )
                rows[key] = _SourceRow(
                    member_name=member_name,
                    source_row=source_row,
                    cell_id=cell_id,
                    cell_id_token=_required_token(row, "LCGRID_ID", member_name),
                    longitude_token=_required_token(row, "lonDD", member_name),
                    latitude_token=_required_token(row, "latDD", member_name),
                    longitude_float=longitude,
                    latitude_float=latitude,
                    value_tokens=tuple(
                        _required_token(row, variable, member_name)
                        for variable in variables
                    ),
                    parsed_values=parsed,
                )
    return _SourceTable(headers_by_window, variables_by_window, rows)


def _required_token(row: Mapping[str, object], field: str, member_name: str) -> str:
    value = row.get(field)
    if type(value) is not str or value == "":
        raise LandClimPublishedInventoryRefusal(
            f"LandClim source token is missing: {member_name}: {field}"
        )
    return value


def _require_existing_standard_error_parser(
    source: _SourceTable, parsed: _LandClimIIStandardErrors
) -> None:
    if parsed.headers_by_window != source.headers_by_window:
        raise LandClimPublishedInventoryRefusal(
            "LandClim standard-error source disagrees with the existing parser"
        )
    if set(parsed.rows) != set(source.rows):
        raise LandClimPublishedInventoryRefusal(
            "LandClim standard-error row universe disagrees with the existing parser"
        )
    for key, source_row in source.rows.items():
        parsed_row = parsed.rows[key]
        if (
            parsed_row.longitude != source_row.longitude_float
            or parsed_row.latitude != source_row.latitude_float
            or parsed_row.values != source_row.parsed_values
        ):
            raise LandClimPublishedInventoryRefusal(
                f"LandClim standard-error row disagrees with existing parser: {key}"
            )
