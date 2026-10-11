"""Explicit tiny source-profile databases and independently assembled WKB bytes."""

from __future__ import annotations

from pathlib import Path
import sqlite3
import struct

from pyproj import CRS

from bijux_pollenomics.collection.sources.raa.materialization.contracts import (
    GEOMETRY_TYPES,
    SOURCE_COLUMNS,
)
from bijux_pollenomics.collection.sources.raa.materialization.reading import (
    quote_identifier,
)

from ..materialization.support import A, identity

__all__ = [
    "A",
    "identity",
    "database",
    "add_geometry",
    "gpkg",
    "point",
    "line",
    "polygon",
    "multi",
]


def point(x: float = 0, y: float = 0, endian: str = "<") -> bytes:
    return struct.pack(endian + "BIdd", int(endian == "<"), 1, x, y)


def line(points: list[tuple[float, float]], endian: str = "<") -> bytes:
    return struct.pack(endian + "BII", int(endian == "<"), 2, len(points)) + b"".join(
        struct.pack(endian + "dd", *p) for p in points
    )


def polygon(rings: list[list[tuple[float, float]]], endian: str = "<") -> bytes:
    return struct.pack(endian + "BII", int(endian == "<"), 3, len(rings)) + b"".join(
        struct.pack(endian + "I", len(ring))
        + b"".join(struct.pack(endian + "dd", *p) for p in ring)
        for ring in rings
    )


def multi(polygons: list[bytes], endian: str = "<") -> bytes:
    return struct.pack(endian + "BII", int(endian == "<"), 6, len(polygons)) + b"".join(
        polygons
    )


def gpkg(
    body: bytes,
    *,
    endian: str = "<",
    empty: bool = False,
    envelope: tuple[float, float, float, float] | None = None,
    srs: int = 3006,
) -> bytes:
    flags = (
        int(endian == "<") | (16 if empty else 0) | (2 if envelope is not None else 0)
    )
    return (
        b"GP\x00"
        + bytes([flags])
        + struct.pack(endian + "i", srs)
        + (struct.pack(endian + "dddd", *envelope) if envelope is not None else b"")
        + body
    )


def database(root: Path) -> Path:
    raw = root / "raw"
    raw.mkdir()
    path = raw / "source.gpkg"
    with sqlite3.connect(path) as con:
        con.execute("PRAGMA application_id=1196444487")
        con.execute("PRAGMA user_version=10400")
        con.execute(
            "CREATE TABLE gpkg_contents(table_name TEXT,data_type TEXT,srs_id INTEGER)"
        )
        con.execute(
            "CREATE TABLE gpkg_geometry_columns(table_name TEXT,column_name TEXT,geometry_type_name TEXT,srs_id INTEGER,z INTEGER,m INTEGER)"
        )
        con.execute(
            "CREATE TABLE gpkg_spatial_ref_sys(srs_id INTEGER,organization TEXT,organization_coordsys_id INTEGER,definition TEXT)"
        )
        con.execute(
            "INSERT INTO gpkg_spatial_ref_sys VALUES(3006,'EPSG',3006,?)",
            (CRS.from_epsg(3006).to_wkt(),),
        )
        for name, columns in SOURCE_COLUMNS.items():
            fields = ['"fid" INTEGER PRIMARY KEY'] + [
                quote_identifier(n) for n in columns[1:]
            ]
            con.execute(f"CREATE TABLE {quote_identifier(name)} ({','.join(fields)})")
            geometry = name in GEOMETRY_TYPES
            con.execute(
                "INSERT INTO gpkg_contents VALUES(?,?,?)",
                (
                    name,
                    "features" if geometry else "attributes",
                    3006 if geometry else 0,
                ),
            )
            if geometry:
                con.execute(
                    "INSERT INTO gpkg_geometry_columns VALUES(?,'geometri',?,3006,0,0)",
                    (name, GEOMETRY_TYPES[name]),
                )
        con.execute("INSERT INTO lamning(fid,uuid) VALUES(1,?)", (A,))
    return path


def add_geometry(path: Path, table: str, value: object, *, fid: int = 1) -> None:
    with sqlite3.connect(path) as con:
        con.execute(
            f"INSERT INTO {quote_identifier(table)} (fid,geometri,lamning_uuid) VALUES(?,?,?)",
            (fid, value, A),
        )
