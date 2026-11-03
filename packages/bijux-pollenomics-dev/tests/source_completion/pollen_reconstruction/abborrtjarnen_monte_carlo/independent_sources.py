"""Reuse qualified source checks while independently retaining the native clock."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import gzip
import io
import json
from pathlib import Path
from typing import Any

from ..abborrtjarnen_age_ppe_dependence.independent_sources import (
    Inputs,
)
from ..abborrtjarnen_age_ppe_dependence.independent_sources import (
    read_inputs as qualified_inputs,
)
from ..abborrtjarnen_age_ppe_dependence.independent_sources import (
    read_ledger as qualify_ledger,
)
from .independent_sampling import BINS, TAXON_IDS, Rows

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/monte-carlo/protocol.json"
)
DESIGN: dict[str, Any] = {
    "batch_size": 128,
    "batches_per_chain": 125,
    "rows_per_chain": 16000,
    "seeds": [314159, 271828],
    "native_first_row": 3502,
    "native_last_row": 19501,
}


@dataclass(frozen=True)
class Sources:
    """Precision protocol, qualified source inputs, and ordered native chains."""

    protocol: dict[str, Any]
    protocol_body: bytes
    qualified: Inputs
    chains: tuple[Rows, Rows]


def ordered_rows(
    body: bytes, *, rows_per_chain: int = 16000, first: int = 3502
) -> tuple[Rows, Rows]:
    """Decode masked rows separately from the complete-case qualification pass."""
    seeds = (314159, 271828)
    expected = [
        (seed, row) for seed in seeds for row in range(first, first + rows_per_chain)
    ]
    result: list[list[tuple[float, ...] | None]] = [[], []]
    reader = csv.DictReader(io.StringIO(gzip.decompress(body).decode()))
    count = 0
    for count, row in enumerate(reader, 1):
        if (
            count > len(expected)
            or (int(row["seed"]), int(row["native_row"])) != expected[count - 1]
        ):
            raise ValueError("Ordered native seed/row identity differs")
        if row["complete"] not in ("0", "1"):
            raise ValueError("Complete indicator must remain binary")
        value = (
            None
            if row["complete"] == "0"
            else tuple(
                float(row[f"cover_{b}_{taxon}"]) for b in BINS for taxon in TAXON_IDS
            )
        )
        result[(count - 1) // rows_per_chain].append(value)
    if count != len(expected):
        raise ValueError("Incomplete native clock cannot be repartitioned")
    return tuple(result[0]), tuple(result[1])


def read_sources(repository: Path) -> Sources:
    """Check precision input pins and retain each native chain position."""
    body = (repository / PROTOCOL).read_bytes()
    protocol = json.loads(body)
    qualified = qualified_inputs(repository)
    if protocol["batch_design"] != DESIGN or any(
        protocol[key] != qualified.protocol[key]
        for key in (
            "repository_inputs",
            "source_result",
            "source_ledger",
            "source_verification",
            "producer_source_commit",
            "observer_source_commit",
            "taxon_axis",
            "native_taxon_ids",
            "window_ids",
        )
    ):
        raise ValueError("Prospective Monte Carlo input pins or design differ")
    # Existing independent validation owns all source members and support reasons.
    qualify_ledger(qualified.ledger, qualified.reference)
    chains = ordered_rows(qualified.ledger)
    if [sum(row is not None for row in chain) for chain in chains] != [16000, 15999]:
        raise ValueError("Native complete indicators differ across chains")
    return Sources(protocol, body, qualified, chains)
