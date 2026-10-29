"""Admit two compact products of the frozen source-derived GPM support proof."""

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

PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/ring-support/"
OWNER = "pollen-reconstruction/author-lra-constrained/ring-support/report-products"
AUTHORITY = "reports/science/source-cohorts/author-love-ring-support.json"
PRODUCTS = ("report.json", "trace-index.json")
SOURCE_CANDIDATE = "992257309805272a22e53c7ebb2cf5004117185e"
PINS = {
    "docs/report/pollen-reconstruction/author-lra-constrained/ring-support/report.json": {
        "sha256": "73e872e39f961de805c875a2a40d194a44befac3ab0edffb5d94f7ba6a2e7d29",
        "bytes": 29557,
    },
    "docs/report/pollen-reconstruction/author-lra-constrained/ring-support/trace-index.json": {
        "sha256": "b71738da7cd3732c73a0f42387afdaa8176c2977f7b5e3c50b1701d9a82db8ab",
        "bytes": 373,
    },
    "reports/science/author-love-ring-support/protocol.json": {
        "sha256": "8e0cf5c97bac4ab5c04f29e88e06a0948e91c6be4e4db4df1b2637cde993d9f8",
        "bytes": 8938,
    },
    "reports/science/author-love-ring-support/source-locations.json": {
        "sha256": "a066965a41dab2ba539c8fc9bf575452d93421024da93ccc5383d00d1f7b9c6b",
        "bytes": 1711,
    },
    "reports/science/author-love-ring-support/source/equivalence.py": {
        "sha256": "82d966d777269c70fd5501ce790e55b225fe9ed33584f00ce9fe6b11ce4de1a4",
        "bytes": 13841,
    },
    "reports/science/author-love-ring-support/source/projection.py": {
        "sha256": "f7dc5df50c1f1ecd07c430f957d9c32eed56e47c5c05f78c611edc25466150c1",
        "bytes": 11262,
    },
    "reports/science/author-love-ring-support/source/replay.py": {
        "sha256": "bf9e4f1c9ecb5620230c6a5ea3cde005665ee91917a562fafdab308c97b3ee81",
        "bytes": 14719,
    },
    "reports/science/source-cohorts/author-love-ring-support.json": {
        "sha256": "e3e7f1ace89f0fa956b9ac18372f2ebd165fadd15c2749467514d4745a73903c",
        "bytes": 4221,
    },
}


def require(condition: bool, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not condition:
        raise ReportRebuildError("Saved ring-support publication: " + reason)


def validate_products(
    report: dict[str, Any], index: dict[str, Any], authority: dict[str, Any]
) -> JsonObject:
    """Check saved products against pinned source and scientific contracts."""
    require(
        authority["schema_version"]
        == "author-love-ring-support-independent-output-review.v1"
        and authority["approved"] is True
        and authority["source_derived_equivalence_admitted"] is True
        and type(authority["actual_exit"]) is int
        and authority["actual_exit"] == 0,
        "independent source-derived output admission required",
    )
    require(
        report["schema_version"] == "author-love-ring-support-publication.v1"
        and report["source_candidate"] == authority["candidate"] == SOURCE_CANDIDATE
        and report["protocol_sha256"] == authority["protocol"]["sha256"],
        "source epoch or protocol differs",
    )
    expected = {
        "accepted_ring0_attempts": 1150,
        "equal_selected_covers": 39,
        "geometry_proofs": 15,
        "inner_projections": 630,
        "new_forward_calls": 0,
        "new_kernel_calls": 0,
        "new_optimizer_calls": 0,
        "new_prediction_manifests_executed": False,
        "new_score_calls": 0,
        "nominal_probability_value_projections": 675,
        "outer_projections": 45,
        "refused_ring0_attempts": 98,
        "saved_ring0_attempts": 1248,
        "selected_support_compositions": 39,
        "support_request_aliases": 39,
    }
    require(
        report["summary"] == authority["summary"] == expected,
        "exact saved populations and zero new calls required",
    )
    rows = report["request_equivalences"]
    require(
        len(rows)
        == len({row["original_request_sha256"] for row in rows})
        == len({row["support_request_sha256"] for row in rows})
        == 39,
        "complete unique39 request correspondence required",
    )
    require(
        all(
            type(row["accepted"]) is int
            and type(row["refused"]) is int
            and row["accepted"] >= 0
            and row["refused"] >= 0
            and row["accepted"] + row["refused"] == 32
            and row["ring0_equals_ring1_cover"] is True
            for row in rows
        )
        and sum(row["accepted"] for row in rows) == 1150
        and sum(row["refused"] for row in rows) == 98,
        "all1248 accepted/refused saved attempts required",
    )
    geometry = report["geometry_proofs"]
    require(
        len(geometry) == len({row["record_id"] for row in geometry}) == 15
        and all(
            row["conditional_kernel_value"] == 0.0
            and row["source_lower_distance_m"] == row["source_upper_distance_m"] == 1000
            and row["forward_inputs_equal_under_zero_row"] is True
            and row["homogeneous_same_cover_required"] is True
            and row["physical_rsap_validated"] is False
            and type(row["kernels_computed"]) is int
            and row["kernels_computed"] == 0
            for row in geometry
        ),
        "named zero-shell/homogeneous geometry scope required",
    )
    groups = {
        (row["kind"], row["baseline"]): row["slots"]
        for row in report["projection_groups"]
    }
    require(
        len(report["projection_groups"]) == 6
        and groups
        == {
            (kind, baseline): count
            for kind, count in (("inner", 210), ("outer", 15))
            for baseline in (
                "training_mean",
                "inverse_distance_squared",
                "nearest_site",
            )
        }
        and report["all_probability_values_equal_by_source_projection"] is True,
        "675 source-derived value projections required",
    )
    require(
        report["original_nominal"]
        == {
            "source_candidate": "70dd58ce28071d3b4ef34af2c800370a52d42bf9",
            "native_exit": 1,
            "native_qualification": "refused_post_scientific_body_origin",
            "saved_product_recovery_native_exit": 0,
            "full_later_import_origin_admission": "not established",
            "original_post_report_final_return": "not established",
        },
        "original nominal native1 and separate recovery0 required",
    )
    require(
        report["preserved_pure_function_qualifications"]
        == {
            "scientific_acceptance": "not_evaluated",
            "request_native_reuse_admitted": [False],
            "ring0_native_authority_status": "not_admitted_by_this_pure_function",
        },
        "original pure-function qualifications must remain literal",
    )
    observation = authority["observation"]
    require(
        index
        == {
            "schema_version": "author-love-ring-support-trace-index.v1",
            "objects": [
                {
                    "sha256": observation["sha256"],
                    "bytes": observation["bytes"],
                    "retention_key": "sha256:" + observation["sha256"],
                    "roles": ["source-derived-ring-support-proof"],
                }
            ],
        },
        "exact external detailed-proof identity required",
    )
    return {
        "support_request_aliases": 39,
        "saved_ring0_attempts": 1248,
        "accepted_ring0_attempts": 1150,
        "refused_ring0_attempts": 98,
        "selected_covers": 39,
        "geometry_proofs": 15,
        "conditional_probability_value_projections": 675,
        "private_trace_payloads_read": 0,
        "new_model_or_score_calls": 0,
        "source_derived_only": True,
    }


def validated_author_ring_support_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate retained author ring-support evidence and original inputs."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared:
        return (), {}
    paths = declared[0].get("paths")
    require(
        len(declared) == 1
        and declared[0].get("role") == "retained_source"
        and isinstance(paths, list)
        and all(isinstance(name, str) for name in paths)
        and len(paths) == 2
        and set(paths) == {PREFIX + name for name in PRODUCTS},
        "one exact two-product retained owner required",
    )
    bodies: dict[str, bytes] = {}
    for name, expected in PINS.items():
        path = _regular_confined_file(repository, name, "ring-support publication")
        require(
            path.stat().st_nlink == 1 and path.stat().st_size == expected["bytes"],
            "physical source/product size or alias differs",
        )
        raw = path.read_bytes()
        require(
            hashlib.sha256(raw).hexdigest() == expected["sha256"],
            "frozen public source/product bytes differ",
        )
        bodies[name] = raw
    entries = []
    for name in PRODUCTS:
        entry = tracked_by_path.get(PREFIX + name)
        require(
            entry is not None
            and entry.sha256 == PINS[PREFIX + name]["sha256"]
            and entry.size == PINS[PREFIX + name]["bytes"],
            "current compact product inventory differs",
        )
        assert entry is not None
        entries.append(entry)
    evidence = validate_products(
        json.loads(bodies[PREFIX + "report.json"]),
        json.loads(bodies[PREFIX + "trace-index.json"]),
        json.loads(bodies[AUTHORITY]),
    )
    evidence["authority_sha256"] = PINS[AUTHORITY]["sha256"]
    evidence["original_failed_ring_native_exit"] = 1
    evidence["corrected_ring_native_exit"] = 0
    return tuple(entries), evidence
