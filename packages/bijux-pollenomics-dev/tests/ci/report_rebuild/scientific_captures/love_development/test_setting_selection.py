"""Frozen joint choices retain every pair disposition and original saved outcome."""

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
    / "src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/love_development/setting_selection.py",
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


def test_current_compact_callback_without_private_metrics() -> None:
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
    entries, result = GUARD["validated_development_setting_selection"](
        REPOSITORY, tracked, owners
    )
    assert (
        len(entries) == 2 and result["ranking_rows"] == 480 and result["choices"] == 15
    )
    assert (
        result["private_trace_payloads_read"]
        == result["new_scoring_or_model_calls"]
        == 0
    )
    assert result["untouched_accuracy_admitted"] is False
    assert GUARD["validated_development_setting_selection"](REPOSITORY, {}, []) == (
        (),
        {},
    )


def test_complete_choice_prediction_metric_population() -> None:
    result = GUARD["validate_products"](*publication())
    assert result["declared_pairs"] == 32 and result["selected_predictions"] == 15
    assert (
        result["selected_refusals"] == 0
        and result["source_inner_rows_referenced"] == 4410
    )


CASES = (
    "missing-pair",
    "missing-rank",
    "missing-choice",
    "changed-winner",
    "changed-coverage",
    "changed-mean",
    "promoted-prerequisite",
    "changed-alias",
    "changed-slot",
    "changed-manifest",
    "changed-signed-error",
    "changed-deviance",
    "changed-outcome",
    "missing-inner-source",
    "changed-source-metrics",
    "changed-freeze",
    "changed-ordering",
    "native0-promotion",
    "accuracy-promotion",
    "changed-observer-counter",
    "wrong-source",
    "wrong-trace",
    "bool-exit",
    "wrong-observation",
    "wrong-public-binding",
)


@pytest.mark.parametrize("case", CASES)
def test_population_ordering_source_or_accuracy_promotion_refuses(case: str) -> None:
    report, index, authority = deepcopy(publication())
    if case == "missing-pair":
        report["catalogue"].pop()
    elif case == "missing-rank":
        report["choices"][0]["ranking"].pop()
    elif case == "missing-choice":
        report["choices"].pop()
    elif case == "changed-winner":
        report["choices"][0]["selected_pair"]["candidate_id"] = "foreign"
    elif case == "changed-coverage":
        report["choices"][0]["ranking"][0]["complete_inner_predictions"] = 14
    elif case == "changed-mean":
        report["choices"][0]["ranking"][2]["mean_inner_total_variation"] += 1e-8
    elif case == "promoted-prerequisite":
        report["catalogue"][0]["eligibility"] = "saved_prediction"
    elif case == "changed-alias":
        report["source_equivalent_aliases"][0]["source_candidate_id"] = "foreign"
    elif case == "changed-slot":
        report["selected_predictions"][0]["source_slot_sha256"] = "0" * 64
    elif case == "changed-manifest":
        report["selected_predictions"][0]["source_prediction_manifest_sha256"] = (
            "0" * 64
        )
    elif case == "changed-signed-error":
        report["selected_outcomes"][0]["original_score"]["signed_error_by_taxon"][0][
            1
        ] += 1e-8
    elif case == "changed-deviance":
        report["selected_outcomes"][0]["original_score"][
            "count_conditioned_deviance"
        ] += 1
    elif case == "changed-outcome":
        report["selected_outcomes"][0]["outer_target"] = "foreign"
    elif case == "missing-inner-source":
        report["physical_inner_evidence"].pop()
    elif case == "changed-source-metrics":
        report["physical_inner_evidence"][0]["complete_original_rows_sha256"] = "0" * 64
    elif case == "changed-freeze":
        report["outcome_access"][0]["choice_freeze"]["sha256"] = "0" * 64
    elif case == "changed-ordering":
        report["freeze_ordering"] = "after outcomes"
    elif case == "native0-promotion":
        report["original_nominal"]["native_exit"] = 0
    elif case == "accuracy-promotion":
        report["scientific_limits"]["untouched_accuracy_admitted"] = True
    elif case == "changed-observer-counter":
        report["observer_summary"]["new_calls"]["scoring_calls"] = 1
    elif case == "wrong-source":
        next(iter(report["scientific_sources"].values()))["sha256"] = "0" * 64
    elif case == "wrong-trace":
        index["objects"][0]["sha256"] = "0" * 64
    elif case == "bool-exit":
        authority["actual_exit"] = False
    elif case == "wrong-observation":
        authority["observation"]["sha256"] = "0" * 64
    else:
        authority["public_products"]["report.json"]["sha256"] = "0" * 64
    with pytest.raises(ReportRebuildError):
        GUARD["validate_products"](report, index, authority)


@pytest.mark.parametrize("change", ["size", "same_size_hash"])
def test_changed_choice_source_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    import hashlib

    callback = GUARD["validated_development_setting_selection"]
    name = "reports/science/development-setting-selection/source/choice.py"
    assert name in GUARD["SCIENTIFIC_SOURCES"]
    raw = b"constructed-computational-source"
    target = tmp_path / name
    target.parent.mkdir(parents=True)
    target.write_bytes(raw + b"\n" if change == "size" else b"X" + raw[1:])
    monkeypatch.setitem(
        callback.__globals__,
        "PINS",
        {name: {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}},
    )
    owners = [
        {
            "owner_id": GUARD["OWNER"],
            "role": "retained_source",
            "paths": sorted(GUARD["PREFIX"] + value for value in GUARD["PRODUCTS"]),
        }
    ]
    with pytest.raises(ReportRebuildError, match="alias or size|computational source"):
        callback(tmp_path, {}, owners)
