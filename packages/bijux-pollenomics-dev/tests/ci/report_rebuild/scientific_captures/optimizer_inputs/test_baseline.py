"""Read-reference ownership cannot become a produced numerical claim."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.optimizer_inputs import (
    baseline,
)


def fixture(helper: Any) -> tuple[dict[str, Any], ...]:
    baseline = {"path": "/declared/source/" + helper.BASELINE, **helper.BASELINE_PIN}
    pins = [
        baseline,
        *[
            {
                "path": "/declared/source/member-" + str(i),
                "sha256": "0" * 64,
                "bytes": 0,
            }
            for i in range(33319)
        ],
    ]
    stages = [
        {
            "id": name,
            "argv": ["python", name],
            "timeout_seconds": 1,
            "must_succeed": True,
        }
        for name in ("gradient", "finite", "observer")
    ]
    plan: dict[str, Any] = {
        "candidate": helper.CANDIDATE,
        "repository": "/declared/source",
        "canonical_identity": {"candidate": helper.CANDIDATE},
        "input_pins": pins,
        "gradient_baseline": baseline,
        "stages": stages,
    }
    history = {
        "candidate": helper.CANDIDATE,
        "original_plan_sha256": helper.PLAN_SHA,
        "original_input_count": 33320,
        "input_custody": [{"original": row} for row in pins],
        "original_controller_members": 8,
        "exact_derived_input_files": 47,
    }
    capture: dict[str, Any] = {
        "schema_version": "retained-author-optimizer-diagnostic-source-capture.v1",
        "original_execution_custody": {"optimizer-diagnostics": history},
        "reference_inputs": [
            {
                "path": helper.BASELINE,
                "record": baseline,
                "classification": "Read input; not produced by this diagnostic execution",
            }
        ],
        "report_outputs": [{"path": "a-diagnostic"}, {"path": "another-diagnostic"}],
    }
    common: dict[str, Any] = {
        "candidate": helper.CANDIDATE,
        "plan_sha256": helper.PLAN_SHA,
        "canonical_before": plan["canonical_identity"],
        "canonical_after": plan["canonical_identity"],
        "before_pin_mismatches": [],
        "after_pin_mismatches": [],
        "absent_input_paths_unchanged": True,
        "status": "passed",
        "actual_exit": 0,
        "stages": [{**row, "actual_exit": 0, "timed_out": False} for row in stages],
    }
    outer: dict[str, Any] = {
        "candidate": helper.CANDIDATE,
        "plan_sha256": helper.PLAN_SHA,
        "common_terminal": {"sha256": helper.COMMON_SHA},
        "actual_exit": 0,
        "common_actual_exit": 0,
        "memory_bound_pass": True,
        "storage_bound_pass": True,
    }
    review: dict[str, Any] = {
        "candidate": helper.CANDIDATE,
        "all_complete_diagnostic_typed_values_exact": True,
        "all_original_baselines_and_refusals_exact": True,
        "actual_diagnostic_optimizers_run": True,
        "full_experiment_fit_or_new_prediction_executed": False,
        "R_executed": False,
        "scientific_or_official_release_acceptance": False,
        "held_out_prediction_count": 0,
    }
    return (capture, plan, common, outer, review)


def test_read_input_certificate_preserves_native_refusals() -> None:
    documents = fixture(baseline)
    evidence = baseline.record_join(*documents)
    assert evidence["baseline_role"] == "read_input"
    assert evidence["baseline_produced_by_diagnostic"] is False
    assert evidence["original_baseline_generation_recovered"] is False
    documents[4]["all_original_baselines_and_refusals_exact"] = False
    with pytest.raises(ValueError):
        baseline.record_join(*documents)


def test_certificate_does_not_accept_boolean_native_success() -> None:
    documents = fixture(baseline)
    documents[2]["actual_exit"] = False
    with pytest.raises(ValueError):
        baseline.record_join(*documents)


def test_original_criterion_and_reference_recipe_are_exact() -> None:
    owner = deepcopy(baseline.ORIGINAL_OWNER)
    assert baseline.owner_projection([owner]) is False
    owner["role"] = "retained_source"
    assert baseline.owner_projection([owner]) is True
    owner["verification"] = "This diagnostic produced the baseline"
    with pytest.raises(ValueError):
        baseline.owner_projection([owner])


def test_published_certificate_cannot_disappear(tmp_path: Path) -> None:
    owner = deepcopy(baseline.ORIGINAL_OWNER)
    assert baseline.validated_optimizer_input_reference(tmp_path, [owner]) == {}
    owner["role"] = "retained_source"
    with pytest.raises(ValueError):
        baseline.validated_optimizer_input_reference(tmp_path, [owner])


def test_public_packet_namespace_refuses_unknown_file(tmp_path: Path) -> None:
    (tmp_path / "capture.json").write_text("{}")
    (tmp_path / "member").write_text("bound")
    baseline.exact_namespace(tmp_path, {"member"})
    (tmp_path / "unknown.py").write_text("shadow")
    with pytest.raises(ValueError):
        baseline.exact_namespace(tmp_path, {"member"})
