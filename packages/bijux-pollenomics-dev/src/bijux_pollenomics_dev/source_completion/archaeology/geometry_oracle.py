"""Independent NumPy traversal of standard XY GeoPackage/WKB coordinate blocks."""

from __future__ import annotations

import math
import struct
from typing import Literal

import numpy as np
from numpy.typing import NDArray


def coordinate_summary(blob: bytes, expected_kind: str) -> dict[str, object]:
    """Check finite coordinate blocks, shape counts and envelope without the reader."""
    kinds = {"POINT": 1, "LINESTRING": 2, "POLYGON": 3, "MULTIPOLYGON": 6}
    if len(blob) < 8 or blob[:3] != b"GP\x00" or blob[3] & 0xE0:
        raise ValueError("independent_invalid_standard_geopackage_header")
    flags = blob[3]
    envelope_code = (flags >> 1) & 7
    if envelope_code not in (0, 1):
        raise ValueError("independent_unsupported_envelope_dimensions")
    header_order = "<" if flags & 1 else ">"
    if struct.unpack_from(header_order + "i", blob, 4)[0] != 3006:
        raise ValueError("independent_crs_mismatch")
    offset = 8 + envelope_code * 32
    if offset + 5 > len(blob):
        raise ValueError("independent_truncated_payload")
    arrays: list[NDArray[np.float64]] = []
    rings = polygons = empty_polygons = lines = 0

    def number(order: Literal["little", "big"]) -> int:
        nonlocal offset
        if offset + 4 > len(blob):
            raise ValueError("independent_truncated_count")
        count = int.from_bytes(blob[offset : offset + 4], order)
        offset += 4
        return count

    def coordinates(
        order: Literal["little", "big"], count: int, *, ring: bool = False
    ) -> None:
        nonlocal offset
        if count > (len(blob) - offset) // 16:
            raise ValueError("independent_truncated_coordinates")
        dtype = "<f8" if order == "little" else ">f8"
        values = np.frombuffer(
            blob, dtype=dtype, count=2 * count, offset=offset
        ).reshape(count, 2)
        offset += 16 * count
        if not np.isfinite(values).all():
            raise ValueError("independent_nonfinite_coordinates")
        if ring and (count < 4 or not np.array_equal(values[0], values[-1])):
            raise ValueError("independent_invalid_ring")
        if count:
            arrays.append(values)

    pending = [kinds[expected_kind]]
    while pending:
        expected = pending.pop()
        if offset + 5 > len(blob) or blob[offset] not in (0, 1):
            raise ValueError("independent_invalid_wkb_header")
        order: Literal["little", "big"] = "little" if blob[offset] else "big"
        offset += 1
        kind = number(order)
        if kind != expected or kind not in {1, 2, 3, 6}:
            raise ValueError("independent_wkb_type_or_dimension_mismatch")
        if kind == 1:
            canonical_empty = (
                bytes.fromhex(
                    "000000000000f87f" if order == "little" else "7ff8000000000000"
                )
                * 2
            )
            if blob[offset : offset + 16] == canonical_empty:
                offset += 16
            else:
                coordinates(order, 1)
        elif kind == 2:
            lines += 1
            count = number(order)
            if count == 1:
                raise ValueError("independent_invalid_linestring_count")
            coordinates(order, count)
        elif kind == 3:
            count = number(order)
            if count > (len(blob) - offset) // 4:
                raise ValueError("independent_truncated_rings")
            polygons += 1
            rings += count
            empty_polygons += int(count == 0)
            for _ in range(count):
                coordinates(order, number(order), ring=True)
        else:
            count = number(order)
            if count > (len(blob) - offset) // 9:
                raise ValueError("independent_truncated_polygons")
            pending.extend([3] * count)
    if offset != len(blob):
        raise ValueError("independent_trailing_wkb_bytes")
    points = sum(len(values) for values in arrays)
    if bool(flags & 16) != (points == 0) or (flags & 16 and envelope_code):
        raise ValueError("independent_empty_flag_or_envelope_mismatch")
    bounds: list[float] | None = None
    if arrays:
        bounds = [
            min(float(np.min(values[:, 0])) for values in arrays),
            max(float(np.max(values[:, 0])) for values in arrays),
            min(float(np.min(values[:, 1])) for values in arrays),
            max(float(np.max(values[:, 1])) for values in arrays),
        ]
    if envelope_code:
        envelope = list(struct.unpack_from(header_order + "dddd", blob, 8))
        if not all(math.isfinite(value) for value in envelope) or envelope != bounds:
            raise ValueError("independent_source_envelope_mismatch")
    return {
        "coordinate_count": points,
        "ring_count": rings,
        "polygon_count": polygons,
        "empty_polygon_count": empty_polygons,
        "linestring_component_count": lines,
        "zero_coordinate_values": sum(
            int(np.count_nonzero(values == 0)) for values in arrays
        ),
        "coordinate_extrema_xy": bounds,
    }
