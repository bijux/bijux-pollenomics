"""Guard source identity and the undeleted Markov-chain row clock."""

from __future__ import annotations

import csv
import gzip
import io
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_age_ppe_dependence.quadratic_forms import (
    scalar_axes,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_monte_carlo import (
    inputs,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.abborrtjarnen_ppe_dependence.sources import (
    TAXON_IDS,
    WINDOWS,
)


@pytest.fixture
def metadata() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    repository = Path(__file__).resolve().parents[6]
    protocol = json.loads((repository / inputs.PROTOCOL).read_text())
    source = {
        "source_commit": protocol["producer_source_commit"],
        "count_profile": "pangaea_recorded_zeros_local_nc",
        "requested_draws": 32000,
        "complete_draws": 31999,
        "undefined_draws": 1,
        "unconditional": {"status": "refused_undefined_mass"},
        "conditional_on_complete": {"status": "conditional_on_complete"},
        "chain_summaries": [{"seed": seed} for seed in inputs.SEEDS],
        "component_axis": [
            {key: value for key, value in row.items() if key != "kind"}
            for row in scalar_axes()[:20]
        ],
        "draw_ledger": {
            "path": "draw-ledger.csv.gz",
            "rows": 32000,
            **protocol["repository_inputs"][protocol["source_ledger"]],
        },
    }
    check = {
        "status": "passed",
        "producer_source_commit": protocol["producer_source_commit"],
        "observer_source_commit": protocol["observer_source_commit"],
        "result_sha256": protocol["repository_inputs"][protocol["source_result"]][
            "sha256"
        ],
        "count_profile": "pangaea_recorded_zeros_local_nc",
        "native_samples_checked": 107,
        "saved_joint_age_rows_checked": 32000,
        "complete_rows": 31999,
        "undefined_rows": 1,
        "original_count_slots_checked": 535,
        "native_reported_count_pairs_checked": 527,
        "source_zero_slots_checked": 8,
        "covariance_entries_checked": 2400,
        "contrasts_checked": 30,
        "model_fits": 0,
        "maximum_ledger_cover_gap": 0,
        "maximum_moment_gap": 0,
        "common_native_maximum_moment_gap": 0,
        "maximum_profile_difference_gap": 0,
    }
    return protocol, source, check


def test_exact_source_qualification_metadata_is_required(
    metadata: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
) -> None:
    inputs.validate_metadata(*metadata)


@pytest.mark.parametrize(
    ("object_index", "key", "value"),
    [
        (0, "batch_design", {"batch_size": 125}),
        (0, "native_taxon_ids", [29, 74, 4416, 1287]),
        (1, "complete_draws", 32000),
        (1, "count_profile", "neotoma_explicit_five_taxon"),
        (1, "component_axis", []),
        (2, "status", "not_checked"),
        (2, "result_sha256", "different_source"),
        (2, "source_zero_slots_checked", 7),
        (2, "maximum_moment_gap", 1e-8),
    ],
)
def test_changed_source_or_design_metadata_refuses(
    metadata: tuple[dict[str, Any], dict[str, Any], dict[str, Any]],
    object_index: int,
    key: str,
    value: Any,
) -> None:
    metadata[object_index][key] = value
    with pytest.raises(ValueError):
        inputs.validate_metadata(*metadata)


def tiny_ledger(changes: dict[str, str]) -> bytes:
    row = {"seed": "314159", "native_row": "3502", "complete": "1"}
    for window in WINDOWS:
        row[f"bin_{window}_status"] = "defined"
        for taxon in TAXON_IDS:
            row[f"cover_{window}_{taxon}"] = "0.2"
    row.update(changes)
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    return gzip.compress(stream.getvalue().encode())


@pytest.mark.parametrize(
    "changes",
    [
        {"seed": "271828"},
        {"native_row": "3503"},
        {"complete": "0"},
        {"cover_3_29": "nan"},
        {"bin_3_status": "invented_status"},
        {"bin_3_status": "empty_native_window"},
    ],
)
def test_saved_seed_order_native_clock_and_missingness_refuse(
    changes: dict[str, str],
) -> None:
    with pytest.raises(ValueError):
        inputs.ordered_chains(tiny_ledger(changes), {})


def test_short_ledger_cannot_supply_a_trimmed_chain() -> None:
    with pytest.raises(ValueError, match="totals differ"):
        inputs.ordered_chains(
            tiny_ledger({}), {"requested_draws": 32000, "complete_draws": 31999}
        )
