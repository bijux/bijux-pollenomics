"""Qualify source metadata boundaries with invented receipts and no corpus copies."""

from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.controlled_numerical.native_execution import (
    _exact,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.vegetation_reference import (
    nfi_measurement as nfi,
)
from bijux_pollenomics_dev.native_backend import retained_performance as performance


def _nfi_receipts() -> tuple[dict[str, Any], ...]:
    """Describe the original metadata-only contract without any workbook or raw values."""
    stages = [
        {"id": "metadata", "argv": ["invented-reader"]},
        {"id": "readback", "argv": ["invented-observer"]},
    ]
    plan = {
        "candidate": nfi.ORIGINAL_CANDIDATE,
        "canonical_identity": {"invented": "fixed"},
        "stages": stages,
    }
    common = {
        "candidate": nfi.ORIGINAL_CANDIDATE,
        "plan_sha256": nfi.RECEIPTS["plan.json"],
        "actual_exit": 0,
        "canonical_before": plan["canonical_identity"],
        "canonical_after": plan["canonical_identity"],
        "before_pin_mismatches": [],
        "after_pin_mismatches": [],
        "absent_input_paths_unchanged": True,
        "stages": [{**stage, "actual_exit": 0, "timed_out": False} for stage in stages],
    }
    outer = {
        "candidate": nfi.ORIGINAL_CANDIDATE,
        "plan_sha256": nfi.RECEIPTS["plan.json"],
        "actual_exit": 0,
        "common_actual_exit": 0,
        "common_terminal": {"sha256": nfi.RECEIPTS["terminal.json"]},
        "memory_bound_pass": True,
        "storage_bound_pass": True,
    }
    review = {
        "candidate": nfi.ORIGINAL_CANDIDATE,
        "plan_sha256": nfi.RECEIPTS["plan.json"],
        "actual_exit": 0,
        "actual_maintained_producer_native_exit": 0,
        "plot_year_rows": 43892,
        "metadata_cells_decoded": 131676,
        "measurement_outcome_cells_decoded": 0,
        "benchmark_admission": "no_measured_pairs_admitted",
        "calibration_guide": {"retained_owner_admitted": False},
    }
    return plan, common, outer, review


def test_metadata_only_native_scope_is_preserved() -> None:
    """The explicit zero outcome counter differs from an unreported or false value."""
    nfi._native_records(*_nfi_receipts())


@pytest.mark.parametrize(
    "change",
    [
        "outcome",
        "missing_outcome",
        "false_outcome",
        "year_count",
        "guide",
        "epoch",
        "stage",
        "integer_zero",
    ],
)
def test_nfi_scope_promotion_refuses(change: str) -> None:
    """Reject outcome/guide/source/stage/count promotion of retained metadata."""
    records = copy.deepcopy(_nfi_receipts())
    plan, common, outer, review = records
    if change == "outcome":
        review["measurement_outcome_cells_decoded"] = 1
    elif change == "missing_outcome":
        review.pop("measurement_outcome_cells_decoded")
    elif change == "false_outcome":
        review["measurement_outcome_cells_decoded"] = False
    elif change == "year_count":
        review["plot_year_rows"] = 43891
    elif change == "guide":
        review["calibration_guide"]["retained_owner_admitted"] = True
    elif change == "epoch":
        plan["candidate"] = "different"
    elif change == "stage":
        common["stages"][0]["argv"] = ["unqualified"]
    else:
        outer["actual_exit"] = False
    with pytest.raises(ReportRebuildError):
        nfi._native_records(*records)


@pytest.mark.parametrize(
    "left,right",
    [(None, 0), (False, 0), (0.0, 0), ([None], [0]), ({"owner": None}, {"owner": 0})],
)
def test_controlled_missing_and_typed_zero_are_distinct(left: Any, right: Any) -> None:
    """Preserve missing/type distinctions rather than inventing zero observations."""
    with pytest.raises(ReportRebuildError):
        _exact(left, right)


@pytest.mark.parametrize("altered", [False, True])
def test_nfi_named_control_namespace_is_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, altered: bool
) -> None:
    """The source namespace delegates cryptography while retaining all eight controls."""
    controls = {
        "source-controls/check_contract.py",
        "source-controls/contracts.py",
        "source-controls/invoke.py",
        "source-controls/observe.py",
        "source-controls/prepare.py",
        "source-controls/run.py",
        "source-controls/runtime_custody.py",
        "source-controls/common-runner.py",
    }
    names = controls | {"source-code/packages/example/src/own.py"}
    members = {name: {"bytes": 3, "sha256": "0" * 64} for name in names}
    declared = set(names)
    if altered:
        declared.remove("source-controls/runtime_custody.py")

    def descriptor(
        repository: Path, prefix: str, selected: dict[str, Any]
    ) -> SimpleNamespace:
        assert repository == tmp_path and prefix == "invented" and selected is members
        return SimpleNamespace(detached=frozenset(declared))

    monkeypatch.setattr(nfi, "validated_descriptor", descriptor)
    if altered:
        with pytest.raises(ReportRebuildError):
            nfi._validate_source_transport(tmp_path, "invented", members)
    else:
        assert nfi._validate_source_transport(
            tmp_path, "invented", members
        ).detached == frozenset(names)


@pytest.mark.parametrize("altered", [False, True])
def test_performance_named_execution_roles_are_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, altered: bool
) -> None:
    """Retain original control/replay roles without copying a real timing packet."""
    controls = {
        "controls/boundary.py",
        "controls/check_contracts.py",
        "controls/measure.py",
        "controls/observe.py",
        "controls/prepare.py",
        "controls/run.py",
        "controls/scaling.py",
        "controls/storage.py",
        "controls/workloads.py",
        "controls/shared/run_account_qualification.py",
        "publication-controls/assemble.py",
        "publication-controls/contracts.py",
        "publication-controls/check_contracts.py",
        "publication-controls/observe.py",
        "publication-controls/prepare.py",
        "publication-controls/run.py",
        "publication-controls/proposal/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/retained_performance.py",
    }
    names = controls | {
        "source-code/packages/example/src/own.py",
        "reference-inputs/docs/report/method-certification/author-site-uncertainty/replay.py",
    }
    members = [{"path": name, "bytes": 3, "sha256": "0" * 64} for name in sorted(names)]
    declared = set(names)
    if altered:
        declared.add("controls/unqualified.py")

    def descriptor(
        repository: Path, prefix: str, selected: list[dict[str, Any]]
    ) -> SimpleNamespace:
        assert repository == tmp_path and prefix == "invented" and selected is members
        return SimpleNamespace(detached=frozenset(declared))

    monkeypatch.setattr(performance, "validated_descriptor", descriptor)
    if altered:
        with pytest.raises(ValueError):
            performance._validate_source_transport(
                tmp_path, tmp_path / "invented", members
            )
    else:
        assert performance._validate_source_transport(
            tmp_path, tmp_path / "invented", members
        ).detached == frozenset(names)
