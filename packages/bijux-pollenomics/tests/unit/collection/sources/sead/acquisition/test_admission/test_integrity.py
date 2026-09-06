"""Integrity tests."""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    validate_sead_acquisition_admission,
)

from .fixtures import (
    _RUN_ID,
    _expected_identity,
    _materialize,
    _read_json,
    _refresh_manifest,
    _refresh_scoped_receipt,
    _validate,
    _write_fixture,
    _write_json,
)


class SeadAcquisitionAdmissionTests(unittest.TestCase):
    def test_payload_corruption_is_rejected_before_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            payload_path = snapshot / "payloads" / "tbl_sites.json"
            payload_path.write_bytes(payload_path.read_bytes() + b" ")

            with self.assertRaisesRegex(ValueError, "byte_count mismatch"):
                _materialize(snapshot, decisions, root / "admitted")
            self.assertFalse((root / "admitted" / _RUN_ID).exists())

    def test_receipt_row_count_and_identity_drift_are_rejected(self) -> None:
        for field, value, message in (
            ("row_count", 2, "receipt row_count"),
            ("build_id", "sha256:" + "3" * 64, "receipts disagree on build_id"),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                snapshot, decisions = _write_fixture(root)
                receipt_path = snapshot / "receipts" / "tbl_sites.json"
                receipt = _read_json(receipt_path)
                receipt[field] = value
                _refresh_scoped_receipt(receipt)
                _write_json(receipt_path, receipt)
                _refresh_manifest(snapshot)

                with self.assertRaisesRegex(ValueError, message):
                    _validate(snapshot, decisions)

    def test_missing_join_and_country_partition_drift_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            joins_path = snapshot / "reconciliation" / "joins.json"
            joins = _read_json(joins_path)
            edges = joins["edges"]
            self.assertIsInstance(edges, list)
            if not isinstance(edges, list):
                self.fail("fixture join edges must be a list")
            joins["edges"] = edges[:-1]
            _write_json(joins_path, joins)
            _refresh_manifest(snapshot)

            with self.assertRaisesRegex(ValueError, "exactly the 25 declared joins"):
                _validate(snapshot, decisions)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            decision_payload = _read_json(decisions)
            decision_payload["country_counts"] = {
                "SE": 0,
                "DK": 1,
                "NO": 0,
                "FI": 0,
                "UNASSIGNED": 0,
            }
            _write_json(decisions, decision_payload)

            with self.assertRaisesRegex(ValueError, "country decision counts"):
                _validate(snapshot, decisions)

    def test_join_ledger_must_equal_independent_payload_recomputation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            joins_path = snapshot / "reconciliation" / "joins.json"
            joins = _read_json(joins_path)
            edges = joins.get("edges")
            if not isinstance(edges, list) or not isinstance(edges[0], dict):
                self.fail("fixture join ledgers must be object rows")
            edges[0]["parent_key"] = "forged_site_id"
            _write_json(joins_path, joins)
            _refresh_manifest(snapshot)

            with self.assertRaisesRegex(ValueError, "independently recomputed ledger"):
                _validate(snapshot, decisions)

    def test_caller_pins_and_safe_identity_syntax_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            expected = _expected_identity(snapshot, decisions)
            with self.assertRaisesRegex(ValueError, "caller-pinned scope_id"):
                validate_sead_acquisition_admission(
                    snapshot,
                    country_decisions_path=decisions,
                    expected_identity=replace(expected, scope_id="sha256:" + "f" * 64),
                )
            with self.assertRaisesRegex(ValueError, "acquisition manifest SHA-256"):
                validate_sead_acquisition_admission(
                    snapshot,
                    country_decisions_path=decisions,
                    expected_identity=replace(
                        expected, acquisition_manifest_sha256="f" * 64
                    ),
                )
            with self.assertRaisesRegex(ValueError, "country decisions SHA-256"):
                validate_sead_acquisition_admission(
                    snapshot,
                    country_decisions_path=decisions,
                    expected_identity=replace(
                        expected, country_decisions_sha256="f" * 64
                    ),
                )
            with self.assertRaisesRegex(ValueError, "safe path identity"):
                validate_sead_acquisition_admission(
                    snapshot,
                    country_decisions_path=decisions,
                    expected_identity=replace(expected, parent_run_id="../unsafe"),
                )
