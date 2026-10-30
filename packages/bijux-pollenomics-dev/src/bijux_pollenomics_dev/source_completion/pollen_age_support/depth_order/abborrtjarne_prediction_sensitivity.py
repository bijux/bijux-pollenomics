"""Frozen ABBO predictor rankings conditional on ordered native age supports."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import csv
from decimal import Decimal
from fractions import Fraction
import hashlib
import io
import json
import math
from pathlib import Path
import subprocess
import sys
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_static_basin import (
    sources as native,
)

from .. import abborrtjarne_membership as ledger
from .. import joint_membership
from ..joint_membership import AgeBin, MarginalAgeCountSample
from . import count_fraction, domains, extrema, prediction_sensitivity
from .domains import AgeOrderAssessment
from .extrema import DepthCountSample
from .prediction_sensitivity import ScoreWitness, ordered_prediction_sensitivity

CORE = "neotoma-dataset:19913"
FAMILY = Path("docs/report/pollen-reconstruction/age-interval-sensitivity")
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json")
PREDICTIONS = FAMILY / "predictions/site-13338.json"
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared", "clr_rbf_ridge")
BINS = (3, 4, 5, 9)
TAXA = (
    "Alnus",
    "Amaranthaceae",
    "Betula",
    "Cichorioideae",
    "Cyperaceae",
    "Filipendula",
    "Frangula alnus",
    "Nuphar",
    "Plantago lanceolata",
    "Plantago media",
    "Populus",
    "Quercus",
    "Rosaceae undiff.",
    "Salix",
    "Thalictrum",
    "Ulmus",
)
INPUTS = {
    RAW: ledger.SOURCE_INPUT_SHA256[RAW],
    ledger.SUPPORT: ledger.SOURCE_INPUT_SHA256[ledger.SUPPORT],
    ledger.CONFIG: ledger.SOURCE_INPUT_SHA256[ledger.CONFIG],
    # Existing prediction identity frozen before target scoring in comparison.json.
    PREDICTIONS: "46235c8db2bfe6b0fefc3932a468556a978e28209267bb11f0276a9ff1deecd3",
}
ZERO_RULE = (
    "Retains the original Neotoma count-matrix structural-zero rule: an unlisted "
    "cell on the declared exact-name closed 16-taxon axis is zero. The maintained "
    "native reader retains finite nonnegative integer-valued pollen/NISP measurements, "
    "including integral floats, with its exact-name aggregation and row filters. "
    "Literal null, missing measurement values, booleans and fractional counts in "
    "selected pollen rows are refused, as are invalid units and duplicate native "
    "taxon-ID/name pairs. No taxon crosswalk, renormalization or new pseudocount is applied."
)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate source JSON field")
        result[key] = value
    return result


def _json(body: bytes) -> dict[str, Any]:
    value = json.loads(body, object_pairs_hook=_pairs)
    if not isinstance(value, dict):
        raise ValueError("Source JSON object required")
    return value


def _support(body: bytes) -> tuple[list[dict[str, str]], tuple[DepthCountSample, ...]]:
    reader = csv.DictReader(io.StringIO(body.decode()))
    if tuple(reader.fieldnames or ()) != ledger.SUPPORT_FIELDS:
        raise ValueError("ABBO source ledger columns differ")
    rows = list(reader)
    if len(rows) != 107 or len({row["sample_id"] for row in rows}) != 107:
        raise ValueError("Exactly 107 distinct ABBO source samples required")
    if any(
        set(row) != set(ledger.SUPPORT_FIELDS)
        or any(not isinstance(v, str) for v in row.values())
        for row in rows
    ):
        raise ValueError("ABBO source ledger row width differs")
    samples = tuple(
        DepthCountSample(
            MarginalAgeCountSample(
                row["sample_id"],
                Decimal(row["legacyage_min_cal_bp"]),
                Decimal(row["legacyage_max_cal_bp"]),
                ledger._count(row["closed_nisp_count"]),
                ledger._count(row["all_nisp_count"], positive=True),
            ),
            Decimal(row["depth_cm"]),
        )
        for row in rows
    )
    return rows, tuple(sorted(samples, key=lambda s: (s.depth, s.sample.sample_id)))


def _native_counts(
    payload: dict[str, Any], rows: Sequence[Mapping[str, str]]
) -> dict[str, tuple[int, ...]]:
    sites = [
        row["site"]
        for row in payload["rows"]
        if str(row["site"].get("dataset", {}).get("datasetid")) == "19913"
    ]
    if len(sites) != 1:
        raise ValueError("Exactly one native ABBO dataset required")
    site = sites[0]
    source = site["dataset"]
    nested = site["collectionunit"]["dataset"]
    if (
        str(site["siteid"]) != "13338"
        or str(nested["datasetid"]) != "19913"
        or source.get("datasettype") != "pollen"
        or source.get("database") != "European Pollen Database"
    ):
        raise ValueError("Native ABBO dataset/site identity differs")
    expected = {row["sample_id"]: row for row in rows}
    result = {}
    all_names: set[str] = set()
    for sample in nested["samples"]:
        if type(sample["sampleid"]) is not int:
            raise ValueError("Native sample integer identity required")
        sample_id = f"neotoma:sample:{sample['sampleid']}"
        if sample_id not in expected or sample_id in result:
            raise ValueError("Unmatched or duplicate native ABBO sample")
        row = expected[sample_id]
        if Decimal(str(sample["depth"])) != Decimal(row["depth_cm"]):
            raise ValueError("Native ABBO sample depth differs")
        # The original Swedish profile admits exactly one calibrated native age
        # per sample. Reconcile that same frozen point with the retained ledger.
        ages = sample["ages"]
        if (
            len(ages) != 1
            or ages[0].get("agetype") != native.CALIBRATED_BP
            or Decimal(str(ages[0]["age"])) != Decimal(row["neotoma_age_cal_bp"])
        ):
            raise ValueError("Native ABBO sample point age differs")
        extracted = native.pollen_counts(sample)
        counts = extracted["counts"]
        all_names.update(counts)
        vector = tuple(counts.get(taxon, 0) for taxon in TAXA)
        if sum(vector) != ledger._count(row["closed_nisp_count"]) or extracted[
            "reported_all_pollen_NISP_sum"
        ] != ledger._count(row["all_nisp_count"], positive=True):
            raise ValueError(
                "Native closed 16-taxon or all-NISP sum differs from source ledger"
            )
        result[sample_id] = vector
    if set(result) != set(expected) or not set(TAXA).issubset(all_names):
        raise ValueError(
            "Native ABBO sample population or declared taxon inventory differs"
        )
    return result


def _predictions(
    payload: dict[str, Any], config: dict[str, Any]
) -> tuple[dict[int, dict[str, tuple[float, ...]]], list[dict[str, Any]]]:
    if (
        config.get("closed_taxa") != list(TAXA)
        or config.get("common_age_bin_ids") != list(BINS)
        or config.get("methods") != list(METHODS)
        or config.get("age_bin_width_cal_bp") != 500
        or payload.get("schema_version")
        != "swedish-direct-pollen-held-out-predictions.v1"
        or payload.get("target_dataset_id") != "19913"
        or payload.get("target_site_id") != "13338"
    ):
        raise ValueError("Frozen prediction support or target declaration differs")
    result: dict[int, dict[str, tuple[float, ...]]] = {b: {} for b in BINS}
    predictions, fits = payload["predictions"], payload["fit_records"]
    if len(predictions) != 16 or len(fits) != 16:
        raise ValueError("Exactly four methods by four bins required")
    for row in predictions:
        method, bin_id = row["candidate_id"], row["bin_id"]
        if (
            method not in METHODS
            or type(bin_id) is not int
            or bin_id not in BINS
            or method in result[bin_id]
            or row["target_dataset_id"] != "19913"
            or row["target_site_id"] != "13338"
            or row["taxon_denominator"] != list(TAXA)
            or row["training_dataset_ids"] != ["53995", "54001"]
            or row["target_outcome_input"]
            != "target count profile was not opened by this prediction process"
            or row["target_coordinate_used"]
            != {"latitude": 63.88333, "longitude": 14.45}
            or set(row["predicted_fractions"]) != set(TAXA)
        ):
            raise ValueError(
                "Frozen target exclusion, taxon axis or training population differs"
            )
        values = [row["predicted_fractions"][taxon] for taxon in TAXA]
        if any(
            type(value) not in (int, float)
            or not math.isfinite(value)
            or not 0 <= value <= 1
            for value in values
        ):
            raise ValueError("Finite frozen binary64 fractions required")
        vector = tuple(float(value) for value in values)
        if not math.isclose(sum(vector), 1.0, rel_tol=0, abs_tol=1e-9):
            raise ValueError("Frozen prediction composition is not closed")
        result[bin_id][method] = vector
    expected = {(b, method) for b in BINS for method in METHODS}
    keys = {(row["bin_id"], row["method"]) for row in fits}
    if keys != expected or any(
        type(row["bin_id"]) is not int
        or row["training_dataset_ids"] != ["53995", "54001"]
        or row["training_site_ids"] != ["28869", "28872"]
        for row in fits
    ):
        raise ValueError("Frozen fit identities or target exclusion differs")
    for row in fits:
        identifiers = (
            ("model_sha256", "prediction_sha256")
            if row["method"] == "clr_rbf_ridge"
            else ("training_manifest_sha256",)
        )
        if any(
            not isinstance(row.get(key), str)
            or len(row[key]) != 64
            or any(c not in "0123456789abcdef" for c in row[key])
            for key in identifiers
        ):
            raise ValueError("Frozen fit/prediction identity missing")
    return {b: {method: result[b][method] for method in METHODS} for b in BINS}, fits


def _fraction(value: Fraction) -> dict[str, Any]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "approximate": float(value),
    }


def _order(
    order: AgeOrderAssessment | None, samples: Sequence[DepthCountSample]
) -> dict[str, Any] | None:
    if order is None:
        return None
    if order.attainable:
        by_id = {row.sample_id: row for row in order.assignments}
        if (
            len(by_id) != len(samples)
            or set(by_id) != {row.sample.sample_id for row in samples}
            or any(by_id[row.sample.sample_id].depth != row.depth for row in samples)
        ):
            raise ValueError("Complete native depth/age witness required")
        return {
            "attainable": True,
            "ages_in_source_order": [
                str(by_id[row.sample.sample_id].native_age) for row in samples
            ],
        }
    refusal = order.refusal
    assert refusal is not None
    return {
        "attainable": False,
        "refusal": {
            "sample_id": refusal.sample_id,
            "depth_cm": str(refusal.depth),
            "minimum_required_age": str(refusal.minimum_required_age),
            "previous_depth_sample_ids": list(refusal.previous_depth_sample_ids),
            "equal_depth_sample_ids": list(refusal.equal_depth_sample_ids),
        },
    }


def derive(support: bytes, raw: bytes, frozen: bytes, config: bytes) -> dict[str, Any]:
    """Reconcile literal source counts once, then score only frozen predictions."""
    rows, samples = _support(support)
    counts = _native_counts(_json(raw), rows)
    predictions, fits = _predictions(_json(frozen), _json(config))
    indices = {row.sample.sample_id: i for i, row in enumerate(samples)}
    bins = []
    native_order = None
    for b in BINS:
        result = ordered_prediction_sensitivity(
            samples,
            AgeBin(str(b), Decimal(b * 500), Decimal((b + 1) * 500)),
            counts,
            predictions[b],
            core_id=CORE,
        )
        if native_order is None:
            native_order = _order(result.native_age_order, samples)
        allocations: dict[str, dict[str, Any]] = {}

        def block(selected: tuple[str, ...]) -> tuple[str, int, int]:
            positions = [indices[sample_id] for sample_id in selected]
            first, stop = min(positions), max(positions) + 1
            if positions != list(range(first, stop)):
                raise ValueError("A contiguous native depth block is required")
            return f"samples[{first}:{stop}]", first, stop

        def endpoint(
            witness: ScoreWitness | None,
            retained_allocations: dict[str, dict[str, Any]] = allocations,
        ) -> dict[str, Any] | None:
            if witness is None:
                return None
            name, first, stop = block(witness.selected_sample_ids)
            allocation = {
                "sample_start_index_inclusive": first,
                "sample_stop_index_exclusive": stop,
                "pooled_taxon_counts": list(witness.pooled_taxon_counts),
                "closed_count_denominator": sum(witness.pooled_taxon_counts),
                "age_order": _order(witness.age_order, samples),
            }
            if (
                name in retained_allocations
                and retained_allocations[name] != allocation
            ):
                raise ValueError("A retained allocation has inconsistent witnesses")
            retained_allocations[name] = allocation
            return {"value": _fraction(witness.value), "allocation": name}

        method_bounds = [
            {
                "method": row.method,
                "lower": endpoint(row.lower),
                "upper": endpoint(row.upper),
            }
            for row in result.method_bounds
        ]
        pairwise = [
            {
                "left_method": row.left_method,
                "right_method": row.right_method,
                "difference": "left MAE minus right MAE on the same allocation",
                "lower": endpoint(row.lower),
                "upper": endpoint(row.upper),
                "negative_attainable": row.negative_attainable,
                "zero_attainable": row.zero_attainable,
                "positive_attainable": row.positive_attainable,
                "ranking_reversal": row.ranking_reversal,
            }
            for row in result.pairwise_bounds
        ]
        winners = [
            {"methods": list(row.methods), "minimum_mae": endpoint(row.witness)}
            for row in result.winner_sets
        ]
        bins.append(
            {
                "bin_id": b,
                "younger_cal_bp_inclusive": b * 500,
                "older_cal_bp_exclusive": (b + 1) * 500,
                "depth_group_count": result.depth_group_count,
                "candidate_block_count": result.candidate_block_count,
                "tested_block_count": result.tested_block_count,
                "feasible_block_count": result.feasible_block_count,
                "scored_block_count": result.scored_block_count,
                "refusal": result.refusal,
                "empty_selection_age_order": _order(
                    result.empty_selection_age_order, samples
                ),
                "zero_closed_count_blocks": [
                    block(selected)[0]
                    for selected in result.zero_closed_count_selections
                ],
                "method_mae_bounds": method_bounds,
                "paired_mae_difference_bounds": pairwise,
                "possible_winners": list(result.possible_winners),
                "winner_set_changes": result.winner_set_changes,
                "unique_winner_changes": result.unique_winner_changes,
                "winner_sets": winners,
                "attaining_allocations": allocations,
            }
        )
    return {
        "schema_version": "abbo-ordered-frozen-prediction-sensitivity.v1",
        "question": "Can feasible age-depth allocations reverse the MAE ranking of frozen direct-pollen predictors?",
        "target_dataset_id": "19913",
        "target_site_id": "13338",
        "taxon_axis": list(TAXA),
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
        "native_age_order": native_order,
        "frozen_fit_identities": fits,
        "bins": bins,
        "zero_semantics": ZERO_RULE,
        "quantity": "Mean absolute fraction error over 16 declared taxa: fixed stored binary64 predictions as exact rationals versus pooled integer counts closed on their selected 16-taxon sum. Existing input composition closure uses absolute 1e-9 admission only, without reclosure. Pairwise differences and best-method sets use one common feasible allocation; exact decisions have no tolerance and approximate displays never decide signs or ties.",
        "assumption": "One nondecreasing native age function of depth; equal depths share one age. Literal closed LegacyAge marginal intervals and native negative ages retained; this conditional model is not source-verified sediment history or a joint age posterior.",
        "limits": [
            "Prior-exposed Swedish development sensitivity; frozen training and predictions remain unchanged. Only target chronology allocation varies; no fitting, new prediction, pseudocount or vegetation validation.",
            "Sharp single-bin bounds and winner sets need not be jointly attainable across the four bins. No whole-study or site-macro ranking change is established.",
            "No calibrated chronology probability, sampling confidence interval, independent ecological accuracy, source permission, human scientific approval or release qualification follows.",
            "No newly qualified age reference epoch or physical core admission follows from treating the retained dataset as one ordered core.",
            "Empty and zero-closed-count selections remain unscored; exact attainable ties differ from an interval merely spanning zero.",
        ],
    }


def _revision(repository: Path) -> str:
    modules = (
        native,
        ledger,
        joint_membership,
        count_fraction,
        domains,
        extrema,
        prediction_sensitivity,
    )
    paths = [Path(module.__file__ or "") for module in modules] + [Path(__file__)]
    if any(
        path.resolve(strict=True) != path
        or not path.is_relative_to(repository / "packages")
        for path in paths
    ):
        raise ValueError(
            "Scientific modules must load from the selected canonical repository"
        )
    relative = [str(path.relative_to(repository)) for path in paths]
    command = ["git", "-C", str(repository)]
    revision = subprocess.check_output(
        [*command, "rev-parse", "HEAD"], text=True, timeout=30
    ).strip()
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
    """Consume one authenticated raw buffer and publish one bounded report."""
    repository = repository.absolute()
    if repository.resolve(strict=True) != repository:
        raise ValueError("A physical canonical repository is required")
    destination = require_absent_artifact_output(repository, output)
    revision = _revision(repository)
    buffers, identities = {}, {}
    for relative, expected in INPUTS.items():
        path = repository / relative
        if (
            not path.is_file()
            or path.resolve(strict=True) != path
            or path.stat().st_size > 32 * 1024**2
        ):
            raise ValueError("Bounded physical scientific input required")
        body = path.read_bytes()
        if hashlib.sha256(body).hexdigest() != expected:
            raise ValueError(f"Scientific input identity differs: {relative}")
        buffers[relative] = body
        identities[str(relative)] = {"sha256": expected, "bytes": len(body)}
    result = derive(
        buffers[ledger.SUPPORT],
        buffers[RAW],
        buffers[PREDICTIONS],
        buffers[ledger.CONFIG],
    )
    result.update(
        source_git_revision=revision, command=sys.orig_argv, input_identities=identities
    )
    body = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    if len(body) > 1024**2:
        raise ValueError("Scientific report exceeds 1 MiB")
    if _revision(repository) != revision:
        raise ValueError("Scientific source changed during execution")
    with destination.open("xb") as stream:
        stream.write(body)
    return result


def main(argv: list[str] | None = None) -> int:
    """Assess fixed predictions only after scientific source inputs are admitted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
