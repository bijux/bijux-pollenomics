"""Compact seeded search account retains exact refusals and source boundaries."""

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
    / "src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/love_development/seeded_search.py",
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
        n: InventoryEntry(n, "file", r["bytes"], r["sha256"], r["sha256"])
        for n, r in GUARD["PINS"].items()
        if n.startswith(GUARD["PREFIX"])
    }
    owners = [
        {
            "owner_id": GUARD["OWNER"],
            "role": "retained_source",
            "paths": sorted(GUARD["PREFIX"] + n for n in GUARD["PRODUCTS"]),
        }
    ]
    entries, result = GUARD["validated_seeded_love_domain"](REPOSITORY, tracked, owners)
    assert (
        len(entries) == 2
        and result["requests"] == 39
        and result["attempted_rings"] == result["refused_rings"] == 78
    )
    assert (
        result["accepted_rings"]
        == result["private_trace_payloads_read"]
        == result["models_or_scores_executed"]
        == 0
    )
    assert GUARD["validated_seeded_love_domain"](REPOSITORY, {}, []) == ((), {})


def test_complete_budget_refusal_population() -> None:
    result = GUARD["validate_products"](*publication())
    assert result["search_evaluations"] == 1248000 and result["refused_rings"] == 78


CASES = (
    "missing-request",
    "duplicate-request",
    "missing-ring",
    "promoted-convergence",
    "changed-budget",
    "changed-seed",
    "changed-background",
    "changed-parameter",
    "changed-source",
    "changed-taxa",
    "nominal-native0",
    "observer-native-confusion",
    "score-promotion",
    "kernel-promotion",
    "trace-reference",
    "bool-exit",
    "bool-counter",
    "wrong-public-binding",
    "native-reference",
    "source-plan",
)


@pytest.mark.parametrize("case", CASES)
def test_changed_population_promotion_or_source_refuses(case: str) -> None:
    report, index, authority = deepcopy(publication())
    if case == "missing-request":
        report["requests"].pop()
    elif case == "duplicate-request":
        report["requests"][1] = report["requests"][0]
    elif case == "missing-ring":
        report["ring_dispositions"].pop()
    elif case == "promoted-convergence":
        report["ring_dispositions"][0]["optimizer"]["success"] = True
    elif case == "changed-budget":
        report["ring_dispositions"][0]["optimizer"]["nfev"] = 15999
    elif case == "changed-seed":
        report["requests"][0]["local_seed"] = 7
    elif case == "changed-background":
        report["requests"][0]["raw_regional_cover"][0] += 1e-9
    elif case == "changed-parameter":
        report["parameters"][0]["ppe"] += 1e-9
    elif case == "changed-source":
        next(iter(report["scientific_sources"].values()))["sha256"] = "0" * 64
    elif case == "changed-taxa":
        report["taxa"][0] = "foreign_taxon"
    elif case == "nominal-native0":
        report["original_nominal"]["native_exit"] = 0
    elif case == "observer-native-confusion":
        report["native_calls"]["optimizer_attempts"] = 0
    elif case == "score-promotion":
        report["predictions_scores_or_selection_admitted"] = True
    elif case == "kernel-promotion":
        report["observer_summary"]["kernels_independently_recomputed"] = True
    elif case == "trace-reference":
        index["objects"][0]["sha256"] = "0" * 64
    elif case == "bool-exit":
        authority["actual_exit"] = False
    elif case == "bool-counter":
        report["observer_summary"]["new_model_optimizer_kernel_forward_score_calls"] = (
            False
        )
    elif case == "native-reference":
        authority["native_terminal"]["sha256"] = "0" * 64
    elif case == "source-plan":
        authority["original_plan"]["sha256"] = "0" * 64
    else:
        authority["public_products"]["report.json"]["sha256"] = "0" * 64
    with pytest.raises(ReportRebuildError):
        GUARD["validate_products"](report, index, authority)
