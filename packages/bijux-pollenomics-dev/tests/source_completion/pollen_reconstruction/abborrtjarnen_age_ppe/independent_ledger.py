"""Observe every saved age identity, source membership and five-axis ledger row."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
import csv
from dataclasses import dataclass
from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .independent_moments import PopulationMoments, fixed_window, pooled_windows
from .independent_sources import BINS, TAXON_IDS, Membership, Sample, memberships

STATUS = {
    "defined": "defined",
    "refused_empty_window": "empty_native_window",
    "refused_missing_explicit_panel": "missing_explicit_five_taxon_member",
    "refused_zero_panel": "nonempty_zero_panel_mass",
}


def close(actual: Any, expected: Any, label: str) -> float:
    """Compare finite arrays at absolute tolerance and return the maximum gap."""
    left, right = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    if (
        left.shape != right.shape
        or not np.all(np.isfinite(left))
        or not np.all(np.isfinite(right))
    ):
        raise ValueError(f"Nonfinite or different {label} axes")
    gap = float(np.max(np.abs(left - right))) if left.size else 0.0
    if gap > 1e-12:
        raise ValueError(f"Independent {label} differs: {gap}")
    return gap


def check_support(row: dict[str, str], window: int, expected: Membership) -> None:
    """Check known subtotal separately from an undefined complete panel mass."""
    prefix = f"bin_{window}_"
    integer_fields = {
        "sample_count": len(expected.sample_ids),
        "reported_panel_subtotal": expected.panel_subtotal,
        "all_reported_pollen_nisp": expected.reported_nisp,
        "omitted_reported_pollen_nisp": expected.reported_nisp
        - expected.panel_subtotal,
    }
    if (
        row[prefix + "status"] != STATUS[expected.status]
        or json.loads(row[prefix + "sample_ids"]) != list(expected.sample_ids)
        or json.loads(row[prefix + "missing_members"])
        != {str(k): list(v) for k, v in expected.missing.items()}
        or any(row[prefix + key] != str(value) for key, value in integer_fields.items())
        or row[prefix + "panel_mass"]
        != ("" if expected.missing else str(expected.panel_subtotal))
    ):
        raise ValueError("Source membership, missing support or counted mass differs")


@dataclass
class Observation:
    """Collect ledger counts, support states and independent population moments."""

    rows: int
    complete: int
    support: dict[int, Counter[str]]
    chains: dict[int, PopulationMoments]
    moments: PopulationMoments
    maximum_cover_gap: float


def observe_ledger(
    repository: Path,
    protocol: dict[str, Any],
    result_path: Path,
    ledger: dict[str, Any],
    samples: dict[int, Sample],
    response: np.ndarray,
    ppe: np.ndarray,
    sd: np.ndarray,
    *,
    comparison: Callable[
        [dict[str, str], np.ndarray, tuple[int, ...], tuple[Membership, ...]], None
    ]
    | None = None,
    additional_fields: tuple[str, ...] = (),
) -> Observation:
    """Stream source ages and saved ledgers together, retaining all multiplicities."""
    path = Path(ledger["path"])
    path = path if path.is_absolute() else result_path.parent / path
    if (
        not path.resolve().is_relative_to(result_path.parent.resolve())
        or path.is_symlink()
    ):
        raise ValueError("Ledger escaped its owning result directory")
    body = path.read_bytes()
    if (
        len(body) != ledger["bytes"]
        or hashlib.sha256(body).hexdigest() != ledger["sha256"]
    ):
        raise ValueError("Saved draw ledger identity differs")
    core = json.loads((repository / protocol["core_input"]).read_text())
    labels = tuple(core["sample_ids"])
    if any(not label.startswith("neotoma:sample:") for label in labels):
        raise ValueError("Native age ID namespace differs")
    ids = tuple(int(label.removeprefix("neotoma:sample:")) for label in labels)
    if (
        len(ids) != 107
        or len(set(ids)) != 107
        or set(ids) != set(samples)
        or labels != tuple(f"neotoma:sample:{i}" for i in ids)
    ):
        raise ValueError("Native age/source census differs")
    close(core["depths"], [samples[i].depth for i in ids], "native sample depths")
    out = Observation(
        0, 0, {b: Counter() for b in BINS}, {}, PopulationMoments.empty(20, sd), 0.0
    )

    @lru_cache(maxsize=1024)
    def single(counts: tuple[int, ...]) -> np.ndarray:
        return fixed_window(counts, response, ppe)[0]

    @lru_cache(maxsize=1024)
    def joint(
        counts: tuple[tuple[int, ...], ...],
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        return pooled_windows(counts, response, ppe)

    with gzip.open(path, "rt", newline="") as stream:
        records = csv.DictReader(stream)
        expected_fields = {"seed", "native_row", "complete"}
        for b in BINS:
            expected_fields.update(
                f"bin_{b}_{field}"
                for field in (
                    "status",
                    "sample_ids",
                    "sample_count",
                    "reported_panel_subtotal",
                    "panel_mass",
                    "all_reported_pollen_nisp",
                    "omitted_reported_pollen_nisp",
                    "missing_members",
                )
            )
            expected_fields.update(f"cover_{b}_{taxon_id}" for taxon_id in TAXON_IDS)
        expected_fields.update(additional_fields)
        if (
            records.fieldnames is None
            or len(records.fieldnames) != len(expected_fields)
            or set(records.fieldnames) != expected_fields
        ):
            raise ValueError("Saved membership ledger axes differ")
        for chain in protocol["age_inputs"]:
            seed = chain["seed"]
            moments = PopulationMoments.empty(20, sd)
            out.chains[seed] = moments
            with gzip.open(repository / chain["path"], "rt", newline="") as ages_stream:
                ages_rows = csv.reader(ages_stream)
                if tuple(next(ages_rows)) != labels:
                    raise ValueError("Saved source age header differs")
                chain_rows = 0
                last_native = None
                for native_row, tokens in enumerate(
                    ages_rows, chain["first_native_row"]
                ):
                    last_native = native_row
                    ages = np.asarray(list(map(float, tokens)))
                    if ages.shape != (107,) or np.any(np.diff(ages) < 0):
                        raise ValueError("Saved age support is not finite and monotone")
                    row = next(records, None)
                    if row is None or (row["seed"], row["native_row"]) != (
                        str(seed),
                        str(native_row),
                    ):
                        raise ValueError("Saved chain/native-row identity differs")
                    windows = memberships(ages, ids, samples)
                    if comparison is not None:
                        comparison(row, ages, ids, windows)
                    complete = all(w.status == "defined" for w in windows)
                    if row["complete"] != str(int(complete)):
                        raise ValueError("Saved five-axis complete event differs")
                    for b, w in zip(BINS, windows, strict=True):
                        check_support(row, b, w)
                        out.support[b][STATUS[w.status]] += 1
                        cells = [row[f"cover_{b}_{taxon_id}"] for taxon_id in TAXON_IDS]
                        if w.status == "defined":
                            assert w.pooled is not None
                            out.maximum_cover_gap = max(
                                out.maximum_cover_gap,
                                close(cells, single(w.pooled), "saved per-bin cover"),
                            )
                        elif any(cells):
                            raise ValueError("Refused bin has invented cover values")
                    if complete:
                        pools = tuple(w.pooled for w in windows)
                        assert all(n is not None for n in pools)
                        values = joint(tuple(n for n in pools if n is not None))
                        out.moments.add(*values)
                        moments.add(*values)
                        out.complete += 1
                    out.rows += 1
                    chain_rows += 1
                if chain_rows != 16000 or last_native != chain["last_native_row"]:
                    raise ValueError("Saved age chain population differs")
            if moments.observations > chain_rows:
                raise ValueError("Conditional chain multiplicity exceeds source rows")
        if (
            next(records, None) is not None
            or out.rows != ledger["rows"]
            or out.rows != 32000
        ):
            raise ValueError("Saved draw ledger has a different complete population")
    return out
