"""Finite SQLite and geometry refusal controls; no national input is opened."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import struct
import tempfile
from typing import cast
import unittest

from bijux_pollenomics.collection.sources.raa.geometry.binary import describe_geometry
from bijux_pollenomics.collection.sources.raa.materialization.contracts import (
    GEOMETRY_TYPES,
    SOURCE_COLUMNS,
)
from bijux_pollenomics.collection.sources.raa.materialization.reading import (
    quote_identifier,
    read_only_database,
)
from bijux_pollenomics_dev.source_completion.archaeology.native_lead_support.geometry import (
    envelope_distances,
    support_class,
)
from bijux_pollenomics_dev.source_completion.archaeology.native_lead_support.native import (
    allow_native_rtree_reads,
    candidates,
    indexed_rows,
    inspect_local_schema,
    native,
)

ROOT = Path(__file__).resolve().parents[6]
A = ROOT / "artifacts/tests/raa-native-support"


class LocalSupport(unittest.TestCase):
    def setUp(self) -> None:
        A.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=A)
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "fixture.gpkg"
        connection = sqlite3.connect(self.path)
        for table, columns in SOURCE_COLUMNS.items():
            fields = [
                quote_identifier(n)
                + (
                    " INTEGER PRIMARY KEY"
                    if n == "fid"
                    else " BLOB"
                    if n == "geometri"
                    else " TEXT"
                )
                for n in columns
            ]
            connection.execute(
                f"CREATE TABLE {quote_identifier(table)}({','.join(fields)})"
            )
        connection.execute("CREATE INDEX lamning_uuid ON lamning(uuid)")
        connection.execute("CREATE INDEX egenskap_owner ON egenskap(lamning_uuid)")
        for table in GEOMETRY_TYPES:
            connection.execute(
                f"CREATE VIRTUAL TABLE {quote_identifier('rtree_' + table + '_geometri')} USING rtree(id,minx,maxx,miny,maxy)"
            )
        from pyproj import CRS

        connection.execute("PRAGMA application_id=1196444487")
        connection.execute("PRAGMA user_version=10400")
        connection.execute("CREATE TABLE gpkg_contents(table_name TEXT)")
        connection.execute(
            "CREATE TABLE gpkg_geometry_columns(table_name TEXT,column_name TEXT,geometry_type_name TEXT,srs_id INTEGER,z INTEGER,m INTEGER)"
        )
        connection.execute(
            "CREATE TABLE gpkg_spatial_ref_sys(srs_id INTEGER,organization TEXT,organization_coordsys_id INTEGER,definition TEXT)"
        )
        connection.execute(
            "INSERT INTO gpkg_spatial_ref_sys VALUES(3006,'EPSG',3006,?)",
            (CRS.from_epsg(3006).to_wkt(),),
        )
        for table, kind in GEOMETRY_TYPES.items():
            connection.execute(
                "INSERT INTO gpkg_geometry_columns VALUES(?, 'geometri', ?,3006,0,0)",
                (table, kind),
            )
        self.point = (
            b"GP\x00\x01"
            + struct.pack("<i", 3006)
            + struct.pack("<BIdd", 1, 1, 100.0, 200.0)
        )
        connection.execute(
            "INSERT INTO point VALUES(1,?,'native-uuid','1')", (self.point,)
        )
        connection.execute("INSERT INTO rtree_point_geometri VALUES(1,100,100,200,200)")
        connection.execute(
            "INSERT INTO lamning(fid,uuid,publiceringsdatum,beskrivning) VALUES(1,'native-uuid','2026-09-12','Järnålder; record date is not event age')"
        )
        connection.commit()
        connection.close()
        self.digest = sha256(self.path.read_bytes()).hexdigest()
        self.size = self.path.stat().st_size

    def test_source_schema_and_crs_without_national_counts(self) -> None:
        with read_only_database(
            self.path, expected_sha256=self.digest, expected_byte_count=self.size
        ) as c:
            profile = inspect_local_schema(c)
            self.assertEqual(profile["national_row_counts"], "not_requested")
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        c.execute(
            "UPDATE gpkg_geometry_columns SET srs_id=4326 WHERE table_name='point'"
        )
        with self.assertRaisesRegex(ValueError, "geometry/CRS profile differs"):
            inspect_local_schema(c)
        c.close()

    def test_fifth_lead_remains_coordinate_refusal(self) -> None:
        leads = json.loads(
            (
                ROOT / "reports/science/archaeology-native-lead-support/protocol.json"
            ).read_bytes()
        )["lead_population"]
        self.assertEqual(len(leads), 5)
        self.assertEqual(sum(row["latitude"] is not None for row in leads), 4)
        self.assertEqual(leads[-1]["lead_id"], "uppakra-lund")
        self.assertIsNone(leads[-1]["latitude"])
        self.assertEqual(
            leads[-1]["coordinate_status"], "refused_physical_study_object_unresolved"
        )

    def test_exact_point_and_closed_boundary(self) -> None:
        description = describe_geometry(self.point, geometry_type="POINT")
        self.assertEqual(
            description["coordinate_extrema_xy"], [100.0, 100.0, 200.0, 200.0]
        )
        lower, upper = envelope_distances([100, 100, 200, 200], (100, 190))
        self.assertEqual((lower, upper), (10.0, 10.0))
        self.assertEqual(
            support_class(lower, upper, 10, point=True), "point_within_projected_circle"
        )
        self.assertEqual(
            support_class(lower, upper, 9, point=True), "point_outside_projected_circle"
        )

    def test_envelope_overlap_never_means_exact_polygon_intersection(self) -> None:
        low, high = envelope_distances([-10, 10, -10, 10], (0, 0))
        self.assertEqual(low, 0)
        self.assertEqual(
            support_class(low, high, 1, point=False),
            "ambiguous_envelope_overlap_not_exact_shape_intersection",
        )
        self.assertEqual(
            support_class(low, high, 20, point=False),
            "entire_envelope_within_projected_circle",
        )

    def test_indexed_candidate_and_uuid_selection(self) -> None:
        with read_only_database(
            self.path, expected_sha256=self.digest, expected_byte_count=self.size
        ) as c:
            allow_native_rtree_reads(c)
            selected = list(candidates(c, "point", (100, 200), 5, 5))
            self.assertEqual(len(selected), 1)
            self.assertEqual(
                cast(dict[str, object], selected[0]["source"])["lamning_uuid"],
                "native-uuid",
            )
            rows, status = indexed_rows(c, "lamning", "native-uuid", 5)
            self.assertEqual(status["status"], "indexed_native_rows")
            self.assertEqual(rows[0]["publiceringsdatum"], "2026-09-12")
            self.assertIn("Järnålder", str(rows[0]["beskrivning"]))

    def test_unindexed_child_lookup_refuses_without_scanning(self) -> None:
        with read_only_database(
            self.path, expected_sha256=self.digest, expected_byte_count=self.size
        ) as c:
            rows, status = indexed_rows(c, "ingaendelamning", "native-uuid", 5)
            self.assertEqual(rows, [])
            self.assertEqual(status["status"], "refused_missing_indexed_uuid_lookup")

    def test_missing_rtree_refuses(self) -> None:
        c = sqlite3.connect(self.path)
        c.execute("DROP TABLE rtree_point_geometri")
        with self.assertRaisesRegex(ValueError, "RTree index absent"):
            list(candidates(c, "point", (100, 200), 5, 5))
        c.close()

    def test_rtree_adapter_preserves_all_write_and_runtime_guards(self) -> None:
        with read_only_database(
            self.path, expected_sha256=self.digest, expected_byte_count=self.size
        ) as c:
            observed = allow_native_rtree_reads(c)
            list(candidates(c, "point", (100, 200), 5, 5))
            self.assertTrue(observed)
            c.isolation_level = None
            controls = [
                "DELETE FROM lamning",
                "DELETE FROM rtree_point_geometri_node",
                "INSERT INTO rtree_point_geometri_node VALUES(99,zeroblob(1228))",
                "CREATE TEMP TABLE unauthorized(value)",
                "ATTACH ':memory:' AS unauthorized",
                "SELECT load_extension('untrusted')",
                "PRAGMA query_only=OFF",
                "PRAGMA trusted_schema=ON",
            ]
            for sql in controls:
                with self.subTest(sql=sql), self.assertRaises(sqlite3.DatabaseError):
                    c.execute(sql)

    def test_original_source_identity_mismatch_refuses(self) -> None:
        with (
            self.assertRaisesRegex(ValueError, "SHA256"),
            read_only_database(
                self.path, expected_sha256="0" * 64, expected_byte_count=self.size
            ),
        ):
            self.fail("changed source accepted")

    def test_bad_geometry_and_native_null_types_preserved(self) -> None:
        self.assertEqual(
            describe_geometry(b"bad", geometry_type="POINT")["status"], "invalid"
        )
        self.assertEqual(native(None), {"sqlite_type": "null", "value": None})
        self.assertEqual(
            native("Järnålder"), {"sqlite_type": "text", "value": "Järnålder"}
        )
        self.assertEqual(native(1)["sqlite_type"], "integer")
        self.assertEqual(native(1.0)["sqlite_type"], "real")


if __name__ == "__main__":
    unittest.main(verbosity=2)
