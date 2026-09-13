"""Read-only SQLite boundary for finalized hash-bound RAÄ GeoPackages."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import sqlite3

from .contracts import GEOMETRY_TYPES, SOURCE_COLUMNS, inspect_database_identity


def _authorize(
    action: int,
    first: str | None,
    second: str | None,
    database: str | None,
    origin: str | None,
) -> int:
    del database
    if origin is not None:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_PRAGMA:
        allowed = {
            "application_id",
            "user_version",
            "table_info",
            "table_xinfo",
            "foreign_key_list",
            "quick_check",
        }
        if first not in allowed:
            return sqlite3.SQLITE_DENY
        if first in {"application_id", "user_version"} and second is not None:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    if action in {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ}:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and second not in {
        "load_extension",
        "writefile",
        "readfile",
    }:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


@contextmanager
def read_only_database(
    path: Path, *, expected_sha256: str, expected_byte_count: int
) -> Iterator[sqlite3.Connection]:
    """Read admitted base tables only; close and verify original bytes on exit."""
    identity = inspect_database_identity(
        path, expected_sha256=expected_sha256, expected_byte_count=expected_byte_count
    )
    connection = sqlite3.connect(
        identity.path.as_uri() + "?mode=ro&immutable=1", uri=True
    )
    try:
        connection.row_factory = sqlite3.Row
        # Builds without SQLite loadable-extension support omit this method.
        # SQL extension loading is also refused by the authorizer below.
        if hasattr(connection, "enable_load_extension"):
            connection.enable_load_extension(False)
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA trusted_schema=OFF")
        if tuple(connection.execute("PRAGMA query_only").fetchone()) != (1,) or tuple(
            connection.execute("PRAGMA trusted_schema").fetchone()
        ) != (0,):
            raise ValueError("RAÄ SQLite read-only guards are unavailable")
        connection.set_authorizer(_authorize)
        yield connection
    finally:
        connection.close()
        identity.verify_unchanged()


def quote_identifier(value: str) -> str:
    """Quote an inspected SQLite identifier without interpreting its contents."""
    return '"' + value.replace('"', '""') + '"'


def source_profile(connection: sqlite3.Connection) -> dict[str, object]:
    """Admit the inspected national profile, retaining unexecuted SQL objects."""
    application = connection.execute("PRAGMA application_id").fetchone()[0]
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    if (application, version) != (1196444487, 10400):
        raise ValueError("Unsupported RAÄ GeoPackage application/version")
    schema = [
        dict(row)
        for row in connection.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name"
        )
    ]
    tables = {row["name"]: row for row in schema if row["type"] == "table"}
    metadata_names = {
        "gpkg_contents",
        "gpkg_geometry_columns",
        "gpkg_spatial_ref_sys",
        "gpkg_extensions",
        "gpkg_ogr_contents",
        "gpkg_tile_matrix",
        "gpkg_tile_matrix_set",
    }
    required = {"gpkg_contents", "gpkg_geometry_columns", "gpkg_spatial_ref_sys"}
    if not (required | set(SOURCE_COLUMNS)) <= tables.keys():
        raise ValueError("RAÄ required source/metadata table is absent")
    indexes = {
        f"rtree_{name}_geometri{suffix}"
        for name in GEOMETRY_TYPES
        for suffix in ("", "_node", "_parent", "_rowid")
    }
    allowed = (
        set(SOURCE_COLUMNS)
        | metadata_names
        | indexes
        | {"sqlite_sequence", "sqlite_stat1", "sqlite_stat4"}
    )
    if tables.keys() - allowed:
        raise ValueError("RAÄ source profile has unaccounted tables")
    declarations: dict[str, object] = {}
    for name, item in tables.items():
        sql = item["sql"] or ""
        if "CREATE VIRTUAL TABLE" in sql.upper():
            if name not in {f"rtree_{key}_geometri" for key in GEOMETRY_TYPES}:
                raise ValueError("RAÄ unexpected virtual source table")
            declarations[name] = {"status": "virtual_table_not_executed"}
            continue
        columns = [
            dict(row)
            for row in connection.execute(
                f"PRAGMA table_xinfo({quote_identifier(name)})"
            )
        ]
        if name in SOURCE_COLUMNS and (
            tuple(row["name"] for row in columns) != SOURCE_COLUMNS[name]
            or columns[0]["name"] != "fid"
            or columns[0]["type"] != "INTEGER"
            or columns[0]["pk"] != 1
            or any(row["hidden"] for row in columns)
        ):
            raise ValueError("RAÄ source columns/row identity profile mismatch")
        declarations[name] = {
            "columns": columns,
            "foreign_keys": [
                dict(row)
                for row in connection.execute(
                    f"PRAGMA foreign_key_list({quote_identifier(name)})"
                )
            ],
            "row_count": connection.execute(
                f"SELECT count(*) FROM {quote_identifier(name)}"
            ).fetchone()[0],
        }
    metadata = {
        name: [
            dict(row)
            for row in connection.execute(
                f"SELECT * FROM {quote_identifier(name)} ORDER BY rowid"
            )
        ]
        for name in sorted(metadata_names & tables.keys())
    }
    expected_geometry = dict(GEOMETRY_TYPES)
    expected_geometry.update(
        {
            "lämningar_sverige_" + name: GEOMETRY_TYPES[name]
            for name in ("point", "linestring", "polygon")
            if any(
                row["type"] == "view" and row["name"] == "lämningar_sverige_" + name
                for row in schema
            )
        }
    )
    actual = metadata["gpkg_geometry_columns"]
    if len(actual) != len(expected_geometry) or {
        (
            row["table_name"],
            row["column_name"],
            row["geometry_type_name"],
            row["srs_id"],
            row["z"],
            row["m"],
        )
        for row in actual
    } != {
        (name, "geometri", kind, 3006, 0, 0) for name, kind in expected_geometry.items()
    }:
        raise ValueError("RAÄ geometry/CRS metadata profile mismatch")
    contents = metadata["gpkg_contents"]
    if len(contents) != len(SOURCE_COLUMNS) + len(expected_geometry) - len(
        GEOMETRY_TYPES
    ) or {(row["table_name"], row["data_type"], row["srs_id"]) for row in contents} != (
        {(name, "features", 3006) for name in expected_geometry}
        | {
            (name, "attributes", 0)
            for name in SOURCE_COLUMNS
            if name not in GEOMETRY_TYPES
        }
    ):
        raise ValueError("RAÄ source content inventory mismatch")
    if not any(
        row["srs_id"] == 3006
        and row["organization"] == "EPSG"
        and row["organization_coordsys_id"] == 3006
        for row in metadata["gpkg_spatial_ref_sys"]
    ):
        raise ValueError("RAÄ declared EPSG3006 reference is missing")
    if any(
        row["extension_name"] != "gpkg_rtree_index"
        or row["table_name"] not in GEOMETRY_TYPES
        or row["column_name"] != "geometri"
        for row in metadata.get("gpkg_extensions", [])
    ):
        raise ValueError("RAÄ unsupported GeoPackage extension")
    return {
        "application_id": application,
        "user_version": version,
        "sqlite_objects": schema,
        "tables": declarations,
        "metadata": metadata,
        "sql_views_executed": False,
    }
