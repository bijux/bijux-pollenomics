"""Bind the qualified saved-cover ledger and preserve its complete chain clock."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from ..abborrtjarnen_age_ppe_dependence.inputs import cover_rows
from ..abborrtjarnen_age_ppe_dependence.quadratic_forms import scalar_axes
from ..abborrtjarnen_ppe_dependence.sources import (
    TAXA,
    TAXON_IDS,
    WINDOWS,
    bound_files,
)
from .batch_means import Array, require

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/monte-carlo/protocol.json"
)
SEEDS = (314159, 271828)


def validate_metadata(
    protocol: dict[str, Any], source: dict[str, Any], check: dict[str, Any]
) -> None:
    """Use the previously independent source qualification within its exact scope."""
    require(
        protocol["batch_design"]
        == {
            "batch_size": 128,
            "batches_per_chain": 125,
            "rows_per_chain": 16000,
            "seeds": list(SEEDS),
            "native_first_row": 3502,
            "native_last_row": 19501,
        }
        and protocol["window_ids"] == list(WINDOWS)
        and protocol["taxon_axis"] == list(TAXA)
        and protocol["native_taxon_ids"] == list(TAXON_IDS),
        "Prospective batch design or scientific axes differ",
    )
    pins = protocol["repository_inputs"]
    require(
        len(pins) == 3
        and set(pins)
        == {
            protocol[name]
            for name in ("source_result", "source_ledger", "source_verification")
        },
        "Exactly three qualified scientific inputs required",
    )
    require(
        source["source_commit"]
        == check["producer_source_commit"]
        == protocol["producer_source_commit"]
        and check["observer_source_commit"] == protocol["observer_source_commit"]
        and check["result_sha256"] == pins[protocol["source_result"]]["sha256"]
        and check["status"] == "passed"
        and source["count_profile"]
        == check["count_profile"]
        == "pangaea_recorded_zeros_local_nc",
        "Qualified source-supported result/check identity differs",
    )
    for key, expected in {
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
    }.items():
        require(check.get(key) == expected, "Independent source check is incomplete")
    for key in (
        "maximum_ledger_cover_gap",
        "maximum_moment_gap",
        "common_native_maximum_moment_gap",
        "maximum_profile_difference_gap",
    ):
        value = check[key]
        require(
            type(value) in (int, float)
            and math.isfinite(value)
            and 0 <= value <= 1e-12,
            "Independent source numerical qualification differs",
        )
    require(
        (source["requested_draws"], source["complete_draws"], source["undefined_draws"])
        == (32000, 31999, 1)
        and source["unconditional"]["status"] == "refused_undefined_mass"
        and source["conditional_on_complete"]["status"] == "conditional_on_complete"
        and [row["seed"] for row in source["chain_summaries"]] == list(SEEDS)
        and source["component_axis"]
        == [
            {key: value for key, value in row.items() if key != "kind"}
            for row in scalar_axes()[:20]
        ],
        "Qualified source population or estimand differs",
    )
    ledger = source["draw_ledger"]
    require(
        ledger["path"] == Path(protocol["source_ledger"]).name
        and ledger["rows"] == 32000
        and all(
            ledger[key] == pins[protocol["source_ledger"]][key]
            for key in ("bytes", "sha256")
        ),
        "Source result identifies a different ledger",
    )


def load(repository: Path) -> dict[str, Any]:
    protocol = json.loads((repository / PROTOCOL).read_bytes())
    bodies = bound_files(repository, protocol["repository_inputs"])
    source = json.loads(bodies[protocol["source_result"]])
    check = json.loads(bodies[protocol["source_verification"]])
    validate_metadata(protocol, source, check)
    return {
        "protocol": protocol,
        "source_result": source,
        "ledger_body": bodies[protocol["source_ledger"]],
    }


def ordered_chains(
    ledger_body: bytes, source: dict[str, Any]
) -> tuple[list[Array], list[NDArray[np.bool_]]]:
    """Keep the validated row stream intact, including the single undefined state."""
    covers = np.full((2, 16000, 20), np.nan, dtype=float)
    defined = np.zeros((2, 16000), dtype=bool)
    count = 0
    for index, row in enumerate(cover_rows(ledger_body, source)):
        chain, position = divmod(index, 16000)
        if row is not None:
            require(len(row) == 20, "Twenty cover components required")
            covers[chain, position] = row
            defined[chain, position] = True
        count += 1
    require(
        count == 32000 and [int(mask.sum()) for mask in defined] == [16000, 15999],
        "Ordered complete-chain population differs",
    )
    return list(covers), list(defined)


def source_scalars(source: dict[str, Any]) -> list[dict[str, float]]:
    """Read qualified empirical means and total mixture spreads without rerunning."""
    conditional = source["conditional_on_complete"]
    means = conditional["mean"]
    spreads = conditional["conditional_standard_deviation"]
    require(len(means) == len(spreads) == 20, "Qualified component axes differ")
    values = [
        {"mean": mean, "mixture_standard_deviation": sd}
        for mean, sd in zip(means, spreads, strict=True)
    ]
    contrasts = conditional["contrasts"]
    require(len(contrasts) == 30, "Qualified contrast population differs")
    for identity, row in zip(scalar_axes()[20:], contrasts, strict=True):
        require(
            all(
                identity[key] == row[key]
                for key in ("younger_window_id", "older_window_id", "taxon")
            ),
            "Qualified contrast identities differ",
        )
        values.append(
            {
                "mean": row["mean_difference"],
                "mixture_standard_deviation": row["standard_deviation"],
            }
        )
    require(
        all(
            math.isfinite(row["mean"])
            and math.isfinite(row["mixture_standard_deviation"])
            and row["mixture_standard_deviation"] > 0
            for row in values
        ),
        "Qualified mean/spread has an unsupported numerical domain",
    )
    return values
