"""Retain the complete nonselectable circular-receiver population and source scope."""

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
    / "src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/love_development/circular_receiver.py",
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
    entries, result = GUARD["validated_circular_receiver_domain"](
        REPOSITORY, tracked, owners
    )
    assert len(entries) == 2 and result["diagnostic_slots"] == 675
    assert (
        result["private_trace_payloads_read"]
        == result["models_or_scores_executed"]
        == 0
    )
    assert result["selection_eligible"] is False
    assert GUARD["validated_circular_receiver_domain"](REPOSITORY, {}, []) == ((), {})


def test_complete_diagnostic_population_is_not_observational_accuracy() -> None:
    result = GUARD["validate_products"](*publication())
    assert result["predicted_diagnostic"] == 675 and result["refused"] == 0
    assert result["outer_slots"] == 45 and result["inner_slots"] == 630
    assert (
        result["source_kernel_calls"] == 1800 and result["source_forward_calls"] == 675
    )


CASES = (
    "missing-slot",
    "duplicate-slot",
    "missing-context",
    "wrong-ancestry",
    "wrong-target",
    "wrong-baseline",
    "changed-tv",
    "changed-pair",
    "changed-radius",
    "changed-kernel",
    "changed-error",
    "missing-table",
    "changed-ppe",
    "changed-taxa",
    "changed-profile",
    "promoted-selection",
    "promoted-inverse",
    "promoted-accuracy",
    "promoted-kernels",
    "nominal-native0",
    "observer-calls",
    "bool-exit",
    "wrong-trace",
    "wrong-source",
    "wrong-public-binding",
    "wrong-observation",
)


@pytest.mark.parametrize("case", CASES)
def test_population_source_or_scientific_promotion_refuses(case: str) -> None:
    report, index, authority = deepcopy(publication())
    if case == "missing-slot":
        report["dispositions"].pop()
    elif case == "duplicate-slot":
        report["dispositions"][1] = report["dispositions"][0]
    elif case == "missing-context":
        report["contexts"].pop(next(iter(report["contexts"])))
    elif case == "wrong-ancestry":
        next(iter(report["contexts"].values()))["source_request_sha256s"][0] = "0" * 64
    elif case == "wrong-target":
        report["dispositions"][0]["target"] = "foreign"
    elif case == "wrong-baseline":
        report["dispositions"][0]["baseline"] = "foreign"
    elif case == "changed-tv":
        report["dispositions"][0]["prediction_difference_total_variation"] += 1e-8
    elif case == "changed-pair":
        report["dispositions"][0]["source_slot_sha256"] = "0" * 64
    elif case == "changed-radius":
        next(iter(report["response_tables"].values()))["receiver_radius_m"] += 1
    elif case == "changed-kernel":
        next(iter(report["response_tables"].values()))["full_k"][0][0] += 1e-8
    elif case == "changed-error":
        next(iter(report["response_tables"].values()))["estimated_absolute_error"][0][
            0
        ] += 1e-8
    elif case == "missing-table":
        report["response_tables"].pop(next(iter(report["response_tables"])))
    elif case == "changed-ppe":
        report["parameters"][0]["ppe"] += 1e-8
    elif case == "changed-taxa":
        report["taxa"][0] = "foreign"
    elif case == "changed-profile":
        report["setting"]["forward_profile"] = "foreign"
    elif case == "promoted-selection":
        report["dispositions"][0]["selection_eligible"] = True
    elif case == "promoted-inverse":
        report["scientific_limits"]["matched_inverse_qualified"] = True
    elif case == "promoted-accuracy":
        report["scientific_limits"]["target_accuracy_admitted"] = True
    elif case == "promoted-kernels":
        report["observer_summary"]["independently_recomputed_kernel_values"] = True
    elif case == "nominal-native0":
        report["original_nominal"]["native_exit"] = 0
    elif case == "observer-calls":
        report["observer_calls"]["kernel"] = 1
    elif case == "bool-exit":
        authority["actual_exit"] = False
    elif case == "wrong-trace":
        index["objects"][0]["sha256"] = "0" * 64
    elif case == "wrong-source":
        next(iter(report["scientific_sources"].values()))["sha256"] = "0" * 64
    elif case == "wrong-observation":
        authority["observation"]["sha256"] = "0" * 64
    else:
        authority["public_products"]["report.json"]["sha256"] = "0" * 64
    with pytest.raises(ReportRebuildError):
        GUARD["validate_products"](report, index, authority)


@pytest.mark.parametrize("change", ["size", "same_size_hash"])
def test_changed_computational_source_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    import hashlib

    callback = GUARD["validated_circular_receiver_domain"]
    name = next(
        name for name in GUARD["SCIENTIFIC_SOURCES"] if name.endswith("receiver.py")
    )
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
