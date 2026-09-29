"""Freeze selected Nordic pollen predictions before paired outer-country scoring."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from bijux_pollenomics.analysis.lra_validation.baselines import (
    predict_spatial_baseline,
)
from bijux_pollenomics.analysis.lra_validation.contracts import Fold
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

from .nordic_direct_pollen import (
    COUNTRIES,
    TAXA,
    _nordic_target_outcomes,
    _sha,
)
from .nordic_pollen_development import _quantile

DIRECT = Path("docs/report/regions/nordic/direct-pollen")
DEVELOPMENT = Path("docs/report/regions/nordic/pollen-development/report.json")
SCORE_FIELDS = (
    "country",
    "target_site_id",
    "target_site_name",
    "bin_id",
    "selected_candidate",
    "target_sample_count",
    "target_closed_nisp",
    "target_all_pollen_nisp",
    "selected_mae_fraction",
    "idw_mae_fraction",
    "fixed_rbf_mae_fraction",
    "selected_hellinger",
    "idw_hellinger",
    "fixed_rbf_hellinger",
    "selected_minus_idw_mae",
    "selected_minus_fixed_rbf_mae",
    "prediction_sha256",
)


def _site_macro(rows_by_site: dict[str, list[dict[str, Any]]], field: str) -> float:
    return mean(
        mean(float(row[field]) for row in rows) for rows in rows_by_site.values()
    )


def _coordinate(profile: dict[str, Any]) -> SiteCoordinate:
    return SiteCoordinate(
        latitude=float(profile["coordinate"]["latitude"]),
        longitude=float(profile["coordinate"]["longitude"]),
    )


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def _selection(repository: Path) -> tuple[dict[str, dict[str, Any]], str]:
    path = repository / DEVELOPMENT
    report = json.loads(path.read_text(encoding="utf-8"))
    if report["schema_version"] != "nordic-observed-pollen-development.v1":
        raise ValueError("Nordic development result version changed")
    selected: dict[str, dict[str, Any]] = {}
    for country in report["countries"]:
        code = country["outer_country"]
        chosen = [
            candidate
            for candidate in report["candidates"]
            if candidate["id"] == country["selected_candidate"]
        ]
        if code not in COUNTRIES or len(chosen) != 1:
            raise ValueError("Nordic development selection changed")
        selected[code] = chosen[0]
    if set(selected) != set(COUNTRIES):
        raise ValueError("Nordic development countries changed")
    return selected, _sha(path)


def predict(repository: Path, inputs: Path, output: Path) -> dict[str, Any]:
    """Read no outer pollen outcomes and seal predictions before scoring."""
    repository, inputs, output = (
        repository.resolve(),
        inputs.resolve(),
        output.resolve(),
    )
    if output.exists():
        raise ValueError("Selected-prediction output must be absent before freeze")
    input_path = inputs / "input-manifest.json"
    published = json.loads((repository / DIRECT / "manifest.json").read_text())
    if json.loads(input_path.read_text()) != published["input_identity"]:
        raise ValueError("Nordic prepared source identity changed")
    selected, development_hash = _selection(repository)
    output.mkdir(parents=True)
    prediction_hashes: dict[str, str] = {}
    prepared_hashes: dict[str, dict[str, str]] = {}
    counts_by_country: dict[str, dict[str, int]] = {}
    with (repository / DIRECT / "cohort.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        cohort = list(csv.DictReader(stream))
    if _sha(repository / DIRECT / "cohort.csv") != published["cohort_sha256"]:
        raise ValueError("Published Nordic site cohort changed")
    for country in COUNTRIES:
        training_path = inputs / "inputs" / f"training-{country}.json"
        metadata_path = inputs / "inputs" / f"metadata-{country}.json"
        training = json.loads(training_path.read_text(encoding="utf-8"))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if any(profile["country"] == country for profile in training.values()):
            raise ValueError("Outer target country leaked into training profiles")
        cohort_sites = {
            row["site_id"]: row for row in cohort if row["country"] == country
        }
        target_sites = {site["site_id"]: site for site in metadata["sites"]}
        if set(cohort_sites) != set(target_sites):
            raise ValueError("Prepared target site identities changed")
        for site_id, site in target_sites.items():
            row = cohort_sites[site_id]
            if (
                len(site["candidate_sample_ids"]) != int(row["candidate_samples"])
                or ";".join(site["candidate_bin_ids"]) != row["candidate_age_bins"]
            ):
                raise ValueError("Prepared target site denominator changed")
        candidate = selected[country]
        rows: list[dict[str, Any]] = []
        refusals: list[dict[str, Any]] = []
        candidate_bins = sorted(
            {
                bin_id
                for site in target_sites.values()
                for bin_id in site["candidate_bin_ids"]
            },
            key=int,
        )
        for bin_id in candidate_bins:
            targets = [
                site
                for site in target_sites.values()
                if bin_id in site["candidate_bin_ids"]
            ]
            available = [
                profile
                for profile in training.values()
                if bin_id in profile["bins"]
                and profile["bins"][bin_id]["closed_nisp"] > 0
            ]
            if len(available) < 2:
                refusals.extend(
                    {
                        "target_site_id": target["site_id"],
                        "bin_id": int(bin_id),
                        "reason": "fewer_than_two_training_site_groups_with_positive_closed_counts",
                    }
                    for target in targets
                )
                continue
            train_groups = tuple(profile["group_id"] for profile in available)
            fold = Fold(
                f"selected-country:{country}:bin:{bin_id}",
                tuple(profile["record_id"] for profile in available),
                tuple(f"target:{target['site_id']}:{bin_id}" for target in targets),
                train_groups,
                tuple(target["group_id"] for target in targets),
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
                raise ValueError("Prepared training taxon axis changed")
            model = None
            if candidate["model"] == "clr_wgs84_rbf_ridge":
                pairwise = [
                    distance_km(coordinates[left], coordinates[right])
                    for index, left in enumerate(train_groups)
                    for right in train_groups[index + 1 :]
                ]
                scale = _quantile(
                    pairwise, candidate["training_pairwise_distance_quantile"]
                )
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
                        f"nordic-selected:{country}:{bin_id}",
                    ),
                    input_ids=fold.train_record_ids,
                    dependency_graph=graph,
                    predictor_group_ids=train_groups,
                )
            for target in targets:
                point = _coordinate(target)
                if model is None:
                    distances = {
                        group: distance_km(coordinate, point)
                        for group, coordinate in coordinates.items()
                    }
                    baseline = predict_spatial_baseline(
                        fold,
                        compositions,
                        method=candidate["model"],
                        input_ids=fold.train_record_ids,
                        dependency_graph=graph,
                        distances_km=distances
                        if candidate["model"] != "training_mean"
                        else None,
                        predictor_group_ids=train_groups,
                    )
                    fractions = dict(baseline.fractions)
                else:
                    predicted = model.predict(
                        target_group_id=target["group_id"],
                        coordinate=point,
                        support_id=model.config.support_id,
                    )
                    fractions = dict(predicted.fractions)
                rows.append(
                    {
                        "country": country,
                        "target_site_id": target["site_id"],
                        "target_site_name": target["site_name"],
                        "bin_id": int(bin_id),
                        "candidate": candidate["id"],
                        "prediction_fractions": fractions,
                        "training_site_ids": sorted(
                            profile["site_id"] for profile in available
                        ),
                        "target_pollen_counts_read": False,
                    }
                )
        expected = sum(len(site["candidate_bin_ids"]) for site in target_sites.values())
        if len(rows) + len(refusals) != expected:
            raise ValueError("Selected country prediction denominator does not close")
        prediction_path = output / f"predictions-{country}.json"
        _write_json(
            prediction_path,
            {
                "schema_version": "nordic-selected-pollen-predictions.v1",
                "country": country,
                "selection": candidate,
                "target_outcomes_read": False,
                "predictions": rows,
                "refusals": refusals,
            },
        )
        prediction_hashes[country] = _sha(prediction_path)
        prepared_hashes[country] = {
            "training": _sha(training_path),
            "metadata": _sha(metadata_path),
        }
        counts_by_country[country] = {
            "candidate_site_bins": expected,
            "predicted_site_bins": len(rows),
            "refused_site_bins": len(refusals),
        }
    freeze: dict[str, Any] = {
        "schema_version": "nordic-selected-pollen-freeze.v1",
        "producer_sha256": _sha(Path(__file__).resolve()),
        "selection_report_sha256": development_hash,
        "published_fixed_manifest_sha256": _sha(repository / DIRECT / "manifest.json"),
        "prepared_manifest_sha256": _sha(input_path),
        "prepared_file_sha256": prepared_hashes,
        "prediction_sha256": prediction_hashes,
        "countries": counts_by_country,
        "target_outcomes_read": False,
    }
    _write_json(output / "freeze.json", freeze)
    return freeze


def score(
    repository: Path, inputs: Path, frozen: Path, freeze_sha256: str, output: Path
) -> dict[str, Any]:
    """Open target outcomes only after the caller pins the prediction freeze."""
    repository, inputs, frozen, output = (
        repository.resolve(),
        inputs.resolve(),
        frozen.resolve(),
        output.resolve(),
    )
    if output.exists() or _sha(frozen / "freeze.json") != freeze_sha256:
        raise ValueError("Selected predictions are not frozen at the supplied digest")
    freeze = json.loads((frozen / "freeze.json").read_text(encoding="utf-8"))
    if (
        freeze["schema_version"] != "nordic-selected-pollen-freeze.v1"
        or freeze["target_outcomes_read"] is not False
        or freeze["producer_sha256"] != _sha(Path(__file__).resolve())
        or freeze["selection_report_sha256"] != _sha(repository / DEVELOPMENT)
        or freeze["published_fixed_manifest_sha256"]
        != _sha(repository / DIRECT / "manifest.json")
        or freeze["prepared_manifest_sha256"] != _sha(inputs / "input-manifest.json")
    ):
        raise ValueError("Selected prediction freeze dependencies changed")
    published = json.loads((repository / DIRECT / "manifest.json").read_text())
    fixed_scores_path = repository / DIRECT / "scores.csv"
    if _sha(fixed_scores_path) != published["scores_sha256"]:
        raise ValueError("Published fixed score identity changed")
    with fixed_scores_path.open(newline="", encoding="utf-8") as stream:
        fixed_rows = list(csv.DictReader(stream))
    fixed = {
        (row["country"], row["target_site_id"], int(row["bin_id"]), row["method"]): row
        for row in fixed_rows
    }
    if len(fixed) != len(fixed_rows):
        raise ValueError("Published fixed score keys are not unique")
    output.mkdir(parents=True)
    score_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for country in COUNTRIES:
        prediction_path = frozen / f"predictions-{country}.json"
        if _sha(prediction_path) != freeze["prediction_sha256"][country]:
            raise ValueError("Selected prediction bytes changed after freeze")
        for kind in ("training", "metadata"):
            path = inputs / "inputs" / f"{kind}-{country}.json"
            if _sha(path) != freeze["prepared_file_sha256"][country][kind]:
                raise ValueError("Prepared prediction input changed after freeze")
    for country in COUNTRIES:
        prediction_path = frozen / f"predictions-{country}.json"
        payload = json.loads(prediction_path.read_text(encoding="utf-8"))
        if (
            payload["country"] != country
            or payload["target_outcomes_read"] is not False
        ):
            raise ValueError("Selected prediction source role changed")
        metadata = json.loads(
            (inputs / "inputs" / f"metadata-{country}.json").read_text(encoding="utf-8")
        )
        outcomes = _nordic_target_outcomes(
            repository / "data/neotoma/relational", country, metadata
        )["sites"]
        candidates = {
            (site["site_id"], int(bin_id))
            for site in metadata["sites"]
            for bin_id in site["candidate_bin_ids"]
        }
        positive = {
            (key.rsplit(":", 1)[0], int(key.rsplit(":", 1)[1]))
            for key, cell in outcomes.items()
            if cell["closed_nisp"] > 0
        }
        predicted_keys: set[tuple[str, int]] = set()
        country_rows: list[dict[str, Any]] = []
        for prediction in payload["predictions"]:
            site_id, bin_id = prediction["target_site_id"], prediction["bin_id"]
            key = (site_id, bin_id)
            if key in predicted_keys or key not in candidates:
                raise ValueError(
                    "Selected prediction target is duplicate or outside cohort"
                )
            predicted_keys.add(key)
            if key not in positive:
                continue
            observed = outcomes[f"{site_id}:{bin_id}"]
            fractions = prediction["prediction_fractions"]
            if set(fractions) != set(TAXA):
                raise ValueError("Selected prediction taxon axis changed")
            selected_score = score_pollen(fractions, observed["counts"])
            if selected_score.status != "scored" or selected_score.mae_fraction is None:
                raise ValueError("Selected prediction cannot be scored")
            normalized = {
                taxon: count / observed["closed_nisp"]
                for taxon, count in observed["counts"].items()
            }
            fixed_pair = {}
            for method in ("inverse_distance_squared", "clr_rbf_ridge"):
                row = fixed.get((country, site_id, bin_id, method))
                if row is None or row["status"] != "scored":
                    raise ValueError("Selected prediction lacks matched fixed score")
                if (
                    int(row["target_closed_nisp"]) != observed["closed_nisp"]
                    or int(row["target_all_pollen_nisp"]) != observed["all_pollen_nisp"]
                    or row["training_site_ids"]
                    != ";".join(prediction["training_site_ids"])
                ):
                    raise ValueError("Selected and fixed comparison support differ")
                fixed_pair[method] = row
            score_row = {
                "country": country,
                "target_site_id": site_id,
                "target_site_name": prediction["target_site_name"],
                "bin_id": bin_id,
                "selected_candidate": prediction["candidate"],
                "target_sample_count": len(set(observed["sample_ids"])),
                "target_closed_nisp": observed["closed_nisp"],
                "target_all_pollen_nisp": observed["all_pollen_nisp"],
                "selected_mae_fraction": selected_score.mae_fraction,
                "idw_mae_fraction": float(
                    fixed_pair["inverse_distance_squared"]["mae_fraction"]
                ),
                "fixed_rbf_mae_fraction": float(
                    fixed_pair["clr_rbf_ridge"]["mae_fraction"]
                ),
                "selected_hellinger": hellinger_distance(fractions, normalized),
                "idw_hellinger": float(
                    fixed_pair["inverse_distance_squared"]["hellinger_distance"]
                ),
                "fixed_rbf_hellinger": float(
                    fixed_pair["clr_rbf_ridge"]["hellinger_distance"]
                ),
                "selected_minus_idw_mae": selected_score.mae_fraction
                - float(fixed_pair["inverse_distance_squared"]["mae_fraction"]),
                "selected_minus_fixed_rbf_mae": selected_score.mae_fraction
                - float(fixed_pair["clr_rbf_ridge"]["mae_fraction"]),
                "prediction_sha256": freeze["prediction_sha256"][country],
            }
            country_rows.append(score_row)
            score_rows.append(score_row)
        if len(predicted_keys) != freeze["countries"][country]["predicted_site_bins"]:
            raise ValueError("Frozen country prediction denominator changed")
        refused_keys = {
            (row["target_site_id"], row["bin_id"]) for row in payload["refusals"]
        }
        if (
            len(refused_keys) != len(payload["refusals"])
            or predicted_keys & refused_keys
            or predicted_keys | refused_keys != candidates
            or len(refused_keys) != freeze["countries"][country]["refused_site_bins"]
        ):
            raise ValueError("Frozen country prediction/refusal support changed")
        by_site: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in country_rows:
            by_site[row["target_site_id"]].append(row)
        if not by_site:
            raise ValueError("Selected country has no scored sites")

        summaries.append(
            {
                "country": country,
                "selected_candidate": payload["selection"]["id"],
                "candidate_site_bins": len(candidates),
                "positive_closed_site_bins": len(positive),
                "predicted_site_bins": len(predicted_keys),
                "scored_site_bins": len(country_rows),
                "scored_sites": len(by_site),
                "refused_site_bins": len(candidates) - len(country_rows),
                "site_macro_selected_mae": _site_macro(
                    by_site, "selected_mae_fraction"
                ),
                "site_macro_idw_mae": _site_macro(by_site, "idw_mae_fraction"),
                "site_macro_fixed_rbf_mae": _site_macro(
                    by_site, "fixed_rbf_mae_fraction"
                ),
                "site_macro_selected_minus_idw_mae": _site_macro(
                    by_site, "selected_minus_idw_mae"
                ),
                "site_macro_selected_minus_fixed_rbf_mae": _site_macro(
                    by_site, "selected_minus_fixed_rbf_mae"
                ),
                "site_macro_selected_hellinger": _site_macro(
                    by_site, "selected_hellinger"
                ),
                "site_macro_idw_hellinger": _site_macro(by_site, "idw_hellinger"),
                "site_macro_fixed_rbf_hellinger": _site_macro(
                    by_site, "fixed_rbf_hellinger"
                ),
            }
        )
    scores_path = output / "paired-scores.csv"
    with scores_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=SCORE_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(score_rows)
    report: dict[str, Any] = {
        "schema_version": "nordic-selected-pollen-transfer.v1",
        "prior_exposure": "Country outcomes were inspected before this protocol; paired country results are development evidence, not independent confirmation.",
        "response": "exact 16-label observed-pollen subcomposition",
        "freeze_sha256": freeze_sha256,
        "prediction_sha256": freeze["prediction_sha256"],
        "paired_scores_sha256": _sha(scores_path),
        "countries": summaries,
        "lra_or_vegetation_validation": False,
    }
    _write_json(output / "report.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("predict", "score"):
        sub = commands.add_parser(name)
        sub.add_argument("--repository", type=Path, required=True)
        sub.add_argument("--inputs", type=Path, required=True)
        sub.add_argument("--output", type=Path, required=True)
        if name == "score":
            sub.add_argument("--frozen", type=Path, required=True)
            sub.add_argument("--freeze-sha256", required=True)
    args = parser.parse_args()
    if args.command == "predict":
        freeze = predict(args.repository, args.inputs, args.output)
        print(
            json.dumps(
                {
                    "prediction_sha256": freeze["prediction_sha256"],
                    "freeze_sha256": _sha(args.output / "freeze.json"),
                }
            )
        )
    else:
        report = score(
            args.repository, args.inputs, args.frozen, args.freeze_sha256, args.output
        )
        print(
            json.dumps(
                {
                    "countries": report["countries"],
                    "freeze_sha256": report["freeze_sha256"],
                }
            )
        )


if __name__ == "__main__":
    main()
