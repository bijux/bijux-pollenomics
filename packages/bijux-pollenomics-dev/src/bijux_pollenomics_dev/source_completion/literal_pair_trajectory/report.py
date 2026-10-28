"""Consume native source aliquots under a prespecified counting-only scenario."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_lra import fixed_two_taxon_counting_interval

from .arithmetic import family_confidence, transition, weighted_bin
from .source import DATASETS, SOURCE, SOURCE_SHA256, TAXA, read_population


def produce(repository: Path, output: Path) -> None:
    """Write detailed private custody and aggregate conditional counting results."""
    output = require_absent_artifact_output(repository, output)
    rows = read_population(repository)
    population = len(rows)
    confidence = family_confidence(population)
    output.mkdir()
    journal = output / "interval-requests.jsonl"
    for row in rows:
        if row["admitted"]:
            request = {
                "source_pointer": row["source_pointer"],
                "counts": row["counts"],
                "confidence_level": confidence,
                "family_native_sample_population": population,
            }
            with journal.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps({"request": request}, allow_nan=False) + "\n")
                stream.flush()
            row["interval"] = asdict(
                fixed_two_taxon_counting_interval(
                    row["counts"],
                    [1, 1],
                    [1, 1],
                    taxon_measured=[True, True],
                    confidence_level=confidence,
                )
            )
            with journal.open("a", encoding="utf-8") as stream:
                stream.write(
                    json.dumps(
                        {
                            "source_pointer": row["source_pointer"],
                            "result": row["interval"],
                        },
                        allow_nan=False,
                    )
                    + "\n"
                )
                stream.flush()
    bins: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for dataset in DATASETS:
        native = [row for row in rows if row["dataset_id"] == dataset]
        for identifier in range(-1, 12):
            source = [row for row in native if row["bin_id"] == identifier]
            admitted = [row for row in source if row["admitted"]]
            bins.append(
                {
                    "dataset_id": dataset,
                    "bin_id": identifier,
                    "native_sample_count": len(source),
                    "refused_sample_count": len(source) - len(admitted),
                    **weighted_bin(admitted),
                }
            )
        coverage.append(
            {
                "dataset_id": dataset,
                "all_native_samples": len(native),
                "admitted_samples": sum(row["admitted"] for row in native),
                "unresolved_age_samples": sum(row["bin_id"] is None for row in native),
                "outside_declared_bins": sum(
                    row["bin_id"] is not None and row["bin_id"] not in range(-1, 12)
                    for row in native
                ),
                "refusal_reason_occurrences": dict(
                    sorted(
                        Counter(
                            reason
                            for row in native
                            for reason in row["refusal_reasons"]
                        ).items()
                    )
                ),
                "observed_complete_pair_count_mass": sum(
                    row["pair_total"] for row in native if row["pair_total"] is not None
                ),
                "admitted_pair_count_mass": sum(
                    row["pair_total"] for row in native if row["admitted"]
                ),
            }
        )
        selected = [row for row in bins if row["dataset_id"] == dataset]
        for before, after in zip(selected, selected[1:], strict=False):
            transitions.append(
                {
                    "dataset_id": dataset,
                    "before_bin": before["bin_id"],
                    "after_bin": after["bin_id"],
                    **transition(before, after),
                }
            )
    joint = []
    for identifier in range(-1, 11):
        compared = [row for row in transitions if row["before_bin"] == identifier]
        directions = [row["direction"] for row in compared]
        supported = all(
            direction in ("positive", "negative") for direction in directions
        )
        joint.append(
            {
                "before_bin": identifier,
                "after_bin": identifier + 1,
                "directions": directions,
                "relation": ("agreement" if len(set(directions)) == 1 else "opposition")
                if supported
                else "unsupported",
            }
        )
    exact_error = population * (1 - Fraction.from_float(confidence))
    report = {
        "schema_version": "literal-pair-count-trajectory.v1",
        "source": {"path": SOURCE, "sha256": SOURCE_SHA256, "datasets": DATASETS},
        "taxa": TAXA,
        "family_native_sample_population": population,
        "family_exact_max_error": "1/20",
        "binary64_confidence": confidence,
        "actual_union_bound_fraction": str(exact_error),
        "coverage": coverage,
        "bins": bins,
        "transitions": transitions,
        "joint_lake_relations": joint,
        "scenario": {
            "fixed_deposition": [1, 1],
            "fixed_ppe": [1, 1],
            "weights": "original aliquot pair-count mass",
            "sampling_model": "conditional per-aliquot two-taxon binomial; no homogeneous pooled probability assumed",
            "selection_limit": "Simultaneous intervals under declared binomial model; no nominal coverage conditional on data-dependent admission, random observed totals or source representativeness is established.",
            "comparison_limit": "Different panel, support and uncertainty target from the original48all-NISP/closed16threshold classes; no recertification.",
        },
        "admissions": dict.fromkeys(
            [
                "ecological_accuracy",
                "total_vegetation",
                "physical_LRA",
                "chronology_uncertainty",
                "independent_validation",
                "rights",
                "release",
            ],
            False,
        ),
    }
    private = output / "aliquot-intervals.json"
    private.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )
    report["private_aliquot_witness_sha256"] = hashlib.sha256(
        private.read_bytes()
    ).hexdigest()
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    )


def main() -> None:
    """Accept an explicit owned input tree and a new artifact destination."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    produce(args.repository, args.output)


if __name__ == "__main__":
    main()
