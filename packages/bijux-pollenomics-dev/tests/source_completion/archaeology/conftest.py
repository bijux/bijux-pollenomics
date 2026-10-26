"""Shared exact native-table fixture for national RAÄ source consumers."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
import sqlite3

from pyproj import CRS
import pytest

from bijux_pollenomics.collection.sources.raa.materialization.contracts import (
    GEOMETRY_TYPES,
    SOURCE_COLUMNS,
)
from bijux_pollenomics.collection.sources.raa.materialization.reading import (
    quote_identifier,
)

UUID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def connection(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    c = sqlite3.connect(tmp_path / "native.gpkg")
    c.row_factory = sqlite3.Row
    for table, columns in SOURCE_COLUMNS.items():
        fields = []
        for name in columns:
            kind = (
                "INTEGER PRIMARY KEY"
                if name == "fid"
                else "BLOB"
                if name == "geometri"
                else "INTEGER"
                if name in {"id", "ingaendelamning_id", "antal"}
                else "TEXT"
            )
            fields.append(quote_identifier(name) + " " + kind)
        c.execute(f"CREATE TABLE {quote_identifier(table)}({','.join(fields)})")
    c.execute("PRAGMA application_id=1196444487")
    c.execute("PRAGMA user_version=10400")
    c.execute(
        "CREATE TABLE gpkg_contents(table_name TEXT,data_type TEXT,srs_id INTEGER)"
    )
    c.execute(
        "CREATE TABLE gpkg_geometry_columns(table_name TEXT,column_name TEXT,geometry_type_name TEXT,srs_id INTEGER,z INTEGER,m INTEGER)"
    )
    c.execute(
        "CREATE TABLE gpkg_spatial_ref_sys(srs_id INTEGER,organization TEXT,organization_coordsys_id INTEGER,definition TEXT)"
    )
    c.execute(
        "INSERT INTO gpkg_spatial_ref_sys VALUES(3006,'EPSG',3006,?)",
        (CRS.from_epsg(3006).to_wkt(),),
    )
    for table in SOURCE_COLUMNS:
        c.execute(
            "INSERT INTO gpkg_contents VALUES(?,?,?)",
            (
                table,
                "features" if table in GEOMETRY_TYPES else "attributes",
                3006 if table in GEOMETRY_TYPES else 0,
            ),
        )
    for table, kind in GEOMETRY_TYPES.items():
        c.execute(
            "INSERT INTO gpkg_geometry_columns VALUES(?,'geometri',?,3006,0,0)",
            (table, kind),
        )
    c.executemany(
        "INSERT INTO lamning(fid,uuid,antikvariskbedomning,skadestatus) VALUES(?,?,?,?)",
        [
            (1, UUID, "Fornlämning", None),
            (2, UUID, "Möjlig fornlämning", ""),
            (3, None, None, ""),
        ],
    )
    c.executemany(
        "INSERT INTO ingaendelamning(fid,id,lamning_uuid,antal) VALUES(?,?,?,?)",
        [(1, 9, UUID, 0), (2, 9, UUID, None)],
    )
    c.execute(
        "INSERT INTO egenskap(fid,ingaendelamning_id,typ,varde) VALUES(1,9,'Datering','Järnålder')"
    )
    c.executemany(
        "INSERT INTO point(fid,lamning_uuid) VALUES(?,?)",
        [(1, UUID), (2, "00000000-0000-0000-0000-000000000002")],
    )
    yield c
    c.close()
