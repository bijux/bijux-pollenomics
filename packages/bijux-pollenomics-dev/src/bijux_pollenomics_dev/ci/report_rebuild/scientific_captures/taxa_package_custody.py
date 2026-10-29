"""Admit a frozen taxa package aggregate without reopening private products."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import (
    JsonObject,
    ReportRebuildError,
    canonical_json_sha256,
    require_mapping,
)
from ..ownership import _regular_confined_file

REPORT = "docs/report/taxa-review/package-custody.json"
OWNER = "taxa-review/package-custody"
REPORT_SHA256 = "a901097c3da24a7e1774aca4659dbb96d176c906438faae5bb96f90cf331b347"
REPORT_BYTES = 6506
PRODUCTS_SHA256 = "5f6daf40c14c46f455ec4ed609c8115f8162122a430f407761fd98575f206086"
SOURCE_CANDIDATE = "b30acdff340aa36c9ab28974232f73badd53393d"


def validate_package_custody(payload: JsonObject) -> JsonObject:
    """Keep structural custody separate from human, rights and scientific admission."""
    execution = require_mapping(
        payload.get("actual_current_execution"), "taxa execution"
    )
    products = require_mapping(payload.get("products"), "taxa product identities")
    if (
        payload.get("schema_version") != "taxon-review-package-custody.v1"
        or payload.get("candidate") != SOURCE_CANDIDATE
        or payload.get("native_sha256")
        != "8974ff060cf9f6a6b378e714df56a1ffbb7836cb5eb7884d472a252c61ec1838"
        or payload.get("independent_saved_output_admission_sha256")
        != "6cc619015ef58ab6eef6a307d0a5ee64652358fe836c706f1ca49c23f98a392c"
        or any(
            type(value) is not int or value != 0
            for value in (
                payload.get("actual_exit"),
                execution.get("native_exit"),
                execution.get("whole_runner_exit"),
                payload.get("accepted_samples"),
                payload.get("received_qualified_human_decisions"),
                payload.get("fresh_source_requests"),
            )
        )
        or execution.get("source_before_after_mismatches") != []
        or any(
            payload.get(key) is not False
            for key in (
                "canonical_import_allowed",
                "publication_allowed",
                "historical_missing_bundle_restored",
                "original_attribution_bytes_replayed",
                "original_primary_papers_verified",
                "prerequisite_factory_rebuilt_by_observer",
            )
        )
        or payload.get("rights_admission") != "not_evaluated"
        or payload.get("scientific_acceptance") != "not_evaluated"
        or payload.get("all_review_states") != {"needs_discussion": 10908}
        or any(
            type(payload.get(key)) is not int or payload[key] != count
            for key, count in {
                "review_rows": 10908,
                "basin_rows": 163,
                "chronology_rows": 10637,
                "parameter_authorities": 72,
                "parameter_concepts": 1006,
                "publication_records": 223,
                "native_datasets_with_citation_responses": 169,
                "complete_controlled_unresolved_return_routes": 3,
                "private_product_files": 20,
                "private_product_bytes": 110260059,
            }.items()
        )
        or len(products) != 20
        or canonical_json_sha256(products) != PRODUCTS_SHA256
    ):
        raise ReportRebuildError(
            "Frozen taxa package custody/status/product identities differ"
        )
    return {
        "source_candidate": SOURCE_CANDIDATE,
        "private_product_hash_entries": 20,
        "review_rows": 10908,
        "qualified_human_decisions": 0,
        "accepted_samples": 0,
        "scientific_acceptance": "not_evaluated",
        "rights_admission": "not_evaluated",
        "private_product_payloads_reopened": False,
        "historical_structural_readiness_owner_admitted": False,
    }


def validated_taxa_package_custody(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit only the exact aggregate and its independent retained-source owner."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared and not (repository / REPORT).exists():
        return (), {}
    entry = tracked_by_path.get(REPORT)
    if (
        len(declared) != 1
        or declared[0].get("role") != "retained_source"
        or declared[0].get("paths") != [REPORT]
        or declared[0].get("producer_paths") != []
        or declared[0].get("producer_inputs") != []
        or entry is None
        or entry.sha256 != REPORT_SHA256
        or entry.size != REPORT_BYTES
    ):
        raise ReportRebuildError(
            "Exact retained-source taxa aggregate ownership/Git identity required"
        )
    path: Path = _regular_confined_file(
        repository, REPORT, "taxa package custody aggregate"
    )
    if path.stat().st_nlink != 1 or path.stat().st_size != REPORT_BYTES:
        raise ReportRebuildError("Taxa package custody aggregate size/alias differs")
    raw = path.read_bytes()
    if len(raw) != REPORT_BYTES or hashlib.sha256(raw).hexdigest() != REPORT_SHA256:
        raise ReportRebuildError(
            "Frozen taxa package custody aggregate identity differs"
        )
    payload = require_mapping(json.loads(raw), "taxa package custody aggregate")
    return (entry,), {
        "owner_id": OWNER,
        "aggregate_sha256": REPORT_SHA256,
        **validate_package_custody(payload),
    }
