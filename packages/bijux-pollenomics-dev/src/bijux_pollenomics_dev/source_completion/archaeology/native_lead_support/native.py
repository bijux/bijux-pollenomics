"""Bound native GeoPackage fields and built-in indexed source reads."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from hashlib import sha256
import math
import re
import sqlite3

from pyproj import CRS

from bijux_pollenomics.collection.sources.raa.materialization.contracts import (
    GEOMETRY_TYPES,
    SOURCE_COLUMNS,
)
from bijux_pollenomics.collection.sources.raa.materialization.reading import (
    _authorize,
    quote_identifier,
)


def require(condition: bool, reason: str) -> None:
    """Refuse a violated native-source invariant."""
    if not condition:
        raise ValueError(reason)


def native(value: object) -> dict[str, object]:
    """Preserve bounded native values with their SQLite storage types."""
    if value is None:
        return {"sqlite_type": "null", "value": None}
    if isinstance(value, bytes):
        return {
            "sqlite_type": "blob",
            "sha256": sha256(value).hexdigest(),
            "bytes": len(value),
        }
    if type(value) is int:
        return {"sqlite_type": "integer", "value": value}
    if type(value) is float:
        return {
            "sqlite_type": "real",
            "value": value if math.isfinite(value) else None,
            "float_hex": value.hex(),
        }
    require(isinstance(value, str), "unsupported native SQLite storage type")
    require(
        len(str(value).encode()) <= 1048576, "finite native field byte limit exceeded"
    )
    return {"sqlite_type": "text", "value": value}


def inspect_local_schema(connection: sqlite3.Connection) -> dict[str, object]:
    """Validate the native GeoPackage tables, geometry profile and CRS."""
    require(
        connection.execute("PRAGMA application_id").fetchone()[0] == 1196444487,
        "GeoPackage application id differs",
    )
    require(
        connection.execute("PRAGMA user_version").fetchone()[0] == 10400,
        "GeoPackage version differs",
    )
    objects = [
        dict(r)
        for r in connection.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name"
        )
    ]
    tables = {r["name"]: r for r in objects if r["type"] == "table"}
    required = set(SOURCE_COLUMNS) | {
        "gpkg_geometry_columns",
        "gpkg_spatial_ref_sys",
        "gpkg_contents",
    }
    require(required <= tables.keys(), "required source base/metadata table absent")
    declarations: dict[str, object] = {}
    for name, expected in SOURCE_COLUMNS.items():
        sql = str(tables[name]["sql"])
        require("VIRTUAL" not in sql.upper(), "source data must be native base tables")
        columns = [
            dict(r)
            for r in connection.execute(f"PRAGMA table_xinfo({quote_identifier(name)})")
        ]
        require(
            tuple(r["name"] for r in columns) == expected
            and not any(r["hidden"] for r in columns),
            "native source field profile differs",
        )
        require(
            columns[0]["type"] == "INTEGER" and columns[0]["pk"] == 1,
            "native fid primary key differs",
        )
        declarations[name] = columns
    geometry = [
        dict(r) for r in connection.execute("SELECT * FROM gpkg_geometry_columns")
    ]
    for name, kind in GEOMETRY_TYPES.items():
        matches = [r for r in geometry if r["table_name"] == name]
        require(
            len(matches) == 1
            and matches[0]["column_name"] == "geometri"
            and matches[0]["geometry_type_name"] == kind
            and matches[0]["srs_id"] == 3006
            and matches[0]["z"] == 0
            and matches[0]["m"] == 0,
            "native geometry/CRS profile differs",
        )
    srs = [
        dict(r)
        for r in connection.execute(
            "SELECT * FROM gpkg_spatial_ref_sys WHERE srs_id=3006"
        )
    ]
    require(
        len(srs) == 1
        and srs[0]["organization"] == "EPSG"
        and srs[0]["organization_coordsys_id"] == 3006,
        "native CRS authority differs",
    )
    require(
        CRS.from_wkt(str(srs[0]["definition"])).equals(CRS.from_epsg(3006)),
        "native CRS WKT differs",
    )
    return {
        "sqlite_objects": objects,
        "source_columns": declarations,
        "geometry_columns": geometry,
        "srs_3006": srs,
        "national_row_counts": "not_requested",
        "views_executed": False,
    }


def allow_native_rtree_reads(connection: sqlite3.Connection) -> dict[str, int]:
    """Permit built-in read-connection preparation, retaining four write barriers.

    SQLite's built-in RTree xConnect compiles shadow INSERT/DELETE statements
    even for SELECT. Their preparation is distinct from executing a write.
    The finalized file remains opened mode=ro/immutable, query_only is already
    ON, and transaction/schema actions remain denied by the original policy.
    """
    names = {"rtree_" + name + "_geometri" for name in GEOMETRY_TYPES}
    for name in names:
        row = connection.execute(
            "SELECT type,sql FROM sqlite_schema WHERE name=?", (name,)
        ).fetchone()
        pattern = (
            r'CREATE\s+VIRTUAL\s+TABLE\s+"?'
            + re.escape(name)
            + r'"?\s+USING\s+rtree\s*\(\s*id\s*,\s*minx\s*,\s*maxx\s*,\s*miny\s*,\s*maxy\s*\)\s*;?'
        )
        require(
            row is not None
            and row[0] == "table"
            and isinstance(row[1], str)
            and re.fullmatch(pattern, row[1], flags=re.IGNORECASE) is not None,
            "exact built-in native RTree declaration required",
        )
    shadows = {
        name + suffix for name in names for suffix in ("_node", "_parent", "_rowid")
    }
    observed: Counter[str] = Counter()

    def authorize(
        action: int,
        first: str | None,
        second: str | None,
        database: str | None,
        origin: str | None,
    ) -> int:
        if (
            action in {sqlite3.SQLITE_INSERT, sqlite3.SQLITE_DELETE}
            and first in shadows
            and database == "main"
            and origin is None
        ):
            observed[str(action) + ":" + str(first)] += 1
            return sqlite3.SQLITE_OK
        return _authorize(action, first, second, database, origin)

    connection.set_authorizer(authorize)
    return observed


def indexed_rows(
    connection: sqlite3.Connection, table: str, uuid: str, limit: int
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Read bounded UUID-owned rows only through an indexed lookup."""
    column = "uuid" if table == "lamning" else "lamning_uuid"
    sql = f"SELECT * FROM {quote_identifier(table)} WHERE {quote_identifier(column)}=? ORDER BY fid LIMIT ?"
    details = [
        str(row[3])
        for row in connection.execute("EXPLAIN QUERY PLAN " + sql, (uuid, limit + 1))
    ]
    permitted = any(
        "SEARCH " + table in d and "INDEX" in d for d in details
    ) and not any("SCAN " + table in d for d in details)
    if not permitted:
        return [], {"status": "refused_missing_indexed_uuid_lookup", "plan": details}
    result = [dict(row) for row in connection.execute(sql, (uuid, limit + 1))]
    require(len(result) <= limit, "local native owner/child limit exceeded")
    return result, {
        "status": "indexed_native_rows",
        "plan": details,
        "rows": len(result),
    }


def candidates(
    connection: sqlite3.Connection,
    table: str,
    centre: tuple[float, float],
    radius: float,
    limit: int,
) -> Iterator[dict[str, object]]:
    """Yield bounded geometry candidates through the declared RTree index."""
    index = "rtree_" + table + "_geometri"
    row = connection.execute(
        "SELECT type,sql FROM sqlite_schema WHERE name=?", (index,)
    ).fetchone()
    require(
        row is not None and row[0] == "table" and "USING rtree" in row[1],
        "required native RTree index absent",
    )
    columns = [
        r[1]
        for r in connection.execute(f"PRAGMA table_info({quote_identifier(index)})")
    ]
    require(
        columns == ["id", "minx", "maxx", "miny", "maxy"], "native RTree columns differ"
    )
    x, y = centre
    sql = f"SELECT id,minx,maxx,miny,maxy FROM {quote_identifier(index)} WHERE maxx>=? AND minx<=? AND maxy>=? AND miny<=? ORDER BY id LIMIT ?"
    args = (x - radius, x + radius, y - radius, y + radius, limit + 1)
    plan = [str(r[3]) for r in connection.execute("EXPLAIN QUERY PLAN " + sql, args)]
    require(
        any("VIRTUAL TABLE INDEX" in p for p in plan), "RTree constraints not planned"
    )
    rows = connection.execute(sql, args)
    for count, indexed in enumerate(rows, start=1):
        require(count <= limit, "finite RTree candidate limit exceeded")
        fid = indexed["id"]
        require(type(fid) is int, "native RTree identity is not integer")
        selected = connection.execute(
            f"SELECT * FROM {quote_identifier(table)} WHERE fid=?", (fid,)
        ).fetchall()
        require(len(selected) == 1, "RTree reference has no unique native occurrence")
        yield {
            "source": dict(selected[0]),
            "index_envelope": list(indexed)[1:],
            "query_plan": plan,
        }
