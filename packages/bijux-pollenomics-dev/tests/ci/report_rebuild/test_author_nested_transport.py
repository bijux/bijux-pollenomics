"""Frozen nested transport publication keeps refusals and trace membership explicit."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import runpy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import _regular_entry, load_policy
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

REPOSITORY = Path(__file__).absolute().parents[5]
MODULE = (
    REPOSITORY
    / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/author_nested_transport.py"
)
GUARD = runpy.run_path(str(MODULE))


def test_current_publication_admits_only_compact_public_products() -> None:
    policy = load_policy(REPOSITORY / "configs/ci/reproducible-report-build.json")
    owners = json.loads((REPOSITORY / "configs/ci/report-ownership.json").read_bytes())[
        "owners"
    ]
    entries = {
        GUARD["PREFIX"] + name: _regular_entry(
            REPOSITORY / GUARD["PREFIX"] / name, GUARD["PREFIX"] + name, policy
        )
        for name in GUARD["PRODUCTS"].values()
    }
    admitted, evidence = GUARD["validated_author_transport_capture"](
        REPOSITORY,
        entries,
        owners,
        authority_sha256="f82f7c83447d52981bafdb63546b45840e26f60c1ade47627ea4c79e358306e8",
    )
    assert {entry.path for entry in admitted} == set(entries)
    assert evidence["candidate_dispositions"] == 225
    assert evidence["inner_dispositions"] == 3150
    assert evidence["selected_scores"] == 45
    assert evidence["selected_refusals"] == 0
    assert evidence["raw_trace_roles"] == 17
    assert evidence["private_trace_payloads_read"] == 0
    assert evidence["models_or_rescoring_executed"] is False
    assert (
        evidence["original_native_qualification"]
        == "refused_post_scientific_body_origin"
    )


def artificial_publication() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    methods = GUARD["METHODS"]
    baselines = GUARD["BASELINES"]
    records = [f"artificial-site:{index:02d}" for index in range(15)]
    dispositions = [
        {
            "method": method,
            "outer_target": record,
            "baseline": baseline,
            "status": "refused",
            "reason": "Artificial no accepted training start",
            "reason_code": "no_accepted_training_start",
        }
        for method in methods
        for record in records
        for baseline in baselines
    ]
    inner = {
        method: {"expected": 630, "predicted": 0, "refused": 630} for method in methods
    }
    report = {
        "schema_version": "author-love-nested-transport-development.v1",
        "candidate": "a" * 40,
        "protocol_sha256": "b" * 64,
        "methods": list(methods),
        "scientific_acceptance": "not_evaluated",
        "prior_attempts_reused": 1728,
        "max_new_start_slots": 10752,
        "actual_new_attempts": 10752,
        "total_unique_attempts": 12480,
        "new_attempts_accepted": 0,
        "new_attempts_refused": 10752,
        "candidate_dispositions": dispositions,
        "candidate_scores": [],
        "selected_scores": [],
        "selected_refusals": [
            {
                "outer_target": record,
                "baseline": baseline,
                "status": "refused",
                "reason": "No candidate has complete inner predictions",
            }
            for record in records
            for baseline in baselines
        ],
        "inner_prediction_dispositions": inner,
    }
    objects: list[dict[str, Any]] = [
        {
            "sha256": hashlib.sha256(role.encode()).hexdigest(),
            "bytes": 100,
            "retention_key": "sha256:" + hashlib.sha256(role.encode()).hexdigest(),
            "roles": [role],
        }
        for role in sorted(GUARD["TRACE_ROLES"])
    ]
    report_raw = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    report_pin: dict[str, Any] = {
        "sha256": hashlib.sha256(report_raw).hexdigest(),
        "bytes": len(report_raw),
    }
    report_object = next(
        row for row in objects if row["roles"] == ["evaluation:report.json"]
    )
    report_object.update(**report_pin, retention_key="sha256:" + report_pin["sha256"])
    index = {
        "schema_version": "author-love-transport-trace-index.v1",
        "objects": objects,
    }
    authority = {
        "source_candidate": "a" * 40,
        "products": {"report": {"original_reference": report_pin}},
        "protocol": {"sha256": "b" * 64},
        "execution": {
            "candidate": "a" * 40,
            "native_exit": 0,
            "source_before_after_equal": True,
            "inputs_before_after_equal": True,
            "runtime_before_after_equal": True,
        },
        "training_recovery": {
            "observer_native_exit": 0,
            "original_native_exits": dict.fromkeys(methods, 1),
            "original_native_qualification": "refused_post_scientific_body_origin",
            "original_full_import_origin_admission": "not established",
        },
        "independent_semantics": {
            "approved": True,
            "scientific_saved_products_admitted": True,
            "source_candidate": "a" * 40,
            "actual_new_attempts": 10752,
            "new_attempts_accepted": 0,
            "new_attempts_refused": 10752,
            "total_unique_attempts": 12480,
            "inner_prediction_dispositions": copy.deepcopy(inner),
        },
        "record_ids": records,
        "raw_trace_products": {
            row["roles"][0]: {"sha256": row["sha256"], "bytes": row["bytes"]}
            for row in objects
        },
    }
    return report, index, authority


def test_complete_refused_publication_preserves_denominators() -> None:
    report, index, authority = artificial_publication()
    result = GUARD["validate_public_result"](report, index, authority)
    assert result["candidate_dispositions"] == 225
    assert result["selected_dispositions"] == result["selected_refusals"] == 45
    assert result["selected_scores"] == 0
    assert result["private_trace_payloads_read"] == 0
    assert result["models_or_rescoring_executed"] is False


def test_original_failed_native_cannot_be_relabelled_zero() -> None:
    report, index, authority = artificial_publication()
    authority["training_recovery"]["original_native_exits"]["gpm neutral"] = 0
    with pytest.raises(ReportRebuildError):
        GUARD["validate_public_result"](report, index, authority)


def test_missing_candidate_disposition_refused() -> None:
    report, index, authority = artificial_publication()
    report["candidate_dispositions"].pop()
    with pytest.raises(ReportRebuildError):
        GUARD["validate_public_result"](report, index, authority)


def test_selected_refusal_cannot_disappear() -> None:
    report, index, authority = artificial_publication()
    report["selected_refusals"].pop()
    with pytest.raises(ReportRebuildError):
        GUARD["validate_public_result"](report, index, authority)


def test_changed_attempt_denominator_refused() -> None:
    report, index, authority = artificial_publication()
    report["actual_new_attempts"] = 10751
    with pytest.raises(ReportRebuildError):
        GUARD["validate_public_result"](report, index, authority)


def test_duplicate_or_firstparty_source_trace_role_refused() -> None:
    report, index, authority = artificial_publication()
    index["objects"][0]["roles"] = ["source/replay.py"]
    with pytest.raises(ReportRebuildError):
        GUARD["validate_public_result"](report, index, authority)


def test_changed_trace_content_identity_refused() -> None:
    report, index, authority = artificial_publication()
    index["objects"][0]["bytes"] += 1
    with pytest.raises(ReportRebuildError):
        GUARD["validate_public_result"](report, index, authority)


def test_draft_authority_hash_refused() -> None:
    with pytest.raises(ReportRebuildError):
        GUARD["validated_author_transport_capture"](
            REPOSITORY, {}, [{"owner_id": GUARD["OWNER"]}], authority_sha256=""
        )


def test_retained_report_cannot_disagree_with_public_report() -> None:
    report, index, authority = artificial_publication()
    row = next(
        value
        for value in index["objects"]
        if value["roles"] == ["evaluation:report.json"]
    )
    row["sha256"] = "0" * 64
    row["retention_key"] = "sha256:" + row["sha256"]
    authority["raw_trace_products"]["evaluation:report.json"] = {
        "sha256": row["sha256"],
        "bytes": row["bytes"],
    }
    with pytest.raises(ReportRebuildError):
        GUARD["validate_public_result"](report, index, authority)
