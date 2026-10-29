"""Admit compact evidence of persisted grouped experiment input isolation."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.ownership import _regular_confined_file

PREFIX = "docs/report/synthetic-validation/persisted-experiment-isolation/"
OWNER = "synthetic-validation/persisted-experiment-isolation/report-products"
AUTHORITY = "reports/science/source-cohorts/persisted-experiment-isolation.json"
SOURCE_PREFIX = "reports/science/persisted-experiment-isolation/"
PRODUCTS = ("report.json", "trace-index.json")
METHODS = {
    "baselines": ("training_mean", "nearest_site", "inverse_distance_squared"),
    "fitted": ("clr-wgs84-rbf-ridge-v1", "training_mean"),
}
VARIANTS = ("reference", "target-perturbed")
TARGETS = ("vegetation_cover", "pollen_composition")
SUMMARY_FIELDS = (
    "actual_batch_items",
    "actual_unique_requests",
    "actual_cache_misses",
    "actual_cache_hits",
    "actual_engine_calls",
    "observed_parent_engine_calls",
    "actual_new_basin_products",
    "authenticated_seeded_basin_products",
    "cumulative_unique_basin_products",
    "actual_spatial_fit_operations",
    "score_dispositions",
    "target_metric_cells",
    "target_fingerprints",
    "identity_records",
    "identity_groups",
    "predictions_published_before_scoring",
    "prefit_ordering_verified",
)


def require(condition: bool, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not condition:
        raise ReportRebuildError("Persisted experiment isolation: " + reason)


def identity(row: dict[str, Any]) -> tuple[str, int]:
    """Validate the declared retained-source identity."""
    checksum, size = row["sha256"], row["bytes"]
    require(
        isinstance(checksum, str)
        and re.fullmatch(r"[0-9a-f]{64}", checksum) is not None
        and type(size) is int
        and size >= 0,
        "finite content identity required",
    )
    return checksum, size


def validate_products(
    report: dict[str, Any], index: dict[str, Any], authority: dict[str, Any]
) -> JsonObject:
    """Check saved products against pinned source and scientific contracts."""
    require(
        authority["schema_version"] == "development-input-isolation-output-review.v1"
        and authority["approved"] is True
        and authority["scientific_saved_products_admitted"] is True
        and type(authority["actual_exit"]) is int
        and authority["actual_exit"] == 0,
        "actual independent output admission required",
    )
    require(
        report["schema_version"] == "persisted-experiment-isolation-publication.v1"
        and report["source_epoch"]
        == authority["candidate"]
        == authority["source_epoch"]
        and report["scientific_protocol"] == authority["scientific_protocol"]
        and report["source_manifest"] == authority["source_manifest"],
        "actual source/plan epoch differs",
    )
    status = authority["native_status"]
    require(
        all(
            type(status[key]) is int and status[key] == 0
            for key in ("native_exit", "stage_exit", "collector_exit")
        )
        and status["scientific_main_return"] == "not_captured_by_borrowed_entry",
        "native outcomes and uncaptured main return must remain separate",
    )
    summary = report["summary"]
    require(
        set(summary) == set(SUMMARY_FIELDS)
        and summary == {name: authority["summary"][name] for name in SUMMARY_FIELDS},
        "exact independently adjudicated populations required",
    )
    expected = {
        "actual_batch_items": 32,
        "actual_unique_requests": 8,
        "actual_cache_misses": 3,
        "actual_cache_hits": 29,
        "actual_new_basin_products": 3,
        "authenticated_seeded_basin_products": 5,
        "cumulative_unique_basin_products": 8,
        "score_dispositions": 80,
        "target_metric_cells": 20,
        "target_fingerprints": 4,
        "identity_records": 9,
        "identity_groups": 4,
    }
    require(
        all(
            type(summary[key]) is int and summary[key] == value
            for key, value in expected.items()
        )
        and summary["actual_engine_calls"]
        == summary["observed_parent_engine_calls"]
        == {}
        and type(summary["actual_spatial_fit_operations"]) is int
        and summary["actual_spatial_fit_operations"] == 5
        and summary["predictions_published_before_scoring"] is True
        and summary["prefit_ordering_verified"] is True,
        "whole current software witness required",
    )
    seed = report["saved_cache_seed"]
    stages = report["child_stage_qualification"]
    require(
        seed["original_native_exit"] == authority["original_failed_native_exit"] == 1
        and seed["seeded_products"] == 5
        and seed["seeded_files"] == 115
        and seed["seeded_bytes"] == 195665
        and seed["new_model_calls_during_seed"] == 0
        and len(seed["request_sha256s"]) == len(set(seed["request_sha256s"])) == 5
        and stages == authority["child_stage_qualification"]
        and stages["old_recorded_stage_products"]
        == {"REVEALS": 5, "LOVE-analytical": 5}
        and stages["new_recorded_stage_products"]
        == {"REVEALS": 3, "LOVE-analytical": 3}
        and len(stages["recorded_manifests"]) == 8,
        "five original products and three new products must remain separate from parent instrumentation",
    )
    rows = report["score_dispositions"]
    keys = [
        (row["lane"], row["variant"], row["record_id"], row["method"], row["target"])
        for row in rows
    ]
    expected_keys = {
        (lane, variant, record, method, target)
        for lane, methods in METHODS.items()
        for variant in VARIANTS
        for record in ("p01", "p02", "p03", "p04")
        for method in methods
        for target in TARGETS
    }
    require(
        len(keys) == len(set(keys)) == 80 and set(keys) == expected_keys,
        "all80 unique scored/refused dispositions required",
    )
    require(
        all(
            row["score"]["status"]
            in {"scored", "prediction_failed", "observation_refused"}
            for row in rows
        ),
        "unknown score disposition",
    )
    counts = {
        lane: {
            variant: dict(
                Counter(
                    row["score"]["status"]
                    for row in rows
                    if row["lane"] == lane and row["variant"] == variant
                )
            )
            for variant in VARIANTS
        }
        for lane in METHODS
    }
    require(
        report["score_status_counts"] == authority["score_status_counts"] == counts,
        "all actual scored/refused populations must remain literal",
    )
    targets = [row for row in rows if row["record_id"] == "p01"]
    require(
        report["target_metric_cells"] == targets
        and len(targets) == 20
        and all(row["score"]["status"] == "scored" for row in targets),
        "all20 target metric cells required",
    )
    for target in targets:
        value = target["score"]["mae_fraction"]
        require(
            type(value) in {int, float} and 0 <= value <= 1,
            "finite fraction-unit target MAE required",
        )
    fingerprints = report["target_fingerprints"]
    require(
        len(fingerprints) == 4
        and {(row["lane"], row["variant"]) for row in fingerprints}
        == {(lane, variant) for lane in METHODS for variant in VARIANTS},
        "four complete target fingerprints required",
    )
    for lane, methods in METHODS.items():
        left, right = [row for row in fingerprints if row["lane"] == lane]
        require(
            all(
                row["record_id"] == "p01"
                and row["training_observed"] is True
                and row["prediction_count"] == len(methods)
                and set(row["methods"]) == set(methods)
                and len(row["methods"]) == len(methods)
                for row in (left, right)
            )
            and left["training_sha256"] == right["training_sha256"]
            and left["predictions_sha256"] == right["predictions_sha256"],
            "target labels changed training or prediction identity",
        )
        for row in (left, right):
            dispositions = row["method_dispositions"]
            require(
                len(dispositions) == len(methods)
                and {item["method"] for item in dispositions} == set(methods)
                and all(
                    item["status"] == "predicted" and item["failure"] is None
                    for item in dispositions
                ),
                "actual complete successful target method dispositions required",
            )
            require(
                all(
                    isinstance(row[key], str)
                    and re.fullmatch(r"[0-9a-f]{64}", row[key]) is not None
                    for key in ("training_sha256", "predictions_sha256")
                ),
                "exact target fingerprint required",
            )
    require(
        report["scope_limits"]
        == {
            "constructed_exposed_development": True,
            "historical_sidecars_replaced": False,
            "historical_receipts_restored": False,
            "old_ten_basin_products_reused": False,
            "measured_ecological_accuracy": False,
            "qualified_real_source_graph": False,
            "untouched_confirmation": False,
            "release_acceptance": False,
            "scientific_acceptance": "not_evaluated",
        },
        "scientific/historical limits must remain explicit",
    )
    require(
        index["schema_version"] == "persisted-experiment-isolation-trace-index.v1",
        "exact external trace index required",
    )
    objects = index["objects"]
    identities = [identity(row) for row in objects]
    require(
        len(identities) == len({row["sha256"] for row in objects}) and bool(identities),
        "unique content-addressed trace objects required",
    )
    for row in objects:
        require(
            row["retention_key"] == "sha256:" + row["sha256"]
            and bool(row["logical_paths"])
            and all(
                isinstance(name, str)
                and name
                and not Path(name).is_absolute()
                and ".." not in Path(name).parts
                for name in row["logical_paths"]
            ),
            "portable retained trace identity required",
        )
    for key, role in (
        ("report", "raw-witness-report"),
        ("journal", "flushed-read-journal"),
    ):
        required = identity(authority[key])
        require(
            any(identity(row) == required and role in row["roles"] for row in objects),
            "exact admitted raw report/journal object required",
        )
    require(
        any("analytical-basin-cache-file" in row["roles"] for row in objects),
        "actual analytical cache object identities required",
    )
    return {
        "score_dispositions": 80,
        "target_metric_cells": 20,
        "target_fingerprints": 4,
        "actual_unique_requests": 8,
        "actual_spatial_fit_operations": summary["actual_spatial_fit_operations"],
        "private_trace_payloads_read": 0,
        "new_model_or_score_calls": 0,
        "software_contract_only": True,
    }


def validated_persisted_experiment_isolation(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
    *,
    authority_sha256: str,
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate saved experiment isolation and exact input membership."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared:
        return (), {}
    paths = declared[0].get("paths")
    require(
        len(declared) == 1
        and declared[0].get("role") == "retained_source"
        and isinstance(paths, list)
        and all(isinstance(name, str) for name in paths)
        and set(paths) == {PREFIX + name for name in PRODUCTS}
        and len(paths) == 2,
        "one exact two-product retained owner required",
    )
    path = _regular_confined_file(
        repository, AUTHORITY, "experiment-isolation authority"
    )
    raw = path.read_bytes()
    require(
        path.stat().st_nlink == 1
        and hashlib.sha256(raw).hexdigest() == authority_sha256,
        "actual public authority changed",
    )
    authority = json.loads(raw)
    bodies: dict[str, bytes] = {}
    expected_paths = {PREFIX + name for name in PRODUCTS}
    require(
        set(authority["public_products"]) == expected_paths,
        "exact two public products required",
    )
    sources = authority["public_sources"]
    require(
        set(sources)
        == {
            SOURCE_PREFIX + name
            for name in (
                "source/replay.py",
                "source/evidence.py",
                "protocol.json",
                "source-locations.json",
            )
        },
        "exact two scientific sources/protocol/location map required",
    )
    for name, expected in {**sources, **authority["public_products"]}.items():
        physical = _regular_confined_file(
            repository, name, "experiment-isolation publication"
        )
        value = physical.read_bytes()
        require(
            physical.stat().st_nlink == 1
            and identity(expected) == (hashlib.sha256(value).hexdigest(), len(value)),
            "public scientific source/product identity differs",
        )
        bodies[name] = value
    entries: list[InventoryEntry] = []
    for name in sorted(expected_paths):
        entry = tracked_by_path.get(name)
        expected = authority["public_products"][name]
        require(
            entry is not None
            and entry.sha256 == expected["sha256"]
            and entry.size == expected["bytes"],
            "current two-product inventory differs",
        )
        assert entry is not None
        entries.append(entry)
    evidence = validate_products(
        json.loads(bodies[PREFIX + "report.json"]),
        json.loads(bodies[PREFIX + "trace-index.json"]),
        authority,
    )
    evidence["authority_sha256"] = authority_sha256
    return tuple(entries), evidence
