"""Compare native and source-supported events on the same saved age identities."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
import csv
from functools import lru_cache
import gzip
import json
from pathlib import Path
from typing import Any

import numpy as np

from .independent_ledger import STATUS, Observation, check_support, close
from .independent_moments import PopulationMoments, pooled_windows
from .independent_sources import BINS, TAXON_IDS, Membership, Sample, memberships

ADDITIONAL_FIELDS = (
    "native_complete",
    *(
        f"bin_{b}_{key}"
        for b in BINS
        for key in ("native_missing_members", "source_recorded_zero_sample_ids")
    ),
)


class ProfileComparison:
    """Reconstruct the old event rather than trusting a producer support bridge."""

    def __init__(
        self,
        native: dict[int, Sample],
        records: Iterator[dict[str, str]],
        response: np.ndarray,
        ppe: np.ndarray,
        sd: np.ndarray,
    ) -> None:
        """Initialize paired-ledger observation with cached joint-window moments."""
        self.native = native
        self.records = records
        self.sd = sd
        self.transitions: Counter[str] = Counter()
        self.window_transitions: dict[int, Counter[str]] = {b: Counter() for b in BINS}
        self.observed = Observation(
            0, 0, {b: Counter() for b in BINS}, {}, PopulationMoments.empty(20, sd), 0.0
        )
        self.maximum_common_cover_gap = 0.0

        @lru_cache(maxsize=1024)
        def joint(
            counts: tuple[tuple[int, ...], ...],
        ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
            return pooled_windows(counts, response, ppe)

        self.joint = joint

    def observe(
        self,
        row: dict[str, str],
        ages: np.ndarray,
        ids: tuple[int, ...],
        active: tuple[Membership, ...],
    ) -> None:
        """Track ledger identities, support transitions and shared moments."""
        old = next(self.records, None)
        if old is None or (old["seed"], old["native_row"]) != (
            row["seed"],
            row["native_row"],
        ):
            raise ValueError("Old/source ledger age identities differ")
        native = memberships(ages, ids, self.native)
        native_complete = all(w.status == "defined" for w in native)
        source_complete = all(w.status == "defined" for w in active)
        if row["native_complete"] != str(int(native_complete)):
            raise ValueError("Saved native-complete bridge differs")
        if old["complete"] != str(int(native_complete)):
            raise ValueError("Old ledger native complete event differs")
        if native_complete and not source_complete:
            raise ValueError("Native-complete age row became source undefined")
        self.transitions[f"{int(native_complete)}->{int(source_complete)}"] += 1
        seed = int(row["seed"])
        if seed not in self.observed.chains:
            self.observed.chains[seed] = PopulationMoments.empty(20, self.sd)
        for b, strict, source in zip(BINS, native, active, strict=True):
            check_support(old, b, strict)
            if json.loads(row[f"bin_{b}_native_missing_members"]) != {
                str(k): list(v) for k, v in strict.missing.items()
            } or json.loads(row[f"bin_{b}_source_recorded_zero_sample_ids"]) != [
                i for i in strict.sample_ids if i in strict.missing
            ]:
                raise ValueError(
                    "Native missing or original-zero support bridge differs"
                )
            if (strict.sample_ids, strict.panel_subtotal, strict.reported_nisp) != (
                source.sample_ids,
                source.panel_subtotal,
                source.reported_nisp,
            ):
                raise ValueError("Source profile changed membership or measured counts")
            self.observed.support[b][STATUS[strict.status]] += 1
            self.window_transitions[b][
                f"{STATUS[strict.status]}->{STATUS[source.status]}"
            ] += 1
            old_cells = [old[f"cover_{b}_{taxon_id}"] for taxon_id in TAXON_IDS]
            if strict.status == "defined":
                if source.status != "defined" or strict.pooled != source.pooled:
                    raise ValueError(
                        "Native-defined panel was changed by source support"
                    )
                new_cells = [row[f"cover_{b}_{taxon_id}"] for taxon_id in TAXON_IDS]
                self.maximum_common_cover_gap = max(
                    self.maximum_common_cover_gap,
                    close(old_cells, new_cells, "native-defined source cover"),
                )
            elif any(old_cells):
                raise ValueError("Old undefined bin contains invented cover")
        if native_complete:
            counts = tuple(w.pooled for w in active)
            if any(n is None for n in counts):
                raise ValueError("Common event lacks an analytical pool")
            values = self.joint(tuple(n for n in counts if n is not None))
            self.observed.moments.add(*values)
            self.observed.chains[seed].add(*values)
            self.observed.complete += 1
        self.observed.rows += 1

    def finish(self, expected_rows: int) -> None:
        """Require both ledgers to end at the expected row count."""
        if next(self.records, None) is not None or self.observed.rows != expected_rows:
            raise ValueError("Old/source ledger populations differ")


def check_native_ledger_binding(
    reference: dict[str, Any], route: str, pin: dict[str, Any]
) -> None:
    """Use the governed account's explicit scientific-output identity surface."""
    entries = [
        row for row in reference["scientific_outputs"] if row.get("path") == route
    ]
    expected = {"path": route, "bytes": pin["bytes"], "sha256": pin["sha256"]}
    if len(entries) != 1 or entries[0] != expected:
        raise ValueError("Old native reference and ledger identity differ")


def observe_source_ledger(
    repository: Path,
    profile: dict[str, Any],
    protocol: dict[str, Any],
    result_path: Path,
    result: dict[str, Any],
    native: dict[int, Sample],
    analytical: dict[int, Sample],
    response: np.ndarray,
    ppe: np.ndarray,
    sd: np.ndarray,
) -> tuple[Observation, dict[str, Any]]:
    """Check the saved source result and immutable native reference in one pass."""
    from .independent_ledger import observe_ledger
    from .independent_profile_moments import check_profile_comparison

    reference_path, ledger_path = (
        profile["native_reference_result"],
        profile["native_reference_ledger"],
    )
    if any(
        p not in profile["repository_inputs"] for p in (reference_path, ledger_path)
    ):
        raise ValueError("Native comparison escaped its pinned scientific inputs")
    old = json.loads((repository / reference_path).read_bytes())
    pin = profile["repository_inputs"][ledger_path]
    check_native_ledger_binding(old, ledger_path, pin)
    with gzip.open(repository / ledger_path, "rt", newline="") as stream:
        comparison = ProfileComparison(
            native, csv.DictReader(stream), response, ppe, sd
        )
        observed = observe_ledger(
            repository,
            protocol,
            result_path,
            result["draw_ledger"],
            analytical,
            response,
            ppe,
            sd,
            comparison=comparison.observe,
            additional_fields=ADDITIONAL_FIELDS,
        )
        comparison.finish(observed.rows)
    checked = check_profile_comparison(
        result["comparison_to_native_explicit"],
        old,
        observed,
        comparison,
        reference_path,
    )
    return observed, {
        "count_profile": "pangaea_recorded_zeros_local_nc",
        "native_complete_rows": comparison.observed.complete,
        "original_count_slots_checked": 535,
        "native_reported_count_pairs_checked": 527,
        "source_zero_slots_checked": 8,
        **checked,
    }
