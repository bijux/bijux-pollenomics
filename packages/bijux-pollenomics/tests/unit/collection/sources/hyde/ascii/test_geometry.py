"""Source grid arithmetic stays separate from CRS and country admission."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.hyde.ascii.contracts import (
    AsciiWindowSelection,
    NativeAsciiHeader,
    NativeAsciiWindow,
)
from bijux_pollenomics.collection.sources.hyde.ascii.geometry import (
    native_axis_geometry,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal


def _window(*, step: str = "0.0833333") -> NativeAsciiWindow:
    selection = AsciiWindowSelection(
        archive_path="original/base/2000AD_lu.zip",
        member_index=0,
        expected_member_name="cropland2000AD.asc",
        row_start=216,
        row_stop=218,
        column_start=2208,
        column_stop=2210,
        native_labels=(
            ("scenario", "base"),
            ("time", "2000AD"),
            ("variable", "cropland"),
        ),
    )
    header = NativeAsciiHeader(
        bytes_base64="",
        tokens=(
            ("ncols", "4320"),
            ("nrows", "2160"),
            ("xllcorner", "-180"),
            ("yllcorner", "-90"),
            ("cellsize", step),
            ("NODATA_value", "-9999"),
        ),
        rows=2160,
        columns=4320,
    )
    return NativeAsciiWindow(
        Path("retained-window"),
        "a" * 64,
        "b" * 64,
        "c" * 64,
        selection,
        header,
        ("-9999", "0", "0.25", "0.5"),
        (True, False, False, False),
    )


def test_native_edges_preserve_truncated_source_step_without_crs_admission() -> None:
    result = native_axis_geometry(_window(), archive_sha256="d" * 64)
    assert result["source_axis_edges"] == {
        "global_west": "-180",
        "global_south": "-90",
        "global_east": "179.9998560",
        "global_north": "89.9999280",
        "window_west": "3.9999264",
        "window_east": "4.1665930",
        "window_south": "71.8332686",
        "window_north": "71.9999352",
        "step": "0.0833333",
        "row_order": "north_to_south",
    }
    assert (
        result["selected_cells"],
        result["selected_missing"],
        result["selected_zero"],
    ) == (4, 1, 1)
    assert result["native_labels"] == {
        "scenario": "base",
        "time": "2000AD",
        "variable": "cropland",
    }
    assert result["coordinate_reference_system"] is None
    assert result["calendar_support"] is None
    assert result["country_projection"] == "not_performed"
    assert result["public_release_allowed"] is False


@pytest.mark.parametrize("step", ["0", "NaN", "invalid"])
def test_bad_native_step_is_refused(step: str) -> None:
    with pytest.raises(IntakeRefusal):
        native_axis_geometry(_window(step=step), archive_sha256="d" * 64)


def test_missing_cell_or_invalid_archive_identity_is_refused() -> None:
    window = _window()
    with pytest.raises(IntakeRefusal):
        native_axis_geometry(window, archive_sha256="not-a-digest")
    incomplete = NativeAsciiWindow(
        window.directory,
        window.manifest_sha256,
        window.custody_manifest_sha256,
        window.member_sha256,
        window.selection,
        window.header,
        window.source_tokens[:-1],
        window.missing_mask[:-1],
    )
    with pytest.raises(IntakeRefusal):
        native_axis_geometry(incomplete, archive_sha256="d" * 64)
