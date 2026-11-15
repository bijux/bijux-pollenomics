from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.evidence.sources.neotoma import (
    validate_neotoma_relational_materialization,
)
from bijux_pollenomics.evidence.sources.neotoma.contract import (
    canonical_json_bytes,
    materialization_digest,
)

from .native_snapshot import _rebind_authenticated_file, _snapshot


class NeotomaMaterializationTests(unittest.TestCase):
    def test_part_parent_validation_uses_the_authenticated_buffer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "relational"
            materialize_neotoma_relational_snapshot(output, _snapshot())
            relative = "surfaces/samples/part-00001.json"
            part_path = output / relative
            original = part_path.read_bytes()
            part = json.loads(original)
            part["rows"][0]["dataset_id"] = "neotoma:dataset:missing"
            bad = canonical_json_bytes(part)
            _rebind_authenticated_file(output, relative, bad)
            read_bytes = Path.read_bytes
            reads = 0

            def read_part(path: Path) -> bytes:
                nonlocal reads
                if path == part_path:
                    reads += 1
                    if reads == 2:
                        return original
                return read_bytes(path)

            with (
                patch.object(Path, "read_bytes", read_part),
                self.assertRaisesRegex(ValueError, "missing parent"),
            ):
                validate_neotoma_relational_materialization(output)
            self.assertEqual(part_path.read_bytes(), bad)

    def test_reconciliation_validation_uses_the_authenticated_buffer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "relational"
            materialize_neotoma_relational_snapshot(output, _snapshot())
            path = output / "reconciliation.json"
            original = path.read_bytes()
            payload = json.loads(original)
            payload["reconciliation"]["normalized_row_counts"]["samples"] += 1
            bad = canonical_json_bytes(payload)
            _rebind_authenticated_file(output, "reconciliation.json", bad)
            read_bytes = Path.read_bytes
            reads = 0

            def read_reconciliation(candidate: Path) -> bytes:
                nonlocal reads
                if candidate == path:
                    reads += 1
                    if reads == 2:
                        return original
                return read_bytes(candidate)

            with (
                patch.object(Path, "read_bytes", read_reconciliation),
                self.assertRaisesRegex(ValueError, "reconciled samples row_count"),
            ):
                validate_neotoma_relational_materialization(output)
            self.assertEqual(path.read_bytes(), bad)

    def test_valid_part_does_not_parse_an_unauthenticated_second_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "relational"
            materialize_neotoma_relational_snapshot(output, _snapshot())
            expected = json.loads((output / "manifest.json").read_bytes())
            part = output / "surfaces/samples/part-00001.json"
            read_bytes = Path.read_bytes
            reads = 0

            def read_part(path: Path) -> bytes:
                nonlocal reads
                if path == part:
                    reads += 1
                    if reads == 2:
                        return b"{}"
                return read_bytes(path)

            with patch.object(Path, "read_bytes", read_part):
                self.assertEqual(
                    validate_neotoma_relational_materialization(output), expected
                )

    def test_correctly_rehashed_missing_sample_parent_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "relational"
            materialize_neotoma_relational_snapshot(output, _snapshot())
            manifest = json.loads((output / "manifest.json").read_text())
            part_record = manifest["surfaces"]["observations"]["parts"][0]
            part_path = output / part_record["path"]
            part = json.loads(part_path.read_text())
            part["rows"][0]["sample_id"] = "neotoma:sample:missing"
            content = canonical_json_bytes(part)
            part_path.write_bytes(content)
            part_record["sha256"] = hashlib.sha256(content).hexdigest()
            records = [
                {"path": part["path"], "sha256": part["sha256"]}
                for surface in manifest["surfaces"].values()
                for part in surface["parts"]
            ]
            records.append(
                {
                    "path": manifest["reconciliation"]["path"],
                    "sha256": manifest["reconciliation"]["sha256"],
                }
            )
            manifest["materialization_sha256"] = materialization_digest(records)
            (output / "manifest.json").write_bytes(canonical_json_bytes(manifest))
            with self.assertRaisesRegex(ValueError, "missing parent"):
                validate_neotoma_relational_materialization(output)

    def test_published_validation_recomputes_country_partitions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory) / "relational"
            materialize_neotoma_relational_snapshot(output_root, _snapshot())
            manifest_path = output_root / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            site_part_record = manifest["surfaces"]["sites"]["parts"][0]
            site_part_path = output_root / site_part_record["path"]
            site_part = json.loads(site_part_path.read_text())
            site_part["rows"][1]["country_code"] = "SE"
            site_content = canonical_json_bytes(site_part)
            site_part_path.write_bytes(site_content)
            site_part_record["sha256"] = hashlib.sha256(site_content).hexdigest()
            digest_records = [
                {"path": part["path"], "sha256": part["sha256"]}
                for surface in manifest["surfaces"].values()
                for part in surface["parts"]
            ]
            digest_records.append(
                {
                    "path": manifest["reconciliation"]["path"],
                    "sha256": manifest["reconciliation"]["sha256"],
                }
            )
            manifest["materialization_sha256"] = materialization_digest(digest_records)
            manifest_path.write_bytes(canonical_json_bytes(manifest))

            with self.assertRaisesRegex(ValueError, "sites SE country partition"):
                validate_neotoma_relational_materialization(output_root)
