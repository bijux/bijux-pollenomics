"""Compact software-isolation evidence retains every disposition and source limit."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import runpy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)

MODULE = (
    Path(__file__).parents[3]
    / "src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/persisted_experiment_isolation.py"
)
GUARD = runpy.run_path(str(MODULE))


def fixture() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    summary = {
        "actual_batch_items": 32,
        "actual_unique_requests": 8,
        "actual_cache_misses": 3,
        "actual_cache_hits": 29,
        "actual_engine_calls": {},
        "observed_parent_engine_calls": {},
        "actual_new_basin_products": 3,
        "authenticated_seeded_basin_products": 5,
        "cumulative_unique_basin_products": 8,
        "actual_spatial_fit_operations": 5,
        "score_dispositions": 80,
        "target_metric_cells": 20,
        "target_fingerprints": 4,
        "identity_records": 9,
        "identity_groups": 4,
        "predictions_published_before_scoring": True,
        "prefit_ordering_verified": True,
    }
    rows = [
        {
            "lane": lane,
            "variant": variant,
            "record_id": record,
            "method": method,
            "target": target,
            "score": {
                "status": "scored"
                if variant == "reference" or record == "p01"
                else "prediction_failed",
                "mae_fraction": 0.1
                if variant == "reference" or record == "p01"
                else None,
            },
        }
        for lane, methods in GUARD["METHODS"].items()
        for variant in GUARD["VARIANTS"]
        for record in ("p01", "p02", "p03", "p04")
        for method in methods
        for target in GUARD["TARGETS"]
    ]
    counts = {
        lane: {
            variant: dict(
                Counter(
                    row["score"]["status"]
                    for row in rows
                    if row["lane"] == lane and row["variant"] == variant
                )
            )
            for variant in GUARD["VARIANTS"]
        }
        for lane in GUARD["METHODS"]
    }
    fingerprints = [
        {
            "lane": lane,
            "variant": variant,
            "record_id": "p01",
            "prediction_count": len(methods),
            "methods": list(methods),
            "training_sha256": "a" * 64,
            "training_observed": True,
            "predictions_sha256": "b" * 64,
            "method_dispositions": [
                {
                    "method": method,
                    "status": "predicted",
                    "failure": None,
                    "prediction_sha256": "b" * 64,
                }
                for method in methods
            ],
        }
        for lane, methods in GUARD["METHODS"].items()
        for variant in GUARD["VARIANTS"]
    ]
    report = {
        "schema_version": "persisted-experiment-isolation-publication.v1",
        "source_epoch": "a" * 40,
        "scientific_protocol": {"sha256": "c" * 64, "bytes": 1},
        "source_manifest": {"sha256": "d" * 64, "bytes": 1},
        "summary": summary,
        "saved_cache_seed": {
            "original_native_exit": 1,
            "seeded_products": 5,
            "seeded_files": 115,
            "seeded_bytes": 195665,
            "new_model_calls_during_seed": 0,
            "request_sha256s": [str(i) * 64 for i in range(5)],
        },
        "child_stage_qualification": {
            "old_recorded_stage_products": {"REVEALS": 5, "LOVE-analytical": 5},
            "new_recorded_stage_products": {"REVEALS": 3, "LOVE-analytical": 3},
            "recorded_manifests": [
                {"sha256": str(i) * 64, "bytes": 1} for i in range(8)
            ],
            "qualification": "Artificial source-qualified product metadata, not observed calls.",
        },
        "score_dispositions": rows,
        "score_status_counts": counts,
        "target_metric_cells": [row for row in rows if row["record_id"] == "p01"],
        "target_fingerprints": fingerprints,
        "scope_limits": {
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
    }
    index = {
        "schema_version": "persisted-experiment-isolation-trace-index.v1",
        "objects": [
            {
                "sha256": "e" * 64,
                "bytes": 100,
                "retention_key": "sha256:" + "e" * 64,
                "logical_paths": ["report.json"],
                "roles": ["raw-witness-report"],
            },
            {
                "sha256": "f" * 64,
                "bytes": 101,
                "retention_key": "sha256:" + "f" * 64,
                "logical_paths": ["read-journal.jsonl"],
                "roles": ["flushed-read-journal"],
            },
            {
                "sha256": "1" * 64,
                "bytes": 102,
                "retention_key": "sha256:" + "1" * 64,
                "logical_paths": ["cache/product/manifest.json"],
                "roles": ["analytical-basin-cache-file"],
            },
        ],
    }
    authority = {
        "schema_version": "development-input-isolation-output-review.v1",
        "approved": True,
        "scientific_saved_products_admitted": True,
        "actual_exit": 0,
        "candidate": "a" * 40,
        "source_epoch": "a" * 40,
        "scientific_protocol": report["scientific_protocol"],
        "source_manifest": report["source_manifest"],
        "summary": deepcopy(summary),
        "original_failed_native_exit": 1,
        "child_stage_qualification": deepcopy(report["child_stage_qualification"]),
        "score_status_counts": deepcopy(counts),
        "native_status": {
            "native_exit": 0,
            "stage_exit": 0,
            "collector_exit": 0,
            "scientific_main_return": "not_captured_by_borrowed_entry",
        },
        "report": {"sha256": "e" * 64, "bytes": 100},
        "journal": {"sha256": "f" * 64, "bytes": 101},
    }
    return report, index, authority


def test_complete_compact_populations_and_limits() -> None:
    result = GUARD["validate_products"](*fixture())
    assert result["score_dispositions"] == 80
    assert (
        result["private_trace_payloads_read"] == result["new_model_or_score_calls"] == 0
    )


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "lost_refusal",
        "training",
        "prediction",
        "science",
        "epoch",
        "journal",
        "cache",
        "mainreturn",
        "parent_calls",
        "new_products",
        "unobserved_training",
        "seed_history",
    ],
)
def test_altered_disposition_identity_or_scope_refuses(change: str) -> None:
    report, index, authority = deepcopy(fixture())
    if change == "parent_calls":
        report["summary"]["actual_engine_calls"] = {"REVEALS": 8}
        authority["summary"]["actual_engine_calls"] = {"REVEALS": 8}
    elif change == "new_products":
        report["summary"]["actual_new_basin_products"] = 8
        authority["summary"]["actual_new_basin_products"] = 8
    elif change == "unobserved_training":
        report["target_fingerprints"][0]["training_observed"] = False
    elif change == "seed_history":
        report["saved_cache_seed"]["original_native_exit"] = 0
    elif change == "missing":
        report["score_dispositions"].pop()
    elif change == "duplicate":
        report["score_dispositions"][1] = report["score_dispositions"][0]
    elif change == "lost_refusal":
        next(
            row
            for row in report["score_dispositions"]
            if row["score"]["status"] == "prediction_failed"
        )["score"]["status"] = "scored"
    elif change == "training":
        report["target_fingerprints"][1]["training_sha256"] = "9" * 64
    elif change == "prediction":
        report["target_fingerprints"][1]["predictions_sha256"] = "9" * 64
    elif change == "science":
        report["scope_limits"]["scientific_acceptance"] = "accepted"
    elif change == "epoch":
        authority["candidate"] = "9" * 40
    elif change == "journal":
        index["objects"][1]["sha256"] = "9" * 64
    elif change == "cache":
        index["objects"].pop()
    else:
        authority["native_status"]["scientific_main_return"] = 0
    with pytest.raises(ReportRebuildError):
        GUARD["validate_products"](report, index, authority)


def test_two_product_callback_requires_no_private_trace_payloads(
    tmp_path: Path,
) -> None:
    report, index, authority = fixture()
    public = {
        GUARD["PREFIX"] + "report.json": report,
        GUARD["PREFIX"] + "trace-index.json": index,
    }
    authority["public_products"] = {}
    authority["public_sources"] = {}
    for name, value in public.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        raw = path.read_bytes()
        authority["public_products"][name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    for name in (
        "source/replay.py",
        "source/evidence.py",
        "protocol.json",
        "source-locations.json",
    ):
        path = tmp_path / (GUARD["SOURCE_PREFIX"] + name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("artificial declared source fixture\n")
        raw = path.read_bytes()
        authority["public_sources"][GUARD["SOURCE_PREFIX"] + name] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    path = tmp_path / GUARD["AUTHORITY"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(authority))
    entries = {
        name: InventoryEntry(
            path=name.removeprefix("docs/report/"),
            kind="file",
            size=row["bytes"],
            sha256=row["sha256"],
            canonical_sha256=row["sha256"],
        )
        for name, row in authority["public_products"].items()
    }
    owners: list[JsonObject] = [
        {"owner_id": GUARD["OWNER"], "role": "retained_source", "paths": list(public)}
    ]
    admitted, evidence = GUARD["validated_persisted_experiment_isolation"](
        tmp_path,
        entries,
        owners,
        authority_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )
    assert isinstance(admitted, tuple) and len(admitted) == 2
    assert evidence["private_trace_payloads_read"] == 0
    assert GUARD["validated_persisted_experiment_isolation"](
        tmp_path, {}, [], authority_sha256="0" * 64
    ) == ((), {})
