"""Exercise only synthetic collection, native-type, membership and source custody boundaries."""

from __future__ import annotations

import ast
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from census import record, summarize, tagged
from contracts import (
    SOURCE,
    exact,
    frozen_pin_union,
    pin,
    source_namespace,
    verify_frozen_pins,
)
from observe import independently_validate, native, validate_census_claims
from scanner import CollectionScanner
from stream import Collection, Cursor


class Guards(unittest.TestCase):
    def setUp(self) -> None:
        self.storage = tempfile.TemporaryDirectory(dir=SOURCE / "preflight")
        self.root = Path(self.storage.name)

    def tearDown(self) -> None:
        self.storage.cleanup()

    def source(self, body: bytes) -> Path:
        path = self.root / "source.geojson"
        path.write_bytes(body)
        return path

    def feature(self, key: str = "one") -> dict[str, object]:
        return {
            "type": "Feature",
            "properties": {
                "record_id": key,
                "area_km2": 0,
                "date": None,
                "unit": "unqualified",
                "country": "Sweden",
            },
            "geometry": {"type": "Point", "coordinates": [0, 1]},
        }

    def wire(self, features: list[object]) -> bytes:
        return json.dumps(
            {"type": "FeatureCollection", "features": features},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode()

    def test_both_parsers_preserve_order_hashes_and_complete_wrapper(self) -> None:
        path = self.source(self.wire([self.feature("a"), self.feature("b")]))
        left = Collection(path, block=7)
        right = CollectionScanner(path, block=7)
        self.assertEqual(list(left.features()), list(right.features()))
        self.assertTrue(left.document_complete and right.document_complete)
        self.assertEqual(left.metadata, right.metadata)
        self.assertEqual(left.total_feature_bytes, right.total_feature_bytes)

    def test_all_chunk_boundaries_of_numbers_and_unicode(self) -> None:
        raw = b'{"type":"FeatureCollection","scale":123.45e-6,"features":[{"name":"\\u00f6-\xc3\xb6","features":[1,2.0,-1e2]}]}'
        path = self.source(raw)
        expected = json.loads(raw, parse_float=Decimal)
        for block in range(1, 31):
            with self.subTest(block=block):
                for parser in (Collection, CollectionScanner):
                    reader = parser(path, block=block)
                    rows = list(reader.features())
                    self.assertEqual(rows[0][1], expected["features"][0])
                    self.assertEqual(reader.metadata["scale"], expected["scale"])

    def test_quoted_features_delimiters_and_escapes_are_not_structure(self) -> None:
        raw = b'{"label":"features [{]} \\"","type":"FeatureCollection","features":[{"text":"[}\\\\\\"","nested":{"features":[]}}]}'
        path = self.source(raw)
        self.assertEqual(
            list(Collection(path, block=2).features()),
            list(CollectionScanner(path, block=2).features()),
        )

    def test_invalid_duplicate_nonfinite_and_trailing_documents_refuse(self) -> None:
        samples = [
            b'{"type":"FeatureCollection","features":[],"features":[]}',
            b'{"type":"FeatureCollection","features":[{"a":1,"a":2}]}',
            b'{"type":"FeatureCollection","features":[NaN]}',
            b'{"type":"FeatureCollection","features":[1,]}',
            b'{"type":"FeatureCollection","features":[],}',
            b'{"type":"FeatureCollection","features":[]} false',
            b'{"type":"FeatureCollection","features":[1e]}',
            b'{"type":"FeatureCollection","features":["unterminated]}',
            b'{"features":[]}',
            b'{"type":"Other","features":[]}',
        ]
        for raw in samples:
            for parser in (Collection, CollectionScanner):
                with (
                    self.subTest(raw=raw, parser=parser),
                    self.assertRaises((ValueError, UnicodeError)),
                ):
                    list(parser(self.source(raw), block=3).features())

    def test_bounded_single_feature_capacity_refuses(self) -> None:
        path = self.source(self.wire([{"name": "x" * 1000}]))
        for parser in (Collection, CollectionScanner):
            with self.assertRaises(ValueError):
                list(parser(path, limit=80, block=8).features())

    def test_cursor_does_not_accept_partial_numeric_prefix(self) -> None:
        cursor = Cursor(io.BytesIO(b"123.45e-6,"), block=1)
        value, raw = cursor.value()
        self.assertEqual(value, Decimal("123.45e-6"))
        self.assertEqual(raw, b"123.45e-6")

    def test_native_null_zero_bool_integer_decimal_and_literal_strings_stay_distinct(
        self,
    ) -> None:
        values = [None, 0, False, Decimal("0.0"), "0"]
        self.assertEqual([tagged(x) for x in values], [native(x) for x in values])
        self.assertEqual(len({json.dumps(tagged(x)) for x in values}), 5)
        self.assertFalse(exact(tagged(1), tagged(Decimal("1.0"))))

    def test_complete_ledger_matches_independent_source_and_subset(self) -> None:
        path = self.source(self.wire([self.feature("a"), self.feature("b")]))
        ledger = self.root / "ledger.jsonl"
        actual = summarize(path, ledger)
        expected, joins = independently_validate(
            path, ledger, {"features": [self.feature("a")]}
        )
        self.assertTrue(exact(actual, expected))
        self.assertEqual(joins[0]["match_count"], 1)
        self.assertEqual(actual["feature_array_items"], 2)

    def test_self_consistent_tampered_ledger_refuses_independent_source_join(
        self,
    ) -> None:
        path = self.source(self.wire([self.feature()]))
        ledger = self.root / "ledger.jsonl"
        summarize(path, ledger)
        value = json.loads(ledger.read_text())
        value["properties"][1][0][1] = ["string", "fabricated"]
        ledger.write_text(json.dumps(value) + "\n")
        hashlib.sha256(ledger.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "independent source"):
            independently_validate(path, ledger, {"features": [self.feature()]})

    def test_missing_extra_reordered_ledger_rows_refuse(self) -> None:
        path = self.source(self.wire([self.feature("a"), self.feature("b")]))
        ledger = self.root / "ledger.jsonl"
        summarize(path, ledger)
        original = ledger.read_bytes()
        rows = original.splitlines(keepends=True)
        for changed in (rows[0], original + rows[0], b"".join(reversed(rows))):
            ledger.write_bytes(changed)
            with self.assertRaises(ValueError):
                independently_validate(path, ledger, {"features": [self.feature("a")]})

    def test_duplicate_missing_native_ids_are_measured_not_promoted(self) -> None:
        missing = self.feature()
        missing["properties"] = {"record_id": False}
        path = self.source(self.wire([self.feature("a"), self.feature("a"), missing]))
        ledger = self.root / "ledger.jsonl"
        summary = summarize(path, ledger)
        expected, joins = independently_validate(
            path, ledger, {"features": [self.feature("a"), self.feature("absent")]}
        )
        self.assertTrue(exact(summary, expected))
        self.assertEqual(summary["duplicate_record_id_occurrences"], 1)
        self.assertEqual(summary["missing_or_non_string_or_empty_record_id"], 1)
        self.assertEqual([row["match_count"] for row in joins], [2, 0])

    def test_all_four_native_identity_fields_preserve_missingness_and_duplicates(
        self,
    ) -> None:
        first = self.feature("a")
        first["properties"] = {
            "record_id": "a",
            "sjoid": "same",
            "sj_uuid": None,
            "sj_vatten_id": False,
        }
        second = self.feature("b")
        second["properties"] = {
            "record_id": "b",
            "sjoid": "same",
            "sj_uuid": "uuid",
            "sj_vatten_id": "",
        }
        path = self.source(self.wire([first, second]))
        ledger = self.root / "ledger.jsonl"
        report = summarize(path, ledger)
        independent, _ = independently_validate(path, ledger, {"features": [first]})
        self.assertTrue(exact(report, independent))
        self.assertEqual(
            report["native_identity_field_counts"]["sjoid"]["duplicate_occurrences"], 1
        )
        self.assertEqual(
            report["native_identity_field_counts"]["sj_uuid"][
                "missing_or_null_or_empty_or_non_string"
            ],
            1,
        )
        self.assertEqual(
            report["native_identity_field_counts"]["sj_vatten_id"][
                "missing_or_null_or_empty_or_non_string"
            ],
            2,
        )

    def test_subset_area_type_disagreement_is_explicit(self) -> None:
        path = self.source(self.wire([self.feature()]))
        ledger = self.root / "ledger.jsonl"
        summarize(path, ledger)
        ref = self.feature()
        ref["properties"] = {"record_id": "one", "area_km2": "0"}
        _, joins = independently_validate(path, ledger, {"features": [ref]})
        self.assertFalse(
            joins[0]["full_source_matches"][0]["field_agreement"]["area_km2"][
                "typed_value_equal"
            ]
        )

    def test_missing_geometry_and_native_coordinate_metadata_are_descriptive(
        self,
    ) -> None:
        feature = self.feature()
        feature["geometry"] = None
        path = self.source(self.wire([feature, self.feature("other")]))
        ledger = self.root / "ledger.jsonl"
        summary = summarize(path, ledger)
        independent, _ = independently_validate(
            path, ledger, {"features": [self.feature()]}
        )
        self.assertTrue(exact(summary, independent))
        self.assertEqual(summary["missing_or_null_geometry"], 1)
        self.assertFalse(
            record(0, feature, "a")["geometry"]["CRS_or_geometric_validity_qualified"]
        )

    def test_missing_null_and_invalid_geometry_type_are_separate_native_facts(
        self,
    ) -> None:
        from census import geometry_profile
        from observe import shape

        for value, kind, present in (
            (None, "null", False),
            (False, "boolean", False),
            ({}, "object", False),
            ({"coordinates": None}, "object", True),
        ):
            left = geometry_profile(value)
            self.assertTrue(exact(left, shape(value)))
            self.assertEqual(left["geometry_value_type"], kind)
            self.assertIs(left["coordinates_present"], present)

    def test_frozen_original_pin_and_duplicate_role_conflict_refuse(self) -> None:
        path = self.source(b"original")
        row = pin(path)
        path.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            verify_frozen_pins([row])
        with self.assertRaises(ValueError):
            frozen_pin_union([row, pin(path)])

    def test_claim_only_fabrication_bool_count_and_extra_claim_refuse(self) -> None:
        expected = {
            "schema_version": "svar-normalized-feature-census.v1",
            "measured_source": {"feature_array_items": 1},
            "scope": "ranking remains unqualified",
        }
        validate_census_claims(expected, expected)
        for changed in (
            {**expected, "scope": "ranking admitted"},
            {**expected, "measured_source": {"feature_array_items": True}},
            {**expected, "rights_admitted": True},
        ):
            with self.assertRaises(ValueError):
                validate_census_claims(changed, expected)

    def test_signed_zero_and_equal_decimal_bounds_follow_source_coordinate_order(
        self,
    ) -> None:
        raw = b'{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"record_id":"one"},"geometry":{"type":"MultiLineString","coordinates":[[[0.0,15.0],[-0.0,15.00],[0.00,15.000]],[[-0.00,15.0000],[0.000,15.00000]]]}}]}'
        path = self.source(raw)
        ledger = self.root / "signed-decimal-ledger.jsonl"
        actual = summarize(path, ledger)
        independent, _ = independently_validate(
            path, ledger, {"features": [self.feature()]}
        )
        self.assertTrue(exact(actual, independent))
        row = json.loads(ledger.read_text())
        self.assertEqual(
            row["geometry"]["native_xy_bounds"], ["0.0", "15.0", "0.0", "15.0"]
        )
        self.assertEqual(
            row["raw_feature_sha256"], next(Collection(path).features())[2]
        )

    def run_entry_prefix(self, name: str, entry: Path) -> None:
        tree = ast.parse((SOURCE / name).read_text())
        boundary = next(
            i
            for i, node in enumerate(tree.body)
            if isinstance(node, ast.ImportFrom) and node.module == "contracts"
        )
        prefix = ast.Module(body=tree.body[:boundary], type_ignores=[])
        before = list(sys.path)
        try:
            exec(compile(prefix, str(SOURCE / name), "exec"), {"__file__": str(entry)})
        finally:
            sys.path[:] = before

    def prefix_fixture(self) -> Path:
        root = self.root / "owned"
        root.mkdir()
        (root / "preflight").mkdir()
        for p in SOURCE.glob("*.py"):
            (root / p.name).write_text(
                "raise RuntimeError('never imported by a prefix control')"
            )
        return root

    def test_each_entrypoint_prefix_allows_exact_physical_owned_namespace(self) -> None:
        root = self.prefix_fixture()
        for name in ("prepare.py", "run.py", "census.py", "observe.py"):
            self.run_entry_prefix(name, root / name)

    def test_native_helper_shadows_refuse_before_local_import(self) -> None:
        root = self.prefix_fixture()
        for shadow in ("contracts.so", "runtime.so"):
            target = root / shadow
            target.write_bytes(b"not a native library; must never reach loader")
            try:
                for name in ("prepare.py", "run.py", "census.py", "observe.py"):
                    with self.assertRaisesRegex(ValueError, "before helper import"):
                        self.run_entry_prefix(name, root / name)
            finally:
                target.unlink()

    def test_helper_alias_fifo_and_import_directory_refuse_in_prefix(self) -> None:
        root = self.prefix_fixture()
        extra = root / "outside-entry"
        for kind in ("alias", "fifo", "directory"):
            if kind == "alias":
                extra.symlink_to(root / "contracts.py")
            elif kind == "fifo":
                os.mkfifo(extra)
            else:
                extra.mkdir()
            try:
                for name in ("prepare.py", "run.py", "census.py", "observe.py"):
                    with self.assertRaisesRegex(ValueError, "before helper import"):
                        self.run_entry_prefix(name, root / name)
            finally:
                if kind == "directory":
                    extra.rmdir()
                else:
                    extra.unlink()

    def test_entry_file_and_ancestor_alias_refuse_before_import(self) -> None:
        root = self.prefix_fixture()
        alias = self.root / "alias"
        alias.symlink_to(root, target_is_directory=True)
        script = self.root / "entry.py"
        script.symlink_to(root / "run.py")
        for name in ("prepare.py", "run.py", "census.py", "observe.py"):
            for entry in (alias / name, script):
                with self.assertRaisesRegex(ValueError, "Physical absolute"):
                    self.run_entry_prefix(name, entry)

    def test_actual_source_namespace_refuses_fifo_and_unlisted_import(self) -> None:
        import os

        extra = SOURCE / "unlisted-source-control.py"
        try:
            extra.write_text("raise RuntimeError('never imported')")
            with self.assertRaises(ValueError):
                source_namespace()
            extra.unlink()
            os.mkfifo(extra)
            with self.assertRaises(ValueError):
                source_namespace()
        finally:
            if extra.exists():
                extra.unlink()


if __name__ == "__main__":
    unittest.main()
