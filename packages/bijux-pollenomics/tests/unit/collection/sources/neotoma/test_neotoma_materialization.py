from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics.collection.sources.neotoma import materialization
from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
    validate_neotoma_relational_materialization,
)


def _snapshot() -> dict[str, object]:
    surfaces: dict[str, object] = {
        "sites": [
            {
                "site_id": "neotoma:site:3",
                "source_site_id": 3,
                "country_code": "UNASSIGNED",
                "country_decision_status": "review",
                "country_propagation_eligible": False,
            },
            {
                "site_id": "neotoma:site:1",
                "source_site_id": 1,
                "country_code": "SE",
                "country_decision_status": "assigned",
                "country_propagation_eligible": True,
            },
            {
                "site_id": "neotoma:site:2",
                "source_site_id": 2,
                "country_code": "UNASSIGNED",
                "country_decision_status": "unassigned",
                "country_propagation_eligible": False,
            },
        ],
        "collection_units": [
            {
                "collection_unit_id": "neotoma:collection-unit:1",
                "site_id": "neotoma:site:1",
                "country_code": "SE",
            },
            {
                "collection_unit_id": "neotoma:collection-unit:3",
                "site_id": "neotoma:site:3",
                "country_code": "UNASSIGNED",
            },
        ],
        "datasets": [],
        "chronologies": [],
        "chronology_controls": [],
        "samples": [],
        "age_claims": [],
        "variables": [],
        "observations": [
            {
                "observation_id": "neotoma:observation:3",
                "site_id": "neotoma:site:3",
                "country_code": "UNASSIGNED",
                "source_value": 0,
            }
        ],
        "conflicts": [],
        "orphans": [],
    }
    country_fields = (
        "sites",
        "collection_units",
        "datasets",
        "chronologies",
        "chronology_controls",
        "samples",
        "age_claim_rows",
        "observation_rows",
    )
    country_counts = {
        country_code: dict.fromkeys(country_fields, 0)
        for country_code in ("SE", "DK", "NO", "FI", "UNASSIGNED")
    }
    country_counts["SE"].update({"sites": 1, "collection_units": 1})
    country_counts["UNASSIGNED"].update(
        {"sites": 2, "collection_units": 1, "observation_rows": 1}
    )
    return {
        "schema_version": "neotoma-relational-snapshot.v2",
        "source_family": "neotoma",
        "source_snapshot_id": "sha256:source-fixture",
        "build_id": "fixture-build",
        **surfaces,
        "reconciliation": {
            "normalized_row_counts": {
                "sites": 3,
                "collection_units": 2,
                "datasets": 0,
                "chronologies": 0,
                "chronology_controls": 0,
                "samples": 0,
                "age_claims": 0,
                "variables": 0,
                "observations": 1,
            },
            "conflict_count": 0,
            "orphan_count": 0,
            "country_counts": country_counts,
            "country_attribution_counts": {
                "decision_statuses": {
                    "assigned": 1,
                    "review": 1,
                    "unassigned": 1,
                },
                "final_country_codes": {"SE": 1, "UNASSIGNED": 2},
                "propagation_eligibility": {"blocked": 2, "eligible": 1},
            },
        },
    }


def _published_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class NeotomaMaterializationTests(unittest.TestCase):
    def test_publishes_all_surfaces_in_stable_digest_verified_parts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            first_root = workspace / "first-relational"
            second_root = workspace / "second-relational"
            snapshot = _snapshot()

            manifest_path = materialize_neotoma_relational_snapshot(
                first_root, snapshot, rows_per_part=2
            )
            reversed_snapshot = copy.deepcopy(snapshot)
            reversed_snapshot["sites"] = list(reversed(reversed_snapshot["sites"]))
            materialize_neotoma_relational_snapshot(
                second_root, reversed_snapshot, rows_per_part=2
            )

            manifest = validate_neotoma_relational_materialization(first_root)
            self.assertEqual(manifest_path, first_root / "manifest.json")
            self.assertEqual(
                manifest["schema_version"],
                "neotoma-relational-materialization-manifest.v1",
            )
            site_surface = manifest["surfaces"]["sites"]
            self.assertEqual(site_surface["row_count"], 3)
            self.assertEqual(site_surface["part_count"], 2)
            first_part_record = site_surface["parts"][0]
            self.assertEqual(
                first_part_record["schema_version"],
                "neotoma-relational-part.v1",
            )
            self.assertEqual(
                first_part_record["surface_schema_version"],
                "neotoma-relational-sites.v2",
            )
            first_part_path = first_root / first_part_record["path"]
            self.assertEqual(
                hashlib.sha256(first_part_path.read_bytes()).hexdigest(),
                first_part_record["sha256"],
            )
            all_sites = []
            for part_record in site_surface["parts"]:
                part = json.loads((first_root / part_record["path"]).read_text())
                self.assertEqual(part["row_count"], len(part["rows"]))
                all_sites.extend(part["rows"])
            self.assertEqual(
                [row["site_id"] for row in all_sites],
                ["neotoma:site:1", "neotoma:site:2", "neotoma:site:3"],
            )
            self.assertEqual(
                [row["country_code"] for row in all_sites],
                ["SE", "UNASSIGNED", "UNASSIGNED"],
            )
            self.assertEqual(
                _published_files(first_root), _published_files(second_root)
            )
            self.assertFalse((workspace / ".first-relational.staging").exists())
            self.assertFalse((workspace / ".first-relational.recovery").exists())

    def test_refuses_duplicate_row_identifiers_without_publishing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            output_root = workspace / "relational"
            snapshot = _snapshot()
            duplicate = copy.deepcopy(snapshot["sites"][0])
            snapshot["sites"].append(duplicate)

            with self.assertRaisesRegex(ValueError, "Duplicate site_id"):
                materialize_neotoma_relational_snapshot(output_root, snapshot)

            self.assertFalse(output_root.exists())
            self.assertFalse((workspace / ".relational.staging").exists())

    def test_refuses_reconciliation_row_loss_without_publishing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            output_root = workspace / "relational"
            snapshot = _snapshot()
            snapshot["reconciliation"]["normalized_row_counts"]["sites"] = 4

            with self.assertRaisesRegex(ValueError, "reconciled sites row_count"):
                materialize_neotoma_relational_snapshot(output_root, snapshot)

            self.assertFalse(output_root.exists())
            self.assertFalse((workspace / ".relational.staging").exists())

    def test_refuses_country_partition_mismatch_without_publishing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            output_root = workspace / "relational"
            snapshot = _snapshot()
            snapshot["reconciliation"]["country_counts"]["SE"]["observation_rows"] = 1

            with self.assertRaisesRegex(
                ValueError, "observations SE country partition"
            ):
                materialize_neotoma_relational_snapshot(output_root, snapshot)

            self.assertFalse(output_root.exists())

    def test_refuses_incomplete_site_decision_accounting(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            output_root = workspace / "relational"
            snapshot = _snapshot()
            snapshot["reconciliation"]["country_attribution_counts"][
                "decision_statuses"
            ] = {"assigned": 1, "review": 1}

            with self.assertRaisesRegex(ValueError, "do not sum to site rows"):
                materialize_neotoma_relational_snapshot(output_root, snapshot)

            self.assertFalse(output_root.exists())

    def test_refuses_staging_collision_without_deleting_foreign_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            output_root = workspace / "relational"
            staging_root = workspace / ".relational.staging"
            staging_root.mkdir()
            marker = staging_root / "owner-marker"
            marker.write_text("foreign", encoding="utf-8")

            with self.assertRaisesRegex(FileExistsError, "staging path collision"):
                materialize_neotoma_relational_snapshot(output_root, _snapshot())

            self.assertEqual(marker.read_text(encoding="utf-8"), "foreign")
            self.assertFalse(output_root.exists())

    def test_detects_part_tampering_and_refuses_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            output_root = workspace / "relational"
            materialize_neotoma_relational_snapshot(output_root, _snapshot())
            part_path = output_root / "surfaces/sites/part-00001.json"
            part_path.write_text("{}\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                validate_neotoma_relational_materialization(output_root)
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                materialize_neotoma_relational_snapshot(output_root, _snapshot())

            self.assertEqual(part_path.read_text(encoding="utf-8"), "{}\n")

    def test_published_validation_recomputes_country_partitions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_root = Path(temporary_directory) / "relational"
            materialize_neotoma_relational_snapshot(output_root, _snapshot())
            manifest_path = output_root / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            site_part_record = manifest["surfaces"]["sites"]["parts"][0]
            site_part_path = output_root / site_part_record["path"]
            site_part = json.loads(site_part_path.read_text())
            site_part["rows"][0]["country_code"] = "UNASSIGNED"
            site_content = materialization._canonical_json(site_part)
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
            manifest["materialization_sha256"] = (
                materialization._materialization_digest(digest_records)
            )
            manifest_path.write_bytes(materialization._canonical_json(manifest))

            with self.assertRaisesRegex(ValueError, "sites SE country partition"):
                validate_neotoma_relational_materialization(output_root)

    def test_refuses_unsafe_output_and_manifest_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            with self.assertRaisesRegex(ValueError, "must be absolute"):
                materialize_neotoma_relational_snapshot(
                    Path("relative-relational"), _snapshot()
                )
            with self.assertRaisesRegex(ValueError, "Unsafe"):
                materialize_neotoma_relational_snapshot(Path("/"), _snapshot())

            output_root = workspace / "relational"
            materialize_neotoma_relational_snapshot(output_root, _snapshot())
            manifest_path = output_root / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["surfaces"]["sites"]["parts"][0]["path"] = "../escape.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "Unsafe materialization path"):
                validate_neotoma_relational_materialization(output_root)

    def test_failed_candidate_keeps_prior_valid_tree_and_cleans_staging(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            output_root = workspace / "relational"
            materialize_neotoma_relational_snapshot(output_root, _snapshot())
            prior_files = _published_files(output_root)
            original_write = materialization._write_json_exclusive

            def fail_during_candidate(path: Path, payload: object) -> str:
                if path.name == "part-00001.json" and "observations" in path.parts:
                    raise OSError("candidate write failed")
                return original_write(path, payload)

            with (
                patch.object(
                    materialization,
                    "_write_json_exclusive",
                    side_effect=fail_during_candidate,
                ),
                self.assertRaisesRegex(OSError, "candidate write failed"),
            ):
                materialize_neotoma_relational_snapshot(output_root, _snapshot())

            self.assertEqual(_published_files(output_root), prior_files)
            self.assertFalse((workspace / ".relational.staging").exists())
            self.assertFalse((workspace / ".relational.recovery").exists())


if __name__ == "__main__":
    unittest.main()
