"""Negative analytical diagnostics preserve raw dispositions and source boundaries."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import runpy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

REPOSITORY = Path(__file__).absolute().parents[5]
MODULE = (
    Path(__file__).absolute().parents[3]
    / "src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/author_analytical_diagnostics.py"
)
GUARD = runpy.run_path(str(MODULE))


def publication() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    values = [
        json.loads((REPOSITORY / name).read_bytes())
        for name in [
            GUARD["PREFIX"] + "report.json",
            GUARD["PREFIX"] + "trace-index.json",
            GUARD["AUTHORITY"],
        ]
    ]
    return values[0], values[1], values[2]


def test_current_compact_negative_diagnostics_without_private_traces() -> None:
    entries = {
        name: InventoryEntry(name, "file", row["bytes"], row["sha256"], row["sha256"])
        for name, row in GUARD["PINS"].items()
        if name.startswith(GUARD["PREFIX"])
    }
    owners = [
        {
            "owner_id": GUARD["OWNER"],
            "role": "retained_source",
            "paths": [GUARD["PREFIX"] + name for name in GUARD["PRODUCTS"]],
        }
    ]
    admitted, evidence = GUARD["validated_author_analytical_capture"](
        REPOSITORY, entries, owners
    )
    assert len(admitted) == 2 and evidence["invalid_raw_compositions"] == 78
    assert (
        evidence["closed_compositions"]
        == evidence["private_trace_payloads_read"]
        == evidence["models_or_scores_executed"]
        == 0
    )
    assert GUARD["validated_author_analytical_capture"](REPOSITORY, {}, []) == ((), {})


def test_full78_raw_rings_and_distinct39_requests() -> None:
    report, index, authority = publication()
    evidence = GUARD["validate_products"](report, index, authority)
    assert (
        evidence["negative_taxon_cells"] == 605
        and evidence["above_one_taxon_cells"] == 29
    )


@pytest.mark.parametrize(
    "case",
    [
        "missing_ring",
        "duplicate_ring",
        "lost_negative",
        "closed_promotion",
        "changed_request",
        "changed_taxon",
        "source_reference",
        "nominal_native",
        "trace_reference",
        "host_execution",
        "prediction_promotion",
        "bool_exit",
        "bool_counter",
    ],
)
def test_changed_population_source_or_scientific_promotion_refuses(case: str) -> None:
    report, index, authority = deepcopy(publication())
    if case == "missing_ring":
        report["ring_dispositions"].pop()
    elif case == "duplicate_ring":
        report["ring_dispositions"][1] = report["ring_dispositions"][0]
    elif case == "lost_negative":
        report["ring_dispositions"][0]["negative_taxon_count"] -= 1
    elif case == "closed_promotion":
        report["ring_dispositions"][0]["status"] = "closed_composition"
    elif case == "changed_request":
        report["request_joins"][0]["analytical_request_sha256"] = report[
            "request_joins"
        ][0]["nominal_request_sha256"]
    elif case == "changed_taxon":
        report["taxa"][0] = "foreign_taxon"
    elif case == "source_reference":
        next(iter(report["scientific_source_refs"].values()))["sha256"] = "0" * 64
    elif case == "nominal_native":
        report["original_nominal"]["native_exit"] = 0
    elif case == "trace_reference":
        index["objects"][0]["sha256"] = "0" * 64
    elif case == "host_execution":
        report["full_run_lra_cached_request_execution"] = True
    elif case == "prediction_promotion":
        report["prediction_compositions_admitted"] = True
    elif case == "bool_counter":
        report["summary"]["refused_requests"] = False
        authority["summary"]["refused_requests"] = False
    else:
        authority["actual_exit"] = False
    with pytest.raises(ReportRebuildError):
        GUARD["validate_products"](report, index, authority)
