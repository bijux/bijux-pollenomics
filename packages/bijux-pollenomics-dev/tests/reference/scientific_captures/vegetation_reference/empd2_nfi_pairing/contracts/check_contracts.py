"""Exercise source, metadata-only access and refusal boundaries on synthetic artifacts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from typing import Any
import unittest
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    FIELDS,
    GAPS,
    INPUTS,
    LOCATION_FIELDS,
    PACKAGE_ROOTS,
    PUBLIC_FIELDS,
    SOURCE,
    csv_wire,
    exact,
    finite,
    load,
    namespace,
    output_root,
    pin,
    public_projection,
    union,
)
from metadata import (
    NS,
    authorizer,
    expected_rows,
    nfi_metadata,
    validate_products,
)
from run import accounted_receipt


class Guards(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = tempfile.TemporaryDirectory(dir=SOURCE / "preflight")
        self.root = Path(self.storage.name)

    def tearDown(self) -> None:
        self.storage.cleanup()

    def workbook(
        self,
        *,
        bad_header: bool = False,
        duplicate: bool = False,
        nonfinite: bool = False,
    ) -> Path:
        strings = ["Year", "TractID", "PlotID", "Inventory_Date", "Easting", "Northing"]
        if bad_header:
            strings[0] = "TREE_OUTCOME"
        shared = (
            '<sst xmlns="'
            + NS[1:-1]
            + '">'
            + "".join("<si><t>" + x + "</t></si>" for x in strings)
            + "</sst>"
        )
        header = (
            '<row r="1">'
            + "".join(
                (f'<c r="{c}1" t="s"><v>{i}</v></c>' for i, c in enumerate("ABCDEF"))
            )
            + "</row>"
        )

        def row(index: int) -> str:
            vals = [
                "2020",
                "tract",
                "plot",
                "native-date",
                "nan" if nonfinite else "500000",
                "7000000",
            ]
            return (
                f'<row r="{index}">'
                + "".join(
                    (
                        f'<c r="{c}{index}"><v>{v}</v></c>'
                        for c, v in zip("ABCDEF", vals, strict=True)
                    )
                )
                + f'<c r="G{index}" t="s"><v>999999</v></c></row>'
            )

        body = (
            '<worksheet xmlns="'
            + NS[1:-1]
            + '"><sheetData>'
            + header
            + row(2)
            + (row(3) if duplicate else "")
            + "</sheetData></worksheet>"
        )
        path = self.root / "controlled.xlsx"
        with ZipFile(path, "w") as archive:
            archive.writestr("xl/sharedStrings.xml", shared)
            archive.writestr("xl/worksheets/sheet2.xml", body)
        return path

    def test_full_four_package_source_roots_match_real_repository_layout(self) -> None:
        self.assertEqual(
            [p.parent.name for p in PACKAGE_ROOTS],
            [
                "bijux-pollenomics",
                "bijux-pollenomics-dev",
                "bijux-pollenomics-lra",
                "pollenomics",
            ],
        )
        self.assertTrue(all(p.is_dir() and not p.is_symlink() for p in PACKAGE_ROOTS))

    def test_workbook_selects_six_columns_and_never_decodes_outcome_sentinel(
        self,
    ) -> None:
        rows, scope = nfi_metadata(self.workbook())
        self.assertEqual(
            rows, [("2020", "tract", "plot", "native-date", 500000.0, 7000000.0)]
        )
        self.assertEqual(scope["outcome_columns_decoded"], 0)
        self.assertEqual(scope["selected_cells"], 12)

    def test_workbook_header_refuses(self) -> None:
        with self.assertRaises(ValueError):
            nfi_metadata(self.workbook(bad_header=True))

    def test_workbook_duplicate_native_identity_refuses(self) -> None:
        with self.assertRaises(ValueError):
            nfi_metadata(self.workbook(duplicate=True))

    def test_workbook_nonfinite_coordinate_refuses(self) -> None:
        with self.assertRaises(ValueError):
            nfi_metadata(self.workbook(nonfinite=True))

    def database(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.root / "synthetic.sqlite3")
        db.execute(
            "CREATE TABLE metadata(samplename TEXT, agebp REAL, vegdescription TEXT)"
        )
        db.execute("INSERT INTO metadata VALUES('sample',0,'SEALED')")
        db.execute("CREATE TABLE counts(value REAL)")
        db.execute("INSERT INTO counts VALUES(1)")
        db.commit()
        db.set_authorizer(authorizer)
        return db

    def test_SQL_metadata_native_fields_allowed(self) -> None:
        db = self.database()
        try:
            self.assertEqual(
                db.execute("SELECT samplename,agebp FROM metadata").fetchall(),
                [("sample", 0.0)],
            )
        finally:
            db.close()

    def test_SQL_tree_description_refused(self) -> None:
        db = self.database()
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                db.execute("SELECT vegdescription FROM metadata").fetchall()
        finally:
            db.close()

    def test_SQL_pollen_count_table_refused(self) -> None:
        db = self.database()
        try:
            with self.assertRaises(sqlite3.DatabaseError):
                db.execute("SELECT value FROM counts").fetchall()
        finally:
            db.close()

    def test_SQL_write_and_attach_refused(self) -> None:
        db = self.database()
        try:
            for text in (
                "UPDATE metadata SET agebp=1",
                "ATTACH ':memory:' AS extra",
                "PRAGMA table_info(counts)",
            ):
                with self.assertRaises(sqlite3.DatabaseError):
                    db.execute(text)
        finally:
            db.close()

    def source_rows(self) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for index in range(16):
            row: dict[str, object] = dict.fromkeys(FIELDS, "refused")
            row.update(
                candidate_id=f"private:{index}",
                empd2_sample=f"sample{index}",
                nfi_tract="PRIVATE_TRACT",
                nfi_plot=f"PRIVATE_PLOT{index}",
                nfi_year="2020",
                nfi_inventory_date_source_native="PRIVATE_DATE",
                nfi_easting_sweref99tm=500000.0,
                nfi_northing_sweref99tm=7000000.0,
                nfi_longitude_wgs84=15.0,
                nfi_latitude_wgs84=63.0,
                nfi_source_sha256=INPUTS["workbook"][1],
                empd2_source_agebp=None,
                empd2_source_age_code=None,
                source_identity_status="unresolved" if index < 5 else "not_established",
                empd2_collection_time_status="source_note_requires_review"
                if index == 0
                else "not_authenticated_from_source_fields",
                scientific_admission="false",
                current_benchmark_decision="refused_missing_pair_evidence",
            )
            rows.append(row)
        return rows

    def test_public_projection_excludes_exact_private_fields(self) -> None:
        rows = self.source_rows()
        public = public_projection(rows)
        self.assertTrue(all(LOCATION_FIELDS.isdisjoint(row) for row in public))
        self.assertNotIn(b"PRIVATE_", csv_wire(public, PUBLIC_FIELDS))
        self.assertEqual(len({r["candidate_id"] for r in public}), 16)

    def test_public_native_identity_hash_is_source_bound(self) -> None:
        rows = self.source_rows()
        public = public_projection(rows)
        row = rows[0]
        token = hashlib.sha256(
            json.dumps(
                {
                    "nfi_source_sha256": INPUTS["workbook"][1],
                    "row": [row[k] for k in sorted(LOCATION_FIELDS)],
                },
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        self.assertEqual(public[0]["nfi_row_identity_sha256"], token)
        changed = copy.deepcopy(rows)
        changed[0]["nfi_year"] = "2021"
        self.assertNotEqual(
            public_projection(changed)[0]["candidate_id"], public[0]["candidate_id"]
        )

    def test_public_duplicate_identity_refused(self) -> None:
        rows = self.source_rows()
        with self.assertRaises(ValueError):
            public_projection([rows[0], rows[0]])

    def products(self) -> tuple[Path, list[dict[str, object]], dict[str, Any]]:
        output = self.root / "producer"
        output.mkdir()
        rows = self.source_rows()
        public = csv_wire(public_projection(rows), PUBLIC_FIELDS)
        (output / "pairs-source-bound.csv").write_bytes(csv_wire(rows, FIELDS))
        (output / "pairs.csv").write_bytes(public)
        tracked: dict[str, Any] = {
            "denominators": {
                "measured_pairs_admitted": 0,
                "distinct_selected_nfi_plot_years": 16,
            },
            "missing_or_unreviewed_fields_all_pairs": list(GAPS),
            "pair_specific_extra_gaps": {
                "cross_source_identity_unresolved": 5,
                "collection_note_requires_review": 1,
            },
            "pairs_csv": {
                "bytes": len(public),
                "sha256": hashlib.sha256(public).hexdigest(),
            },
        }
        (output / "report.json").write_text(json.dumps(tracked))
        return (output, rows, tracked)

    def test_complete_source_public_report_contract(self) -> None:
        output, rows, tracked = self.products()
        self.assertEqual(validate_products(output, rows, tracked)["refusals"], 16)

    def test_source_bound_row_tamper_refused(self) -> None:
        output, rows, tracked = self.products()
        p = output / "pairs-source-bound.csv"
        p.write_bytes(p.read_bytes().replace(b"PRIVATE_DATE", b"OTHER_DATE"))
        with self.assertRaises(ValueError):
            validate_products(output, rows, tracked)

    def test_self_consistent_public_hash_cannot_hide_semantic_tamper(self) -> None:
        output, rows, tracked = self.products()
        p = output / "pairs.csv"
        p.write_bytes(
            p.read_bytes().replace(b"refused_missing_pair_evidence", b"accepted")
        )
        value = copy.deepcopy(tracked)
        value["pairs_csv"] = {"bytes": p.stat().st_size, "sha256": pin(p)["sha256"]}
        (output / "report.json").write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            validate_products(output, rows, tracked)

    def test_zero_admission_cannot_be_boolean(self) -> None:
        output, rows, tracked = self.products()
        value = copy.deepcopy(tracked)
        value["denominators"]["measured_pairs_admitted"] = False
        (output / "report.json").write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            validate_products(output, rows, tracked)

    def test_unexpected_report_semantics_refused(self) -> None:
        output, rows, tracked = self.products()
        value = copy.deepcopy(tracked)
        value["new_scientific_acceptance"] = True
        (output / "report.json").write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            validate_products(output, rows, tracked)

    def test_geodesic_bound_and_raw_date_are_not_relaxed(self) -> None:
        item = {
            "spatial_lead": {
                "pollen_sample": "s",
                "nfi_tract": "t",
                "nfi_plot": "p",
                "nfi_year": "2020",
                "nfi_inventory_date_source_native": "native",
                "distance_m_wgs84": 1.0,
                "pollen_review_reason_codes": [],
            },
            "source_metadata_excluding_vegdescription": {
                "longitude": 15.0,
                "latitude": 63.0,
                "agebp": None,
                "ageuncertainty": None,
            },
            "collection_time_status": "not_authenticated_from_source_fields",
        }

        class Transform:
            def transform(self, x: float, y: float) -> tuple[float, float]:
                return (15.0, 63.0)

        class Geod:
            def __init__(self, distance: float) -> None:
                self.distance = distance

            def inv(self, *args: float) -> tuple[float, float, float]:
                return (0.0, 0.0, self.distance)

        nfi = [("2020", "t", "p", "native", 1.0, 2.0)]
        self.assertEqual(
            len(expected_rows([item], nfi, Transform(), Geod(1.000001))), 1
        )
        with self.assertRaises(ValueError):
            expected_rows([item], nfi, Transform(), Geod(1.0001))
        with self.assertRaises(ValueError):
            expected_rows(
                [item], [("2020", "t", "p", "other", 1.0, 2.0)], Transform(), Geod(1.0)
            )

    def test_exact_types_null_zero_and_nonfinite_refusals(self) -> None:
        self.assertFalse(exact(None, 0))
        self.assertFalse(exact(False, 0))
        self.assertFalse(exact(1, 1.0))
        for value in (True, "1", float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                finite(value)

    def test_original_pin_conflict_refuses(self) -> None:
        p = self.root / "input"
        p.write_bytes(b"a")
        row = pin(p)
        self.assertEqual(union([row], [row]), [row])
        p.write_bytes(b"b")
        with self.assertRaises(ValueError):
            union([row], [pin(p)])

    def test_duplicate_or_nonfinite_JSON_refuses(self) -> None:
        p = self.root / "input.json"
        for value in ('{"a":1,"a":2}', '{"a":NaN}'):
            p.write_text(value)
            with self.assertRaises(ValueError):
                load(p)

    def test_output_ancestor_alias_refuses(self) -> None:
        link = self.root / "alias"
        link.symlink_to(self.root)
        with self.assertRaises(ValueError):
            output_root(link / "future", absent=True)

    def test_inclusive_receipt_resource_accounting(self) -> None:
        (self.root / "bytes").write_bytes(b"a" * 20)
        raw = accounted_receipt(self.root, {"actual_exit": 0}, 2048)
        value = json.loads(raw)
        self.assertEqual(
            value["completed_output_bytes_including_receipt"], 20 + len(raw)
        )
        with self.assertRaises(ValueError):
            accounted_receipt(self.root, {"actual_exit": 0}, 10)

    def test_actual_controller_namespace_refuses_special_member(self) -> None:
        path = SOURCE / "unlisted-controlled.py"
        try:
            path.write_text('raise RuntimeError("never imported")')
            with self.assertRaises(ValueError):
                namespace()
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
