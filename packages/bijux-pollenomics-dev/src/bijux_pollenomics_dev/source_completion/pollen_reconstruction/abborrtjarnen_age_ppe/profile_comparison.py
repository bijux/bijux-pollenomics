"""Compare source-supported moments with the same frozen native-complete owners."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
import csv
import gzip
import json
from pathlib import Path
from typing import Any

import numpy as np

from ..abborrtjarnen_ppe_dependence.sources import WINDOWS, require
from . import moments


class NativeComparison:
    """Compare identical saved-age owners before comparing different C populations."""

    def __init__(
        self, case: dict[str, Any], covariance: np.ndarray, rows: csv.DictReader[str]
    ) -> None:
        """Load the native reference and initialize shared-population accumulators."""
        protocol = case["count_profile_protocol"]
        self.reference_path = protocol["native_reference_result"]
        self.reference = json.loads(
            (Path(case["repository"]) / self.reference_path).read_bytes()
        )
        self.rows = rows
        self.moments = moments.PopulationMoments(covariance)
        self.transitions: Counter[str] = Counter()
        self.window_transitions: dict[str, Counter[str]] = {
            str(b): Counter() for b in WINDOWS
        }
        self.checked = 0

    def observe(
        self,
        seed: int,
        native_row: int,
        native: list[dict[str, Any]],
        source: list[dict[str, Any]],
        joint: tuple[np.ndarray, np.ndarray, np.ndarray] | None,
    ) -> int:
        """Check one native ledger row and accumulate shared-population moments."""
        prior = next(self.rows, None)
        require(prior is not None, "Frozen native ledger is truncated")
        assert prior is not None
        require(
            prior["seed"] == str(seed) and prior["native_row"] == str(native_row),
            "Frozen native ledger row identity differs",
        )
        for b, old, new in zip(WINDOWS, native, source, strict=True):
            for key, value in old.items():
                expected = (
                    json.dumps(value, separators=(",", ":"), sort_keys=True)
                    if key in {"sample_ids", "missing_members"}
                    else ""
                    if value is None
                    else str(value)
                )
                require(
                    prior[f"bin_{b}_{key}"] == expected,
                    "Independently reconstructed native membership differs from frozen ledger",
                )
            self.window_transitions[str(b)][old["status"] + "->" + new["status"]] += 1
        complete = int(all(s["status"] == "defined" for s in native))
        require(
            prior["complete"] == str(complete), "Original complete-event mask differs"
        )
        require(
            not complete or joint is not None,
            "Recorded-zero profile lost a native-complete row",
        )
        self.transitions[f"native_{complete}->source_{int(joint is not None)}"] += 1
        self.checked += 1
        if complete:
            assert joint is not None
            self.moments.add(*joint)
        return complete

    def result(self, source: dict[str, Any], requested: int) -> dict[str, Any]:
        """Compare conditional profile moments and report native-population checks."""
        native = self.reference["conditional_on_complete"]
        common = self.moments.result()
        require(
            self.checked == requested == self.reference["requested_draws"]
            and self.moments.n == self.reference["complete_draws"],
            "Native reference population differs",
        )
        keys = (
            "mean",
            "mean_ppe_gradient",
            "covariance_components",
            "conditional_standard_deviation",
        )
        gap = 0.0
        for key in keys:
            if native[key] is None:
                require(
                    common[key] is None, "Native empty population has invented moments"
                )
                continue
            pairs = (
                ((common[key][n], native[key][n]) for n in moments.COMPONENTS)
                if key == "covariance_components"
                else [(common[key], native[key])]
            )
            for actual, expected in pairs:
                gap = max(
                    gap,
                    float(np.max(np.abs(np.asarray(actual) - np.asarray(expected)))),
                )
        for actual, expected in zip(
            common["contrasts"], native["contrasts"], strict=True
        ):
            require(
                all(
                    actual[k] == expected[k]
                    for k in ("younger_window_id", "older_window_id", "taxon", "status")
                ),
                "Native contrast identities differ",
            )
            if native["draws"]:
                gap = max(
                    gap,
                    abs(actual["mean_difference"] - expected["mean_difference"]),
                    abs(actual["standard_deviation"] - expected["standard_deviation"]),
                    *(
                        abs(
                            actual["variance_components"][k]
                            - expected["variance_components"][k]
                        )
                        for k in moments.COMPONENTS
                    ),
                )
        require(gap <= 1e-12, "Common native-complete population moments changed")
        defined = bool(source["draws"] and native["draws"])
        return {
            "native_reference_result": self.reference_path,
            "rows_checked": self.checked,
            "support_transition_counts": dict(self.transitions),
            "window_status_transition_counts": {
                b: dict(n) for b, n in self.window_transitions.items()
            },
            "native_complete_draws": native["draws"],
            "source_complete_draws": source["draws"],
            "complete_probability_difference": (source["draws"] - native["draws"])
            / requested,
            "common_native_population_check": {
                "draws": self.moments.n,
                "maximum_moment_gap": gap,
                "contrasts_checked": 30,
                "passed": True,
            },
            "comparison_population": "Source-complete C_source versus native-complete C_native; conditional populations differ, not a count or law perturbation within C_native.",
            "conditional_mean_difference": (
                np.asarray(source["mean"]) - np.asarray(native["mean"])
            ).tolist()
            if defined
            else None,
            "conditional_covariance_component_differences": {
                n: (
                    np.asarray(source["covariance_components"][n])
                    - np.asarray(native["covariance_components"][n])
                ).tolist()
                for n in moments.COMPONENTS
            }
            if defined
            else None,
            "conditional_contrast_differences": [
                {
                    "younger_window_id": a["younger_window_id"],
                    "older_window_id": a["older_window_id"],
                    "taxon": a["taxon"],
                    "mean_difference_change": a["mean_difference"]
                    - b["mean_difference"],
                    "variance_component_changes": {
                        n: a["variance_components"][n] - b["variance_components"][n]
                        for n in moments.COMPONENTS
                    },
                    "standard_deviation_change": a["standard_deviation"]
                    - b["standard_deviation"],
                }
                for a, b in zip(source["contrasts"], native["contrasts"], strict=True)
            ]
            if defined
            else None,
        }


@contextmanager
def native_reference(
    case: dict[str, Any], covariance: np.ndarray
) -> Iterator[NativeComparison | None]:
    """Close the old ledger and refuse extra rows on a successful comparison."""
    if "count_profile_protocol" not in case:
        yield None
        return
    protocol = case["count_profile_protocol"]
    with gzip.open(
        Path(case["repository"]) / protocol["native_reference_ledger"], "rt", newline=""
    ) as stream:
        comparison = NativeComparison(case, covariance, csv.DictReader(stream))
        yield comparison
        require(
            next(comparison.rows, None) is None, "Frozen native ledger has extra rows"
        )
