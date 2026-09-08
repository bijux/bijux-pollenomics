"""Materialization tests."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    ADMISSION_SCHEMA_VERSION,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_LINKED_SOURCE_TABLES,
)

from .fixtures import (
    _RUN_ID,
    _canonical_bytes,
    _digest,
    _expected_identity,
    _materialize,
    _write_fixture,
)


class SeadAcquisitionAdmissionTests(unittest.TestCase):
    def test_valid_bundle_is_admitted_with_explicit_downstream_refusals(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            output_root = root / "admitted"

            result = _materialize(snapshot, decisions, output_root)
            repeated = _materialize(snapshot, decisions, output_root)

            self.assertEqual(result.output_root, repeated.output_root)
            self.assertEqual(
                result.admission["schema_version"], ADMISSION_SCHEMA_VERSION
            )
            self.assertEqual(
                result.admission["declared_scope"],
                {
                    "scope_key": "declared_chronology_relations",
                    "table_count": 19,
                    "tables": sorted(SEAD_LINKED_SOURCE_TABLES),
                    "join_count": 25,
                    "status": "complete_for_declared_relations",
                    "wp01_complete": False,
                },
            )
            self.assertEqual(
                result.admission["country_accounting"],
                {
                    "bbox_site_count": 1,
                    "admitted_site_count": 1,
                    "scope_excluded_count": 0,
                    "country_counts": {"SE": 1, "DK": 0, "NO": 0, "FI": 0},
                    "review_site_count": 0,
                    "unassigned_site_count": 0,
                    "country_assignment_sha256": _digest(
                        _canonical_bytes([{"site_id": 1, "country_code": "SE"}])
                    ),
                    "boundary_authority_id": _expected_identity(
                        snapshot, decisions
                    ).country_authority_id,
                    "excluded_coordinate_validation": {
                        "status": "not_independently_verified",
                        "reason_code": "preflight_payload_not_preserved",
                    },
                    "reconciles": True,
                },
            )
            self.assertEqual(
                result.admission["downstream_statuses"],
                {
                    "chronology_claims": {
                        "status": "refused",
                        "reason_code": "typed_chronology_claims_not_materialized",
                    },
                    "evidence_events": {
                        "status": "refused",
                        "reason_code": "observation_relations_not_captured",
                    },
                    "propagation_events": {
                        "status": "refused",
                        "reason_code": "propagation_events_not_materialized",
                    },
                },
            )
            for source_path in snapshot.rglob("*"):
                if source_path.is_file():
                    copied_path = result.output_root / source_path.relative_to(snapshot)
                    self.assertEqual(copied_path.read_bytes(), source_path.read_bytes())
            self.assertEqual(
                (result.output_root / "country-decisions.json").read_bytes(),
                decisions.read_bytes(),
            )

    def test_existing_non_identical_admission_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            output_root = root / "admitted"
            result = _materialize(snapshot, decisions, output_root)
            result.admission_path.write_bytes(b"different\n")

            with self.assertRaisesRegex(FileExistsError, "Non-identical"):
                _materialize(snapshot, decisions, output_root)
            self.assertEqual(result.admission_path.read_bytes(), b"different\n")

    def test_relative_output_and_interrupted_publish_are_safe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            with self.assertRaisesRegex(ValueError, "safe absolute path"):
                _materialize(snapshot, decisions, Path("relative-admission"))

            output_root = root / "admitted"
            with (
                patch(
                    "bijux_pollenomics.collection.sources.sead."
                    "acquisition.admission.service.os.replace",
                    side_effect=OSError("injected rename failure"),
                ),
                self.assertRaisesRegex(OSError, "injected rename failure"),
            ):
                _materialize(snapshot, decisions, output_root)
            self.assertFalse((output_root / _RUN_ID).exists())
            self.assertEqual(list(output_root.glob(".*.staging-*")), [])

    def test_materialization_publishes_the_validated_cached_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            payload_path = snapshot / "payloads" / "tbl_sites.json"
            validated_bytes = payload_path.read_bytes()
            real_replace = os.replace

            def mutate_source_then_publish(source: Path, destination: Path) -> None:
                payload_path.write_bytes(b"mutated after validation\n")
                real_replace(source, destination)

            with patch(
                "bijux_pollenomics.collection.sources.sead."
                "acquisition.admission.service.os.replace",
                side_effect=mutate_source_then_publish,
            ):
                result = _materialize(snapshot, decisions, root / "admitted")

            self.assertEqual(
                (result.output_root / "payloads" / "tbl_sites.json").read_bytes(),
                validated_bytes,
            )
            self.assertNotEqual(payload_path.read_bytes(), validated_bytes)

    def test_output_cannot_overlap_source_or_country_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            with self.assertRaisesRegex(ValueError, "overlaps acquisition source"):
                _materialize(snapshot, decisions, snapshot / "admitted")

            independent_decisions = (
                root / "decisions" / _RUN_ID / "country-decisions.json"
            )
            independent_decisions.parent.mkdir(parents=True)
            independent_decisions.write_bytes(decisions.read_bytes())
            with self.assertRaisesRegex(ValueError, "overlaps country decisions"):
                _materialize(snapshot, independent_decisions, root / "decisions")
