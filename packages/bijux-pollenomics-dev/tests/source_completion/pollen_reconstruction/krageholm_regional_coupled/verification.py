"""Posthoc fixed-cohort observer after all native prediction/score products close."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import subprocess
import time
from typing import Any

from .lineage import expected_folds
from .materialization import NAMES, check_materialization
from .predictions import check_prediction
from .reading import decode, exact, read_file
from .scalar import AXIS, METHODS, require
from .scores import check_scores
from .source_accounts import WINDOWS

PROTOCOL = (
    "reports/science/pollen-reconstruction/krageholm-regional-coupled/protocol.json"
)


def artifact_pin(
    repository: Path, pin: dict[str, Any]
) -> tuple[Path, bytes, dict[str, Any]]:
    path = Path(pin["path"])
    require(
        path.is_absolute() and path.is_relative_to(repository / "artifacts"),
        "owned absolute artifact input required",
    )
    body = read_file(path, 2 * 1024**2, pin["sha256"])
    if "bytes" in pin:
        require(
            type(pin["bytes"]) is int and pin["bytes"] == len(body),
            "artifact input byte count differs",
        )
    return path, body, decode(body)


def closed_batch(
    value: dict[str, Any], operation: str, head: str, protocol_pin: dict[str, Any]
) -> None:
    require(
        value["schema_version"] == "krageholm-regional-coupled-batch.v1"
        and value["operation"] == operation
        and value["source_commit"] == head
        and value["protocol"] == protocol_pin
        and value["all_bins_accounted"] is True
        and value["requested_folds"] == 18
        and value["requested_method_dispositions"] == 54
        and value["scientific_acceptance"] == "not_evaluated"
        and value["exposure"] == "prior_exposed_development",
        "closed complete fixed-cohort batch authority differs",
    )
    require(
        [row["bin"] for row in value["bins"]] == list(NAMES)
        and len(value["method_dispositions"]) == 54,
        "six ordered bins/all54 dispositions required",
    )
    for row in value["bins"]:
        fold_ids = [fold["fold_id"] for fold in row["folds"]]
        require(
            len(fold_ids) == len(set(fold_ids)) == 3
            and len(row["method_dispositions"]) == 9
            and {
                (item["fold_id"], item["method"]) for item in row["method_dispositions"]
            }
            == {(fold_id, method) for fold_id in fold_ids for method in METHODS},
            "complete unique nine-method bin dispositions required",
        )
    exact(
        value["method_dispositions"],
        [
            {"bin": row["bin"], **item}
            for row in value["bins"]
            for item in row["method_dispositions"]
        ],
    )
    exact(
        value["status_counts"],
        dict(Counter(row["status"] for row in value["method_dispositions"])),
    )


def verify(repository: Path, result_path: Path, result_sha256: str) -> dict[str, Any]:
    started = time.monotonic()
    repository = repository.resolve(strict=True)
    git = ["git", "-C", str(repository)]
    head = subprocess.check_output(
        [*git, "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    index = subprocess.check_output([*git, "diff", "--cached", "--raw"], timeout=10)
    protocol_body = read_file(repository / PROTOCOL, 65536)
    committed = subprocess.check_output(
        [*git, "show", head + ":" + PROTOCOL], timeout=10
    )
    require(
        committed == protocol_body,
        "prospective protocol is not committed current bytes",
    )
    protocol = decode(protocol_body)
    require(
        protocol["schema_version"] == "krageholm-regional-coupled-protocol.v1"
        and protocol["axis"] == list(AXIS)
        and protocol["windows_cal_bp"] == [list(window) for window in WINDOWS]
        and protocol["population"]["methods"] == list(METHODS),
        "prespecified source/response/fold contract differs",
    )
    tolerance = protocol["independent_oracle"]
    require(
        tolerance["scalar_absolute_tolerance"] == 2e-12
        and tolerance["scalar_relative_tolerance"] == 2e-10
        and tolerance["no_post_outcome_retuning"] is True,
        "prospective scalar tolerance changed",
    )
    protocol_pin = {
        "path": PROTOCOL,
        "sha256": sha256(protocol_body).hexdigest(),
        "bytes": len(protocol_body),
    }
    require(
        result_path.is_relative_to(repository / "artifacts"),
        "closed score batch must be owned artifacts",
    )
    result_body = read_file(result_path, 2 * 1024**2, result_sha256)
    score = decode(result_body)
    closed_batch(score, "score", head, protocol_pin)
    prediction_path, prediction_body, prepared = artifact_pin(
        repository, score["prediction_index"]
    )
    closed_batch(prepared, "prepare", head, protocol_pin)
    input_path, input_body, inputs = artifact_pin(repository, score["input_index"])
    exact(prepared["input_index"], score["input_index"])
    require(
        inputs["source_commit"] == head and inputs["protocol"] == protocol_pin,
        "materialized source/protocol revision differs",
    )
    contexts = check_materialization(repository, input_path, inputs, protocol)
    small_supports = {
        code: sum(
            contexts[name]["small_source_sample_supports"][code] for name in NAMES
        )
        for code in ("BOKE", "BUS", "SOLSOE83")
    }
    require(
        sum(small_supports.values())
        == inputs["source_population"]["small_selected_sample_supports"],
        "derived qualified sample support total differs",
    )
    require(
        score["ordering"]
        == "all_available_six_bin_prediction_products_authenticated_before_any_score_api",
        "source-only prediction closure ordering contract differs",
    )
    checked: dict[str, dict[str, Any]] = {}
    for row in prepared["bins"]:
        name = row["bin"]
        context = contexts[name]
        expected = expected_folds(
            context["experiment"]["sites"],
            context["experiment"]["target_record_ids"],
            context["ids"]["KRAGMJNY"],
        )
        exact(row["folds"], expected)
        if "prediction" in row:
            require(
                Path(row["prediction"]["directory"]) == prediction_path.parent / name,
                "prediction bin directory differs",
            )
            observed = check_prediction(
                repository, row["prediction"], context, tolerance
            )
            exact(row["method_dispositions"], observed["dispositions"])
            expected_batches = {
                key: value
                for key, value in observed["manifest"]["files"].items()
                if key.startswith("batches/")
            }
            exact(row["native_batch_members"], expected_batches)
            checked[name] = observed
        else:
            require(
                row["status"] == "refused" and row["reason_code"] and row["detail"],
                "unavailable prediction bin needs explicit original refusal",
            )
            require(
                len(row["method_dispositions"]) == 9
                and {
                    (item["fold_id"], item["method"])
                    for item in row["method_dispositions"]
                }
                == {
                    (fold["fold_id"], method) for fold in expected for method in METHODS
                }
                and all(
                    item["status"] == "refused" for item in row["method_dispositions"]
                ),
                "unavailable prediction bin must retain all9 dispositions",
            )
    scored = 0
    native_references = sum(row["native_fit_references"] for row in checked.values())
    native_requests = {
        value for row in checked.values() for value in row["native_request_sha256"]
    }
    require(
        native_references <= 36 and len(native_requests) <= 18,
        "native source/local request population exceeds fixed study",
    )
    maximum = max(
        (row["maximum_scalar_difference"] for row in checked.values()), default=0.0
    )
    for row, original in zip(score["bins"], prepared["bins"], strict=True):
        name = row["bin"]
        exact(row["folds"], original["folds"])
        if name not in checked:
            require(
                row["status"] == "prediction_unavailable" and "scores" not in row,
                "unavailable predictions must not acquire scores",
            )
            exact(row["method_dispositions"], original["method_dispositions"])
        elif "scores" in row:
            require(
                Path(row["scores"]["directory"]) == result_path.parent / name,
                "score bin directory differs",
            )
            outcome = check_scores(
                repository,
                row["scores"],
                original["prediction"],
                checked[name],
                contexts[name],
                tolerance,
            )
            exact(row["method_dispositions"], outcome["dispositions"])
            scored += outcome["scored"]
            maximum = max(maximum, outcome["maximum_scalar_difference"])
        else:
            require(
                row["status"] == "refused"
                and row["reason_code"]
                and row["detail"]
                and len(row["method_dispositions"]) == 9
                and all(
                    item["status"] == "refused" for item in row["method_dispositions"]
                ),
                "failed scoring bin must retain all9 original refusals",
            )
    require(
        read_file(result_path, 2 * 1024**2) == result_body
        and read_file(prediction_path, 2 * 1024**2) == prediction_body
        and read_file(input_path, 2 * 1024**2) == input_body
        and read_file(repository / PROTOCOL, 65536) == protocol_body,
        "closed study inputs mutated during observation",
    )
    require(
        subprocess.check_output(
            [*git, "rev-parse", "HEAD"], text=True, timeout=10
        ).strip()
        == head
        and subprocess.check_output([*git, "diff", "--cached", "--raw"], timeout=10)
        == index,
        "frozen HEAD/index changed during observation",
    )
    return {
        "status": "independent_krageholm_regional_coupled_pass",
        "source_commit": head,
        "closed_score_batch_sha256": result_sha256,
        "closed_prediction_batch_sha256": sha256(prediction_body).hexdigest(),
        "source_input_index_sha256": sha256(input_body).hexdigest(),
        "krag_audit_native_owners_checked": 96,
        "krag_selected_literal_owners_checked": 19,
        "small_source_sample_supports": inputs["source_population"][
            "small_selected_sample_supports"
        ],
        "small_source_sample_supports_by_core": small_supports,
        "small_source_support_scope": "Per-core and total sample supports derived from each pinned qualified source row's exact positive integer count and fingerprint; no preset sample total or fresh literal-owner reconciliation.",
        "fixed_bins_checked": 6,
        "target_folds_checked": 18,
        "method_dispositions_checked": 54,
        "scored_dispositions": scored,
        "unscored_dispositions": 54 - scored,
        "native_fit_references_checked": native_references,
        "distinct_native_requests_checked": len(native_requests),
        "native_negative_final_covers_retained": sum(
            row["native_negative_final_covers"] for row in checked.values()
        ),
        "maximum_scalar_difference": maximum,
        "scalar_scope": "Conditional on saved native kernels and distances; no continuous kernel certification or independent geodesy.",
        "withholding_scope": "Controlled per-fold source admission and preserved quantitative lineage, supported by guarded I/O synthetic controls; no OS-enforced isolation or independent dynamic filesystem tracing.",
        "numerical_engine_calls": 0,
        "model_fits": 0,
        "scientific_acceptance": "not_evaluated",
        "elapsed_seconds": time.monotonic() - started,
    }
