"""Frozen temporal minima, complete score populations and external trace boundary."""

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
    / "src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/love_development/temporal_fixed_starts.py",
)
GUARD = runpy.run_path(str(MODULE))


def publication() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    rows = [
        json.loads((REPOSITORY / name).read_bytes())
        for name in (
            GUARD["PREFIX"] + "report.json",
            GUARD["PREFIX"] + "trace-index.json",
            GUARD["AUTHORITY"],
        )
    ]
    return rows[0], rows[1], rows[2]


def test_actual_two_product_callback_without_private_traces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tracked = {
        name: InventoryEntry(name, "file", row["bytes"], row["sha256"], row["sha256"])
        for name, row in GUARD["PINS"].items()
        if name.startswith(GUARD["PREFIX"])
    }
    owners = [
        {
            "owner_id": GUARD["OWNER"],
            "role": "retained_source",
            "paths": sorted(GUARD["PREFIX"] + name for name in GUARD["PRODUCTS"]),
        }
    ]
    original = Path.read_bytes

    def public_only(path: Path) -> bytes:
        if "author-love-temporal-fixed-start-TW" in str(path):
            raise AssertionError(
                "Private native traces must not be opened by compact admission"
            )
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", public_only)
    entries, result = GUARD["validated_temporal_fixed_starts"](
        REPOSITORY, tracked, owners
    )
    assert (
        len(entries) == 2
        and result["requests"] == 48
        and result["ring_dispositions"] == 96
    )
    assert (
        result["new_attempts"] == 3072
        and result["accepted_attempts"] == 2592
        and result["refused_attempts"] == 480
    )
    assert result["prediction_slots"] == result["scored_rows"] == 81
    assert (
        result["private_trace_payloads_read"]
        == result["models_or_scores_executed"]
        == 0
    )
    assert GUARD["validated_temporal_fixed_starts"](REPOSITORY, {}, []) == ((), {})


def test_complete_current_projection_and_stored_score_summaries() -> None:
    result = GUARD["validate_products"](*publication())
    assert result["scored_rows"] == 81


CASES = (
    "lost-request",
    "duplicate-request",
    "lost-ring",
    "accepted-denominator",
    "changed-minimum",
    "changed-seed",
    "closed-raw-background",
    "rounded-composition",
    "lost-slot",
    "changed-score-total",
    "foreign-target-graph",
    "wrong-summary-mean",
    "promoted-uniform",
    "promoted-uncertainty",
    "native-observer-confusion",
    "trace-reference",
    "bool-exit",
    "public-binding",
)


@pytest.mark.parametrize("case", CASES)
def test_changed_population_method_or_claim_is_refused(case: str) -> None:
    report, index, authority = deepcopy(publication())
    window = report["windows"][0]
    if case == "lost-request":
        window["requests"].pop()
    elif case == "duplicate-request":
        window["requests"][1] = window["requests"][0]
    elif case == "lost-ring":
        window["ring_dispositions"].pop()
    elif case == "accepted-denominator":
        window["ring_dispositions"][0]["refused"] += 1
    elif case == "changed-minimum":
        window["ring_dispositions"][0]["selected_start_id"] = "taxon-29-half-uniform"
    elif case == "changed-seed":
        window["requests"][0]["local_seed"] = 7
    elif case == "closed-raw-background":
        window["requests"][0]["regional_cover"][0] += 1e-5
    elif case == "rounded-composition":
        row = window["ring_dispositions"][0]
        taxon = next(iter(row["composition"]))
        row["composition"][taxon] += 1e-5
    elif case == "lost-slot":
        window["slots"].pop()
    elif case == "changed-score-total":
        window["slots"][0]["score"]["observed_total_count"] += 1
    elif case == "foreign-target-graph":
        window["slots"][0]["input_lineage"][window["slots"][0]["record_id"]] = []
    elif case == "wrong-summary-mean":
        window["score_summary"][0]["mean_total_variation"] += 0.01
    elif case == "promoted-uniform":
        window["original_uniform_summary"]["predicted_slots"] = 39
    elif case == "promoted-uncertainty":
        report["scientific_limits"]["calibrated_uncertainty_admitted"] = True
    elif case == "native-observer-confusion":
        authority["native_jobs"][0]["actual_exit"] = 1
    elif case == "trace-reference":
        index["objects"][0]["sha256"] = "0" * 64
    elif case == "bool-exit":
        authority["actual_exit"] = False
    else:
        authority["public_products"]["report.json"]["sha256"] = "0" * 64
    with pytest.raises(ReportRebuildError):
        GUARD["validate_products"](report, index, authority)
