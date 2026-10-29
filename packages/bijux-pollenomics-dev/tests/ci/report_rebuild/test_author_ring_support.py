"""Frozen ring-support publication preserves population, refusals and source-only scope."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import runpy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import _regular_entry, load_policy
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

REPOSITORY = Path(__file__).absolute().parents[5]
MODULE = (
    Path(__file__).absolute().parents[3]
    / "src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/author_ring_support.py"
)
GUARD = runpy.run_path(str(MODULE))


def publication() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    values = tuple(
        json.loads((REPOSITORY / name).read_bytes())
        for name in (
            GUARD["PREFIX"] + "report.json",
            GUARD["PREFIX"] + "trace-index.json",
            GUARD["AUTHORITY"],
        )
    )

    return values[0], values[1], values[2]


def test_current_compact_products_admit_without_private_traces() -> None:
    policy = load_policy(REPOSITORY / "configs/ci/reproducible-report-build.json")
    owners = json.loads((REPOSITORY / "configs/ci/report-ownership.json").read_bytes())[
        "owners"
    ]
    entries = {
        GUARD["PREFIX"] + name: _regular_entry(
            REPOSITORY / GUARD["PREFIX"] / name, GUARD["PREFIX"] + name, policy
        )
        for name in GUARD["PRODUCTS"]
    }
    admitted, evidence = GUARD["validated_author_ring_support_capture"](
        REPOSITORY, entries, owners
    )
    assert len(admitted) == 2
    assert (
        evidence["private_trace_payloads_read"]
        == evidence["new_model_or_score_calls"]
        == 0
    )
    assert evidence["saved_ring0_attempts"] == 1248
    assert evidence["original_failed_ring_native_exit"] == 1
    assert evidence["corrected_ring_native_exit"] == 0


def test_saved_compact_population_and_qualifiers() -> None:
    report, index, authority = publication()
    observed = GUARD["validate_products"](report, index, authority)
    assert observed["accepted_ring0_attempts"] == 1150
    assert observed["refused_ring0_attempts"] == 98
    assert observed["conditional_probability_value_projections"] == 675


@pytest.mark.parametrize(
    "case",
    [
        "missing_request",
        "duplicate_request",
        "lost_refusal",
        "nonzero_shell",
        "physical_rsap",
        "missing_projection",
        "promoted_native",
        "promoted_science",
        "changed_trace",
        "bool_exit",
    ],
)
def test_changed_population_or_scope_refuses(case: str) -> None:
    report, index, authority = deepcopy(publication())
    if case == "missing_request":
        report["request_equivalences"].pop()
    elif case == "duplicate_request":
        report["request_equivalences"][1] = report["request_equivalences"][0]
    elif case == "lost_refusal":
        report["request_equivalences"][0]["refused"] += 1
    elif case == "nonzero_shell":
        report["geometry_proofs"][0]["conditional_kernel_value"] = 0.1
    elif case == "physical_rsap":
        report["geometry_proofs"][0]["physical_rsap_validated"] = True
    elif case == "missing_projection":
        report["projection_groups"][0]["slots"] -= 1
    elif case == "promoted_native":
        report["original_nominal"]["native_exit"] = 0
    elif case == "promoted_science":
        report["preserved_pure_function_qualifications"]["scientific_acceptance"] = (
            "passed"
        )
    elif case == "changed_trace":
        index["objects"][0]["sha256"] = "0" * 64
    else:
        authority["actual_exit"] = False
    with pytest.raises(ReportRebuildError):
        GUARD["validate_products"](report, index, authority)
