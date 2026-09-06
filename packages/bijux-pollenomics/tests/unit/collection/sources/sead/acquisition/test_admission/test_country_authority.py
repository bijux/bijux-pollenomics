"""Country Authority tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from .fixtures import (
    _canonical_bytes,
    _digest,
    _first_query_receipt,
    _read_json,
    _refresh_manifest,
    _refresh_query_receipt,
    _refresh_scoped_receipt,
    _validate,
    _write_fixture,
    _write_json,
)


class SeadAcquisitionAdmissionTests(unittest.TestCase):
    def test_country_evidence_is_cryptographically_and_semantically_bound(self) -> None:
        for mutation, message in (
            ("authority", "boundary authority ID"),
            ("bbox", "preflight receipt parameters"),
            ("coordinate", "admitted country decision coordinates"),
            ("vocabulary", "country decision method"),
            ("preflight", "preflight receipt receipt_id"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                snapshot, decisions = _write_fixture(root)
                payload = _read_json(decisions)
                if mutation == "authority":
                    authority = payload.get("boundary_authority")
                    if not isinstance(authority, dict):
                        self.fail("fixture boundary authority must be an object")
                    authority["authority_id"] = "sha256:" + "e" * 64
                elif mutation == "bbox":
                    payload["bbox"] = [5.0, 54.0, 35.0, 72.0]
                elif mutation == "coordinate":
                    rows = payload.get("decisions")
                    if not isinstance(rows, list) or not isinstance(rows[0], dict):
                        self.fail("fixture decisions must be object rows")
                    rows[0]["latitude_dd"] = 56.5
                elif mutation == "vocabulary":
                    rows = payload.get("decisions")
                    if not isinstance(rows, list) or not isinstance(rows[0], dict):
                        self.fail("fixture decisions must be object rows")
                    detail = rows[0].get("decision")
                    if not isinstance(detail, dict):
                        self.fail("fixture decision detail must be an object")
                    detail["decision_method"] = "manual_guess"
                else:
                    preflight = payload.get("preflight_receipt")
                    if not isinstance(preflight, dict):
                        self.fail("fixture preflight receipt must be an object")
                    preflight["receipt_id"] = "sead-receipt:" + "f" * 64
                _write_json(decisions, payload)

                with self.assertRaisesRegex(ValueError, message):
                    _validate(snapshot, decisions)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            receipt_path = snapshot / "receipts" / "tbl_sites.json"
            receipt = _read_json(receipt_path)
            scope = receipt.get("spatial_scope")
            if not isinstance(scope, dict):
                self.fail("fixture site spatial scope must be an object")
            scope["country_assignment_sha256"] = "f" * 64
            _refresh_scoped_receipt(receipt)
            _write_json(receipt_path, receipt)
            _refresh_manifest(snapshot)
            with self.assertRaisesRegex(ValueError, "country assignment SHA-256"):
                _validate(snapshot, decisions)

    def test_all_relation_scopes_bind_to_the_site_country_authority(self) -> None:
        for mutation, message in (
            ("bbox", "spatial bbox"),
            ("country_assignment_id", "country assignment authority ID"),
            ("country_assignment_sha256", "country assignment SHA-256"),
            ("query_relation_scope", "query relation_scope"),
            ("query_countries", "query spatial countries"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                snapshot, decisions = _write_fixture(root)
                receipt_path = snapshot / "receipts" / "tbl_sample_groups.json"
                receipt = _read_json(receipt_path)
                query = _first_query_receipt(receipt)
                receipt_scope = receipt.get("spatial_scope")
                query_scope = query.get("spatial_scope")
                if not isinstance(receipt_scope, dict) or not isinstance(
                    query_scope, dict
                ):
                    self.fail("fixture spatial scopes must be objects")
                if mutation == "bbox":
                    receipt_scope["bbox"] = [0.0, 0.0, 1.0, 1.0]
                elif mutation.startswith("query_"):
                    field = mutation.removeprefix("query_")
                    query_scope[field] = ["US"] if field == "countries" else "other"
                    _refresh_query_receipt(query)
                else:
                    receipt_scope[mutation] = (
                        "sha256:" + "e" * 64
                        if mutation == "country_assignment_id"
                        else "e" * 64
                    )
                _refresh_scoped_receipt(receipt)
                _write_json(receipt_path, receipt)
                _refresh_manifest(snapshot)
                with self.assertRaisesRegex(ValueError, message):
                    _validate(snapshot, decisions)

    def test_coherent_country_relabel_is_rejected_by_boundary_geometry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            snapshot, decisions = _write_fixture(root)
            decision_payload = _read_json(decisions)
            decision_rows = decision_payload.get("decisions")
            if not isinstance(decision_rows, list) or not isinstance(
                decision_rows[0], dict
            ):
                self.fail("fixture decisions must contain an object")
            row = decision_rows[0]
            detail = row.get("decision")
            if not isinstance(detail, dict):
                self.fail("fixture decision detail must be an object")
            row["governed_country_code"] = "NO"
            detail["candidate_countries"] = ["Norway"]
            detail["derived_country"] = "Norway"
            decision_payload["country_counts"] = {
                "SE": 0,
                "DK": 0,
                "NO": 1,
                "FI": 0,
                "UNASSIGNED": 0,
            }
            _write_json(decisions, decision_payload)
            assignment = [{"site_id": 1, "country_code": "NO"}]
            assignment_sha256 = _digest(_canonical_bytes(assignment))
            for receipt_path in (snapshot / "receipts").glob("*.json"):
                receipt = _read_json(receipt_path)
                receipt_scope = receipt.get("spatial_scope")
                if not isinstance(receipt_scope, dict):
                    self.fail("fixture receipt spatial scope must be an object")
                receipt_scope["country_assignment_sha256"] = assignment_sha256
                queries = receipt.get("query_receipts")
                if not isinstance(queries, list):
                    self.fail("fixture query receipts must be a list")
                for query in queries:
                    if not isinstance(query, dict):
                        self.fail("fixture query receipt must be an object")
                    query_scope = query.get("spatial_scope")
                    if not isinstance(query_scope, dict):
                        self.fail("fixture query spatial scope must be an object")
                    query_scope["country_assignment_sha256"] = assignment_sha256
                    _refresh_query_receipt(query)
                if receipt.get("table") == "tbl_sites":
                    receipt["governed_country_assignments"] = assignment
                _refresh_scoped_receipt(receipt)
                _write_json(receipt_path, receipt)
            countries_path = snapshot / "reconciliation" / "countries.json"
            countries = _read_json(countries_path)
            countries["counts"] = {
                "SE": 0,
                "DK": 0,
                "NO": 1,
                "FI": 0,
                "UNASSIGNED": 0,
            }
            countries["country_assignment_sha256"] = assignment_sha256
            _write_json(countries_path, countries)
            _refresh_manifest(snapshot)

            with self.assertRaisesRegex(ValueError, "country geometry assignment"):
                _validate(snapshot, decisions)
