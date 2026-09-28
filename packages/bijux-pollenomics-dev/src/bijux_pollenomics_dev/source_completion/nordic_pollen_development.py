"""Select observed-pollen transfer models inside held-out-country training sets."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import gzip
import io
import json
from pathlib import Path
from statistics import mean
from typing import Any

from bijux_pollenomics.analysis.lra_validation.baselines import (
    predict_spatial_baseline,
)
from bijux_pollenomics.analysis.lra_validation.contracts import Fold, ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.metrics import (
    hellinger_distance,
    score_pollen,
)
from bijux_pollenomics.analysis.lra_validation.spatial import (
    SiteCoordinate,
    SpatialConfig,
    fit_spatial_model,
    half_count_composition,
)
from bijux_pollenomics.analysis.lra_validation.spatial.configuration import distance_km

from .nordic_direct_pollen import BASELINE_METHODS, COUNTRIES, TAXA, _sha

PUBLISHED = Path("docs/report/regions/nordic/direct-pollen/manifest.json")
QUANTILES = (0.25, 0.50, 0.75)
RIDGES = (0.001, 0.01, 0.1)
SCORE_FIELDS = (
    "outer_country",
    "inner_fold",
    "target_site_id",
    "target_country",
    "bin_id",
    "candidate",
    "status",
    "mae_fraction",
    "hellinger_distance",
    "training_sites",
    "reason",
)


def _coordinate(profile: dict[str, Any]) -> SiteCoordinate:
    return SiteCoordinate(
        latitude=float(profile["coordinate"]["latitude"]),
        longitude=float(profile["coordinate"]["longitude"]),
    )


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(value for value in values if value > 0)
    if not ordered:
        raise ValueError("No positive training-to-training distance")
    position = (len(ordered) - 1) * q
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    share = position - lower
    return ordered[lower] * (1 - share) + ordered[upper] * share


def _candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = [
        {"id": name, "model": name} for name in BASELINE_METHODS
    ]
    candidates.extend(
        {
            "id": f"clr_rbf_q{int(q * 100)}_ridge_{ridge:g}",
            "model": "clr_wgs84_rbf_ridge",
            "training_pairwise_distance_quantile": q,
            "ridge_penalty": ridge,
        }
        for q in QUANTILES
        for ridge in RIDGES
    )
    return candidates


def _folds(profiles: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Distribute whole physical sites across three country-stratified folds."""
    held_out: list[list[dict[str, Any]]] = [[], [], []]
    for country in sorted({profile["country"] for profile in profiles}):
        members = sorted(
            (profile for profile in profiles if profile["country"] == country),
            key=lambda profile: profile["site_id"],
        )
        for index, member in enumerate(members):
            held_out[index % 3].append(member)
    if sum(map(len, held_out)) != len(profiles) or any(not fold for fold in held_out):
        raise ValueError("Development folds do not partition source sites")
    return held_out


def _scored_row(
    country: str,
    fold: int,
    target: dict[str, Any],
    bin_id: str,
    candidate: str,
    prediction: dict[str, float] | None,
    training_sites: int,
    reason: str = "",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "outer_country": country,
        "inner_fold": fold,
        "target_site_id": target["site_id"],
        "target_country": target["country"],
        "bin_id": int(bin_id),
        "candidate": candidate,
        "status": "refused" if prediction is None else "scored",
        "mae_fraction": None,
        "hellinger_distance": None,
        "training_sites": training_sites,
        "reason": reason,
    }
    if prediction is not None:
        counts = target["bins"][bin_id]["counts"]
        if set(counts) != set(TAXA):
            raise ValueError("Nordic target taxon axis changed")
        total = sum(counts.values())
        if total <= 0:
            raise ValueError("Development target has no positive closed pollen count")
        scored = score_pollen(prediction, counts)
        if scored.status != "scored" or scored.mae_fraction is None:
            raise ValueError("Development prediction could not be scored")
        row["mae_fraction"] = scored.mae_fraction
        row["hellinger_distance"] = hellinger_distance(
            prediction, {taxon: count / total for taxon, count in counts.items()}
        )
    return row


def _train_country(
    country: str, profiles: list[dict[str, Any]], candidates: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    eligible = 0
    positive_target_bins = 0
    fit_attempts = 0
    for fold_number, targets in enumerate(_folds(profiles), start=1):
        target_groups = {target["group_id"] for target in targets}
        training = [
            profile for profile in profiles if profile["group_id"] not in target_groups
        ]
        if not training or set(target_groups) & {p["group_id"] for p in training}:
            raise ValueError("A target physical site remains in its training fold")
        all_bins = sorted(
            {bin_id for profile in targets for bin_id in profile["bins"]}, key=int
        )
        for bin_id in all_bins:
            observed = [
                target
                for target in targets
                if bin_id in target["bins"]
                and target["bins"][bin_id]["closed_nisp"] > 0
            ]
            positive_target_bins += len(observed)
            available = [
                profile
                for profile in training
                if bin_id in profile["bins"]
                and profile["bins"][bin_id]["closed_nisp"] > 0
            ]
            if not observed or len(available) < 2:
                continue
            eligible += len(observed)
            train_groups = tuple(profile["group_id"] for profile in available)
            fold = Fold(
                f"{country}:inner:{fold_number}:bin:{bin_id}",
                tuple(profile["record_id"] for profile in available),
                tuple(target["record_id"] for target in observed),
                train_groups,
                tuple(target["group_id"] for target in observed),
            )
            graph = {record_id: () for record_id in fold.train_record_ids}
            coordinates = {
                profile["group_id"]: _coordinate(profile) for profile in available
            }
            compositions = {
                profile["group_id"]: {
                    taxon: count / profile["bins"][bin_id]["closed_nisp"]
                    for taxon, count in profile["bins"][bin_id]["counts"].items()
                }
                for profile in available
            }
            if any(set(value) != set(TAXA) for value in compositions.values()):
                raise ValueError("Nordic training taxon axis changed")
            for candidate in candidates[: len(BASELINE_METHODS)]:
                name = candidate["id"]
                for target in observed:
                    distances = {
                        group_id: distance_km(point, _coordinate(target))
                        for group_id, point in coordinates.items()
                    }
                    prediction = predict_spatial_baseline(
                        fold,
                        compositions,
                        method=name,
                        input_ids=fold.train_record_ids,
                        dependency_graph=graph,
                        distances_km=distances if name != "training_mean" else None,
                        predictor_group_ids=train_groups,
                    )
                    rows.append(
                        _scored_row(
                            country,
                            fold_number,
                            target,
                            bin_id,
                            name,
                            dict(prediction.fractions),
                            len(available),
                        )
                    )
            pairwise = [
                distance_km(coordinates[left], coordinates[right])
                for index, left in enumerate(train_groups)
                for right in train_groups[index + 1 :]
            ]
            for candidate in candidates[len(BASELINE_METHODS) :]:
                name = candidate["id"]
                try:
                    scale = _quantile(
                        pairwise, candidate["training_pairwise_distance_quantile"]
                    )
                    fit_attempts += 1
                    model = fit_spatial_model(
                        fold,
                        {
                            profile["group_id"]: half_count_composition(
                                profile["bins"][bin_id]["counts"]
                            )
                            for profile in available
                        },
                        coordinates,
                        config=SpatialConfig(
                            scale,
                            candidate["ridge_penalty"],
                            f"nordic-development:{country}:{fold_number}:{bin_id}:{name}",
                        ),
                        input_ids=fold.train_record_ids,
                        dependency_graph=graph,
                        predictor_group_ids=train_groups,
                    )
                except ValidationRefusal as exc:
                    rows.extend(
                        _scored_row(
                            country,
                            fold_number,
                            target,
                            bin_id,
                            name,
                            None,
                            len(available),
                            str(exc),
                        )
                        for target in observed
                    )
                    continue
                for target in observed:
                    try:
                        predicted = model.predict(
                            target_group_id=target["group_id"],
                            coordinate=_coordinate(target),
                            support_id=model.config.support_id,
                        )
                        fractions = dict(predicted.fractions)
                        reason = ""
                    except ValidationRefusal as exc:
                        fractions, reason = None, str(exc)
                    rows.append(
                        _scored_row(
                            country,
                            fold_number,
                            target,
                            bin_id,
                            name,
                            fractions,
                            len(available),
                            reason,
                        )
                    )
    if len(rows) != eligible * len(candidates):
        raise ValueError("Development candidate attempt denominator does not close")
    return rows, {
        "outer_country": country,
        "training_site_count": len(profiles),
        "inner_folds": 3,
        "positive_target_site_bins": positive_target_bins,
        "eligible_target_site_bins": eligible,
        "fit_attempts": fit_attempts,
    }


def publish(repository: Path, inputs: Path, output: Path) -> dict[str, Any]:
    """Choose candidates using only the corresponding outer training profiles."""
    repository, inputs = repository.resolve(), inputs.resolve()
    input_manifest_path = inputs / "input-manifest.json"
    input_manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))
    published = json.loads((repository / PUBLISHED).read_text(encoding="utf-8"))
    if input_manifest != published["input_identity"]:
        raise ValueError(
            "Development input identity differs from published Nordic study"
        )
    candidates = _candidates()
    trial_rows: list[dict[str, Any]] = []
    country_summaries: list[dict[str, Any]] = []
    inputs_used: list[dict[str, str]] = [
        {"path": str(PUBLISHED), "sha256": _sha(repository / PUBLISHED)},
        {"path": "input-manifest.json", "sha256": _sha(input_manifest_path)},
    ]
    for country in COUNTRIES:
        path = inputs / "inputs" / f"training-{country}.json"
        profiles = json.loads(path.read_text(encoding="utf-8"))
        if len(profiles) != len({p["site_id"] for p in profiles.values()}) or any(
            p["country"] == country for p in profiles.values()
        ):
            raise ValueError("Outer target country leaked into development training")
        inputs_used.append(
            {"path": f"inputs/training-{country}.json", "sha256": _sha(path)}
        )
        country_rows, country_summary = _train_country(
            country, list(profiles.values()), candidates
        )
        trial_rows.extend(country_rows)
        by_candidate: dict[str, dict[str, Any]] = {}
        for candidate in candidates:
            name = candidate["id"]
            member_rows = [row for row in country_rows if row["candidate"] == name]
            scored = [row for row in member_rows if row["status"] == "scored"]
            site_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in scored:
                site_groups[row["target_site_id"]].append(row)
            by_candidate[name] = {
                "candidate": name,
                "attempted_site_bins": len(member_rows),
                "scored_site_bins": len(scored),
                "scored_sites": len(site_groups),
                "site_macro_mae_fraction": (
                    mean(
                        mean(row["mae_fraction"] for row in group)
                        for group in site_groups.values()
                    )
                    if site_groups
                    else None
                ),
                "site_macro_hellinger": (
                    mean(
                        mean(row["hellinger_distance"] for row in group)
                        for group in site_groups.values()
                    )
                    if site_groups
                    else None
                ),
            }
        full_coverage = [
            result
            for result in by_candidate.values()
            if result["scored_site_bins"]
            == country_summary["eligible_target_site_bins"]
            and result["site_macro_mae_fraction"] is not None
        ]
        selected = (
            min(
                full_coverage,
                key=lambda result: (
                    result["site_macro_mae_fraction"],
                    result["site_macro_hellinger"],
                    result["candidate"],
                ),
            )
            if full_coverage
            else None
        )
        country_summaries.append(
            {
                **country_summary,
                "selection_rule": "complete eligible-bin coverage, then lowest site-macro MAE, Hellinger and candidate-id ties",
                "selected_candidate": selected["candidate"] if selected else None,
                "candidates": list(by_candidate.values()),
            }
        )
    output.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=SCORE_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(trial_rows)
    compressed = gzip.compress(
        buffer.getvalue().encode("utf-8"), compresslevel=9, mtime=0
    )
    scores_path = output / "trial-scores.csv.gz"
    scores_path.write_bytes(compressed)
    report: dict[str, Any] = {
        "schema_version": "nordic-observed-pollen-development.v1",
        "question": "Which declared predictor has lowest site-macro MAE in country-excluded, three-fold, whole-site training-only development?",
        "prior_exposure": "All three outer country outcomes were previously inspected; these are development comparisons, not confirmatory held-out tests.",
        "response": "16-label exact-name Neotoma pollen subcomposition, fixed before this search",
        "candidates": candidates,
        "countries": country_summaries,
        "trial_score_rows": len(trial_rows),
        "trial_scores_sha256": _sha(scores_path),
        "outer_target_outcome_files_read": 0,
        "lra_or_vegetation_validation": False,
        "inputs": inputs_used,
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = publish(args.repository, args.inputs, args.output)
    print(
        json.dumps(
            {
                "trial_score_rows": result["trial_score_rows"],
                "selected": {
                    row["outer_country"]: row["selected_candidate"]
                    for row in result["countries"]
                },
            }
        )
    )


if __name__ == "__main__":
    main()
