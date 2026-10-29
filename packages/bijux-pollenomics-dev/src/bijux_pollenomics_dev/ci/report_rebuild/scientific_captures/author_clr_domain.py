"""Admit the source-bound CLR zero-composition applicability observation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.ownership import _regular_confined_file

TOPIC = "docs/report/pollen-reconstruction/author-lra-constrained/clr-spatial-domain/"
SOURCES = "reports/science/author-love-clr-spatial-domain/"
AUTHORITY = "reports/science/source-cohorts/author-love-clr-spatial-domain.json"
OWNER = (
    "pollen-reconstruction/author-lra-constrained/clr-spatial-domain/report-products"
)
PRODUCTS = ("report.json", "trace-index.json")
METHODS = ("clr-ridge-20km", "clr-ridge-100km")
COUNTS = {
    "saved_nominal_requests": 39,
    "logical_ancestry_rows": 2715,
    "contexts": 225,
    "maintained_fit_API_attempts": 450,
    "actual_expected_domain_refusals": 450,
    "inner_dispositions": 420,
    "outer_candidate_dispositions": 30,
    "selected_outer_dispositions": 15,
    "selected_outer_refusals": 15,
    "successful_ridge_solves": 0,
    "new_REVEALS_runs": 0,
    "new_LOVE_runs": 0,
    "new_optimizer_attempts": 0,
    "new_kernel_calls": 0,
    "new_forward_calls": 0,
    "new_score_calls": 0,
}


def require(condition: bool, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not condition:
        raise ReportRebuildError("CLR domain observation: " + reason)


def identity(row: dict[str, Any]) -> tuple[str, int]:
    """Validate the declared retained-source identity."""
    checksum, size = row["sha256"], row["bytes"]
    require(
        isinstance(checksum, str)
        and len(checksum) == 64
        and all(c in "0123456789abcdef" for c in checksum)
        and type(size) is int
        and size >= 0,
        "exact finite object identity required",
    )
    return checksum, size


def validate_products(
    report: dict[str, Any], index: dict[str, Any], authority: dict[str, Any]
) -> JsonObject:
    """Check saved products against pinned source and scientific contracts."""
    require(
        authority["schema_version"] == "author-love-clr-output-review.v1"
        and authority["approved"] is True
        and authority["scientific_saved_products_admitted"] is True
        and type(authority["actual_exit"]) is int
        and authority["actual_exit"] == 0,
        "actual independent scientific output admission required",
    )
    status = authority["native_status"]
    require(
        all(
            type(status[k]) is int and status[k] == 0
            for k in ("native_exit", "stage_exit", "collector_exit")
        )
        and status["scientific_main_return"] == "not_observed_by_unchanged_consumer",
        "native success and uncaptured scientific main return are separate",
    )
    require(
        report["schema_version"] == "author-love-clr-domain-publication.v1"
        and report["candidate"] == authority["candidate"]
        and report["scientific_protocol"] == authority["protocol"]
        and report["scientific_acceptance"] == "not_evaluated",
        "original source epoch/protocol and scoped acceptance required",
    )
    counts = report["counts"]
    require(
        counts == COUNTS
        and all(type(counts[k]) is int for k in COUNTS)
        and all(authority["summary"][k] == value for k, value in COUNTS.items()),
        "complete450/420/30/15 population required",
    )
    domain = report["saved_domain"]
    require(
        domain["zero_containing_requests"] == 26
        and domain["zero_cells"] == 80
        and domain["geometry_records"] == 15
        and authority["summary"]["selected_zero_containing_requests"] == 26
        and authority["summary"]["selected_zero_cells"] == 80,
        "original39-vector zero domain required",
    )
    selected = report["selected_outer_dispositions"]
    require(
        isinstance(selected, list)
        and len(selected) == len({row["outer_target"] for row in selected}) == 15,
        "all15 independent outer dispositions required",
    )
    for row in selected:
        require(
            row["baseline"] == "clr-wgs84-rbf-ridge-v1"
            and row["status"] == "refused"
            and row["selected_method"] is None
            and row["reason_code"] == "no_eligible_spatial_scale"
            and row["outer_outcome_decoded"] is False
            and row["outer_score"] is None
            and row["ranking"]
            == [
                {
                    "method": method,
                    "complete_inner_predictions": 0,
                    "mean_inner_total_variation": None,
                }
                for method in METHODS
            ],
            "unscored null selection must never become a tuning winner",
        )
    require(
        report["original_nominal"]
        == {
            "native_exit": 1,
            "native_qualification": "refused_post_scientific_body_origin",
            "original_full_later_import_origins_and_final_return": "not established",
            "separate_saved_product_recovery_native_exit": 0,
            "source_candidate": "70dd58ce28071d3b4ef34af2c800370a52d42bf9",
        },
        "original nominal failure and separate recovery must remain literal",
    )
    require(
        index["schema_version"] == "author-love-clr-trace-index.v1"
        and index["all450_candidate_rows_and420_inner_rows_retained"] is True
        and index["raw_payloads_in_product_git"] is False
        and index["independent_output_review"]
        == authority["original_independent_review"],
        "independent full trace authority required",
    )
    expected = {Path(row["path"]).name: identity(row) for row in authority["products"]}
    objects = index["objects"]
    require(
        set(expected)
        == {"report.json", "candidate-refusals.json", "selection-freeze.json"}
        and len(objects) == 3
        and {row["logical_name"] for row in objects} == set(expected),
        "all three exact raw trace objects required",
    )
    for row in objects:
        require(
            identity(row) == expected[row["logical_name"]]
            and row["retention_key"] == "sha256:" + row["sha256"],
            "raw trace identity differs",
        )
    return {
        "maintained_fit_API_attempts": 450,
        "expected_domain_refusals": 450,
        "inner_dispositions": 420,
        "outer_candidate_dispositions": 30,
        "selected_outer_refusals": 15,
        "successful_ridge_solves": 0,
        "private_trace_payloads_read": 0,
        "new_model_or_score_calls": 0,
        "dataset_specific_domain_observation": True,
    }


def validated_author_clr_domain(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
    *,
    authority_sha256: str,
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate retained CLR domain evidence and exact source refusals."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared:
        return (), {}
    expected_paths = {TOPIC + name for name in PRODUCTS}
    paths = declared[0].get("paths")
    require(
        len(declared) == 1
        and declared[0].get("role") == "retained_source"
        and isinstance(paths, list)
        and len(paths) == 2
        and set(paths) == expected_paths,
        "one exact two-product CLR owner required",
    )
    authority_path = _regular_confined_file(
        repository, AUTHORITY, "CLR domain authority"
    )
    raw = authority_path.read_bytes()
    require(
        authority_path.stat().st_nlink == 1
        and hashlib.sha256(raw).hexdigest() == authority_sha256,
        "actual public authority changed",
    )
    authority = json.loads(raw)
    require(
        set(authority["public_products"]) == expected_paths,
        "exact two products required",
    )
    require(
        set(authority["public_sources"])
        == {
            SOURCES + name
            for name in (
                "protocol.json",
                "source-locations.json",
                "source/inputs.py",
                "source/replay.py",
            )
        },
        "exact scientific source/protocol/location map required",
    )
    bodies = {}
    for name, row in {
        **authority["public_sources"],
        **authority["public_products"],
    }.items():
        path = _regular_confined_file(repository, name, "CLR domain publication")
        body = path.read_bytes()
        require(
            path.stat().st_nlink == 1
            and identity(row) == (hashlib.sha256(body).hexdigest(), len(body)),
            "public scientific object changed",
        )
        bodies[name] = body
    entries = []
    for name in sorted(expected_paths):
        entry = tracked_by_path.get(name)
        require(
            entry is not None
            and (entry.sha256, entry.size)
            == identity(authority["public_products"][name]),
            "exact tracked two-product inventory required",
        )
        assert entry is not None
        entries.append(entry)
    evidence = validate_products(
        json.loads(bodies[TOPIC + "report.json"]),
        json.loads(bodies[TOPIC + "trace-index.json"]),
        authority,
    )
    evidence["authority_sha256"] = authority_sha256
    return tuple(entries), evidence
