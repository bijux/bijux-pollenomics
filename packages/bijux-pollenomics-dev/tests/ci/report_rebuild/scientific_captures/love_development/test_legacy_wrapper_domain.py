"""Compact legacy domain account retains exact refusals and source boundaries."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import runpy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

REPOSITORY = globals().get(
    "PUBLICATION_REPOSITORY", Path(__file__).absolute().parents[7]
)
MODULE = globals().get(
    "PUBLICATION_GUARD",
    Path(__file__).absolute().parents[5]
    / "src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/love_development/legacy_wrapper_domain.py",
)
GUARD = runpy.run_path(str(MODULE))


def publication() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    values = [
        json.loads((REPOSITORY / name).read_bytes())
        for name in (
            GUARD["PREFIX"] + "report.json",
            GUARD["PREFIX"] + "trace-index.json",
            GUARD["AUTHORITY"],
        )
    ]
    return values[0], values[1], values[2]


def test_current_compact_callback_without_private_traces() -> None:
    tracked = {
        name: InventoryEntry(name, "file", r["bytes"], r["sha256"], r["sha256"])
        for name, r in GUARD["PINS"].items()
        if name.startswith(GUARD["PREFIX"])
    }
    owners = [
        {
            "owner_id": GUARD["OWNER"],
            "role": "retained_source",
            "paths": sorted(GUARD["PREFIX"] + n for n in GUARD["PRODUCTS"]),
        }
    ]
    entries, result = GUARD["validated_author_legacy_wrapper_domain"](
        REPOSITORY, tracked, owners
    )
    assert len(entries) == 2 and result["requests"] == result["request_refusals"] == 39
    assert result["ring_placeholders_not_executed"] == 78
    assert (
        result["private_trace_payloads_read"]
        == result["models_or_scores_executed"]
        == 0
    )
    assert GUARD["validated_author_legacy_wrapper_domain"](REPOSITORY, {}, []) == (
        (),
        {},
    )


def test_exact_complete_refusal_population() -> None:
    result = GUARD["validate_products"](*publication())
    assert result["requests"] == 39 and result["ring_placeholders_not_executed"] == 78


@pytest.mark.parametrize(
    "case",
    [
        "missing-request",
        "duplicate-request",
        "promoted-success",
        "executed-ring",
        "wrong-reason",
        "changed-background",
        "changed-seed",
        "changed-source",
        "changed-taxa",
        "nominal-native0",
        "instrumented-count-claim",
        "score-promotion",
        "trace-reference",
        "bool-exit",
        "bool-counter",
        "wrong-public-binding",
        "native-reference",
        "source-plan",
    ],
)
def test_changed_population_promotion_or_source_refuses(case: str) -> None:
    report, index, authority = deepcopy(publication())
    rows = report["request_dispositions"]
    if case == "missing-request":
        rows.pop()
    elif case == "duplicate-request":
        rows[1] = rows[0]
    elif case == "promoted-success":
        rows[0]["status"] = "completed"
    elif case == "executed-ring":
        rows[0]["ring_dispositions"][0]["status"] = "completed"
    elif case == "wrong-reason":
        rows[0]["reason_code"] = "generic_failure"
    elif case == "changed-background":
        rows[0]["raw_regional_cover"][0] += 1e-9
    elif case == "changed-seed":
        rows[0]["local_seed"] = 7
    elif case == "changed-source":
        next(iter(report["scientific_sources"].values()))["sha256"] = "0" * 64
    elif case == "changed-taxa":
        report["taxa"][0] = "foreign_taxon"
    elif case == "nominal-native0":
        report["original_nominal"]["native_exit"] = 0
    elif case == "instrumented-count-claim":
        report["zero_downstream_calls_qualification"] = "Instrumented zero counters"
    elif case == "score-promotion":
        report["predictions_scores_or_selection_admitted"] = True
    elif case == "trace-reference":
        index["objects"][0]["sha256"] = "0" * 64
    elif case == "bool-exit":
        authority["actual_exit"] = False
    elif case == "bool-counter":
        report["summary"][
            "source_qualified_optimizer_kernel_REVEALS_forward_score_calls"
        ] = False
    elif case == "native-reference":
        authority["native_terminal"]["sha256"] = "0" * 64
        index["objects"][1]["sha256"] = "0" * 64
    elif case == "source-plan":
        authority["original_plan"]["sha256"] = "0" * 64
    else:
        authority["public_products"]["report.json"]["sha256"] = "0" * 64
    with pytest.raises(ReportRebuildError):
        GUARD["validate_products"](report, index, authority)
