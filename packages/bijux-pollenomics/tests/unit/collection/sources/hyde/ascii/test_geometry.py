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
    tmp_path: Path,
    *,
    step: str = "0.0833333",
    rows: int = 2,
    columns: int = 3,
    west: str = "-180",
    south: str = "-90",
) -> NativeAsciiWindow:
    tmp_path.mkdir(parents=True, exist_ok=True)
    header = (
        f"ncols {columns}\nnrows {rows}\nxllcorner {west}\nyllcorner {south}\n"
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


def test_tiny_step_preserves_distinct_exact_edges(tmp_path: Path) -> None:
    result = _geometry(_window(tmp_path, step="1e-28"))["source_axis_edges"]
    assert result["global_east"] == "-179.9999999999999999999999999997"
    assert result["window_east"] == "-179.9999999999999999999999999998"
    assert result["global_north"] == "-89.9999999999999999999999999998"


def test_geometry_ignores_ambient_decimal_context(tmp_path: Path) -> None:
    from decimal import Inexact, localcontext

    window = _window(tmp_path)
    expected = _geometry(window)
    with localcontext() as ctx:
        ctx.prec = 3
        ctx.traps[Inexact] = True
        assert _geometry(window) == expected


@pytest.mark.parametrize("step", ["1e-1000000", "1e1000000"])
def test_extreme_axis_expansion_refuses_before_rendering(
    tmp_path: Path, step: str
) -> None:
    with pytest.raises(IntakeRefusal, match="hyde_native_axis_size_limit"):
        _geometry(_window(tmp_path, step=step))


def test_tiny_step_all_edges_are_exact_under_low_context(tmp_path: Path) -> None:
    from decimal import Inexact, localcontext

    window = _window(tmp_path, step="1e-28")
    with localcontext() as ctx:
        ctx.prec = 2
        ctx.traps[Inexact] = True
        edges = _geometry(window)["source_axis_edges"]
    assert edges == {
        "global_west": "-180",
        "global_south": "-90",
        "global_east": "-179.9999999999999999999999999997",
        "global_north": "-89.9999999999999999999999999998",
        "window_west": "-180.0000000000000000000000000000",
        "window_east": "-179.9999999999999999999999999998",
        "window_south": "-90.0000000000000000000000000000",
        "window_north": "-89.9999999999999999999999999998",
        "step": "0.0000000000000000000000000001",
        "row_order": "north_to_south",
    }


def test_axis_limit_near_boundary_and_index_carry(tmp_path: Path) -> None:
    small = _geometry(_window(tmp_path / "small", step="1e-4090"))["source_axis_edges"]
    assert len(small["global_east"]) == 4095
    assert small["global_east"].endswith("9997")
    with pytest.raises(IntakeRefusal, match="hyde_native_axis_size_limit"):
        _geometry(_window(tmp_path / "large", step="1e-4093"))
    carry = _geometry(_window(tmp_path / "carry", step="9.9", columns=12))[
        "source_axis_edges"
    ]
    assert carry["global_east"] == "-61.2"
    assert carry["window_east"] == "-160.2"
    assert carry["global_north"] == "-70.2"
    assert carry["window_south"] == "-90.0"


def test_extreme_zero_origin_spelling_has_bounded_semantics(tmp_path: Path) -> None:
    positive = _geometry(_window(tmp_path / "positive", west="0e1000000"))[
        "source_axis_edges"
    ]
    assert positive["global_west"] == "0"
    assert positive["global_east"] == "0.2499999"
    negative = _geometry(_window(tmp_path / "negative", west="-0e1000000"))[
        "source_axis_edges"
    ]
    assert negative["global_west"] == "-0"
    with pytest.raises(IntakeRefusal, match="hyde_native_axis_size_limit"):
        _geometry(_window(tmp_path / "fractional-zero", west="0e-1000000"))


@pytest.mark.parametrize(
    "west,south,step,rows,columns",
    [
        ("-180", "-90", "1e-28", 2, 3),
        ("-180", "-90", "9.9", 2, 12),
        ("-0.000001", "2.5", "0.0000003", 3, 4),
        ("999.999", "-0.002", "0.004", 2, 3),
    ],
)
def test_all_axis_edges_equal_independent_rational_arithmetic(
    tmp_path: Path, west: str, south: str, step: str, rows: int, columns: int
) -> None:
    from decimal import Inexact, localcontext
    from fractions import Fraction

    window = _window(
        tmp_path, west=west, south=south, step=step, rows=rows, columns=columns
    )
    with localcontext() as ctx:
        ctx.prec = 2
        ctx.Emin = -2
        ctx.Emax = 2
        ctx.traps[Inexact] = True
        edges = _geometry(window)["source_axis_edges"]
    x, y, size = Fraction(west), Fraction(south), Fraction(step)
    expected = {
        "global_west": x,
        "global_south": y,
        "global_east": x + columns * size,
        "global_north": y + rows * size,
        "window_west": x,
        "window_east": x + 2 * size,
        "window_south": y + (rows - 2) * size,
        "window_north": y + rows * size,
    }
    assert {key: Fraction(edges[key]) for key in expected} == expected
