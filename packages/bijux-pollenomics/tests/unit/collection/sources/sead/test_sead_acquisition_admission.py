from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import cast
import unittest
from unittest.mock import patch

from bijux_pollenomics.collection.sources.boundaries.collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_RELEASE_PAGE_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)
from bijux_pollenomics.collection.sources.sead import (
    acquisition_admission as admission_module,
)
from bijux_pollenomics.collection.sources.sead.acquisition import (
    ACQUISITION_MANIFEST_SCHEMA_VERSION,
    ACQUISITION_RECEIPT_SCHEMA_VERSION,
    TABLE_PAYLOAD_SCHEMA_VERSION,
    reconcile_sead_join,
)
from bijux_pollenomics.collection.sources.sead.acquisition_admission import (
    ADMISSION_SCHEMA_VERSION,
    SeadAcquisitionAdmission,
    SeadAdmissionExpectedIdentity,
    materialize_sead_acquisition_admission,
    validate_sead_acquisition_admission,
)
from bijux_pollenomics.collection.sources.sead.api_client import (
    SEAD_LIMIT,
    SEAD_POSTGREST_ROOT,
    build_sead_in_filter,
)
from bijux_pollenomics.collection.sources.sead.archive import (
    SEAD_LINKED_SOURCE_TABLES,
)
from bijux_pollenomics.collection.sources.sead.scoped_acquisition import (
    SCOPED_RECEIPT_SCHEMA_VERSION,
    SEAD_SCOPED_TABLE_PLANS,
)

_RUN_ID = "sead-live-fixture"
_SCOPE_ID = "sha256:" + "1" * 64
_PARENT_RUN_ID = "JOB-SEAD-FIXTURE"
_BUILD_ID = "sha256:" + "2" * 64
_SITE_PROJECTION = (
    "site_id,site_name,national_site_identifier,latitude_dd,longitude_dd,"
    "altitude,site_description,site_uuid"
)
_TABLE_PRIMARY_KEYS = {
    "tbl_sites": "site_id",
    "tbl_sample_groups": "sample_group_id",
    "tbl_physical_samples": "physical_sample_id",
    "tbl_analysis_entities": "analysis_entity_id",
    "tbl_analysis_entity_ages": "analysis_entity_age_id",
    "tbl_geochronology": "geochron_id",
    "tbl_dendro_dates": "dendro_date_id",
    "tbl_analysis_values": "analysis_value_id",
    "tbl_analysis_dating_ranges": "analysis_dating_range_id",
    "tbl_age_types": "age_type_id",
    "tbl_relative_dates": "relative_date_id",
    "tbl_relative_ages": "relative_age_id",
    "tbl_relative_age_refs": "relative_age_ref_id",
    "tbl_dating_uncertainty": "dating_uncertainty_id",
    "tbl_methods": "method_id",
    "tbl_datasets": "dataset_id",
    "tbl_site_references": "site_reference_id",
    "tbl_sample_group_references": "sample_group_reference_id",
    "tbl_biblio": "biblio_id",
}
_JOIN_TABLES = {
    "sites.sample_groups": ("tbl_sites", "tbl_sample_groups"),
    "sample_groups.physical_samples": (
        "tbl_sample_groups",
        "tbl_physical_samples",
    ),
    "physical_samples.analysis_entities": (
        "tbl_physical_samples",
        "tbl_analysis_entities",
    ),
    "analysis_entities.analysis_entity_ages": (
        "tbl_analysis_entities",
        "tbl_analysis_entity_ages",
    ),
    "analysis_entities.geochronology": (
        "tbl_analysis_entities",
        "tbl_geochronology",
    ),
    "analysis_entities.dendro_dates": (
        "tbl_analysis_entities",
        "tbl_dendro_dates",
    ),
    "analysis_entities.analysis_values": (
        "tbl_analysis_entities",
        "tbl_analysis_values",
    ),
    "analysis_values.analysis_dating_ranges": (
        "tbl_analysis_values",
        "tbl_analysis_dating_ranges",
    ),
    "analysis_entities.relative_dates": (
        "tbl_analysis_entities",
        "tbl_relative_dates",
    ),
    "relative_ages.relative_age_refs": (
        "tbl_relative_ages",
        "tbl_relative_age_refs",
    ),
    "sites.site_references": ("tbl_sites", "tbl_site_references"),
    "sample_groups.sample_group_references": (
        "tbl_sample_groups",
        "tbl_sample_group_references",
    ),
    "age_types.analysis_dating_ranges": (
        "tbl_age_types",
        "tbl_analysis_dating_ranges",
    ),
    "age_types.dendro_dates": ("tbl_age_types", "tbl_dendro_dates"),
    "relative_ages.relative_dates": ("tbl_relative_ages", "tbl_relative_dates"),
    "dating_uncertainty.analysis_dating_ranges": (
        "tbl_dating_uncertainty",
        "tbl_analysis_dating_ranges",
    ),
    "dating_uncertainty.geochronology": (
        "tbl_dating_uncertainty",
        "tbl_geochronology",
    ),
    "dating_uncertainty.dendro_dates": (
        "tbl_dating_uncertainty",
        "tbl_dendro_dates",
    ),
    "dating_uncertainty.relative_dates": (
        "tbl_dating_uncertainty",
        "tbl_relative_dates",
    ),
    "methods.relative_dates": ("tbl_methods", "tbl_relative_dates"),
    "datasets.analysis_entities": ("tbl_datasets", "tbl_analysis_entities"),
    "biblio.datasets": ("tbl_biblio", "tbl_datasets"),
    "biblio.site_references": ("tbl_biblio", "tbl_site_references"),
    "biblio.sample_group_references": (
        "tbl_biblio",
        "tbl_sample_group_references",
    ),
    "biblio.relative_age_refs": ("tbl_biblio", "tbl_relative_age_refs"),
}


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
                    "acquisition_admission.os.replace",
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
                "acquisition_admission.os.replace",
                side_effect=mutate_source_then_publish,
            ):
                result = _materialize(snapshot, decisions, root / "admitted")

            self.assertEqual(
                (result.output_root / "payloads" / "tbl_sites.json").read_bytes(),
                validated_bytes,
            )
            self.assertNotEqual(payload_path.read_bytes(), validated_bytes)

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
            admission_module._validate_acquisition_receipt(
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


def _expected_identity(
    snapshot: Path, decisions: Path
) -> SeadAdmissionExpectedIdentity:
    decision_payload = _read_json(decisions)
    boundary_authority = decision_payload.get("boundary_authority")
    if not isinstance(boundary_authority, dict):
        raise TypeError("fixture boundary authority must be an object")
    preflight = decision_payload.get("preflight_receipt")
    if not isinstance(preflight, dict):
        raise TypeError("fixture preflight receipt must be an object")
    return SeadAdmissionExpectedIdentity(
        scope_id=_SCOPE_ID,
        run_id=_RUN_ID,
        parent_run_id=_PARENT_RUN_ID,
        build_id=_BUILD_ID,
        country_authority_id=str(boundary_authority["authority_id"]),
        country_authority_artifact_digest=str(boundary_authority["artifact_digest"]),
        country_authority_root=(snapshot.parent.parent / "boundaries").resolve(),
        bbox_payload_sha256=str(preflight["content_sha256"]),
        acquisition_manifest_sha256=_digest((snapshot / "manifest.json").read_bytes()),
        country_decisions_sha256=_digest(decisions.read_bytes()),
    )


def _validate(snapshot: Path, decisions: Path) -> dict[str, object]:
    return validate_sead_acquisition_admission(
        snapshot,
        country_decisions_path=decisions,
        expected_identity=_expected_identity(snapshot, decisions),
    )


def _materialize(
    snapshot: Path, decisions: Path, output_root: Path
) -> SeadAcquisitionAdmission:
    return materialize_sead_acquisition_admission(
        snapshot,
        country_decisions_path=decisions,
        output_root=output_root,
        expected_identity=_expected_identity(snapshot, decisions),
    )


def _write_fixture(root: Path) -> tuple[Path, Path]:
    boundary_root, authority_id, authority_digest, boundary_version = (
        _write_boundary_fixture(root)
    )
    if boundary_root != (root / "boundaries").resolve():
        raise ValueError("fixture boundary root mismatch")
    boundary_manifest = _read_json(boundary_root / "raw" / "source_manifest.json")
    country_artifacts = boundary_manifest.get("country_artifacts")
    if not isinstance(country_artifacts, dict):
        raise TypeError("fixture country artifacts must be an object")
    country_artifact_sha256 = {
        country: str(record["sha256"])
        for country, record in country_artifacts.items()
        if isinstance(country, str) and isinstance(record, dict)
    }
    snapshot = root / "source" / "snapshot"
    rows_by_table: dict[str, list[dict[str, object]]] = {
        table: [] for table in SEAD_LINKED_SOURCE_TABLES
    }
    rows_by_table["tbl_sites"] = [
        {
            "site_id": 1,
            "site_name": "fixture",
            "national_site_identifier": None,
            "latitude_dd": 56.0,
            "longitude_dd": 13.0,
            "altitude": None,
            "site_description": None,
            "site_uuid": "fixture-site-uuid",
        }
    ]
    assignment_payload = [{"site_id": 1, "country_code": "SE"}]
    assignment_sha256 = _digest(_canonical_bytes(assignment_payload))
    base_scope: dict[str, object] = {
        "scope_id": _SCOPE_ID,
        "relation_scope": "chronology_relations",
        "countries": ["SE", "DK", "NO", "FI"],
        "bbox": [4.0, 54.0, 35.0, 72.0],
        "country_assignment_id": authority_id,
        "country_assignment_sha256": assignment_sha256,
        "orchestration_run_id": _RUN_ID,
        "parent_run_id": _PARENT_RUN_ID,
        "build_id": _BUILD_ID,
    }
    plans = {plan.table: plan for plan in SEAD_SCOPED_TABLE_PLANS}
    for table, rows in rows_by_table.items():
        primary_key = _TABLE_PRIMARY_KEYS[table]
        projection = (
            _SITE_PROJECTION if table == "tbl_sites" else plans[table].projection
        )
        payload = {
            "schema_version": TABLE_PAYLOAD_SCHEMA_VERSION,
            "table": table,
            "rows": rows,
        }
        payload_path = snapshot / "payloads" / f"{table}.json"
        _write_json(payload_path, payload)
        schema = _observed_schema(rows)
        if table == "tbl_sites":
            requested_ids = [1]
            query_receipts = [
                _query_receipt(
                    table,
                    rows=rows,
                    spatial_scope={**base_scope, "kind": "governed_bbox"},
                )
            ]
        else:
            plan = plans[table]
            requested_ids = sorted(
                {
                    _fixture_positive_int(row[dependency.field])
                    for dependency in plan.dependencies
                    for row in rows_by_table[dependency.table]
                    if row.get(dependency.field) is not None
                }
            )
            query_receipts = (
                [
                    _query_receipt(
                        table,
                        rows=rows,
                        spatial_scope={
                            **base_scope,
                            "kind": "dependency_identity_filter",
                            "filter_field": plan.filter_field,
                            "filter_ids": requested_ids,
                        },
                    )
                ]
                if requested_ids
                else []
            )
        receipt: dict[str, object] = {
            "schema_version": SCOPED_RECEIPT_SCHEMA_VERSION,
            "source": "SEAD",
            "route": "postgrest_dependency_scoped",
            "table": table,
            "primary_key": primary_key,
            "projection": projection,
            "filter_field": primary_key
            if table == "tbl_sites"
            else plans[table].filter_field,
            "requested_identity_count": len(requested_ids),
            "requested_identities": requested_ids,
            "query_count": len(query_receipts),
            "query_receipts": query_receipts,
            "completion_basis": (
                "governed_bbox_filter"
                if table == "tbl_sites"
                else (
                    "all_dependency_batches_complete"
                    if requested_ids
                    else "empty_dependency_identity_set"
                )
            ),
            "country_scope": ["SE", "DK", "NO", "FI"],
            "spatial_scope": base_scope,
            "scope_id": _SCOPE_ID,
            "run_id": _RUN_ID,
            "parent_run_id": _PARENT_RUN_ID,
            "build_id": _BUILD_ID,
            "started_at": "2026-09-04T00:00:00Z",
            "completed_at": "2026-09-04T00:00:01Z",
            "row_count": len(rows),
            "canonical_schema": schema,
            "canonical_schema_sha256": _digest(_canonical_bytes(schema)),
            "content_sha256": _digest(payload_path.read_bytes()),
            "tool_version": "sead-scoped-relation-acquisition.v1",
            "status": "complete",
            "failure_reason": None,
        }
        if table == "tbl_sites":
            receipt.update(
                {
                    "bbox_row_count": 1,
                    "governed_row_count": 1,
                    "scope_excluded_site_ids": [],
                    "scope_exclusion_reason": "country_assignment_unassigned",
                    "governed_country_assignments": assignment_payload,
                }
            )
        _refresh_scoped_receipt(receipt)
        _write_json(snapshot / "receipts" / f"{table}.json", receipt)

    _write_json(
        snapshot / "reconciliation" / "countries.json",
        {
            "schema_version": "sead-country-reconciliation.v1",
            "scope_id": _SCOPE_ID,
            "run_id": _RUN_ID,
            "parent_run_id": _PARENT_RUN_ID,
            "build_id": _BUILD_ID,
            "row_count": 1,
            "counts": {"SE": 1, "DK": 0, "NO": 0, "FI": 0, "UNASSIGNED": 0},
            "assigned_count": 1,
            "unassigned_count": 0,
            "duplicate_site_ids": [],
            "reconciles": True,
            "bbox_row_count": 1,
            "scope_excluded_count": 0,
            "scope_excluded_site_ids": [],
            "country_assignment_id": authority_id,
            "country_assignment_sha256": assignment_sha256,
        },
    )
    _write_json(
        snapshot / "reconciliation" / "joins.json",
        {
            "schema_version": "sead-join-reconciliations.v1",
            "edges": [
                _join_row(edge, parent, child, rows_by_table)
                for edge, (parent, child) in _JOIN_TABLES.items()
            ],
        },
    )
    _refresh_manifest(snapshot)
    decisions = root / "source" / "country-decisions.json"
    _write_json(
        decisions,
        {
            "schema_version": "sead-live-country-decisions.v1",
            "job_id": _PARENT_RUN_ID,
            "run_id": _RUN_ID,
            "input_id": _SCOPE_ID,
            "build_id": _BUILD_ID,
            "bbox": [4.0, 54.0, 35.0, 72.0],
            "bbox_site_count": 1,
            "boundary_authority": {
                "schema": "nordic-boundary-authority-identity.v1",
                "authority_id": authority_id,
                "artifact_digest": authority_digest,
                "version": NATURAL_EARTH_VERSION,
                "manifest_sha256": _digest(
                    (boundary_root / "raw" / "source_manifest.json").read_bytes()
                ),
                "normalized_artifact_sha256": authority_digest.removeprefix("sha256:"),
                "source_asset_sha256": "6" * 64,
                "country_artifact_sha256": {
                    country: country_artifact_sha256[country]
                    for country in BOUNDARY_CODES
                },
            },
            "preflight_receipt": _query_receipt(
                "tbl_sites",
                rows=rows_by_table["tbl_sites"],
                spatial_scope={
                    **base_scope,
                    "scope_id": _SCOPE_ID,
                    "kind": "governed_bbox_country_decision_preflight",
                    "boundary_authority_id": authority_id,
                },
                parameters=[
                    [
                        "select",
                        _SITE_PROJECTION,
                    ],
                    ["latitude_dd", "gte.54.0"],
                    ["latitude_dd", "lte.72.0"],
                    ["longitude_dd", "gte.4.0"],
                    ["longitude_dd", "lte.35.0"],
                    ["order", "site_id"],
                ],
                max_pages=100,
            ),
            "country_counts": {
                "SE": 1,
                "DK": 0,
                "NO": 0,
                "FI": 0,
                "UNASSIGNED": 0,
            },
            "decision_method_counts": {"strict_boundary_containment": 1},
            "decision_status_counts": {"assigned": 1},
            "decisions": [
                {
                    "site_id": 1,
                    "site_uuid": "fixture-site-uuid",
                    "latitude_dd": 56.0,
                    "longitude_dd": 13.0,
                    "governed_country_code": "SE",
                    "decision": {
                        "decision_status": "assigned",
                        "decision_method": "strict_boundary_containment",
                        "candidate_countries": ["Sweden"],
                        "derived_country": "Sweden",
                        "ambiguity_reason": None,
                        "refusal_reason": None,
                        "raw_country": None,
                        "raw_country_comparison": "not_supplied",
                        "boundary_artifact_digest": authority_digest,
                        "boundary_version": boundary_version,
                    },
                }
            ],
        },
    )
    return snapshot.resolve(), decisions.resolve()


def _write_boundary_fixture(root: Path) -> tuple[Path, str, str, str]:
    boundary_root = (root / "boundaries").resolve()
    boxes = {
        "Sweden": (12.0, 55.0, 14.0, 57.0),
        "Norway": (8.0, 59.0, 10.0, 61.0),
        "Finland": (23.0, 59.0, 25.0, 61.0),
        "Denmark": (8.0, 54.0, 10.0, 55.0),
    }
    country_records: dict[str, dict[str, object]] = {}
    normalized_features: list[dict[str, object]] = []
    for country, code in BOUNDARY_CODES.items():
        minimum_x, minimum_y, maximum_x, maximum_y = boxes[country]
        collection: dict[str, object] = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"ADM0_A3": code},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [minimum_x, minimum_y],
                                [maximum_x, minimum_y],
                                [maximum_x, maximum_y],
                                [minimum_x, maximum_y],
                                [minimum_x, minimum_y],
                            ]
                        ],
                    },
                }
            ],
        }
        features = collection["features"]
        if not isinstance(features, list) or not isinstance(features[0], dict):
            raise TypeError("fixture boundary features must contain an object")
        normalized_features.append(features[0])
        path = boundary_root / "raw" / f"{country.lower()}.geojson"
        _write_json(path, collection)
        digest = _digest(path.read_bytes())
        country_records[country] = {
            "path": path.name,
            "sha256": digest,
            "feature_count": 1,
        }
    normalized = {
        "type": "FeatureCollection",
        "features": normalized_features,
    }
    normalized_path = boundary_root / "normalized" / "nordic_country_boundaries.geojson"
    _write_json(normalized_path, normalized)
    normalized_digest = _digest(normalized_path.read_bytes())
    source_asset_sha256 = "6" * 64
    manifest = {
        "schema_version": "natural-earth-boundary-receipt.v1",
        "generated_on": "2026-09-04",
        "source": "Natural Earth",
        "dataset": "Admin 0 - Countries",
        "version": NATURAL_EARTH_VERSION,
        "release_page_url": NATURAL_EARTH_RELEASE_PAGE_URL,
        "asset_url": NATURAL_EARTH_ADMIN0_URL,
        "sha256": source_asset_sha256,
        "license": "public_domain",
        "license_url": NATURAL_EARTH_TERMS_URL,
        "source_crs": "EPSG:4326",
        "coordinate_transformation": "none",
        "country_selection_field": "ADM0_A3",
        "geometry_inclusion_policy": (
            "retain_all_geometry_parts_from_each_selected_admin0_feature"
        ),
        "feature_count": 258,
        "country_codes": BOUNDARY_CODES,
        "country_artifacts": country_records,
        "normalized_artifact": {
            "path": "normalized/nordic_country_boundaries.geojson",
            "sha256": normalized_digest,
            "feature_count": len(BOUNDARY_CODES),
        },
    }
    manifest_path = boundary_root / "raw" / "source_manifest.json"
    _write_json(manifest_path, manifest)
    identity = {
        "schema": "nordic-boundary-authority-identity.v1",
        "manifest_sha256": _digest(manifest_path.read_bytes()),
        "source_asset_sha256": source_asset_sha256,
        "country_artifact_sha256": {
            country: record["sha256"] for country, record in country_records.items()
        },
        "normalized_artifact_sha256": normalized_digest,
        "version": NATURAL_EARTH_VERSION,
    }
    authority_id = "sha256:" + _digest(_canonical_bytes(identity))
    return (
        boundary_root,
        authority_id,
        f"sha256:{normalized_digest}",
        f"natural-earth:{NATURAL_EARTH_VERSION}",
    )


def _query_receipt(
    table: str,
    *,
    rows: list[dict[str, object]],
    spatial_scope: Mapping[str, object],
    parameters: list[list[str]] | None = None,
    max_pages: int = 10_000,
) -> dict[str, object]:
    row_count = len(rows)
    plans = {plan.table: plan for plan in SEAD_SCOPED_TABLE_PLANS}
    if table == "tbl_sites":
        projection = _SITE_PROJECTION
        order_by = ["site_id"]
        default_parameters = [
            ["select", projection],
            ["latitude_dd", "gte.54.0"],
            ["latitude_dd", "lte.72.0"],
            ["longitude_dd", "gte.4.0"],
            ["longitude_dd", "lte.35.0"],
            ["order", "site_id"],
        ]
    else:
        plan = plans[table]
        projection = plan.projection
        order_by = [plan.filter_field, plan.primary_key]
        raw_filter_ids = spatial_scope.get("filter_ids")
        filter_ids = (
            [_fixture_positive_int(value) for value in raw_filter_ids]
            if isinstance(raw_filter_ids, list)
            else []
        )
        default_parameters = [
            ["select", projection],
            [plan.filter_field, build_sead_in_filter(filter_ids)],
            ["order", ",".join(order_by)],
        ]
    schema = _observed_schema(rows)
    payload = {
        "schema_version": TABLE_PAYLOAD_SCHEMA_VERSION,
        "table": table,
        "rows": rows,
    }
    receipt: dict[str, object] = {
        "schema_version": ACQUISITION_RECEIPT_SCHEMA_VERSION,
        "source": "SEAD",
        "route": "postgrest",
        "table": table,
        "endpoint": f"{SEAD_POSTGREST_ROOT}/{table}",
        "parameters": parameters if parameters is not None else default_parameters,
        "order_by": order_by,
        "country_scope": ["SE", "DK", "NO", "FI"],
        "spatial_scope": dict(spatial_scope),
        "parent_run_id": _PARENT_RUN_ID,
        "build_id": _BUILD_ID,
        "started_at": "2026-09-04T00:00:00Z",
        "completed_at": "2026-09-04T00:00:01Z",
        "row_count": row_count,
        "canonical_schema": schema,
        "canonical_schema_sha256": _digest(_canonical_bytes(schema)),
        "content_sha256": _digest(_canonical_bytes(payload)),
        "tool_version": "sead-postgrest-acquisition.v1",
        "status": "complete",
        "failure_reason": None,
        "failures": [],
        "pagination": {
            "complete": True,
            "max_pages": max_pages,
            "page_size": SEAD_LIMIT,
            "pages": [
                {
                    "page": 1,
                    "range": f"0-{SEAD_LIMIT - 1}",
                    "row_count": row_count,
                }
            ],
        },
        "result": {"attempt_count": 1, "failure_count": 0, "retry_count": 0},
    }
    receipt["receipt_id"] = "sead-receipt:" + _digest(_canonical_bytes(receipt))
    return receipt


def _join_row(
    edge: str,
    parent_table: str,
    child_table: str,
    rows_by_table: Mapping[str, list[dict[str, object]]],
) -> dict[str, object]:
    parent_key = _TABLE_PRIMARY_KEYS[parent_table]
    child_key = _TABLE_PRIMARY_KEYS[child_table]
    child_foreign_key = parent_key
    reference_required = edge in set(list(_JOIN_TABLES)[:12])
    parent_rows = rows_by_table[parent_table]
    all_child_rows = rows_by_table[child_table]
    referenced_child_rows = [
        row
        for row in all_child_rows
        if reference_required or row.get(child_foreign_key) is not None
    ]
    result = reconcile_sead_join(
        edge=edge,
        parent_rows=parent_rows,
        child_rows=referenced_child_rows,
        parent_key=parent_key,
        child_key=child_key,
        child_foreign_key=child_foreign_key,
    )
    parent_ids = {str(row[parent_key]) for row in parent_rows}
    child_counts: dict[str, int] = {}
    for row in referenced_child_rows:
        foreign_key = row.get(child_foreign_key)
        if foreign_key is not None:
            key = str(foreign_key)
            child_counts[key] = child_counts.get(key, 0) + 1
    matched_ids = sorted(parent_ids & set(child_counts))
    zero_ids = sorted(parent_ids - set(child_counts))
    result.update(
        {
            "scope_id": _SCOPE_ID,
            "run_id": _RUN_ID,
            "parent_run_id": _PARENT_RUN_ID,
            "build_id": _BUILD_ID,
            "reference_required": reference_required,
            "total_child_row_count": len(all_child_rows),
            "referenced_child_row_count": len(referenced_child_rows),
            "null_reference_child_count": 0,
            "null_reference_child_ids": [],
            "matched_parent_count": len(matched_ids),
            "matched_parent_ids": matched_ids,
            "zero_child_parent_count": len(zero_ids),
            "zero_child_parent_ids": zero_ids,
            "one_child_parent_count": sum(
                child_counts.get(key, 0) == 1 for key in parent_ids
            ),
            "many_child_parent_count": sum(
                child_counts.get(key, 0) > 1 for key in parent_ids
            ),
        }
    )
    return result


def _refresh_scoped_receipt(receipt: dict[str, object]) -> None:
    receipt.pop("receipt_id", None)
    receipt["receipt_id"] = "sead-scoped-receipt:" + _digest(_canonical_bytes(receipt))


def _first_query_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    queries = receipt.get("query_receipts")
    if not isinstance(queries, list) or not queries or not isinstance(queries[0], dict):
        raise ValueError("fixture query receipts must contain an object")
    return queries[0]


def _refresh_query_receipt(receipt: dict[str, object]) -> None:
    receipt.pop("receipt_id", None)
    receipt["receipt_id"] = "sead-receipt:" + _digest(_canonical_bytes(receipt))


def _refresh_manifest(snapshot: Path) -> None:
    files = []
    for relative_path in sorted(
        [
            *(f"payloads/{table}.json" for table in SEAD_LINKED_SOURCE_TABLES),
            *(f"receipts/{table}.json" for table in SEAD_LINKED_SOURCE_TABLES),
            "reconciliation/countries.json",
            "reconciliation/joins.json",
        ]
    ):
        content = (snapshot / relative_path).read_bytes()
        files.append(
            {
                "path": relative_path,
                "sha256": _digest(content),
                "byte_count": len(content),
            }
        )
    _write_json(
        snapshot / "manifest.json",
        {
            "schema_version": ACQUISITION_MANIFEST_SCHEMA_VERSION,
            "status": "complete",
            "required_tables": sorted(SEAD_LINKED_SOURCE_TABLES),
            "missing_required_tables": [],
            "incomplete_required_tables": [],
            "failed_join_edges": [],
            "country_reconciliation_status": "complete",
            "files": files,
        },
    )


def _observed_schema(rows: list[dict[str, object]]) -> dict[str, object]:
    fields = sorted({field for row in rows for field in row})
    return {
        "row_count": len(rows),
        "fields": [
            {
                "name": field,
                "presence_count": sum(field in row for row in rows),
                "null_count": sum(
                    row.get(field) is None for row in rows if field in row
                ),
                "json_types": sorted(
                    {_json_type(row[field]) for row in rows if field in row}
                ),
            }
            for field in fields
        ],
    }


def _json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_bytes(value))


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Fixture JSON must be an object: {path}")
    return value


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _fixture_positive_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("fixture source identity must be a positive integer")
    return value


if __name__ == "__main__":
    unittest.main()
