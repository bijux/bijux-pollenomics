"""Independent structural controls and complete accepted/refused payload populations."""

from __future__ import annotations

import io
import json
import sqlite3
import struct
from typing import cast

import pytest

from bijux_pollenomics_dev.source_completion.archaeology import national_geometry
from bijux_pollenomics_dev.source_completion.archaeology.geometry_oracle import (
    coordinate_summary,
)

RING = [(0.0, 0.0), (4.0, 0.0), (4.0, 2.0), (0.0, 0.0)]


def wkb(kind: int, body: bytes, order: str = "<") -> bytes:
    return struct.pack(order + "BI", int(order == "<"), kind) + body


def coordinate_block(values: list[tuple[float, float]], order: str) -> bytes:
    return struct.pack(order + "I", len(values)) + b"".join(
        struct.pack(order + "dd", *xy) for xy in values
    )


def polygon(order: str = "<", *, empty: bool = False) -> bytes:
    return wkb(
        3,
        struct.pack(order + "I", 0 if empty else 1)
        + (b"" if empty else coordinate_block(RING, order)),
        order,
    )


def gpkg(
    body: bytes, order: str = "<", *, envelope: bool = False, empty: bool = False
) -> bytes:
    flags = int(order == "<") | (2 if envelope else 0) | (16 if empty else 0)
    return (
        b"GP\x00"
        + bytes([flags])
        + struct.pack(order + "i", 3006)
        + (struct.pack(order + "dddd", 0, 4, 0, 2) if envelope else b"")
        + body
    )


@pytest.mark.parametrize("header_order", ["<", ">"])
@pytest.mark.parametrize("body_order", ["<", ">"])
@pytest.mark.parametrize("kind", ["POINT", "LINESTRING", "POLYGON", "MULTIPOLYGON"])
def test_coordinate_oracle_uses_independent_orders_and_shape_counts(
    header_order: str, body_order: str, kind: str
) -> None:
    bodies = {
        "POINT": wkb(1, struct.pack(body_order + "dd", 4, 2), body_order),
        "LINESTRING": wkb(2, coordinate_block(RING, body_order), body_order),
        "POLYGON": polygon(body_order),
        "MULTIPOLYGON": wkb(
            6,
            struct.pack(body_order + "I", 2)
            + polygon(body_order, empty=True)
            + polygon(body_order),
            body_order,
        ),
    }
    summary = coordinate_summary(
        gpkg(bodies[kind], header_order, envelope=kind != "POINT"), kind
    )
    assert summary["coordinate_count"] == (1 if kind == "POINT" else 4)
    assert summary["coordinate_extrema_xy"] == (
        [4, 4, 2, 2] if kind == "POINT" else [0, 4, 0, 2]
    )
    assert summary["ring_count"] == int(kind in {"POLYGON", "MULTIPOLYGON"})
    assert summary["polygon_count"] == (
        2 if kind == "MULTIPOLYGON" else 1 if kind == "POLYGON" else 0
    )
    assert summary["empty_polygon_count"] == int(kind == "MULTIPOLYGON")
    assert summary["linestring_component_count"] == int(kind == "LINESTRING")
    assert summary["zero_coordinate_values"] == (0 if kind == "POINT" else 5)


def test_canonical_empty_point_and_numerical_zero_remain_distinct() -> None:
    empty = gpkg(wkb(1, bytes.fromhex("000000000000f87f") * 2), empty=True)
    assert coordinate_summary(empty, "POINT")["coordinate_count"] == 0
    zero = coordinate_summary(gpkg(wkb(1, struct.pack("<dd", 0, 0))), "POINT")
    assert zero["coordinate_count"] == 1
    assert zero["zero_coordinate_values"] == 2


def test_oracle_refuses_wrong_source_envelope_and_crs() -> None:
    with pytest.raises(ValueError, match="source_envelope_mismatch"):
        coordinate_summary(
            gpkg(wkb(1, struct.pack("<dd", 1, 1)), envelope=True), "POINT"
        )
    blob = bytearray(gpkg(wkb(1, struct.pack("<dd", 1, 1))))
    blob[4:8] = struct.pack("<i", 4326)
    with pytest.raises(ValueError, match="crs_mismatch"):
        coordinate_summary(bytes(blob), "POINT")


@pytest.mark.parametrize(
    "body,reason",
    [
        (wkb(1001, struct.pack("<ddd", 1, 2, 3)), "type_or_dimension"),
        (wkb(1, struct.pack("<dd", float("inf"), 1)), "nonfinite"),
        (wkb(2, coordinate_block([(1, 2)], "<")), "linestring_count"),
        (
            wkb(
                3,
                struct.pack("<I", 1)
                + coordinate_block([(0, 0), (1, 0), (1, 1), (0, 1)], "<"),
            ),
            "invalid_ring",
        ),
    ],
)
def test_oracle_refuses_dimensions_nonfinite_and_invalid_structure(
    body: bytes, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        coordinate_summary(
            gpkg(body),
            "POLYGON"
            if reason == "invalid_ring"
            else "LINESTRING"
            if reason == "linestring_count"
            else "POINT",
        )


def add_shapes(connection: sqlite3.Connection) -> None:
    connection.executemany(
        "INSERT INTO point(fid,geometri) VALUES(?,?)",
        [
            (3, gpkg(wkb(1, struct.pack("<dd", 0, 2)))),
            (4, b"bad"),
            (5, gpkg(wkb(1001, struct.pack("<ddd", 1, 2, 3)))),
        ],
    )
    connection.execute(
        "INSERT INTO linestring(fid,geometri) VALUES(1,?)",
        (gpkg(wkb(2, coordinate_block(RING, "<"))),),
    )
    connection.execute(
        "INSERT INTO polygon(fid,geometri) VALUES(1,?)",
        (gpkg(polygon(), envelope=True),),
    )
    connection.execute(
        'INSERT INTO "lämningar_sverige_lägesosäkerhet"(fid,geometri) VALUES(1,?)',
        (
            gpkg(
                wkb(6, struct.pack("<I", 2) + polygon(empty=True) + polygon()),
                envelope=True,
            ),
        ),
    )


def test_native_scan_accounts_for_all_roles_and_refusals(
    connection: sqlite3.Connection,
) -> None:
    add_shapes(connection)
    refused = io.StringIO()
    report = national_geometry.scan(connection, refused)
    summary = cast(dict[str, object], report["native_geometry_summary"])
    assert summary["geometry_occurrences"] == 8
    assert summary["status_counts"] == {
        "invalid": 1,
        "source_null": 2,
        "structurally_valid_nonempty": 4,
        "unsupported": 1,
    }
    assert report["independently_compared_geometry_occurrences"] == 4
    assert cast(dict[str, object], report["crs"])["status"] == "declared_crs_verified"
    witnesses = [json.loads(line) for line in refused.getvalue().splitlines()]
    assert len(witnesses) == 4
    assert {row["fid"] for row in witnesses} == {1, 2, 4, 5}
    assert all(row["mismatch"] is False for row in witnesses)
    roles = cast(dict[str, str], report["geometry_roles"])
    assert roles["point"] == "native_remains_geometry"
    assert roles["lämningar_sverige_lägesosäkerhet"] == "positional_uncertainty"


def test_independent_ring_count_mismatch_is_saved_and_fails(
    connection: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    connection.execute("DELETE FROM point")
    connection.execute(
        "INSERT INTO polygon(fid,geometri) VALUES(1,?)", (gpkg(polygon()),)
    )
    real = coordinate_summary

    def wrong_rings(blob: bytes, expected_kind: str) -> dict[str, object]:
        return {**real(blob, expected_kind), "ring_count": 0}

    monkeypatch.setattr(national_geometry, "coordinate_summary", wrong_rings)
    refused = io.StringIO()
    with pytest.raises(ValueError, match="coordinate or structure comparison differs"):
        national_geometry.scan(connection, refused)
    assert json.loads(refused.getvalue())["mismatch"] is True


def test_crs_refusal_and_witness_budget_do_not_erase_population(
    connection: sqlite3.Connection,
) -> None:
    add_shapes(connection)
    connection.execute("UPDATE gpkg_spatial_ref_sys SET definition='not WKT'")
    report = national_geometry.scan(connection, io.StringIO())
    assert cast(dict[str, object], report["crs"])["status"] == "refused"
    assert report["independently_compared_geometry_occurrences"] == 4
    with pytest.raises(ValueError, match="refusal output byte limit"):
        national_geometry.scan(connection, io.StringIO(), refusal_byte_limit=1)
