"""Admit a compact frozen PPE report without reopening private fit traces."""

from __future__ import annotations

import json
import math
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.author_method_comparison import (
    _read,
)

PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/nested-ppe/"
OWNER = "pollen-reconstruction/author-lra-constrained/nested-ppe/report-products"
AUTHORITY = "reports/science/source-cohorts/author-love-nested-ppe.json"
METHODS = ("gpm neutral", "ppe-minus-source-sd", "ppe-plus-source-sd")
BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")
SOURCES = ("common.py", "replay.py", "requests.py", "selection.py", "training.py")
PRODUCTS = {"report": "report.json", "trace_index": "trace-index.json"}
TRACE_ROLES = {
    *(
        f"fit:{method}:{role}"
        for method in METHODS[1:]
        for role in ("training", "trials")
    ),
    *(
        f"evaluation:{name}"
        for name in (
            "candidate-prediction-freeze.json",
            "inner-label-access.jsonl",
            "inner-scores.json",
            "transport-selection.json",
            "selected-prediction-freeze.json",
            "outer-label-access.jsonl",
            "report.json",
        )
    ),
}


def require(value: object, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not value:
        raise ReportRebuildError("Nested PPE " + reason)


def valid_pin(row: dict[str, Any]) -> bool:
    """Require an exact typed source pin without coercing flags or digests."""
    return (
        type(row.get("bytes")) is int
        and 0 <= row["bytes"] <= 2**53
        and type(row.get("sha256")) is str
        and re.fullmatch("[a-f0-9]{64}", row["sha256"]) is not None
    )


def validate_public_result(
    report: dict[str, Any], trace_index: dict[str, Any], authority: dict[str, Any]
) -> JsonObject:
    """Preserve complete dispositions and compact custody; numerical proof is external."""
    candidate = authority["source_candidate"]
    require(
        type(candidate) is str and re.fullmatch("[a-f0-9]{40}", candidate) is not None,
        "actual source candidate required",
    )
    require(
        report["schema_version"] == "author-love-nested-ppe-development.v1"
        and report["candidate"] == candidate
        and report["protocol_sha256"] == authority["protocol"]["sha256"]
        and tuple(report["methods"]) == METHODS
        and report["scientific_acceptance"] == "not_evaluated",
        "executed report/protocol/scope differs",
    )
    execution = authority["execution"]
    fitting = authority["fitting_execution"]
    nominal = authority["nominal_reuse"]
    require(
        execution["candidate"] == candidate
        and type(execution["native_exit"]) is int
        and execution["native_exit"] == 0
        and all(
            execution[key] is True
            for key in (
                "source_before_after_equal",
                "inputs_before_after_equal",
                "runtime_before_after_equal",
            )
        ),
        "actual evaluation zero and watched source/input/runtime required",
    )
    require(
        set(fitting) == set(METHODS[1:])
        and all(
            type(row["native_exit"]) is int
            and row["native_exit"] == 0
            and all(
                row[key] is True
                for key in (
                    "source_before_after_equal",
                    "inputs_before_after_equal",
                    "runtime_before_after_equal",
                )
            )
            for row in fitting.values()
        ),
        "two actual changed-PPE fit zeros with watched custody required",
    )
    require(
        nominal["source_candidate"] == "70dd58ce28071d3b4ef34af2c800370a52d42bf9"
        and nominal["training_protocol_sha256"]
        == "7953aec717a0bf440eca6d26e5c4d9bca03e3d783a005ab311f09d3d9b4db4dd"
        and nominal["publication_authority"]
        == {
            "path": "reports/science/source-cohorts/author-love-nested-transport.json",
            "sha256": "f82f7c83447d52981bafdb63546b45840e26f60c1ade47627ea4c79e358306e8",
            "bytes": 12604,
        }
        and type(nominal["original_native_exit"]) is int
        and nominal["original_native_exit"] == 1
        and nominal["original_native_qualification"]
        == "refused_post_scientific_body_origin"
        and nominal["original_full_import_origin_admission"] == "not established"
        and type(nominal["saved_product_observer_native_exit"]) is int
        and nominal["saved_product_observer_native_exit"] == 0
        and nominal["attempts"] == 2496
        and nominal["prediction_slots"] == 675
        and report["nominal_source_candidate"] == nominal["source_candidate"]
        and report["nominal_training_protocol_sha256"]
        == nominal["training_protocol_sha256"],
        "original nominal identity/failure and separately admitted reuse required",
    )
    review = authority["independent_semantics"]
    require(
        review["approved"] is True
        and review["scientific_saved_products_admitted"] is True
        and review["source_candidate"] == candidate,
        "actual independent saved-output admission required",
    )
    require(
        report["prior_attempts_reused"] == 2496
        and report["max_new_start_slots"] == report["actual_new_attempts"] == 4992
        and report["total_unique_attempts"] == 7488
        and type(report["new_attempts_accepted"]) is int
        and type(report["new_attempts_refused"]) is int
        and min(report["new_attempts_accepted"], report["new_attempts_refused"]) >= 0
        and report["new_attempts_accepted"] + report["new_attempts_refused"] == 4992,
        "unique/new/reused attempt denominators differ",
    )
    for key in (
        "actual_new_attempts",
        "new_attempts_accepted",
        "new_attempts_refused",
        "total_unique_attempts",
    ):
        require(report[key] == review[key], "independent attempt summary differs")
    records = authority["record_ids"]
    require(
        type(records) is list
        and len(records) == len(set(records)) == 15
        and all(type(value) is str and value for value in records),
        "exact fifteen original site identities required",
    )
    dispositions = report["candidate_dispositions"]
    expected = {
        (method, target, baseline)
        for method in METHODS
        for target in records
        for baseline in BASELINES
    }
    require(
        type(dispositions) is list
        and len(dispositions) == 135
        and {
            (row["method"], row["outer_target"], row["baseline"])
            for row in dispositions
        }
        == expected,
        "complete135 candidate dispositions required",
    )
    predicted = set()
    for row in dispositions:
        require(
            row["status"] in {"predicted", "refused"}, "unknown candidate disposition"
        )
        if row["status"] == "predicted":
            predicted.add((row["method"], row["outer_target"], row["baseline"]))
        else:
            require(
                type(row.get("reason")) is str
                and bool(row["reason"])
                and row.get("reason_code")
                in {"forward_model_refused", "no_accepted_training_start"},
                "candidate refusal lost",
            )
    scores = report["candidate_scores"]
    scorekeys = {
        (row["method"], row["outer_target"], row["baseline"]) for row in scores
    }
    require(
        len(scores) == len(scorekeys) and scorekeys == predicted,
        "candidate score/refusal population differs",
    )
    for row in scores:
        require(
            row.get("target") == "pollen_composition"
            and row.get("status") == "scored"
            and type(row.get("taxon_count")) is int
            and row["taxon_count"] == 30
            and type(row.get("scored_taxon_count")) is int
            and row["scored_taxon_count"] == 30
            and type(row.get("observed_total_count")) is int
            and row["observed_total_count"] > 0,
            "scoring support or denominator differs",
        )
        require(
            all(
                type(row.get(key)) in (int, float) and math.isfinite(row[key])
                for key in (
                    "mae_fraction",
                    "rmse_fraction",
                    "bias_fraction",
                    "total_variation",
                )
            )
            and 0 <= row["total_variation"] <= 1,
            "finite descriptive fraction metrics required",
        )
        require(
            type(row.get("zero_probability_positive_count")) is bool
            and (
                (
                    row["zero_probability_positive_count"]
                    and row.get("count_conditioned_deviance") is None
                )
                or (
                    not row["zero_probability_positive_count"]
                    and type(row.get("count_conditioned_deviance")) in (int, float)
                    and math.isfinite(row["count_conditioned_deviance"])
                    and row["count_conditioned_deviance"] >= 0
                )
            ),
            "qualified finite/null deviance required",
        )
    selected_scores = report["selected_scores"]
    selected_refusals = report["selected_refusals"]
    selected = [*selected_scores, *selected_refusals]
    require(
        len(selected) == 45
        and {(row["outer_target"], row["baseline"]) for row in selected}
        == {(target, baseline) for target in records for baseline in BASELINES},
        "complete45 selected dispositions required",
    )
    require(
        all(
            (row["method"], row["outer_target"], row["baseline"]) in predicted
            and row in scores
            for row in selected_scores
        ),
        "selected score was not a candidate score",
    )
    require(
        all(
            row["status"] == "refused"
            and type(row.get("reason")) is str
            and row["reason"]
            for row in selected_refusals
        ),
        "selected refusal lost",
    )
    require(
        report["inner_prediction_dispositions"]
        == review["inner_prediction_dispositions"]
        and set(report["inner_prediction_dispositions"]) == set(METHODS),
        "independent inner disposition summary differs",
    )
    for row in report["inner_prediction_dispositions"].values():
        require(
            row["expected"] == 630
            and all(
                type(row[key]) is int and row[key] >= 0
                for key in ("predicted", "refused")
            )
            and row["predicted"] + row["refused"] == 630,
            "complete1890 inner dispositions required",
        )
    published_report = authority["products"]["report"]["original_reference"]
    require(
        authority["raw_trace_products"]["evaluation:report.json"]
        == {"sha256": published_report["sha256"], "bytes": published_report["bytes"]},
        "public report and retained evaluation-report identity differ",
    )
    require(
        trace_index["schema_version"] == "author-love-ppe-trace-index.v1"
        and set(authority["raw_trace_products"]) == TRACE_ROLES,
        "exact eleven external scientific product roles required",
    )
    seen = set()
    objects = set()
    for row in trace_index["objects"]:
        require(
            set(row) == {"sha256", "bytes", "retention_key", "roles"}
            and valid_pin(row)
            and row["retention_key"] == "sha256:" + row["sha256"]
            and row["sha256"] not in objects
            and type(row["roles"]) is list
            and len(row["roles"]) == len(set(row["roles"]))
            and bool(row["roles"]),
            "finite content-addressed trace object required",
        )
        objects.add(row["sha256"])
        for role in row["roles"]:
            require(
                role in TRACE_ROLES
                and role not in seen
                and authority["raw_trace_products"][role]
                == {"sha256": row["sha256"], "bytes": row["bytes"]},
                "trace membership or original content identity differs",
            )
            seen.add(role)
    require(
        seen == TRACE_ROLES,
        "complete two changed fit/two-product and seven evaluation trace closure required",
    )
    return {
        "candidate_dispositions": 135,
        "inner_dispositions": 1890,
        "selected_dispositions": 45,
        "selected_scores": len(selected_scores),
        "selected_refusals": len(selected_refusals),
        "new_attempts": 4992,
        "reused_attempts": 2496,
        "unique_attempts": 7488,
        "raw_trace_roles": 11,
        "private_trace_payloads_read": 0,
        "models_or_rescoring_executed": False,
        "original_nominal_native_qualification": "refused_post_scientific_body_origin",
        "scope": "Frozen prior-exposed deterministic marginal-SD PPE development only; independent stored-output authority is separate from broader model development, ecological, rights, human and release acceptance.",
    }


def validated_author_ppe_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
    *,
    authority_sha256: str,
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Bind the final actual authority explicitly; never admit a pending template."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared and not (repository / AUTHORITY).exists():
        return (), {}
    require(
        re.fullmatch("[a-f0-9]{64}", authority_sha256) is not None,
        "actual final authority SHA required",
    )
    authority_path = repository / AUTHORITY
    authority = json.loads(
        _read(repository, AUTHORITY, authority_sha256, authority_path.stat().st_size)
    )
    require(
        authority["schema_version"]
        == "author-love-nested-ppe-publication-authority.v1",
        "frozen publication authority schema differs",
    )
    require(
        len(declared) == 1
        and declared[0].get("role") == "retained_source"
        and declared[0].get("paths")
        == sorted(PREFIX + name for name in PRODUCTS.values())
        and declared[0].get("producer_paths")
        == declared[0].get("producer_inputs")
        == [],
        "exact additive two-product ownership required",
    )
    protocol = authority["protocol"]
    protocol_body = json.loads(
        _read(
            repository, PREFIX + "protocol.json", protocol["sha256"], protocol["bytes"]
        )
    )
    require(
        protocol["sha256"]
        == "d9f4fbae4c8aa373158abfba5a7062dc01a39ebd584cde7e5938f5c6141718b4"
        and protocol_body["schema_version"] == "author-love-nested-ppe-protocol.v1",
        "exact executed deterministic PPE protocol required",
    )
    require(
        len(authority["producer_sources"]) == 5
        and [row["name"] for row in authority["producer_sources"]] == list(SOURCES)
        and authority["producer_sources"]
        == [
            {"name": row["path"], "sha256": row["sha256"], "bytes": row["bytes"]}
            for row in protocol_body["execution_sources"]
        ],
        "exact five maintained evaluation sources required",
    )
    for row in authority["producer_sources"]:
        _read(repository, PREFIX + "source/" + row["name"], row["sha256"], row["bytes"])
    nominal = authority["nominal_reuse"]["publication_authority"]
    require(
        nominal
        == {
            "path": "reports/science/source-cohorts/author-love-nested-transport.json",
            "sha256": "f82f7c83447d52981bafdb63546b45840e26f60c1ade47627ea4c79e358306e8",
            "bytes": 12604,
        },
        "exact existing nominal authority reference required before reading",
    )
    previous = json.loads(
        _read(repository, nominal["path"], nominal["sha256"], nominal["bytes"])
    )
    require(
        previous["source_candidate"] == "70dd58ce28071d3b4ef34af2c800370a52d42bf9"
        and previous["independent_semantics"]["approved"] is True
        and previous["independent_semantics"]["scientific_saved_products_admitted"]
        is True
        and authority["record_ids"] == previous["record_ids"],
        "existing nominal authority differs",
    )
    require(
        set(authority["products"]) == set(PRODUCTS),
        "exact compact report/index products required",
    )
    accepted = []
    bodies = {}
    for role, name in PRODUCTS.items():
        item = authority["products"][role]
        require(item["name"] == name, "unexpected public product name")
        reference = item["original_reference"]
        entry = tracked_by_path.get(PREFIX + name)
        require(
            entry is not None
            and entry.sha256 == reference["sha256"]
            and entry.size == reference["bytes"],
            "Git public product identity differs",
        )
        assert entry is not None
        accepted.append(entry)
        bodies[role] = json.loads(
            _read(repository, PREFIX + name, reference["sha256"], reference["bytes"])
        )
    require(
        bodies["report"]["parameter_sensitivity_scope"]
        == protocol_body["evidence_scope"],
        "executed deterministic marginal-SD scope differs",
    )
    result = validate_public_result(bodies["report"], bodies["trace_index"], authority)
    return tuple(accepted), {
        "owner_id": OWNER,
        "authority_sha256": authority_sha256,
        "executed_source_candidate": authority["source_candidate"],
        **result,
    }
