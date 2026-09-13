"""Actual inspected source schema with explicitly synthetic small source rows."""

from pathlib import Path
import sqlite3

import pytest

from .support import A, blob

B = "00000000-0000-0000-0000-000000000002"
C = "00000000-0000-0000-0000-000000000003"
Z = "00000000-0000-0000-0000-000000000099"
SOURCE_SCHEMA = (
    'CREATE TABLE "egenskap" ( "fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "id" INTEGER, "lamning_uuid" TEXT, "ingaendelamning_id" INTEGER, "typ" TEXT(255), "varde" TEXT(255))',
    "CREATE TABLE gpkg_contents (table_name TEXT NOT NULL PRIMARY KEY,data_type TEXT NOT NULL,identifier TEXT UNIQUE,description TEXT DEFAULT '',last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),min_x DOUBLE, min_y DOUBLE,max_x DOUBLE, max_y DOUBLE,srs_id INTEGER,CONSTRAINT fk_gc_r_srs_id FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id))",
    "CREATE TABLE gpkg_geometry_columns (table_name TEXT NOT NULL,column_name TEXT NOT NULL,geometry_type_name TEXT NOT NULL,srs_id INTEGER NOT NULL,z TINYINT NOT NULL,m TINYINT NOT NULL,CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name),CONSTRAINT uk_gc_table_name UNIQUE (table_name),CONSTRAINT fk_gc_tn FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name),CONSTRAINT fk_gc_srs FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys (srs_id))",
    "CREATE TABLE gpkg_spatial_ref_sys (srs_name TEXT NOT NULL,srs_id INTEGER NOT NULL PRIMARY KEY,organization TEXT NOT NULL,organization_coordsys_id INTEGER NOT NULL,definition  TEXT NOT NULL,description TEXT)",
    'CREATE TABLE "ingaendelamning" ( "fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "id" INTEGER NOT NULL, "lamning_uuid" TEXT, "antal" MEDIUMINT NOT NULL, "lamningstyp" TEXT(255) NOT NULL)',
    'CREATE TABLE "lamning" ( "fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "uuid" TEXT, "lamningsnummer" TEXT(11), "raa_nummer" TEXT(300), "lamningstyp" TEXT(255), "url" TEXT, "beskrivning" TEXT, "publicerad_av" TEXT(255), "publiceringsdatum" DATETIME, "uttagsdatum" DATE, "antikvariskbedomning" TEXT(255), "antikvariskbedomning_motivering" TEXT, "aktualitetstatus" TEXT(255), "skadestatus" TEXT(255), "undersokningsstatus" TEXT(255), "placering" TEXT(255), "terrang" TEXT, "orientering" TEXT, "tradition" TEXT, "lamningsnamn" TEXT(300), "lan" TEXT, "kommun" TEXT, "socken" TEXT, "inspire_ruin" BOOLEAN)',
    'CREATE TABLE "linestring" ( "fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "geometri" LINESTRING NOT NULL, "lamning_uuid" TEXT, "geometrinummer" TEXT)',
    'CREATE TABLE "lämningar_sverige_lägesosäkerhet" ( "fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "geometri" MULTIPOLYGON, "lamning_uuid" TEXT, "lamningsnummer" TEXT(11), "inmatningskvalitet" TEXT(255), "definition_av_kvalitet" TEXT, "lagesosakerhet_i_meter" MEDIUMINT, "url" TEXT)',
    'CREATE TABLE "point" ( "fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "geometri" POINT NOT NULL, "lamning_uuid" TEXT, "geometrinummer" TEXT)',
    'CREATE TABLE "polygon" ( "fid" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "geometri" POLYGON NOT NULL, "lamning_uuid" TEXT, "geometrinummer" TEXT)',
)


@pytest.fixture
def database(tmp_path: Path) -> Path:
    directory = tmp_path / "raw"
    directory.mkdir()
    path = directory / "source.gpkg"
    with sqlite3.connect(path) as con:
        con.execute("PRAGMA application_id=1196444487")
        con.execute("PRAGMA user_version=10400")
        for statement in SOURCE_SCHEMA:
            con.execute(statement)
        con.execute(
            "INSERT INTO gpkg_spatial_ref_sys VALUES ('SWEREF99 TM',3006,'EPSG',3006,'source WKT',NULL)"
        )
        for name, kind in (
            ("point", "POINT"),
            ("linestring", "LINESTRING"),
            ("polygon", "POLYGON"),
            ("lämningar_sverige_lägesosäkerhet", "MULTIPOLYGON"),
        ):
            con.execute(
                "INSERT INTO gpkg_contents(table_name,data_type,identifier,srs_id) VALUES (?,'features',?,3006)",
                (name, name),
            )
            con.execute(
                "INSERT INTO gpkg_geometry_columns VALUES (?,'geometri',?,3006,0,0)",
                (name, kind),
            )
        for name in ("lamning", "ingaendelamning", "egenskap"):
            con.execute(
                "INSERT INTO gpkg_contents(table_name,data_type,identifier,srs_id) VALUES (?,'attributes',?,0)",
                (name, name),
            )
        for fid, key, label in ((1, A, "Å"), (2, B, ""), (3, C, "same-readable")):
            con.execute(
                "INSERT INTO lamning(fid,uuid,lamningsnummer,lamningsnamn,inspire_ruin) VALUES (?,?, 'L1',?,0)",
                (fid, key, label),
            )
        con.execute(
            "INSERT INTO ingaendelamning(fid,id,lamning_uuid,antal,lamningstyp) VALUES (1,10,?,0,'synthetic')",
            (A,),
        )
        con.execute(
            "INSERT INTO ingaendelamning(fid,id,lamning_uuid,antal,lamningstyp) VALUES (2,11,?,2,'synthetic')",
            (Z,),
        )
        for fid, owner, geometry in ((1, A, blob()), (3, C, blob(4326))):
            con.execute(
                "INSERT INTO point(fid,geometri,lamning_uuid) VALUES (?,?,?)",
                (fid, geometry, owner),
            )
        for name, owner in (
            ("polygon", A),
            ("linestring", Z),
            ("lämningar_sverige_lägesosäkerhet", A),
        ):
            con.execute(
                'INSERT INTO "' + name + '"(fid,geometri,lamning_uuid) VALUES (1,?,?)',
                (blob(), owner),
            )
        con.execute(
            'UPDATE "lämningar_sverige_lägesosäkerhet" SET lagesosakerhet_i_meter=0 WHERE fid=1'
        )
        con.execute(
            'INSERT INTO "lämningar_sverige_lägesosäkerhet"(fid,geometri,lamning_uuid) VALUES (2,NULL,?)',
            (B,),
        )
        for fid, parent, child, value in (
            (1, A, None, ""),
            (2, None, 10, "Rund"),
            (3, None, 999, None),
            (4, None, None, "0"),
            (5, A, 10, None),
        ):
            con.execute(
                "INSERT INTO egenskap(fid,id,lamning_uuid,ingaendelamning_id,typ,varde) VALUES (?,?,?,?, 'Form',?)",
                (fid, fid, parent, child, value),
            )
    return path
