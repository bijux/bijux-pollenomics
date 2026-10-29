"""Admit the frozen temporal fixed-start account without opening private traces."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.ownership import _regular_confined_file

PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/temporal-fixed-start-development/"

OWNER = "pollen-reconstruction/author-lra-constrained/temporal-fixed-start-development/report-products"

AUTHORITY = (
    "reports/science/source-cohorts/author-love-temporal-fixed-start-development.json"
)

PRODUCTS = ("report.json", "trace-index.json")

SOURCE_EPOCH = "352246275aee76d8d1afa5b13c53a1006ff1ba26"

UNIFORM_EPOCH = "d60500153ff589db3b93c38fe3bddde46c2994a9"

INPUT_EPOCH = "d863e6c939fab8eed3e53c4dc01c52953bc2434a"

LIMITS = {
    "calibrated_uncertainty_admitted": False,
    "cross_window_winner_admitted": False,
    "epoch_age_calibration_admitted": False,
    "isolated_start_effect_admitted": False,
    "kernels_independently_recomputed": False,
    "method_change": "Thirty-two training-only fixed starts plus explicit unrounded x/xsum diagnostic "
    "compositions; original uniform host products used source rounding. This is a "
    "joint method comparison, not a starting-point causal effect.",
    "point_geometry_only": True,
    "prior_exposed_development_only": True,
    "scientific_main_return_observed": False,
    "vegetation_accuracy_admitted": False,
}

SCIENTIFIC_SOURCES = {
    "reports/science/author-love-temporal-fixed-start/protocol.json": {
        "bytes": 11025,
        "sha256": "3462886d6b4a4e1e7546f995948a509d6457663dce29211be485e2ca1121d80d",
    },
    "reports/science/author-love-temporal-fixed-start/source/regional.py": {
        "bytes": 9677,
        "sha256": "7dad2324b4fcf5e367ed6f3761dcb6363a41f71d06ba9dbd9c158164991ab39c",
    },
    "reports/science/author-love-temporal-fixed-start/source/replay.py": {
        "bytes": 16752,
        "sha256": "930a9c48ccc673b0b86e6f0e449121a68cb3739ab7caab83518726b22577a1e7",
    },
    "reports/science/author-love-temporal-fixed-start/source/training.py": {
        "bytes": 11366,
        "sha256": "78b5738a16c6e41bdb80860f6316f101847694a4d1366be6f7448321fd7b4539",
    },
}

UNIFORM_AUTHORITY = {
    "bytes": 5767,
    "path": "reports/science/source-cohorts/author-love-temporal-development.json",
    "sha256": "565e7cbb494dab8721913ab6148a14c78fa2aeb3d97b5e6cce497f7533e8569b",
}

OBSERVATION = {
    "bytes": 85331,
    "path": "artifacts/science/temporal-fixed-start-output-admission/observation.json",
    "sha256": "7dff93a9ee4dfe527c8fce00dfd818a89502c9a97d336b6d8b8f0350b752dc77",
}

OBSERVER_EXECUTION = {
    "bytes": 2372,
    "path": "artifacts/science/temporal-fixed-start-output-admission/execution.json",
    "sha256": "97d6532b3dff545483e869a22a5f7de4b027186a7bc1baac1050b5c28a885d08",
}

OBSERVER_SOURCE_REVIEW = {
    "bytes": 15424,
    "path": "artifacts/science/temporal-fixed-start-output-admission/source-review.json",
    "sha256": "3cdfeeb3b81a43fe816f32d3a7c2b1fe8a9804dbd562af2716979633e7866950",
}

PINS = {
    "docs/report/pollen-reconstruction/author-lra-constrained/temporal-fixed-start-development/report.json": {
        "bytes": 1340988,
        "sha256": "d11d8713f594582a3b93ac11b7043518935489095215f98dce9bc12ca8229eb9",
    },
    "docs/report/pollen-reconstruction/author-lra-constrained/temporal-fixed-start-development/trace-index.json": {
        "bytes": 4455,
        "sha256": "a53f7c69fec549a0df4d276cb56840d4f7067e473253a83df4f79f62e2785110",
    },
    "reports/science/author-love-temporal-fixed-start/protocol.json": {
        "bytes": 11025,
        "sha256": "3462886d6b4a4e1e7546f995948a509d6457663dce29211be485e2ca1121d80d",
    },
    "reports/science/author-love-temporal-fixed-start/source/regional.py": {
        "bytes": 9677,
        "sha256": "7dad2324b4fcf5e367ed6f3761dcb6363a41f71d06ba9dbd9c158164991ab39c",
    },
    "reports/science/author-love-temporal-fixed-start/source/replay.py": {
        "bytes": 16752,
        "sha256": "930a9c48ccc673b0b86e6f0e449121a68cb3739ab7caab83518726b22577a1e7",
    },
    "reports/science/author-love-temporal-fixed-start/source/training.py": {
        "bytes": 11366,
        "sha256": "78b5738a16c6e41bdb80860f6316f101847694a4d1366be6f7448321fd7b4539",
    },
    "reports/science/source-cohorts/author-love-temporal-development.json": {
        "bytes": 5767,
        "sha256": "565e7cbb494dab8721913ab6148a14c78fa2aeb3d97b5e6cce497f7533e8569b",
    },
    "reports/science/source-cohorts/author-love-temporal-fixed-start-development.json": {
        "bytes": 11107,
        "sha256": "d49b8e945fbc888ea732ca41f3e69697b22f69f72044600f84c37d5196b44108",
    },
}

REPORT_DIGEST = "ecccc7e84f8561b07385a7bb014b715f63a7abdf1a2f8fb1b7e823fb4c65cd44"

AUTHORITY_DIGEST = "5607373e769165677ac24961a1938a20162005c5197ff0d7dc503e792408fed5"

START_IDS = (
    "local-observed-half-uniform",
    "regional-cover-half-uniform",
    "taxon-00-half-uniform",
    "taxon-01-half-uniform",
    "taxon-02-half-uniform",
    "taxon-03-half-uniform",
    "taxon-04-half-uniform",
    "taxon-05-half-uniform",
    "taxon-06-half-uniform",
    "taxon-07-half-uniform",
    "taxon-08-half-uniform",
    "taxon-09-half-uniform",
    "taxon-10-half-uniform",
    "taxon-11-half-uniform",
    "taxon-12-half-uniform",
    "taxon-13-half-uniform",
    "taxon-14-half-uniform",
    "taxon-15-half-uniform",
    "taxon-16-half-uniform",
    "taxon-17-half-uniform",
    "taxon-18-half-uniform",
    "taxon-19-half-uniform",
    "taxon-20-half-uniform",
    "taxon-21-half-uniform",
    "taxon-22-half-uniform",
    "taxon-23-half-uniform",
    "taxon-24-half-uniform",
    "taxon-25-half-uniform",
    "taxon-26-half-uniform",
    "taxon-27-half-uniform",
    "taxon-28-half-uniform",
    "taxon-29-half-uniform",
)


def require(condition: bool, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not condition:
        raise ReportRebuildError("Temporal fixed starts: " + reason)


def digest(value: Any) -> str:
    """Return the exact retained-source byte digest."""
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def finite(value: Any) -> bool:
    """Accept only finite native numerical values, excluding flags."""
    return type(value) in (int, float) and math.isfinite(value)


def composition(values: Any, taxa: list[str]) -> None:
    """Read the declared composition under its finite-value and axis constraints."""
    require(
        isinstance(values, dict) and set(values) == set(taxa),
        "complete labelled composition required",
    )
    require(
        all(finite(x) and 0 <= x <= 1 for x in values.values())
        and abs(math.fsum(values.values()) - 1) <= 1e-9,
        "invalid/unclosed public composition",
    )


def validate_products(
    report: dict[str, Any], index: dict[str, Any], authority: dict[str, Any]
) -> JsonObject:
    """Check saved products against pinned source and scientific contracts."""
    require(
        authority["schema_version"] == "temporal-fixed-start-publication-authority.v1"
        and authority["approved"] is True
        and authority["scientific_saved_products_admitted"] is True
        and type(authority["actual_exit"]) is int
        and authority["actual_exit"] == 0,
        "actual native and independent output admission required",
    )
    require(
        report["schema_version"] == "temporal-fixed-start-publication.v1"
        and report["source_epoch"] == authority["source_epoch"] == SOURCE_EPOCH
        and report["uniform_source_epoch"]
        == authority["uniform_source_epoch"]
        == UNIFORM_EPOCH
        and report["input_epoch"] == authority["input_epoch"] == INPUT_EPOCH,
        "current source/original uniform/input epochs must remain distinct",
    )
    require(
        report["scientific_limits"] == authority["scientific_limits"] == LIMITS,
        "source-qualified kernels and development-only limits required",
    )
    require(
        report["scientific_sources"]
        == authority["scientific_sources"]
        == SCIENTIFIC_SOURCES
        and report["original_uniform_authority"]
        == authority["original_uniform_authority"]
        == UNIFORM_AUTHORITY,
        "exact scientific sources and original uniform authority required",
    )
    require(
        authority["observation"] == OBSERVATION
        and authority["observer_execution"] == OBSERVER_EXECUTION
        and authority["observer_source_review"] == OBSERVER_SOURCE_REVIEW
        and [row["window"] for row in authority["native_jobs"]] == [4, 6]
        and all(
            type(row["actual_exit"]) is int and row["actual_exit"] == 0
            for row in authority["native_jobs"]
        ),
        "separate original native and actual observer zero proofs required",
    )
    taxa = report["taxa"]
    require(len(taxa) == len(set(taxa)) == 30, "thirty ordered taxa required")
    windows = report["windows"]
    require(
        [w["window"] for w in windows] == [4, 6],
        "two original temporal windows required",
    )
    total_requests = total_rings = total_slots = total_accepted = total_refused = 0
    for window in windows:
        number = window["window"]
        n, requests, attempts, accepted, refused, slots = {
            4: (13, 23, 1472, 1276, 196, 39),
            6: (14, 25, 1600, 1316, 284, 42),
        }[number]
        summary = window["observer_summary"]
        require(
            summary["sites"] == summary["folds"] == n
            and summary["unique_requests"] == requests
            and summary["new_attempts"] == attempts
            and summary["accepted_attempts"] == accepted
            and summary["refused_attempts"] == refused
            and summary["predicted_slots"] == summary["scored_rows"] == slots
            and summary["refused_slots"] == summary["refused_training_rings"] == 0,
            "complete admitted attempt/score/refusal denominators required",
        )
        old = window["original_uniform_summary"]
        require(
            old["predicted_slots"] == old["scored_rows"] == {4: 0, 6: 3}[number]
            and old["refused_slots"] == 39,
            "original uniform failures cannot be promoted",
        )
        request_rows = window["requests"]
        keys = {r["request_sha256"] for r in request_rows}
        require(
            len(keys) == len(request_rows) == requests,
            "unique complete original request population required",
        )
        for row in request_rows:
            require(
                row["item_id"] == "request:" + row["request_sha256"]
                and row["root_seed"] == 7
                and row["regional_seed"] == 1201125462
                and row["local_seed"] == 3618983171
                and row["regional_percent_precision_decimals"] == 3,
                "original request/start seed and source rounding required",
            )
            values = row["regional_cover"]
            require(
                len(values) == 30
                and all(finite(x) and 0 <= x <= 1 for x in values)
                and abs(math.fsum(values) - row["regional_fraction_sum"]) <= 1e-12,
                "raw regional fractions must not be silently closed",
            )
        rings = window["ring_dispositions"]
        require(
            len(rings)
            == len({(r["request_sha256"], r["ring_index"]) for r in rings})
            == requests * 2
            and {(r["request_sha256"], r["ring_index"]) for r in rings}
            == {(k, i) for k in keys for i in (0, 1)},
            "all request/ring selections required",
        )
        for row in rings:
            require(
                row["status"] == "selected"
                and row["attempted"] == 32
                and type(row["accepted"]) is int
                and type(row["refused"]) is int
                and row["accepted"] > 0
                and row["refused"] >= 0
                and row["accepted"] + row["refused"] == 32,
                "all accepted/refused starts remain in ring denominator",
            )
            require(
                row["selected_start_id"] in START_IDS
                and finite(row["selected_objective"])
                and row["selected_objective"] >= 0,
                "selected declared start/finite objective required",
            )
            raw = row["raw_x"]
            require(
                len(raw) == 30
                and all(finite(x) and 0 <= x <= 1 for x in raw)
                and abs(math.fsum(raw) - 1) <= 1e-6
                and abs(math.fsum(raw) - row["raw_sum"]) < 1e-12,
                "original accepted raw simplex gate required",
            )
            composition(row["composition"], taxa)
            require(
                all(
                    abs(row["composition"][t] - x / math.fsum(raw)) < 2e-12
                    for t, x in zip(taxa, raw, strict=True)
                ),
                "unrounded x/xsum diagnostic adapter required",
            )
        require(
            sum(r["accepted"] for r in rings) == accepted
            and sum(r["refused"] for r in rings) == refused,
            "retained ring failure mass differs",
        )
        require(
            window["selected_start_counts"]
            == dict(Counter(r["selected_start_id"] for r in rings)),
            "complete selected-start distribution required",
        )
        predictions = window["slots"]
        require(
            len(predictions)
            == len({(r["fold_id"], r["baseline"]) for r in predictions})
            == slots
            and len({r["fold_id"] for r in predictions}) == n,
            "all81 original prediction/score slots required",
        )
        for row in predictions:
            fold = row["fold"]
            require(
                row["status"] == "predicted"
                and row["record_id"] == fold["test_record_ids"][0]
                and row["record_id"] not in fold["train_record_ids"]
                and len(fold["train_record_ids"]) == n - 1,
                "whole target exclusion and original scored status required",
            )
            lineage = row["input_lineage"]
            require(
                row["allowed_input_closure"] == sorted(lineage)
                and row["record_id"] not in lineage
                and all(lineage[record] == [] for record in fold["train_record_ids"]),
                "exact admitted train/forward graph required",
            )
            for key in ("pollen_fraction", "vegetation_fraction"):
                composition(row["prediction"][key], taxa)
            score = row["score"]
            require(
                score["fold_id"] == row["fold_id"]
                and score["record_id"] == row["record_id"]
                and score["baseline"] == row["baseline"]
                and score["status"] == "scored"
                and score["taxon_count"] == score["scored_taxon_count"] == 30
                and type(score["observed_total_count"]) is int
                and score["observed_total_count"] > 0
                and [x[0] for x in score["signed_error_by_taxon"]] == sorted(taxa),
                "complete labelled score/error denominators required",
            )
        for row in window["score_summary"]:
            values = [
                r["score"]["total_variation"]
                for r in predictions
                if r["baseline"] == row["baseline"]
            ]
            require(
                len(values) == row["scored_folds"] == n and row["refused_folds"] == 0,
                "per-baseline equal-fold summary denominator required",
            )
            expected = (
                statistics.fmean(values),
                statistics.median(values),
                min(values),
                max(values),
            )
            require(
                all(
                    finite(row[k]) and abs(row[k] - v) < 1e-14
                    for k, v in zip(
                        (
                            "mean_total_variation",
                            "median_total_variation",
                            "minimum_total_variation",
                            "maximum_total_variation",
                        ),
                        expected,
                        strict=True,
                    )
                ),
                "stored-score descriptive summary differs",
            )
        total_requests += requests
        total_rings += len(rings)
        total_slots += len(predictions)
        total_accepted += accepted
        total_refused += refused
    expected_objects = {}
    for role, reference in authority["trace_roles"].items():
        key = reference["sha256"]
        if key not in expected_objects:
            expected_objects[key] = {
                **reference,
                "retention_key": "sha256:" + key,
                "roles": [],
            }
        expected_objects[key]["roles"].append(role)
    require(
        index
        == {
            "schema_version": "temporal-fixed-start-trace-index.v1",
            "objects": [expected_objects[k] for k in sorted(expected_objects)],
        },
        "exact external trace role/content-address bindings required",
    )
    require(
        all(
            authority["public_products"][name] == PINS[PREFIX + name]
            for name in PRODUCTS
        ),
        "both public product pins required",
    )
    require(
        digest(report) == REPORT_DIGEST and digest(authority) == AUTHORITY_DIGEST,
        "complete independently admitted projection/authority differs",
    )
    return {
        "requests": total_requests,
        "ring_dispositions": total_rings,
        "prediction_slots": total_slots,
        "scored_rows": total_slots,
        "new_attempts": total_accepted + total_refused,
        "accepted_attempts": total_accepted,
        "refused_attempts": total_refused,
        "private_trace_payloads_read": 0,
        "models_or_scores_executed": 0,
    }


def validated_temporal_fixed_starts(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate retained fixed-start temporal outcomes and declared inputs."""
    declared = [r for r in owners if r.get("owner_id") == OWNER]
    if not declared:
        return (), {}
    require(
        len(declared) == 1
        and declared[0].get("role") == "retained_source"
        and declared[0].get("paths") == sorted(PREFIX + n for n in PRODUCTS),
        "one exact two-product retained owner required",
    )
    bodies = {}
    for name, expected in PINS.items():
        path = _regular_confined_file(repository, name, "temporal fixed starts")
        require(
            path.stat().st_nlink == 1 and path.stat().st_size == expected["bytes"],
            "regular physical source/product size differs",
        )
        raw = path.read_bytes()
        require(
            hashlib.sha256(raw).hexdigest() == expected["sha256"],
            "frozen source/product bytes differ",
        )
        bodies[name] = raw
    entries = []
    for name in PRODUCTS:
        entry = tracked_by_path.get(PREFIX + name)
        require(
            entry is not None
            and entry.sha256 == PINS[PREFIX + name]["sha256"]
            and entry.size == PINS[PREFIX + name]["bytes"],
            "current tracked two-product inventory differs",
        )
        assert entry is not None
        entries.append(entry)
    result = validate_products(
        json.loads(bodies[PREFIX + "report.json"]),
        json.loads(bodies[PREFIX + "trace-index.json"]),
        json.loads(bodies[AUTHORITY]),
    )
    result["authority_sha256"] = PINS[AUTHORITY]["sha256"]
    return tuple(entries), result
