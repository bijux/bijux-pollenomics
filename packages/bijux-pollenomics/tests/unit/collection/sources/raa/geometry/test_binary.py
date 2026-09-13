"""Hand-encoded structural counterexamples, preserving null/empty/zero distinctions."""

import math
import struct

import pytest

from bijux_pollenomics.collection.sources.raa.geometry.binary import describe_geometry
from bijux_pollenomics.collection.sources.raa.materialization.ownership import (
    canonical_bytes,
)

from .support import gpkg, line, multi, point, polygon

RING = [(0.0, 0.0), (4.0, 0.0), (4.0, 2.0), (0.0, 0.0)]


@pytest.mark.parametrize("header", ["<", ">"])
@pytest.mark.parametrize("body_order", ["<", ">"])
@pytest.mark.parametrize("kind", ["POINT", "LINESTRING", "POLYGON", "MULTIPOLYGON"])
def test_independent_endianness_and_extrema(
    header: str, body_order: str, kind: str
) -> None:
    bodies = {
        "POINT": point(4, 2, body_order),
        "LINESTRING": line(RING, body_order),
        "POLYGON": polygon([RING], body_order),
        "MULTIPOLYGON": multi([polygon([RING], body_order)], body_order),
    }
    envelope = (4.0, 4.0, 2.0, 2.0) if kind == "POINT" else (0.0, 4.0, 0.0, 2.0)
    result = describe_geometry(
        gpkg(bodies[kind], endian=header, envelope=envelope), geometry_type=kind
    )
    assert result["status"] == "structurally_valid_nonempty"
    assert result["coordinate_extrema_xy"] == list(envelope)
    assert result["topology_validation"] == "not_evaluated"
    assert result["transport_axis_order"] == "x_easting_y_northing"


@pytest.mark.parametrize("endian", ["<", ">"])
@pytest.mark.parametrize("kind", ["POINT", "LINESTRING", "POLYGON", "MULTIPOLYGON"])
def test_valid_empty(endian: str, kind: str) -> None:
    bodies = {
        "POINT": point(math.nan, math.nan, endian),
        "LINESTRING": line([], endian),
        "POLYGON": polygon([], endian),
        "MULTIPOLYGON": multi([], endian),
    }
    result = describe_geometry(gpkg(bodies[kind], empty=True), geometry_type=kind)
    assert result["status"] == "structurally_valid_empty"
    assert result["coordinate_extrema_xy"] is None
    assert result["coordinate_count"] == 0


def test_null_zero_and_nested_empty_are_distinct() -> None:
    assert describe_geometry(None, geometry_type="POINT")["status"] == "source_null"
    zero = describe_geometry(gpkg(point()), geometry_type="POINT")
    assert zero["status"] == "structurally_valid_nonempty"
    assert zero["zero_coordinate_values"] == 2
    mixed = describe_geometry(
        gpkg(multi([polygon([]), polygon([RING])])), geometry_type="MULTIPOLYGON"
    )
    assert mixed["status"] == "structurally_valid_nonempty"
    assert mixed["polygon_count"] == 2
    assert mixed["empty_polygon_count"] == 1


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_nonblob_nonfinite_real_preserved_finitely(value: float) -> None:
    result = describe_geometry(value, geometry_type="POINT")
    assert result["status"] == "invalid"
    assert result["source_value"] == {"float_hex": value.hex()}
    assert canonical_bytes(result)


@pytest.mark.parametrize(
    "raw,kind,reason",
    [
        (b"GP", "POINT", "invalid_geopackage_magic_version_or_length"),
        (gpkg(point(), srs=4326), "POINT", "declared_crs_mismatch"),
        (gpkg(point()) + b"x", "POINT", "trailing_geometry_bytes"),
        (gpkg(point(float("inf"), 1)), "POINT", "nonfinite_coordinate"),
        (gpkg(point(math.nan, 1), empty=True), "POINT", "nonfinite_coordinate"),
        (gpkg(point(), empty=True), "POINT", "empty_flag_disagrees_with_wkb"),
        (gpkg(point(math.nan, math.nan)), "POINT", "empty_flag_disagrees_with_wkb"),
        (
            gpkg(point(math.nan, math.nan), empty=True, envelope=(0, 0, 0, 0)),
            "POINT",
            "empty_geometry_has_envelope",
        ),
        (
            gpkg(point(1, 2), envelope=(0, 1, 0, 2)),
            "POINT",
            "envelope_disagrees_with_coordinate_extrema",
        ),
        (gpkg(point(), envelope=(1, 0, 0, 0)), "POINT", "reversed_envelope"),
        (gpkg(point(), envelope=(0, 0, 0, math.inf)), "POINT", "nonfinite_envelope"),
        (
            gpkg(line([(0, 0)])),
            "LINESTRING",
            "linestring_requires_zero_or_multiple_points",
        ),
        (gpkg(polygon([RING[:-1]])), "POLYGON", "polygon_ring_requires_four_points"),
        (gpkg(polygon([RING[:-1] + [(1, 1)]])), "POLYGON", "polygon_ring_not_closed"),
        (gpkg(multi([point()])), "MULTIPOLYGON", "declared_geometry_type_mismatch"),
        (
            gpkg(struct.pack("<BII", 1, 2, 2**32 - 1)),
            "LINESTRING",
            "declared_count_exceeds_remaining_bytes",
        ),
        (
            gpkg(struct.pack("<BII", 1, 6, 2**32 - 1)),
            "MULTIPOLYGON",
            "declared_count_exceeds_remaining_bytes",
        ),
        (
            gpkg(struct.pack("<BII", 1, 3, 2**32 - 1)),
            "POLYGON",
            "declared_count_exceeds_remaining_bytes",
        ),
        (
            gpkg(b"\x02" + struct.pack("<Idd", 1, 0, 0)),
            "POINT",
            "invalid_wkb_byte_order",
        ),
    ],
)
def test_invalid_structural_records(raw: bytes, kind: str, reason: str) -> None:
    result = describe_geometry(raw, geometry_type=kind)
    assert result["status"] == "invalid"
    assert result["reason_codes"] == [reason]
    assert result["blob_byte_count"] == len(raw)


@pytest.mark.parametrize(
    "bits", [0xFFF8000000000000, 0x7FF0000000000001, 0x7FF8000000000001]
)
def test_noncanonical_nan_is_not_an_empty_point(bits: int) -> None:
    raw = struct.pack("<BIQQ", 1, 1, bits, bits)
    result = describe_geometry(gpkg(raw, empty=True), geometry_type="POINT")
    assert result["reason_codes"] == ["nonfinite_coordinate"]


@pytest.mark.parametrize("code", range(2, 8))
def test_envelope_codes_separate_unsupported_dimensions_from_invalid(code: int) -> None:
    raw = bytearray(gpkg(point()))
    raw[3] = 1 | (code << 1)
    result = describe_geometry(bytes(raw), geometry_type="POINT")
    assert result["status"] == ("invalid" if code > 4 else "unsupported")


@pytest.mark.parametrize("code", [1001, 2001, 3001, 0x80000001, 0x20000001, 7, 99])
def test_other_types_and_extensions_are_refused(code: int) -> None:
    result = describe_geometry(
        gpkg(b"\x01" + struct.pack("<Idd", code, 0, 0)), geometry_type="POINT"
    )
    assert result["status"] == "unsupported"


def test_self_intersection_is_not_a_topology_claim() -> None:
    bow: list[tuple[float, float]] = [(0, 0), (1, 1), (0, 1), (1, 0), (0, 0)]
    result = describe_geometry(gpkg(polygon([bow])), geometry_type="POLYGON")
    assert result["status"] == "structurally_valid_nonempty"
    assert result["topology_validation"] == "not_evaluated"


@pytest.mark.parametrize(
    "flag,status", [(32, "unsupported"), (64, "invalid"), (128, "invalid")]
)
def test_extended_and_reserved_flags(flag: int, status: str) -> None:
    value = bytearray(gpkg(point()))
    value[3] |= flag
    assert describe_geometry(bytes(value), geometry_type="POINT")["status"] == status
