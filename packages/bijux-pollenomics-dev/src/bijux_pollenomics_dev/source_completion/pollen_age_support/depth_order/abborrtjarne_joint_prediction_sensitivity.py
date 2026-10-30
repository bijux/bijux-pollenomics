"""Joint ABBO fixed-bin predictor sensitivity on one conditional chronology."""

from __future__ import annotations

import argparse
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .. import abborrtjarne_membership as ledger
from ..joint_membership import AgeBin
from . import abborrtjarne_prediction_sensitivity as source
from . import joint_allocations, joint_prediction_sensitivity
from .joint_prediction_sensitivity import JointScoreWitness


def derive(support: bytes, raw: bytes, frozen: bytes, config: bytes) -> dict[str, Any]:
    """Reuse literal source admission and vary only shared target age membership."""
    rows, samples = source._support(support)
    counts = source._native_counts(source._json(raw), rows)
    predictions, fits = source._predictions(source._json(frozen), source._json(config))
    bins = tuple(
        AgeBin(str(b), Decimal(b * 500), Decimal((b + 1) * 500)) for b in source.BINS
    )
    result = joint_prediction_sensitivity.joint_prediction_sensitivity(
        samples,
        bins,
        counts,
        {str(b): predictions[b] for b in source.BINS},
        core_id=source.CORE,
    )
    indices = {row.sample.sample_id: i for i, row in enumerate(samples)}
    retained: dict[str, dict[str, Any]] = {}

    def endpoint(w: JointScoreWitness | None) -> dict[str, Any] | None:
        if w is None:
            return None
        selected_bins = []
        name_parts = []
        for b, selected, pooled in zip(
            source.BINS, w.selected_sample_ids, w.pooled_taxon_counts, strict=True
        ):
            positions = [indices[s] for s in selected]
            first, stop = min(positions), max(positions) + 1
            if positions != list(range(first, stop)) or not sum(pooled):
                raise ValueError(
                    "Complete positive-count contiguous bin selections required"
                )
            name_parts.append(f"{b}:samples[{first}:{stop}]")
            selected_bins.append(
                {
                    "bin_id": b,
                    "sample_start_index_inclusive": first,
                    "sample_stop_index_exclusive": stop,
                    "pooled_taxon_counts": list(pooled),
                    "closed_count_denominator": sum(pooled),
                }
            )
        name = ";".join(name_parts)
        scores = {}
        for method in source.METHODS:
            score = sum(
                (
                    sum(
                        (
                            abs(Fraction.from_float(p) - Fraction(n, sum(pooled)))
                            for p, n in zip(predictions[b][method], pooled, strict=True)
                        ),
                        Fraction(),
                    )
                    / len(source.TAXA)
                    for b, pooled in zip(
                        source.BINS, w.pooled_taxon_counts, strict=True
                    )
                ),
                Fraction(),
            ) / len(source.BINS)
            scores[method] = source._fraction(score)
        allocation = {
            "bins": selected_bins,
            "age_order": source._order(w.age_order, samples),
            "method_equal_bin_mae": scores,
        }
        if name in retained and retained[name] != allocation:
            raise ValueError(
                "The same joint selection has inconsistent complete witnesses"
            )
        retained[name] = allocation
        return {"value": source._fraction(w.value), "allocation": name}

    methods = [
        {"method": b.method, "lower": endpoint(b.lower), "upper": endpoint(b.upper)}
        for b in result.method_bounds
    ]
    pairs = [
        {
            "left_method": b.left_method,
            "right_method": b.right_method,
            "difference": "left equal-bin MAE minus right equal-bin MAE on one shared chronology",
            "lower": endpoint(b.lower),
            "upper": endpoint(b.upper),
            "negative_attainable": b.negative_attainable,
            "zero_attainable": b.zero_attainable,
            "positive_attainable": b.positive_attainable,
            "ranking_reversal": b.ranking_reversal,
        }
        for b in result.pairwise_bounds
    ]
    winners = [
        {"methods": list(w.methods), "minimum_equal_bin_mae": endpoint(w.witness)}
        for w in result.winner_sets
    ]
    return {
        "schema_version": "abbo-joint-ordered-frozen-prediction-sensitivity.v1",
        "question": "Can one supported monotone ABBO chronology change the equal-bin MAE ranking of the four already-frozen predictors across bins 3/4/5/9?",
        "target_dataset_id": "19913",
        "target_site_id": "13338",
        "taxon_axis": list(source.TAXA),
        "sample_order": [
            {
                "sample_id": row.sample.sample_id,
                "depth_cm": str(row.depth),
                "younger_native_age_inclusive": str(row.sample.younger_cal_bp),
                "older_native_age_inclusive": str(row.sample.older_cal_bp),
                "closed16_count": row.sample.numerator_count,
                "all_native_nisp_count": row.sample.denominator_count,
            }
            for row in samples
        ],
        "native_age_order": source._order(
            result.graph.single_bin_assessments[0].native_age_order, samples
        ),
        "frozen_fit_identities": fits,
        "bins": [
            {
                "bin_id": int(bin_.bin_id),
                "younger_cal_bp_inclusive": str(bin_.younger_cal_bp),
                "older_cal_bp_exclusive": str(bin_.older_cal_bp_exclusive),
                "depth_group_count": assessment.depth_group_count,
                "candidate_block_count": assessment.candidate_block_count,
                "tested_block_count": assessment.tested_block_count,
                "feasible_nonempty_block_count": len(layer),
                "zero_closed_count_blocks": [
                    {
                        "depth_group_start_inclusive": block.start,
                        "depth_group_stop_exclusive": block.stop,
                    }
                    for block, pooled in zip(layer, totals, strict=True)
                    if not sum(pooled)
                ],
                "empty_selection_age_order": source._order(
                    assessment.empty_selection_age_order, samples
                ),
            }
            for bin_, assessment, layer, totals in zip(
                bins,
                result.graph.single_bin_assessments,
                result.graph.layers,
                result.pooled_counts,
                strict=True,
            )
        ],
        "search": {
            "cartesian_nonempty_block_tuple_count": math.prod(
                len(layer) for layer in result.graph.layers
            ),
            "compatible_edges_between_consecutive_bins": [
                sum(map(len, layer)) for layer in result.graph.successors
            ],
            "joint_feasible_nonempty_membership_count": result.joint_feasible_count,
            "scored_positive_closed_count_membership_count": result.scored_allocation_count,
            "zero_closed_count_excluded_membership_count": result.zero_closed_count_allocation_count,
            "denominator": "Distinct finite joint bin-membership configurations, not chronology draws, probabilities or independent observations. Every scored configuration contains all four fixed bins with positive closed count.",
        },
        "refusal": result.refusal,
        "method_equal_bin_mae_bounds": methods,
        "paired_equal_bin_mae_difference_bounds": pairs,
        "possible_winners": list(result.possible_winners),
        "winner_set_changes": result.winner_set_changes,
        "unique_winner_changes": result.unique_winner_changes,
        "winner_sets": winners,
        "attaining_allocations": retained,
        "zero_semantics": source.ZERO_RULE,
        "quantity": "Equal arithmetic mean over exactly four fixed bins of mean absolute fraction error over 16 taxa. Stored binary64 predictions and literal integer count fractions are exact; prediction closure at 1e-9 is admission only, without reclosure. All method/pair/winner comparisons share one complete monotone 107-sample age vector; exact decisions have no tolerance.",
        "assumption": "A single nondecreasing native age function of depth, with equal depths sharing one age, constrained by the retained closed LegacyAge marginal intervals. Half-open bins remain disjoint; all intervening gap, prefix and suffix samples remain supported.",
        "limits": [
            "Exploratory conditional sensitivity on one previously exposed Swedish target and four previously fixed bins; neither whole-study accuracy nor a new independent transfer/vegetation result.",
            "All-bin positive-count support is required. Empty bins and zero-closed-count allocations have no equal-bin score; no missing bin is dropped, imputed or scored as zero.",
            "Finite membership counts have no probability interpretation. Marginal age supports plus a declared order assumption are not a calibrated joint chronology posterior, simultaneous 95% interval or source-confirmed sediment history.",
            "Only target age allocation varies. Predictions, training identities, count/taxon rules and source bytes remain unchanged; no fitting, renormalization, pseudocount or new parameter selection.",
            "No newly qualified reference epoch, physical core, source permission, human scientific approval, independent vegetation accuracy or release qualification follows.",
        ],
    }


def _revision(repository: Path) -> str:
    revision = source._revision(repository)
    paths = [
        Path(m.__file__ or "")
        for m in (joint_allocations, joint_prediction_sensitivity)
    ] + [Path(__file__)]
    if any(
        p.resolve(strict=True) != p or not p.is_relative_to(repository / "packages")
        for p in paths
    ):
        raise ValueError(
            "Joint scientific modules must load from the canonical repository"
        )
    relative = [str(p.relative_to(repository)) for p in paths]
    command = ["git", "-C", str(repository)]
    subprocess.run(
        [*command, "ls-files", "--error-unmatch", "--", *relative],
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        [*command, "diff", "--exit-code", revision, "--", *relative],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return revision


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Read shared inputs once and retain one bounded result at committed source."""
    repository = repository.absolute()
    if repository.resolve(strict=True) != repository:
        raise ValueError("A physical canonical repository is required")
    destination = require_absent_artifact_output(repository, output)
    revision = _revision(repository)
    buffers, identities = {}, {}
    for relative, expected in source.INPUTS.items():
        path = repository / relative
        if (
            not path.is_file()
            or path.resolve(strict=True) != path
            or path.stat().st_size > 32 * 1024**2
        ):
            raise ValueError("Bounded physical shared scientific input required")
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError(f"Scientific input identity differs: {relative}")
        buffers[relative] = body
        identities[str(relative)] = {"sha256": expected, "bytes": len(body)}
    result = derive(
        buffers[ledger.SUPPORT],
        buffers[source.RAW],
        buffers[source.PREDICTIONS],
        buffers[ledger.CONFIG],
    )
    result.update(
        source_git_revision=revision, command=sys.orig_argv, input_identities=identities
    )
    body = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    if len(body) > 1024**2:
        raise ValueError("Joint scientific report exceeds 1 MiB")
    if _revision(repository) != revision:
        raise ValueError("Consumed scientific source changed during execution")
    with destination.open("xb") as stream:
        stream.write(body)
    return result


def main(argv: list[str] | None = None) -> int:
    """Calculate one fixed-bin conditional sensitivity without refitting."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
