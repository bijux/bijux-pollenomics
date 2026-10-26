"""All-row persistence and honest unconditional/complete-event boundaries."""

from __future__ import annotations

import csv
import gzip
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe import (
    chronology,
    inputs,
    producer,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe.moments import (
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
    monkeypatch.setattr(producer, "source_revision", lambda _: "controlled-source")
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
