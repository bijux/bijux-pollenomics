"""Source grid arithmetic retains its independently authenticated archive owner."""

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.hyde.ascii import prepare_hyde_ascii_window
from bijux_pollenomics.collection.sources.hyde.ascii.contracts import NativeAsciiWindow
from bijux_pollenomics.collection.sources.hyde.ascii.geometry import (
    native_axis_geometry,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

from .test_preparation import fixture


def _window(
    tmp_path: Path, *, step: str = "0.0833333", rows: int = 2, columns: int = 3
) -> NativeAsciiWindow:
    header = (
        f"ncols {columns}\nnrows {rows}\nxllcorner -180\nyllcorner -90\n"
        f"cellsize {step}\nNODATA_value -9999\n"
    )
    body = []
    for row in range(rows):
        tokens = ["0"] * columns
        if row == 0:
            tokens[:3] = ["-9999", "0", "0.25"]
        elif row == 1:
            tokens[:3] = ["0.5", "0.75", "1"]
        body.append(" ".join(tokens))
    source, custody, selection = fixture(
        tmp_path, (header + "\n".join(body) + "\n").encode()
    )
    return prepare_hyde_ascii_window(
        custody.directory,
        expected_custody_manifest_sha256=custody.manifest_sha256,
        source_root=source,
        selection=replace(selection, column_stop=2),
        destination=tmp_path / "window",
    )


def _geometry(window: NativeAsciiWindow) -> dict[str, Any]:
    assert window.archive_sha256 is not None
    return native_axis_geometry(window, archive_sha256=window.archive_sha256)


def test_native_edges_preserve_truncated_source_step_without_crs_admission(
    tmp_path: Path,
) -> None:
    result = _geometry(_window(tmp_path))
    assert result["source_axis_edges"] == {
        "global_west": "-180",
        "global_south": "-90",
        "global_east": "-179.7500001",
        "global_north": "-89.8333334",
        "window_west": "-180.0000000",
        "window_east": "-179.8333334",
        "window_south": "-90.0000000",
        "window_north": "-89.8333334",
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


@pytest.mark.parametrize(
    "rows,columns,edge,expected",
    [
        (2, 4320, "global_east", "179.9998560"),
        (2160, 3, "global_north", "89.9999280"),
    ],
)
def test_global_axis_truncation_is_preserved_by_bounded_generated_sources(
    tmp_path: Path, rows: int, columns: int, edge: str, expected: str
) -> None:
    result = _geometry(_window(tmp_path, rows=rows, columns=columns))
    assert result["source_axis_edges"][edge] == expected


@pytest.mark.parametrize("step", ["0", "NaN", "invalid"])
def test_bad_native_step_is_refused(tmp_path: Path, step: str) -> None:
    with pytest.raises(IntakeRefusal):
        _geometry(_window(tmp_path, step=step))


def test_missing_cell_or_invalid_archive_identity_is_refused(tmp_path: Path) -> None:
    window = _window(tmp_path)
    with pytest.raises(IntakeRefusal):
        native_axis_geometry(window, archive_sha256="not-a-digest")
    incomplete = replace(
        window,
        source_tokens=window.source_tokens[:-1],
        missing_mask=window.missing_mask[:-1],
    )
    with pytest.raises(IntakeRefusal):
        _geometry(incomplete)


def test_valid_digest_from_another_archive_is_refused(tmp_path: Path) -> None:
    window = _window(tmp_path)
    assert window.archive_sha256 != "0" * 64
    with pytest.raises(IntakeRefusal, match="archive_binding_mismatch"):
        native_axis_geometry(window, archive_sha256="0" * 64)


def test_geometry_reauthenticates_the_retained_window_owner(tmp_path: Path) -> None:
    window = _window(tmp_path)
    path = window.directory / "window.json"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(IntakeRefusal):
        _geometry(window)


def test_detached_typed_window_has_no_archive_authority(tmp_path: Path) -> None:
    window = _window(tmp_path)
    detached = replace(window, directory=tmp_path / "absent")
    with pytest.raises(IntakeRefusal):
        _geometry(detached)
