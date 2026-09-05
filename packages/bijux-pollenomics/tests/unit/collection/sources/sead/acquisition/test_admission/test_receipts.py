"""Receipts tests."""

from __future__ import annotations
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
import tempfile
from typing import cast
import unittest
from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    validate_sead_acquisition_admission,
)
from bijux_pollenomics.collection.sources.sead.acquisition.admission.validation import (
    receipts as admission_receipts,
)
from .fixtures import (
    _BUILD_ID,
    _PARENT_RUN_ID,
    _RUN_ID,
    _SCOPE_ID,
    _canonical_bytes,
    _digest,
    _expected_identity,
    _first_query_receipt,
    _query_receipt,
    _read_json,
    _refresh_manifest,
    _refresh_query_receipt,
    _refresh_scoped_receipt,
    _validate,
    _write_fixture,
    _write_json,
)


class SeadAcquisitionAdmissionTests(unittest.TestCase):
    def test_query_receipts_and_requested_identities_are_recomputed(self) -> None:
        for table, mutation, message in (
            (
                "tbl_sites",
                "missing_queries",
                "Nonempty SEAD table lacks query receipts",
            ),
            ("tbl_sites", "forged_query_id", "query receipt 0 receipt_id"),
            ("tbl_sample_groups", "forged_requested_ids", "requested identities"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                snapshot, decisions = _write_fixture(root)
                receipt_path = snapshot / "receipts" / f"{table}.json"
                receipt = _read_json(receipt_path)
                if mutation == "missing_queries":
                    receipt["query_count"] = 0
                    receipt["query_receipts"] = []
                elif mutation == "forged_query_id":
                    queries = receipt.get("query_receipts")
                    if not isinstance(queries, list) or not isinstance(
                        queries[0], dict
                    ):
                        self.fail("fixture query receipts must be object rows")
                    queries[0]["receipt_id"] = "sead-receipt:" + "f" * 64
                else:
                    receipt["requested_identity_count"] = 0
                    receipt["requested_identities"] = []
                    receipt["query_count"] = 0
                    receipt["query_receipts"] = []
                _refresh_scoped_receipt(receipt)
                _write_json(receipt_path, receipt)
                _refresh_manifest(snapshot)

                with self.assertRaisesRegex(ValueError, message):
                    _validate(snapshot, decisions)

    def test_aggregate_receipt_contract_fields_are_exactly_pinned(self) -> None:
        for mutation, message in (
            ("primary_key", "declared primary_key"),
            ("projection", "declared projection"),
            ("filter_field", "filter_field"),
            ("route", "route"),
            ("tool_version", "tool_version"),
            ("completion_basis", "completion_basis"),
            ("country_scope", "country_scope"),
            ("relation_scope", "relation_scope"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                snapshot, decisions = _write_fixture(root)
                receipt_path = snapshot / "receipts" / "tbl_sites.json"
                receipt = _read_json(receipt_path)
                if mutation == "primary_key":
                    receipt[mutation] = "forged_site_id"
                elif mutation == "projection":
                    receipt[mutation] = "site_id"
                elif mutation == "filter_field":
                    receipt[mutation] = "site_uuid"
                elif mutation == "country_scope":
                    receipt[mutation] = ["SE"]
                elif mutation == "relation_scope":
                    scope = receipt.get("spatial_scope")
                    if not isinstance(scope, dict):
                        self.fail("fixture spatial_scope must be an object")
                    scope[mutation] = "sites_only"
                else:
                    receipt[mutation] = "forged"
                _refresh_scoped_receipt(receipt)
                _write_json(receipt_path, receipt)
                _refresh_manifest(snapshot)

                with self.assertRaisesRegex(ValueError, message):
                    _validate(snapshot, decisions)

    def test_nested_query_contract_and_filter_parameters_are_exactly_pinned(
        self,
    ) -> None:
        for mutation, message in (
            ("route", "query receipt 0 route"),
            ("tool_version", "query receipt 0 tool_version"),
            ("country_scope", "query receipt 0 country_scope"),
            ("endpoint", "query receipt 0 endpoint"),
            ("order_by", "query receipt 0 order_by"),
            ("parameters", "query receipt 0 parameters"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                snapshot, decisions = _write_fixture(root)
                receipt_path = snapshot / "receipts" / "tbl_sample_groups.json"
                receipt = _read_json(receipt_path)
                query = _first_query_receipt(receipt)
                if mutation == "country_scope":
                    query[mutation] = ["SE"]
                elif mutation == "order_by":
                    query[mutation] = ["sample_group_id"]
                elif mutation == "parameters":
                    parameters = query.get("parameters")
                    if not isinstance(parameters, list) or not isinstance(
                        parameters[1], list
                    ):
                        self.fail("fixture query parameters must be pairs")
                    parameters[1] = ["site_id", "in.(999)"]
                else:
                    query[mutation] = "forged"
                _refresh_query_receipt(query)
                _refresh_scoped_receipt(receipt)
                _write_json(receipt_path, receipt)
                _refresh_manifest(snapshot)

                with self.assertRaisesRegex(ValueError, message):
                    _validate(snapshot, decisions)

    def test_pagination_and_preflight_parameter_bounds_are_exact(self) -> None:
        for mutation, message in (
            ("page_size", "page_size must be a positive integer"),
            ("max_pages", "max_pages must be a positive integer"),
            ("page_number", "page number"),
            ("page_range", "page range"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                snapshot, decisions = _write_fixture(root)
                receipt_path = snapshot / "receipts" / "tbl_sample_groups.json"
                receipt = _read_json(receipt_path)
                query = _first_query_receipt(receipt)
                pagination = query.get("pagination")
                if not isinstance(pagination, dict):
                    self.fail("fixture pagination must be an object")
                if mutation in {"page_size", "max_pages"}:
                    pagination[mutation] = 0
                else:
                    pages = pagination.get("pages")
                    if not isinstance(pages, list) or not isinstance(pages[0], dict):
                        self.fail("fixture pages must be object rows")
                    pages[0]["page" if mutation == "page_number" else "range"] = (
                        2 if mutation == "page_number" else "1-1000"
                    )
                _refresh_query_receipt(query)
                _refresh_scoped_receipt(receipt)
                _write_json(receipt_path, receipt)
                _refresh_manifest(snapshot)

                with self.assertRaisesRegex(ValueError, message):
                    _validate(snapshot, decisions)

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            snapshot, decisions = _write_fixture(root)
            payload = _read_json(decisions)
            preflight = payload.get("preflight_receipt")
            if not isinstance(preflight, dict):
                self.fail("fixture preflight must be an object")
            parameters = preflight.get("parameters")
            if not isinstance(parameters, list):
                self.fail("fixture preflight parameters must be a list")
            parameters.append(["site_id", "eq.1"])
            _refresh_query_receipt(preflight)
            _write_json(decisions, payload)
            with self.assertRaisesRegex(ValueError, "preflight receipt parameters"):
                _validate(snapshot, decisions)

    def test_preflight_scope_and_max_pages_are_exactly_pinned(self) -> None:
        for mutation, message in (
            ("max_pages", "max_pages"),
            ("spatial_bbox", "preflight spatial bbox"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                snapshot, decisions = _write_fixture(root)
                payload = _read_json(decisions)
                preflight = payload.get("preflight_receipt")
                if not isinstance(preflight, dict):
                    self.fail("fixture preflight must be an object")
                if mutation == "max_pages":
                    pagination = preflight.get("pagination")
                    if not isinstance(pagination, dict):
                        self.fail("fixture preflight pagination must be an object")
                    pagination["max_pages"] = 123
                else:
                    spatial_scope = preflight.get("spatial_scope")
                    if not isinstance(spatial_scope, dict):
                        self.fail("fixture preflight spatial scope must be an object")
                    spatial_scope["bbox"] = [0.0, 0.0, 1.0, 1.0]
                _refresh_query_receipt(preflight)
                _write_json(decisions, payload)

                with self.assertRaisesRegex(ValueError, message):
                    _validate(snapshot, decisions)

    def test_nested_payload_and_attempt_claims_are_recomputed(self) -> None:
        for mutation, message in (
            ("content", "reconstructed canonical_schema"),
            ("attempts", "attempt count"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                snapshot, decisions = _write_fixture(root)
                receipt_path = snapshot / "receipts" / "tbl_sample_groups.json"
                receipt = _read_json(receipt_path)
                query = _first_query_receipt(receipt)
                if mutation == "content":
                    query["content_sha256"] = "f" * 64
                    query["canonical_schema"] = {
                        "row_count": 0,
                        "fields": [
                            {
                                "name": "forged",
                                "presence_count": 0,
                                "null_count": 0,
                                "json_types": [],
                            }
                        ],
                    }
                    query["canonical_schema_sha256"] = _digest(
                        _canonical_bytes(query["canonical_schema"])
                    )
                else:
                    query["result"] = {
                        "attempt_count": 0,
                        "failure_count": 0,
                        "retry_count": 999,
                    }
                _refresh_query_receipt(query)
                _refresh_scoped_receipt(receipt)
                _write_json(receipt_path, receipt)
                _refresh_manifest(snapshot)

                with self.assertRaisesRegex(ValueError, message):
                    _validate(snapshot, decisions)

    def test_bbox_query_payload_identity_is_independently_pinned(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            snapshot, decisions = _write_fixture(root)
            expected = _expected_identity(snapshot, decisions)
            decision_payload = _read_json(decisions)
            preflight = decision_payload.get("preflight_receipt")
            if not isinstance(preflight, dict):
                self.fail("fixture preflight must be an object")
            preflight["content_sha256"] = "f" * 64
            _refresh_query_receipt(preflight)
            _write_json(decisions, decision_payload)
            site_receipt_path = snapshot / "receipts" / "tbl_sites.json"
            site_receipt = _read_json(site_receipt_path)
            site_query = _first_query_receipt(site_receipt)
            site_query["content_sha256"] = "f" * 64
            _refresh_query_receipt(site_query)
            _refresh_scoped_receipt(site_receipt)
            _write_json(site_receipt_path, site_receipt)
            _refresh_manifest(snapshot)
            expected = replace(
                expected,
                acquisition_manifest_sha256=_digest(
                    (snapshot / "manifest.json").read_bytes()
                ),
                country_decisions_sha256=_digest(decisions.read_bytes()),
            )

            with self.assertRaisesRegex(
                ValueError, "caller-pinned preflight payload SHA-256"
            ):
                validate_sead_acquisition_admission(
                    snapshot,
                    country_decisions_path=decisions,
                    expected_identity=expected,
                )

    def test_empty_dependency_queries_and_full_terminal_pages_are_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            snapshot, decisions = _write_fixture(root)
            receipt_path = snapshot / "receipts" / "tbl_physical_samples.json"
            receipt = _read_json(receipt_path)
            spatial_scope = receipt.get("spatial_scope")
            if not isinstance(spatial_scope, dict):
                self.fail("fixture spatial scope must be an object")
            receipt["query_receipts"] = [
                _query_receipt(
                    "tbl_physical_samples",
                    rows=[],
                    spatial_scope={
                        **spatial_scope,
                        "kind": "dependency_identity_filter",
                        "filter_field": "sample_group_id",
                        "filter_ids": [],
                    },
                )
            ]
            receipt["query_count"] = 1
            _refresh_scoped_receipt(receipt)
            _write_json(receipt_path, receipt)
            _refresh_manifest(snapshot)
            with self.assertRaisesRegex(ValueError, "must not contain query receipts"):
                _validate(snapshot, decisions)

        rows: list[dict[str, object]] = [
            {
                "sample_group_id": index,
                "site_id": 1,
                "sample_group_name": None,
            }
            for index in range(1, 1001)
        ]
        query = _query_receipt(
            "tbl_sample_groups",
            rows=rows,
            spatial_scope={
                "scope_id": _SCOPE_ID,
                "relation_scope": "chronology_relations",
                "countries": ["SE", "DK", "NO", "FI"],
                "bbox": [4.0, 54.0, 35.0, 72.0],
                "country_assignment_id": "sha256:" + "3" * 64,
                "country_assignment_sha256": "4" * 64,
                "orchestration_run_id": _RUN_ID,
                "parent_run_id": _PARENT_RUN_ID,
                "build_id": _BUILD_ID,
                "kind": "dependency_identity_filter",
                "filter_field": "site_id",
                "filter_ids": [1],
            },
        )
        with self.assertRaisesRegex(ValueError, "lacks a short terminal page"):
            admission_receipts._validate_acquisition_receipt(
                query,
                table="tbl_sample_groups",
                identities={
                    "scope_id": _SCOPE_ID,
                    "run_id": _RUN_ID,
                    "parent_run_id": _PARENT_RUN_ID,
                    "build_id": _BUILD_ID,
                },
                label="full terminal page",
                require_orchestration_identity=True,
                expected_parameters=cast(Sequence[Sequence[str]], query["parameters"]),
                expected_order=cast(Sequence[str], query["order_by"]),
                expected_max_pages=10_000,
                expected_rows=rows,
            )
