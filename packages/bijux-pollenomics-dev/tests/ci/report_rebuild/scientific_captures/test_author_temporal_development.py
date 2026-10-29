"""Complete negative temporal outcomes and mixed-baseline publication boundaries."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import runpy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

ROOT = Path.cwd()
DEFAULT_SOURCE = (
    ROOT
    / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/author_temporal_development.py"
)
API = runpy.run_path(
    str(globals().get("PUBLICATION_GUARD_SOURCE", DEFAULT_SOURCE)),
    run_name="temporal_publication_tests",
)
Json = dict[str, Any]
PARAMETER_VALUES = (
    (0.12, 6.875, 1.441919999861296),
    (0.021, 13.562, 0.29314899965717095),
    (0.019, 4.28, 0.27),
    (0.025, 3.93667, 0.14624899999658117),
    (0.024, 5.10571, 0.3033250006181489),
    (0.032, 1.89, 0.06799999999999999),
    (0.038, 1.085, 0.029154793773923354),
    (0.042, 4.52, 0.4252660002868793),
    (0.042, 0.24, 0.06999999999999999),
    (0.01, 3.258, 0.059000000000000004),
    (0.06, 1.85, 0.3809490005236922),
    (0.025, 1.71, 0.09997540197468575),
    (0.035, 0.9625, 0.050621102319092184),
    (0.038, 4.265, 0.094),
    (0.057, 5.86333, 0.1763199988656987),
    (0.022, 1.044, 0.04768400150994042),
    (0.016, 2.07, 0.04),
    (0.015, 0.512, 0.075),
    (0.056, 5.4375, 0.09716260082974312),
    (0.031, 6.05833, 0.23667699930495992),
    (0.03, 0.755, 0.201),
    (0.029, 2.33, 0.20144000099285148),
    (0.035, 1.0, 0.0),
    (0.035, 4.53667, 0.08618459839205611),
    (0.035, 11.043, 0.261),
    (0.018, 3.02, 0.2783849995958834),
    (0.022, 1.182, 0.07660289811749944),
    (0.06, 3.99, 0.3204400006241418),
    (0.032, 1.21, 0.11614199929396773),
    (0.032, 1.27, 0.05),
)


def fixture(predicted: bool = False) -> tuple[Json, Json, Json]:
    protocol = json.loads((ROOT / API["PREFIX"] / "protocol.json").read_bytes())
    profile = protocol["profile"]
    taxa = profile["taxa"]
    windows = []
    for window, (n, logical_count, unique_count, slots_count) in API["COUNTS"].items():
        records = ["artificial:" + str(i) for i in range(n)]
        folds = [
            {
                "fold_id": "fold:" + str(i),
                "train_record_ids": [record for record in records if record != target],
                "test_record_ids": [target],
            }
            for i, target in enumerate(records)
        ]
        requests = [
            {
                "request_sha256": format(i, "064x"),
                "status": "completed",
                "result_identity": {
                    "manifest_sha256": "b" * 64,
                    "scientific_content_sha256": "c" * 64,
                },
            }
            for i in range(unique_count)
        ]
        logical: list[Json] = []
        for fold in folds:
            anchor = fold["train_record_ids"][0]
            for local in fold["train_record_ids"][1:]:
                logical.append(
                    {
                        "fold_id": fold["fold_id"],
                        "target_record_id": fold["test_record_ids"][0],
                        "local_record_id": local,
                        "regional_anchor_record_id": anchor,
                        "request_sha256": requests[len(logical) % unique_count][
                            "request_sha256"
                        ],
                    }
                )
        slots = [
            {
                "fold_id": fold["fold_id"],
                "record_id": fold["test_record_ids"][0],
                "baseline": baseline,
                "status": "refused",
                "reason_code": "training_request_or_composition_refused",
                "detail": "Artificial unclosed saved reconstruction",
                "training_refused_requests": [
                    next(
                        row["request_sha256"]
                        for row in logical
                        if row["fold_id"] == fold["fold_id"]
                    )
                ],
            }
            for fold in folds
            for baseline in API["METHODS"]
        ]
        scores = []
        observations = {}
        if predicted and window == 6:
            row = slots[0]
            vector = {taxon: int(i == 0) for i, taxon in enumerate(taxa)}
            row.clear()
            row.update(
                fold_id=folds[0]["fold_id"],
                record_id=records[0],
                baseline=API["METHODS"][0],
                status="predicted",
                pollen_fraction=vector,
                vegetation_fraction=vector,
                prediction_manifest_sha256="a" * 64,
            )
            scores = [
                {
                    "fold_id": row["fold_id"],
                    "record_id": row["record_id"],
                    "baseline": row["baseline"],
                    "target": "pollen_composition",
                    "status": "scored",
                    "taxon_count": 30,
                    "scored_taxon_count": 30,
                    "missing_observed_taxa": [],
                    "observed_total_count": 100,
                    "zero_probability_positive_count": False,
                    "mae_fraction": 0.0,
                    "rmse_fraction": 0.0,
                    "bias_fraction": 0.0,
                    "total_variation": 0.0,
                    "count_conditioned_deviance": 0.0,
                    "signed_error_by_taxon": [[taxon, 0.0] for taxon in sorted(taxa)],
                }
            ]
            observations[records[0]] = {
                taxon: int(i == 0) * 100 for i, taxon in enumerate(taxa)
            }
        successes = len(scores)
        summary = {
            "window": window,
            "sites": n,
            "folds": n,
            "logical_requests": logical_count,
            "unique_requests": unique_count,
            "prediction_slots": slots_count,
            "predicted_slots": successes,
            "refused_slots": slots_count - successes,
            "scored_rows": successes,
            "batch_status_counts": {"completed": unique_count, "refused": 0},
            "refusal_reason_counts": dict(
                Counter(
                    row["reason_code"] for row in slots if row["status"] == "refused"
                )
            ),
            "zero_probability_positive_count_rows": 0,
            "point_pollen_only": True,
        }
        windows.append(
            {
                "window": window,
                "summary": summary,
                "folds": folds,
                "requests": requests,
                "logical_requests": logical,
                "slots": slots,
                "scores": scores,
                "observations": observations,
                "freeze_before_post_freeze_scoring_decode": True,
                "scientific_main_return": "not observed by unchanged consumer",
            }
        )
    report = {
        "schema_version": "author-love-temporal-development-publication.v1",
        "source_epoch": API["SOURCE_EPOCH"],
        "input_epoch": API["INPUT_EPOCH"],
        "protocol_sha256": API["PROTOCOL_SHA256"],
        "profile": profile,
        "parameters": [
            {
                "taxon": taxon,
                "fallspeed_m_s": value[0],
                "ppe": value[1],
                "ppe_sd": value[2],
            }
            for taxon, value in zip(taxa, PARAMETER_VALUES, strict=True)
        ],
        "windows": windows,
        "global_temporal_winner": False,
        "independent_confirmation": False,
        "vegetation_accuracy_admitted": False,
        "whole_owner_acceptance": False,
        "scientific_acceptance": "not_evaluated",
        "admitted_input_populations": [{"window": 4}, {"window": 6}],
        "source_files": API["SOURCES"],
    }
    roles = sorted(
        f"TW{window}:{role}"
        for window in (4, 6)
        for role in (
            "plan",
            "native-terminal",
            "report.json",
            "prediction-freeze.json",
            "batch-result.json",
            "outcome-access.jsonl",
        )
    )
    roles = sorted(
        set(roles)
        | {
            "provenance:" + name
            for name in (
                "root_authority",
                "observation",
                "observer_execution",
                "observer_source_review",
            )
        }
        | {
            f"TW{window['window']}:request:{request['request_sha256']}:manifest"
            for window in windows
            for request in window["requests"]
        }
    )
    index = {
        "schema_version": "author-love-temporal-development-trace-index.v1",
        "objects": [
            {
                "sha256": "b" * 64,
                "bytes": 1,
                "retention_key": "sha256:" + "b" * 64,
                "roles": roles,
            }
        ],
    }
    authority = {
        "schema_version": "author-love-temporal-development-public-authority.v1",
        "candidate": API["SOURCE_EPOCH"],
        "input_epoch": API["INPUT_EPOCH"],
        "approved": True,
        "actual_exit": 0,
        "scientific_saved_products_admitted": True,
        "summaries": [row["summary"] for row in windows],
        "admitted_input_populations": report["admitted_input_populations"],
        "public_products": {},
        "proofs": dict.fromkeys(
            (
                "root_authority",
                "observation",
                "observer_execution",
                "observer_source_review",
            ),
            {"sha256": "b" * 64, "bytes": 1},
        ),
    }
    repin(report, index, authority)
    return report, index, authority


def repin(report: Json, index: Json, authority: Json) -> None:
    authority["public_products"] = {
        name: {
            "sha256": hashlib.sha256(API["encoded"](value)).hexdigest(),
            "bytes": len(API["encoded"](value)),
        }
        for name, value in (("report.json", report), ("trace-index.json", index))
    }


@pytest.mark.parametrize("predicted", [False, True])
def test_complete_negative_and_mixed_baseline_populations(predicted: bool) -> None:
    report, index, authority = fixture(predicted)
    result = API["validate_products"](report, index, authority)
    assert result["baseline_slots"] == 81
    assert result["scored_rows"] == int(predicted)
    assert result["refused_slots"] == 81 - int(predicted)


@pytest.mark.parametrize(
    "change",
    [
        "input_epoch",
        "profile",
        "missing_slot",
        "promoted_refusal",
        "metric",
        "target_training",
        "freeze",
        "trace",
        "scientific_acceptance",
        "source_pin",
    ],
)
def test_publication_refuses_changed_science_or_missing_evidence(change: str) -> None:
    report, index, authority = deepcopy(fixture(True))
    if change == "input_epoch":
        report["input_epoch"] = "0" * 40
    elif change == "profile":
        report["profile"]["configuration"]["seed"] = 8
    elif change == "missing_slot":
        report["windows"][0]["slots"].pop()
    elif change == "promoted_refusal":
        report["windows"][0]["slots"][0]["status"] = "predicted"
    elif change == "metric":
        report["windows"][1]["scores"][0]["total_variation"] = 0.5
    elif change == "target_training":
        report["windows"][0]["logical_requests"][0]["local_record_id"] = report[
            "windows"
        ][0]["folds"][0]["test_record_ids"][0]
    elif change == "freeze":
        report["windows"][0]["freeze_before_post_freeze_scoring_decode"] = False
    elif change == "trace":
        index["objects"][0]["roles"].remove("TW4:prediction-freeze.json")
    elif change == "scientific_acceptance":
        report["whole_owner_acceptance"] = True
    else:
        report["source_files"] = {**report["source_files"], "unexpected.py": {}}
    repin(report, index, authority)
    with pytest.raises(ReportRebuildError):
        API["validate_products"](report, index, authority)


def test_exact_callback_tuple_and_unbound_authority_refusal(tmp_path: Path) -> None:
    assert API["validated_author_temporal_capture"](tmp_path, {}, []) == ((), {})
    owner = {
        "owner_id": API["OWNER"],
        "role": "retained_source",
        "paths": sorted(API["PREFIX"] + name for name in API["PRODUCTS"]),
    }
    namespace = API["validated_author_temporal_capture"].__globals__
    before = namespace["AUTHORITY_SHA256"]
    namespace["AUTHORITY_SHA256"] = None
    try:
        with pytest.raises(ReportRebuildError, match="unbound"):
            API["validated_author_temporal_capture"](tmp_path, {}, [owner])
    finally:
        namespace["AUTHORITY_SHA256"] = before
