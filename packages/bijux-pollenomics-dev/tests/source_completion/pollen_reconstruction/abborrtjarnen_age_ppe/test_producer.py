"""All-row persistence and honest unconditional/complete-event boundaries."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe import (
    chronology,
    count_profiles,
    inputs,
    producer,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe.moments import (
    PopulationMoments,
    joint_window_moments,
    window_moments,
)

from .test_inputs import sample


def controlled_case() -> dict[str, Any]:
    samples = [sample(i + 1, [10] * 5) for i in range(4)]
    ages = [1750.0, 2250.0, 2750.0, 4750.0]
    for s, age in zip(samples, ages, strict=True):
        s["source_point_age_bp"] = age
    reference = [
        {
            "sample_ids": [i + 1],
            "pooled_panel_counts": [10] * 5,
            "cover": [0.2] * 5,
            "counting_covariance": (
                (np.eye(5) * 0.2 - np.full((5, 5), 0.04)) / 50
            ).tolist(),
            "ppe_gradient": (np.full((5, 5), 0.04) - np.eye(5) * 0.2).tolist(),
        }
        for i in range(4)
    ]
    return {
        "protocol": {
            "age_inputs": [
                {"seed": seed, "retained_rows": 2, "first_native_row": 3502}
                for seed in (314159, 271828)
            ],
            "age_authority": {"requested_rows": 4},
            "resource_budget": {"wall_seconds": 180, "output_bytes": 20_000_000},
        },
        "source_protocol": {"source_store_files": {}, "repository_files": {}},
        "parameters": [
            {"ppe": 1.0, "published_sd": 0.1 if i < 4 else 0.0} for i in range(5)
        ],
        "deposition": np.ones(5),
        "physical_response": [{"factor": 1.0}] * 5,
        "sample_ids": [f"neotoma:sample:{i + 1}" for i in range(4)],
        "samples": samples,
        "sample_accounts": [
            {k: v for k, v in s.items() if k != "counts"} for s in samples
        ],
        "age_authority": {"status": "controlled"},
        "fixed_age_reference": reference,
        "input_sha256": {},
    }


def test_fixed_age_analytic_five_axis_control() -> None:
    case = controlled_case()
    control = producer.fixed_age_check(
        case, lambda n: window_moments(n, np.ones(5), np.ones(5), np.zeros((5, 5)))
    )
    assert control["passed"] and control["maximum_absolute_gap"] <= 1e-12


@pytest.mark.parametrize("all_undefined", [False, True])
def test_publish_retains_every_refused_row_and_defined_bin_cover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, all_undefined: bool
) -> None:
    case = controlled_case()
    if all_undefined:
        case["samples"][-1]["missing_taxa"] = ["Poaceae"]
        case["samples"][-1]["counts"] = None
    monkeypatch.setattr(inputs, "prepare", lambda *_: case)
    monkeypatch.setattr(chronology, "check_inputs", lambda *_: None)
    monkeypatch.setattr(producer, "source_revision", lambda *_: "controlled-source")
    monkeypatch.setattr(producer, "fixed_age_check", lambda *_: {"passed": True})

    def rows(_: Path, entry: dict[str, Any], __: list[str]) -> Any:
        yield 3502, [1750.0, 2250.0, 2750.0, 4750.0]
        yield (
            3503,
            [1750.0, 2250.0, 2750.0, 5100.0]
            if entry["seed"] == 314159
            else [1750.0, 2250.0, 2750.0, 4750.0],
        )

    monkeypatch.setattr(chronology, "age_rows", rows)
    (tmp_path / "artifacts").mkdir()
    output = tmp_path / "artifacts/calculation"
    result = producer.publish(tmp_path, tmp_path, output)
    assert (
        result["requested_draws"] == 4
        and result["unconditional"]["status"] == "refused_undefined_mass"
    )
    assert (
        result["unconditional"]["mean"] is result["unconditional"]["covariance"] is None
    )
    assert result["complete_draws"] == (0 if all_undefined else 3)
    assert result["complete_probability"] == (0.0 if all_undefined else 0.75)
    with gzip.open(output / "draw-ledger.csv.gz", "rt", newline="") as stream:
        ledger = list(csv.DictReader(stream))
    assert len(ledger) == 4 and {(r["seed"], r["native_row"]) for r in ledger} == {
        (str(seed), str(row)) for seed in (314159, 271828) for row in (3502, 3503)
    }
    refused = ledger[1]
    assert (
        refused["complete"] == "0" and refused["bin_9_status"] == "empty_native_window"
    )
    assert refused["cover_3_29"] != "" and refused["cover_9_29"] == ""
    assert len(result["conditional_on_complete"]["contrasts"]) == 30
    assert "count_profile" not in result and "source_support" not in result


def source_supported_case(
    root: Path,
    *,
    native_empty: bool = False,
) -> tuple[dict[str, Any], list[tuple[int, int, list[float]]]]:
    """Build small analytical populations without running the original producer."""
    case = controlled_case()
    extra = sample(5, [10, 10, 10, 10, 0], ["Poaceae"])
    extra["source_point_age_bp"] = 5200.0
    case["samples"].append(extra)
    case["sample_accounts"].append({k: v for k, v in extra.items() if k != "counts"})
    case["sample_ids"].append("neotoma:sample:5")
    case["native_samples"] = case["samples"]
    case["samples"] = [
        {
            **s,
            "analytical_missing_taxa": [],
            "analytical_panel_mass": s["reported_panel_subtotal"],
            "source_recorded_zero_support": [{"original_token": "0"}]
            if s["sample_id"] == 5
            else [],
            "counts": [10, 10, 10, 10, 0] if s["sample_id"] == 5 else s["counts"],
        }
        for s in case["native_samples"]
    ]
    states = [
        (314159, 3502, [1750.0, 2250.0, 2750.0, 4750.0, 5200.0]),
        (314159, 3503, [1750.0, 2250.0, 2750.0, 4750.0, 4800.0]),
        (271828, 3502, [1750.0, 2250.0, 2750.0, 4750.0, 5200.0]),
        (271828, 3503, [1750.0, 2250.0, 2750.0, 5100.0, 5200.0]),
    ]
    if native_empty:
        states[0][2][-1] = 4800.0
        states[2][2][-1] = 4800.0
    (root / "artifacts").mkdir()
    ledger = root / "artifacts/native-ledger.csv.gz"
    accumulator = PopulationMoments(np.diag([0.1, 0.1, 0.1, 0.1, 0]) ** 2)
    with gzip.open(ledger, "wt", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=producer.ledger_fields())
        writer.writeheader()
        for seed, row, ages in states:
            record: dict[str, Any] = {"seed": seed, "native_row": row}
            complete = []
            for b in (3, 4, 5, 9):
                support, counts = inputs.membership(case["native_samples"], ages, b)
                record.update(
                    {
                        f"bin_{b}_{k}": json.dumps(
                            v, separators=(",", ":"), sort_keys=True
                        )
                        if isinstance(v, (dict, list))
                        else v
                        for k, v in support.items()
                    }
                )
                if counts is not None:
                    complete.append(
                        window_moments(
                            counts, np.ones(5), np.ones(5), accumulator.covariance
                        )
                    )
            record["complete"] = int(len(complete) == 4)
            if len(complete) == 4:
                accumulator.add(*joint_window_moments(complete))
            writer.writerow(record)
    reference = root / "artifacts/native-result.json"
    reference.write_text(
        json.dumps(
            {
                "requested_draws": 4,
                "complete_draws": accumulator.n,
                "conditional_on_complete": accumulator.result(),
            }
        )
    )
    case["count_profile_protocol"] = {
        "native_reference_result": "artifacts/native-result.json",
        "native_reference_ledger": "artifacts/native-ledger.csv.gz",
        "repository_inputs": {
            str(p.relative_to(root)): {
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in (reference, ledger)
        },
    }
    case["source_support"] = {"count_profile": count_profiles.SOURCE}
    return case, states


@pytest.mark.parametrize(
    "corruption", ["none", "row_identity", "native_mask", "old_moment"]
)
def test_source_profile_publish_checks_old_population_and_retains_transitions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, corruption: str
) -> None:
    case, states = source_supported_case(tmp_path)
    monkeypatch.setattr(inputs, "prepare", lambda *_: case)
    monkeypatch.setattr(chronology, "check_inputs", lambda *_: None)
    monkeypatch.setattr(producer, "source_revision", lambda *_: "controlled-source")
    if corruption == "row_identity":
        states[0] = (314159, 3502, [1750.0, 2250.0, 2750.0, 5100.0, 5200.0])
    elif corruption == "native_mask":
        case["native_samples"][-1]["missing_taxa"] = []
        case["native_samples"][-1]["counts"] = [10, 10, 10, 10, 0]
    elif corruption == "old_moment":
        p = tmp_path / "artifacts/native-result.json"
        content = json.loads(p.read_text())
        content["conditional_on_complete"]["mean"][0] += 0.01
        p.write_text(json.dumps(content))

    def rows(_: Path, entry: dict[str, Any], __: list[str]) -> Any:
        yield from ((row, ages) for seed, row, ages in states if seed == entry["seed"])

    monkeypatch.setattr(chronology, "age_rows", rows)
    output = tmp_path / "artifacts/source-profile"
    if corruption != "none":
        with pytest.raises(ValueError, match="membership|moments changed"):
            producer.publish(tmp_path, tmp_path, output, count_profiles.SOURCE)
        assert not (output / "result.json").exists()
        return
    result = producer.publish(tmp_path, tmp_path, output, count_profiles.SOURCE)
    comparison = result["comparison_to_native_explicit"]
    assert result["complete_draws"] == 3 and result["undefined_draws"] == 1
    assert comparison["support_transition_counts"] == {
        "native_1->source_1": 2,
        "native_0->source_1": 1,
        "native_0->source_0": 1,
    }
    assert comparison["complete_probability_difference"] == 0.25
    assert comparison["common_native_population_check"]["passed"]
    assert len(comparison["conditional_contrast_differences"]) == 30
    with gzip.open(output / "draw-ledger.csv.gz", "rt", newline="") as stream:
        rows_saved = list(csv.DictReader(stream))
    assert [r["native_complete"] for r in rows_saved] == ["1", "0", "1", "0"]
    assert rows_saved[1]["bin_9_native_missing_members"] == '{"5":["Poaceae"]}'
    assert rows_saved[1]["bin_9_source_recorded_zero_sample_ids"] == "[5]"


def test_source_profile_without_native_complete_cases_has_no_invented_deltas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case, states = source_supported_case(tmp_path, native_empty=True)
    monkeypatch.setattr(inputs, "prepare", lambda *_: case)
    monkeypatch.setattr(chronology, "check_inputs", lambda *_: None)
    monkeypatch.setattr(producer, "source_revision", lambda *_: "controlled-source")

    def rows(_: Path, entry: dict[str, Any], __: list[str]) -> Any:
        yield from ((row, ages) for seed, row, ages in states if seed == entry["seed"])

    monkeypatch.setattr(chronology, "age_rows", rows)
    result = producer.publish(
        tmp_path,
        tmp_path,
        tmp_path / "artifacts/no-native-complete",
        count_profiles.SOURCE,
    )
    comparison = result["comparison_to_native_explicit"]
    assert comparison["native_complete_draws"] == 0 and result["complete_draws"] == 3
    assert comparison["common_native_population_check"]["draws"] == 0
    assert comparison["conditional_mean_difference"] is None
    assert comparison["conditional_covariance_component_differences"] is None
    assert comparison["conditional_contrast_differences"] is None
