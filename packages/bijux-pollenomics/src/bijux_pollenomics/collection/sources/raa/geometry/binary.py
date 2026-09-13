"""Bounded 2D standard GP/WKB decoding; no topology or coordinate repair."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math
import struct

from .models import GeometryRefusal

TYPE_CODES = {"POINT": 1, "LINESTRING": 2, "POLYGON": 3, "MULTIPOLYGON": 6}


@dataclass
class _Shape:
    points: int = 0
    rings: int = 0
    polygons: int = 0
    empty_polygons: int = 0
    zero_coordinates: int = 0
    bounds: tuple[float, float, float, float] | None = None

    def point(self, x: float, y: float) -> None:
        if not math.isfinite(x) or not math.isfinite(y):
            raise GeometryRefusal("nonfinite_coordinate")
        self.points += 1
        self.zero_coordinates += int(x == 0) + int(y == 0)
        if self.bounds is None:
            self.bounds = (x, x, y, y)
        else:
            a, b, c, d = self.bounds
            self.bounds = min(a, x), max(b, x), min(c, y), max(d, y)

    def merge(self, other: _Shape) -> None:
        self.points += other.points
        self.rings += other.rings
        self.polygons += other.polygons
        self.empty_polygons += other.empty_polygons
        self.zero_coordinates += other.zero_coordinates
        if other.bounds is not None:
            if self.bounds is None:
                self.bounds = other.bounds
            else:
                a, b, c, d = self.bounds
                e, f, g, h = other.bounds
                self.bounds = min(a, e), max(b, f), min(c, g), max(d, h)


class _Cursor:
    def __init__(self, data: bytes, offset: int) -> None:
        self.data = data
        self.offset = offset

    def take(self, size: int) -> bytes:
        if size > len(self.data) - self.offset:
            raise GeometryRefusal("truncated_wkb")
        start = self.offset
        self.offset += size
        return self.data[start : self.offset]

    def count(self, endian: str, minimum_bytes: int) -> int:
        count: int = struct.unpack(endian + "I", self.take(4))[0]
        if count > (len(self.data) - self.offset) // minimum_bytes:
            raise GeometryRefusal("declared_count_exceeds_remaining_bytes")
        return count


def _coordinates(
    cursor: _Cursor, endian: str, count: int, *, ring: bool = False
) -> _Shape:
    result = _Shape()
    first: tuple[float, float] | None = None
    last: tuple[float, float] | None = None
    for _ in range(count):
        x, y = struct.unpack(endian + "dd", cursor.take(16))
        result.point(x, y)
        if first is None:
            first = x, y
        last = x, y
    if ring and first != last:
        raise GeometryRefusal("polygon_ring_not_closed")
    return result


def _shape(cursor: _Cursor, expected: int) -> _Shape:
    byte_order = cursor.take(1)[0]
    if byte_order not in (0, 1):
        raise GeometryRefusal("invalid_wkb_byte_order")
    endian = "<" if byte_order else ">"
    code: int = struct.unpack(endian + "I", cursor.take(4))[0]
    if code not in TYPE_CODES.values():
        raise GeometryRefusal("unsupported_wkb_type_or_dimensions", unsupported=True)
    if code != expected:
        raise GeometryRefusal("declared_geometry_type_mismatch")
    result = _Shape()
    if code == 1:
        raw = cursor.take(16)
        empty = bytes.fromhex("000000000000f87f" if byte_order else "7ff8000000000000")
        if raw != empty + empty:
            x, y = struct.unpack(endian + "dd", raw)
            result.point(x, y)
        return result
    if code == 2:
        count = cursor.count(endian, 16)
        if count == 1:
            raise GeometryRefusal("linestring_requires_zero_or_multiple_points")
        return _coordinates(cursor, endian, count)
    if code == 3:
        count = cursor.count(endian, 4)
        result.polygons = 1
        result.empty_polygons = int(count == 0)
        for _ in range(count):
            points = cursor.count(endian, 16)
            if points < 4:
                raise GeometryRefusal("polygon_ring_requires_four_points")
            result.merge(_coordinates(cursor, endian, points, ring=True))
            result.rings += 1
        return result
    count = cursor.count(endian, 9)
    for _ in range(count):
        result.merge(_shape(cursor, 3))
    return result


def describe_geometry(
    value: object, *, geometry_type: str, srs_id: int = 3006
) -> dict[str, object]:
    """Account for one occurrence, preserving raw identity on every refusal."""
    if value is None:
        return {"status": "source_null", "reason_codes": ["source_null"]}
    if not isinstance(value, bytes):
        return {
            "status": "invalid",
            "reason_codes": ["non_blob_geometry"],
            "source_storage_type": type(value).__name__,
            "source_value": {"float_hex": value.hex()}
            if isinstance(value, float) and not math.isfinite(value)
            else value,
        }
    result: dict[str, object] = {
        "blob_sha256": sha256(value).hexdigest(),
        "blob_byte_count": len(value),
        "declared_geometry_type": geometry_type,
        "topology_validation": "not_evaluated",
    }
    try:
        if not isinstance(geometry_type, str) or geometry_type not in TYPE_CODES:
            raise GeometryRefusal(
                "unsupported_declared_geometry_type", unsupported=True
            )
        if len(value) < 8 or value[:3] != b"GP\x00":
            raise GeometryRefusal("invalid_geopackage_magic_version_or_length")
        flags = value[3]
        if flags & 0xC0:
            raise GeometryRefusal("reserved_geopackage_flags")
        if flags & 0x20:
            raise GeometryRefusal("extended_geopackage_binary", unsupported=True)
        envelope_code = (flags >> 1) & 7
        if envelope_code > 4:
            raise GeometryRefusal("invalid_envelope_code")
        if envelope_code not in (0, 1):
            raise GeometryRefusal("unsupported_envelope_dimensions", unsupported=True)
        endian = "<" if flags & 1 else ">"
        native_srs: int = struct.unpack(endian + "i", value[4:8])[0]
        empty_flag = bool(flags & 16)
        result.update(
            header_srs_id=native_srs, empty_flag=empty_flag, envelope_code=envelope_code
        )
        if native_srs != srs_id:
            raise GeometryRefusal("declared_crs_mismatch")
        offset = 8 + 32 * envelope_code
        if len(value) < offset + 5:
            raise GeometryRefusal("truncated_geometry_payload")
        envelope: tuple[float, ...] | None = None
        if envelope_code:
            if empty_flag:
                raise GeometryRefusal("empty_geometry_has_envelope")
            envelope = struct.unpack(endian + "dddd", value[8:40])
            if not all(math.isfinite(v) for v in envelope):
                raise GeometryRefusal("nonfinite_envelope")
            if envelope[0] > envelope[1] or envelope[2] > envelope[3]:
                raise GeometryRefusal("reversed_envelope")
            result["source_envelope_xy"] = list(envelope)
        cursor = _Cursor(value, offset)
        shape = _shape(cursor, TYPE_CODES[geometry_type])
        if cursor.offset != len(value):
            raise GeometryRefusal("trailing_geometry_bytes")
        if empty_flag != (shape.points == 0):
            raise GeometryRefusal("empty_flag_disagrees_with_wkb")
        if envelope is not None and envelope != shape.bounds:
            raise GeometryRefusal("envelope_disagrees_with_coordinate_extrema")
        result.update(
            status="structurally_valid_empty"
            if empty_flag
            else "structurally_valid_nonempty",
            reason_codes=[],
            coordinate_count=shape.points,
            ring_count=shape.rings,
            polygon_count=shape.polygons,
            empty_polygon_count=shape.empty_polygons,
            zero_coordinate_values=shape.zero_coordinates,
            coordinate_extrema_xy=list(shape.bounds)
            if shape.bounds is not None
            else None,
            envelope_check="matches_coordinate_extrema"
            if envelope is not None
            else "not_provided",
            transport_axis_order="x_easting_y_northing",
        )
    except GeometryRefusal as exc:
        result.update(status=exc.status, reason_codes=[exc.reason])
    return result
