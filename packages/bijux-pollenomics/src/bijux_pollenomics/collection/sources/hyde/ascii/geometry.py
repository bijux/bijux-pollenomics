"""Exact source-axis bounds for an authenticated HYDE ASCII window.

These coordinates preserve the native header arithmetic. They do not assign a
CRS, country, area, calendar year, unit, or scientific admission.
"""

from __future__ import annotations

from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    Inexact,
    InvalidOperation,
    Rounded,
    localcontext,
)
import re
from typing import Any, cast

from ...quarantine import IntakeRefusal
from .contracts import NativeAsciiWindow
from .reading import read_hyde_ascii_window


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


_MAX_AXIS_CHARACTERS = 4096


def _axis_precision(
    west: Decimal, south: Decimal, step: Decimal, maximum_index: int
) -> int:
    """Bound plain output and exact arithmetic before allocating expanded digits."""
    values = (west, south, step)
    smallest_exponent = min(
        0, *(cast(int, value.as_tuple().exponent) for value in values)
    )
    largest_adjusted = max(
        west.adjusted() if west else 0,
        south.adjusted() if south else 0,
        step.adjusted() + len(str(maximum_index)),
    )
    output_size = max(1, largest_adjusted + 1) + max(0, -smallest_exponent) + 2
    if output_size > _MAX_AXIS_CHARACTERS:
        raise IntakeRefusal(
            "hyde_native_axis_size_limit", "Expanded axis exceeds 4096 characters"
        )
    return max(1, largest_adjusted - smallest_exponent + 3)


def native_axis_geometry(
    window: NativeAsciiWindow, *, archive_sha256: str
) -> dict[str, Any]:
    """Return a compact source-index geometry and denial of geographic authority."""
    if (
        type(window) is not NativeAsciiWindow
        or not isinstance(archive_sha256, str)
        or not re.fullmatch(r"[0-9a-f]{64}", archive_sha256)
    ):
        raise IntakeRefusal(
            "hyde_native_axis_request_invalid", "Typed window/hash required"
        )
    owner = read_hyde_ascii_window(
        window.directory, expected_manifest_sha256=window.manifest_sha256
    )
    if owner != window or owner.archive_sha256 != archive_sha256:
        raise IntakeRefusal(
            "hyde_native_axis_archive_binding_mismatch",
            "Authenticated window owner differs",
        )
    window = owner
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
    precision = _axis_precision(west, south, step, max(header.rows, header.columns))
    context = Context(
        prec=precision,
        rounding=ROUND_HALF_EVEN,
        Emin=-8192,
        Emax=8192,
        traps=[Inexact, Rounded, InvalidOperation],
    )
    with localcontext(context):
        north = south + header.rows * step
        edges = {
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
        }
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
        "archive_sha256": owner.archive_sha256,
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
        "source_axis_edges": edges,
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
