"""Strict paired-row contracts for published LandClim II result CSVs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import csv
from dataclasses import dataclass
from io import TextIOWrapper
import math
from zipfile import ZipFile

from .....core.text import clean_optional_text
from ..catalog import (
    LANDCLIM_II_STANDARD_ERRORS_DIRECTORY,
    time_window_from_tw_filename,
)
from ..sites import parse_float
from .values import _required_numeric_mapping

_IDENTITY_HEADERS = ("LCGRID_ID", "lonDD", "latDD")


@dataclass(frozen=True)
class _LandClimIIPublishedRow:
    longitude: float | None
    latitude: float | None
    values: dict[str, float]


@dataclass(frozen=True)
class _LandClimIIStandardErrors:
    headers_by_window: dict[str, tuple[str, ...]]
    rows: dict[tuple[str, str], _LandClimIIPublishedRow]


def _published_headers(
    fieldnames: Sequence[str] | None, member_name: str
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    headers = tuple(fieldnames or ())
    if (
        not headers
        or any(not header for header in headers)
        or len(headers) != len(set(headers))
        or any(header not in headers for header in _IDENTITY_HEADERS)
    ):
        raise ValueError(
            f"LandClim II CSV headers are invalid: {member_name}: {headers}"
        )
    variables = tuple(header for header in headers if header not in _IDENTITY_HEADERS)
    if not variables:
        raise ValueError(f"LandClim II CSV has no value headers: {member_name}")
    return headers, variables


def _published_identity(
    row: Mapping[str, object], *, member_name: str
) -> tuple[str, float | None, float | None]:
    cell_id = clean_optional_text(row.get("LCGRID_ID"))
    longitude_token = clean_optional_text(row.get("lonDD"))
    latitude_token = clean_optional_text(row.get("latDD"))
    longitude = parse_float(longitude_token)
    latitude = parse_float(latitude_token)
    coordinates_are_published_missing = (
        longitude_token == "#N/A" and latitude_token == "#N/A"
    )
    coordinates_are_finite = (
        longitude is not None
        and latitude is not None
        and math.isfinite(longitude)
        and math.isfinite(latitude)
    )
    if not cell_id or not (coordinates_are_published_missing or coordinates_are_finite):
        raise ValueError(
            "LandClim II row identity is missing or invalid in "
            f"{member_name}: LCGRID_ID={cell_id!r}, "
            f"coordinates={(longitude_token, latitude_token)}"
        )
    return cell_id, longitude, latitude


def _require_exact_tokens(
    row: Mapping[str, object],
    headers: tuple[str, ...],
    *,
    member_name: str,
) -> None:
    if tuple(row) != headers:
        raise ValueError(
            "LandClim II row tokens do not match its headers in "
            f"{member_name}: headers={headers}, row_keys={tuple(row)}"
        )


def _read_landclim_ii_standard_errors(
    archive: ZipFile,
) -> _LandClimIIStandardErrors:
    headers_by_window: dict[str, tuple[str, ...]] = {}
    values: dict[tuple[str, str], _LandClimIIPublishedRow] = {}
    for member_name in sorted(archive.namelist()):
        if not member_name.startswith(
            LANDCLIM_II_STANDARD_ERRORS_DIRECTORY
        ) or not member_name.endswith(".csv"):
            continue
        time_window = time_window_from_tw_filename(member_name)
        with archive.open(member_name) as handle:
            reader = csv.DictReader(TextIOWrapper(handle, encoding="utf-8"))
            headers, variables = _published_headers(reader.fieldnames, member_name)
            if time_window in headers_by_window:
                raise ValueError(
                    "LandClim II standard errors repeat time window "
                    f"{time_window}: {member_name}"
                )
            headers_by_window[time_window] = headers
            for row in reader:
                _require_exact_tokens(row, headers, member_name=member_name)
                cell_id, longitude, latitude = _published_identity(
                    row, member_name=member_name
                )
                key = (time_window, cell_id)
                if key in values:
                    raise ValueError(
                        "LandClim II standard errors contain duplicate "
                        f"(TW, LCGRID_ID) row {key}"
                    )
                values[key] = _LandClimIIPublishedRow(
                    longitude=longitude,
                    latitude=latitude,
                    values=_required_numeric_mapping(
                        row,
                        variables=variables,
                        dataset_id="937075",
                        record_id=f"{cell_id}:{time_window}",
                        value_kind="standard-error",
                        require_nonnegative=True,
                    ),
                )
    return _LandClimIIStandardErrors(headers_by_window, values)


def _landclim_ii_standard_errors(
    archive: ZipFile,
) -> dict[tuple[str, str], dict[str, float]]:
    """Retain the established values-only helper for package-local callers."""
    published = _read_landclim_ii_standard_errors(archive)
    return {key: row.values for key, row in published.rows.items()}
