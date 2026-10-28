"""Synthetic count/depth/identity refusals; no actual scientific source replay."""

from __future__ import annotations

import ast
import copy
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import contracts
from contracts import (
    COMMON_SHA,
    MANIFEST,
    OWNER,
    PRIMARY,
    PRODUCER,
    REPORT,
    SAMPLES,
    SITE,
    UNIT,
    exact,
    input_catalog,
    owner_contract,
    part_rows,
    pin,
    primary_table,
    reconcile,
    sha,
    verify_products,
)
from prepare import data_input, output_root

A = Path(__file__).resolve().parent
R = A.parents[2]


def primary() -> bytes:
    return b"10.1594/PANGAEA.739834\nEvent(s):\tSOLSOE81\nArea: 2.5 ha.\nCreative Commons Attribution-NonCommercial 3.0 Unported\n\tA [#] (A) * PI: source\n\tOldB [#] (B) * PI: source\n\tC [#] (C) * PI: source\n*/\nDepth sed [m]\tA [#]\tB [#]\tC [#]\n1.00\t2\t0\t1\n1.20\t0\t3\t4\n"


def source_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    samples: list[dict[str, object]] = [
        {
            "collection_unit_id": UNIT,
            "site_id": SITE,
            "sample_id": "sample:" + str(index),
            "source_depth": str(depth),
        }
        for index, depth in [(1, 100), (2, 120)]
    ]
    rows = [
        {
            "collection_unit_id": UNIT,
            "site_id": SITE,
            "sample_id": "sample:" + str(index),
            "source_unit": "NISP",
            "unit_family": "count",
            "source_reported_name": name,
            "source_value": value,
        }
        for index, name, value in [
            (1, "A", 2),
            (1, "C", 1),
            (2, "RenamedB", 3),
            (2, "C", 4),
        ]
    ]
    return samples, rows


def csv_bytes(rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=[
            "depth_cm",
            "neotoma_sample_id",
            "positive_source_taxa",
            "source_count_sum",
            "positive_counts_equal",
        ],
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def expected_report(derived: dict[str, object]) -> dict[str, object]:
    return {
        **derived,
        "author_79_sample_selection_identified": False,
        "author_chronology_identified": False,
        "lra_admitted_samples": 0,
        "source_rights": "PANGAEA CC BY-NC 3.0; primary raw text remains external",
        "all_source_sample_depths_match_exactly_cm": True,
        "all_positive_source_counts_match_exactly": True,
        "neotoma_zero_cells_are_sparse_absences": True,
    }


class Contracts(unittest.TestCase):
    def test_independent_synthetic_vectors_and_every_csv_row(self) -> None:
        samples, observations = source_rows()
        derived, ledger = reconcile(primary(), samples, observations)
        self.assertEqual(
            (
                derived["primary_profile_rows"],
                derived["primary_parameter_count"],
                derived["primary_count_cells"],
                derived["primary_positive_count_cells"],
                derived["primary_zero_count_cells"],
                derived["primary_total_count"],
            ),
            (2, 3, 6, 4, 2, 10),
        )
        self.assertEqual(
            (
                derived["exact_same_name_parameter_count"],
                derived["numeric_rename_candidate_count"],
            ),
            (2, 1),
        )
        report = expected_report(derived)
        verify_products(
            report, copy.deepcopy(report), ledger, csv_bytes(ledger), derived
        )
        self.assertEqual(
            [row["neotoma_sample_id"] for row in ledger], ["sample:1", "sample:2"]
        )

    def test_citation_event_and_rights_refuse(self) -> None:
        for token in [
            b"10.1594/PANGAEA.739834",
            b"Event(s):\tSOLSOE81",
            b"Area: 2.5 ha.",
            b"Creative Commons Attribution-NonCommercial 3.0 Unported",
        ]:
            with self.subTest(token=token), self.assertRaises(ValueError):
                primary_table(primary().replace(token, b"unknown"))

    def test_axes_and_parameter_order_refuse(self) -> None:
        for raw in [
            primary().replace(b"OldB [#] (B)", b"A [#] (B)"),
            primary().replace(b"A [#]\tB [#]", b"B [#]\tA [#]"),
            primary().replace(b"A [#]\tB [#]", b"A [#]\tA [#]"),
        ]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                primary_table(raw)

    def test_noninteger_duplicate_and_missing_depths_refuse(self) -> None:
        for raw in [
            primary().replace(b"1.00\t", b"1.001\t"),
            primary().replace(b"1.20\t", b"1.00\t"),
            primary().replace(b"1.20\t0\t3\t4\n", b""),
        ]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                reconcile(raw, *source_rows())

    def test_negative_fractional_blank_count_cells_refuse(self) -> None:
        for value in [b"-2", b"2.0", b""]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                primary_table(
                    primary().replace(b"1.00\t2\t", b"1.00\t" + value + b"\t")
                )

    def test_sample_identity_site_and_depth_sets_refuse(self) -> None:
        for key, value in [
            ("sample_id", "sample:1"),
            ("source_depth", "100"),
            ("site_id", "site:wrong"),
            ("source_depth", "121"),
        ]:
            samples, observations = source_rows()
            samples[1][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                reconcile(primary(), samples, observations)

    def test_observation_source_roles_remain_exact(self) -> None:
        for key, value in [
            ("site_id", "wrong"),
            ("collection_unit_id", "wrong"),
            ("source_unit", "percent"),
            ("unit_family", "fraction"),
        ]:
            samples, observations = source_rows()
            observations[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                reconcile(primary(), samples, observations)

    def test_sparse_counts_reject_boolean_float_zero_and_duplicates(self) -> None:
        for value in [True, 2.0, 0, -1]:
            samples, observations = source_rows()
            observations[0]["source_value"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                reconcile(primary(), samples, observations)
        samples, observations = source_rows()
        with self.assertRaises(ValueError):
            reconcile(primary(), samples, [*observations, observations[0]])

    def test_count_vector_missing_or_ambiguous_refuses(self) -> None:
        samples, observations = source_rows()
        changed = copy.deepcopy(observations)
        changed[2]["source_value"] = 4
        with self.assertRaises(ValueError):
            reconcile(primary(), samples, changed)
        extra = {**observations[2], "source_reported_name": "AnotherB"}
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            reconcile(primary(), samples, [*observations, extra])

    def test_all_literal_name_counts_remain_exact(self) -> None:
        samples, observations = source_rows()
        observations[0]["source_value"] = 3
        with self.assertRaisesRegex(ValueError, "cell differs"):
            reconcile(primary(), samples, observations)

    def test_complete_report_claims_types_and_independent_cells_refuse(self) -> None:
        derived, ledger = reconcile(primary(), *source_rows())
        expected = expected_report(derived)
        for key, value in [
            ("primary_total_count", 11),
            ("primary_total_count", 10.0),
            ("lra_admitted_samples", False),
            ("author_79_sample_selection_identified", True),
            ("source_rights", "redistribution approved"),
        ]:
            changed = {**expected, key: value}
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_products(changed, expected, ledger, csv_bytes(ledger), derived)
        tampered = {**derived, "primary_total_count": 11}
        with self.assertRaises(ValueError):
            verify_products(expected, expected, ledger, csv_bytes(ledger), tampered)

    def test_csv_order_missing_rows_and_wire_changes_refuse(self) -> None:
        derived, ledger = reconcile(primary(), *source_rows())
        report = expected_report(derived)
        for raw in [
            csv_bytes(list(reversed(ledger))),
            csv_bytes(ledger[:1]),
            csv_bytes(ledger).replace(b"\n", b"\r\n"),
            csv_bytes(ledger).replace(b",True", b",1"),
        ]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                verify_products(report, report, ledger, raw, derived)

    def test_named_owner_two_products_only(self) -> None:
        expected = sorted(
            row["path"]
            for row in input_catalog()
            if row["path"].startswith("data/neotoma/relational/")
        )
        owner = {
            "owner_id": OWNER,
            "role": "unresolved",
            "paths": [REPORT, SAMPLES],
            "producer_paths": [PRODUCER],
            "producer_inputs": expected,
            "verification": "External primary; no acquisition, taxonomy or LRA acceptance.",
        }
        self.assertEqual(owner_contract({"owners": [owner]}), owner)
        for key, value in [
            ("role", "generated_owner"),
            ("paths", [REPORT]),
            ("paths", [REPORT, SAMPLES, "other.csv"]),
            ("producer_paths", []),
            ("producer_inputs", []),
            ("verification", ""),
        ]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                owner_contract({"owners": [{**owner, key: value}]})
        with self.assertRaises(ValueError):
            owner_contract({"owners": [owner, owner]})

    def test_part_manifest_hash_count_path_and_unlisted_inputs_refuse(self) -> None:
        with tempfile.TemporaryDirectory(dir=A / "preflight") as directory:
            root = Path(directory)
            path = root / "data/neotoma/relational/surfaces/samples/a.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"rows": [{"x": 1}]}))
            row = {**pin(path), "path": path.relative_to(root).as_posix()}
            part = {
                "path": "surfaces/samples/a.json",
                "sha256": row["sha256"],
                "row_count": 1,
            }
            manifest: dict[str, Any] = {
                "surfaces": {"samples": {"part_count": 1, "parts": [part]}}
            }
            with patch.object(contracts, "input_catalog", return_value=[row]):
                self.assertEqual(list(part_rows(root, manifest, "samples")), [{"x": 1}])
                for key, value in [
                    ("sha256", "0" * 64),
                    ("row_count", True),
                    ("row_count", 2),
                    ("path", "../escape.json"),
                    ("path", "surfaces/samples/unknown.json"),
                ]:
                    changed = copy.deepcopy(manifest)
                    changed["surfaces"]["samples"]["parts"][0][key] = value
                    with (
                        self.subTest(key=key, value=value),
                        self.assertRaises(ValueError),
                    ):
                        list(part_rows(root, changed, "samples"))

    def test_readset_and_four_runtime_controllers_match_authorities(self) -> None:
        rows = input_catalog()
        self.assertEqual(len(rows), 12)
        self.assertEqual(sum(row["bytes"] for row in rows), 542545790)
        self.assertEqual(
            [row["path"] for row in rows if row["path"].startswith("landclim/")],
            [PRIMARY],
        )
        self.assertEqual(
            len([row for row in rows if "/observations/" in row["path"]]), 8
        )
        self.assertIn(MANIFEST, [row["path"] for row in rows])
        old = R / "artifacts/science/solsoe-native-loader-paths"
        for name in ["runtime.py", "run.py", "execute_source.py", "common_runner.py"]:
            self.assertEqual((A / name).read_bytes(), (old / name).read_bytes())
        self.assertEqual(sha(A / "common_runner.py"), COMMON_SHA)
        producer = next(row for row in rows if row["path"] == PRODUCER)
        self.assertEqual(pin(R / PRODUCER), {**producer, "path": str(R / PRODUCER)})
        tree = ast.parse((R / PRODUCER).read_bytes())
        imports = {
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        } | {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        self.assertEqual(
            imports,
            {
                "__future__",
                "argparse",
                "csv",
                "decimal",
                "hashlib",
                "json",
                "pathlib",
                "re",
                "typing",
            },
        )
        flags = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value.startswith("--")
        }
        self.assertEqual(flags, {"--repository", "--source-root", "--output"})

    def test_output_and_physical_source_link_guards(self) -> None:
        with tempfile.TemporaryDirectory(dir=A / "preflight") as directory:
            root = Path(directory)
            original = root / "primary.txt"
            original.write_text("controlled source")
            self.assertEqual(data_input(original), pin(original))
            alias = root / "alias.txt"
            alias.symlink_to(original.name)
            with self.assertRaises(ValueError):
                data_input(alias)
            for path in [A / "new-output", root / "existing"]:
                if path.name == "existing":
                    path.mkdir()
                with self.subTest(path=path), self.assertRaises(ValueError):
                    output_root(path)
        self.assertFalse(exact(False, 0))
        self.assertFalse(exact(0, 0.0))


if __name__ == "__main__":
    unittest.main()
