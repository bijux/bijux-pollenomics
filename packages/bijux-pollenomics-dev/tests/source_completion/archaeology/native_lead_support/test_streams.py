"""Private streaming custody guards, separate from unchanged spatial mathematics."""

from __future__ import annotations

import gzip
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics_dev.source_completion.archaeology.native_lead_support.streams import (
    NativeWitness,
    WitnessBudget,
)

B = Path(__file__).resolve().parents[6] / "artifacts/tests/raa-native-streams"


class NativeStreams(unittest.TestCase):
    def setUp(self) -> None:
        B.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=B)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_native_unicode_null_and_real_type_payload_roundtrip(self) -> None:
        row: dict[str, object] = {
            "uuid": "native",
            "period": "Järnålder",
            "event_interval": None,
            "real": {"value": 1.0, "float_hex": (1.0).hex()},
            "geometry_role": "positional_uncertainty_region",
        }
        writer = NativeWitness(self.root / "records.gz", WitnessBudget(10000), 1000)
        writer.write(row)
        result = writer.close()
        self.assertEqual(
            json.loads(gzip.decompress((self.root / "records.gz").read_bytes())), row
        )
        self.assertEqual(result["rows"], 1)
        self.assertGreater(int(str(result["decoded_bytes"])), 0)

    def test_identical_source_rows_produce_identical_physical_gzip_bytes(self) -> None:
        for name in ("one", "two"):
            writer = NativeWitness(self.root / name, WitnessBudget(1000), 1000)
            writer.write({"z": 1, "a": None})
            writer.close()
        self.assertEqual(
            (self.root / "one").read_bytes(), (self.root / "two").read_bytes()
        )

    def test_cumulative_decoded_budget_is_shared_across_files(self) -> None:
        budget = WitnessBudget(25)
        first = NativeWitness(self.root / "one", budget, 100)
        second = NativeWitness(self.root / "two", budget, 100)
        try:
            first.write({"v": "12345"})
            with self.assertRaisesRegex(ValueError, "decoded witness"):
                second.write({"v": "12345"})
        finally:
            first.close()
            second.close()

    def test_single_row_size_is_not_silently_truncated(self) -> None:
        writer = NativeWitness(self.root / "one", WitnessBudget(1000), 10)
        try:
            with self.assertRaisesRegex(ValueError, "row byte ceiling"):
                writer.write({"native_text": "123456789"})
        finally:
            result = writer.close()
        self.assertEqual(result["rows"], 0)

    def test_large_ancillary_family_refuses_without_truncation(self) -> None:
        from bijux_pollenomics_dev.source_completion.archaeology.native_lead_support.producer import (
            native_family,
        )

        connection = sqlite3.connect(":memory:")
        try:
            with patch(
                "bijux_pollenomics_dev.source_completion.archaeology.native_lead_support.producer.indexed_rows",
                side_effect=ValueError("local native owner/child limit exceeded"),
            ):
                rows, refusal = native_family(
                    connection, "egenskap", "source-native", 500
                )
            self.assertEqual(rows, [])
            self.assertEqual(refusal["minimum_source_rows"], 501)
            self.assertIs(refusal["truncated_rows_admitted"], False)
        finally:
            connection.close()

    def test_other_native_source_failure_is_never_swallowed(self) -> None:
        from bijux_pollenomics_dev.source_completion.archaeology.native_lead_support.producer import (
            native_family,
        )

        connection = sqlite3.connect(":memory:")
        try:
            with (
                patch(
                    "bijux_pollenomics_dev.source_completion.archaeology.native_lead_support.producer.indexed_rows",
                    side_effect=ValueError("native identity conflict"),
                ),
                self.assertRaisesRegex(ValueError, "identity conflict"),
            ):
                native_family(connection, "lamning", "source-native", 500)
        finally:
            connection.close()

    def test_existing_private_witness_cannot_be_replaced(self) -> None:
        (self.root / "one").write_bytes(b"source-owned predecessor")
        with self.assertRaises(FileExistsError):
            NativeWitness(self.root / "one", WitnessBudget(1000), 100)
        self.assertEqual((self.root / "one").read_bytes(), b"source-owned predecessor")

    def test_nonfinite_numeric_json_is_refused(self) -> None:
        writer = NativeWitness(self.root / "one", WitnessBudget(1000), 100)
        try:
            with self.assertRaises(ValueError):
                writer.write({"undeclared": float("nan")})
        finally:
            writer.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
