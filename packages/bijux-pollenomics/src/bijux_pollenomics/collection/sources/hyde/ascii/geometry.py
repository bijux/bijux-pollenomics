"""Exact source-axis bounds for an authenticated HYDE ASCII window.

These coordinates preserve the native header arithmetic. They do not assign a
CRS, country, area, calendar year, unit, or scientific admission.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Any

from ...quarantine import IntakeRefusal
from .contracts import NativeAsciiWindow


def _number(token: str, name: str) -> Decimal:
    try:
        number = Decimal(token)
    except InvalidOperation as exc:
        raise IntakeRefusal("hyde_native_axis_number_invalid", name) from exc
    if not number.is_finite():
        raise IntakeRefusal("hyde_native_axis_number_invalid", name)
    return number


def _plain(number: Decimal) -> str:
    return format(number, "f")


def native_axis_geometry(
    window: NativeAsciiWindow, *, archive_sha256: str
) -> dict[str, Any]:
    """Return a compact source-index geometry and denial of geographic authority."""
    if not isinstance(window, NativeAsciiWindow) or not re.fullmatch(
        r"[0-9a-f]{64}", archive_sha256
    ):
        raise IntakeRefusal(
            "hyde_native_axis_request_invalid", "Typed window/hash required"
        )
    selection, header = window.selection, window.header
    if (
        selection.row_stop > header.rows
        or selection.column_stop > header.columns
        or len(window.source_tokens)
        != (selection.row_stop - selection.row_start)
        * (selection.column_stop - selection.column_start)
        or len(window.missing_mask) != len(window.source_tokens)
    ):
        raise IntakeRefusal(
            "hyde_native_axis_window_invalid", "Source dimensions disagree"
        )
    step = _number(header.value("cellsize"), "cellsize")
    west = _number(header.value("xllcorner"), "xllcorner")
    south = _number(header.value("yllcorner"), "yllcorner")
    if step <= 0:
        raise IntakeRefusal("hyde_native_axis_step_invalid", "cellsize")
    north = south + header.rows * step
    values = [
        _number(token, "source cell")
        for token, missing in zip(
            window.source_tokens, window.missing_mask, strict=True
        )
        if not missing
    ]
    return {
        "schema_version": "hyde-native-axis-geometry.v1",
        "window_manifest_sha256": window.manifest_sha256,
        "custody_manifest_sha256": window.custody_manifest_sha256,
        "archive_path": selection.archive_path,
        "archive_sha256": archive_sha256,
        "archive_member_index": selection.member_index,
        "archive_member_name": selection.expected_member_name,
        "member_sha256": window.member_sha256,
        "native_labels": dict(selection.native_labels),
        "source_header_tokens": dict(header.tokens),
        "source_rows": header.rows,
        "source_columns": header.columns,
        "selected_source_indices": {
            "row_start": selection.row_start,
            "row_stop": selection.row_stop,
            "column_start": selection.column_start,
            "column_stop": selection.column_stop,
        },
        "source_axis_edges": {
            "global_west": _plain(west),
            "global_south": _plain(south),
            "global_east": _plain(west + header.columns * step),
            "global_north": _plain(north),
            "window_west": _plain(west + selection.column_start * step),
            "window_east": _plain(west + selection.column_stop * step),
            "window_south": _plain(north - selection.row_stop * step),
            "window_north": _plain(north - selection.row_start * step),
            "step": _plain(step),
            "row_order": "north_to_south",
        },
        "selected_cells": len(window.source_tokens),
        "selected_missing": sum(window.missing_mask),
        "selected_nonmissing": len(values),
        "selected_zero": sum(value == 0 for value in values),
        "coordinate_reference_system": None,
        "variable_units": None,
        "calendar_support": None,
        "country_projection": "not_performed",
        "scientific_acceptance": "not_evaluated",
        "public_release_allowed": False,
    }
