"""Exercise grouped site exclusions and no-target-pollen prediction on synthetic truth."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.analysis.lra_validation import (
    ForwardInputs,
    SiteRecord,
    ValidationRefusal,
    grouped_leave_one_out,
    predict_withheld_site,
    score_vegetation,
)
from bijux_pollenomics.analysis.lra_validation.contracts import manifest_sha256
from bijux_pollenomics.analysis.lra_validation.metrics import hellinger_distance
from bijux_pollenomics.core.geospatial.distance import wgs84_inverse_geodesic
from bijux_pollenomics_lra.api import forward_deposition
from bijux_pollenomics_lra.models.results import ForwardResult

JsonObject = dict[str, object]
_SITES = (
    ("west-shore", 60.0, 12.00, 0.8),
    ("west-meadow", 60.0, 12.01, 0.8),
    ("central-shore", 60.0, 14.00, 0.5),
    ("central-meadow", 60.0, 14.01, 0.5),
    ("east-shore", 60.0, 16.00, 0.2),
    ("east-meadow", 60.0, 16.01, 0.2),
)
_TAXA = ("tree", "grass")
_EXTERNALS = (
    "synthetic-background",
    "synthetic-ppe",
    "synthetic-geometry",
    "synthetic-time",
)


def _records() -> tuple[SiteRecord, ...]:
    return tuple(
        record
        for name, *_ in _SITES
        for record in (
            SiteRecord(f"{name}:pollen", name),
            SiteRecord(f"{name}:alias", f"alternate:{name}", (f"{name}:pollen",)),
        )
    )


def _truth(tree: float) -> dict[str, float]:
    return {"tree": tree, "grass": 1 - tree}


def _pollen(cover: Mapping[str, float]) -> dict[str, float]:
    total = 2 * cover["tree"] + cover["grass"]
    return {"tree": 2 * cover["tree"] / total, "grass": cover["grass"] / total}


class _ForwardCounter:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(
        self,
        local_cover: tuple[float, ...],
        regional_deposition: tuple[float, ...],
        local_k: tuple[tuple[float, ...], ...],
        terrestrial_fraction: tuple[float, ...],
        ppe: tuple[float, ...],
    ) -> ForwardResult:
        self.calls += 1
        return forward_deposition(
            local_cover, regional_deposition, local_k, terrestrial_fraction, ppe
        )


def build_site_leakage_challenge(
    *,
    scoring_truth: Mapping[str, Mapping[str, float]] | None = None,
) -> JsonObject:
    """Rotate every synthetic physical group and retain all 24 control attempts.

    The optional scoring store is used only after predictions are frozen. It
    never supplies training compositions, distances or forward model inputs.
    """
    records = _records()
    folds = grouped_leave_one_out(records)
    group_owner = {
        fold.test_group_ids[0]: fold.test_record_ids[0].split(":")[0] for fold in folds
    }
    coordinates = {
        name: (latitude, longitude) for name, latitude, longitude, _ in _SITES
    }
    truths = {name: _truth(tree) for name, _, _, tree in _SITES}
    distance_identity = wgs84_inverse_geodesic(
        latitude_a=60.0, longitude_a=12.0, latitude_b=60.0, longitude_b=12.01
    )
    cases: list[JsonObject] = []
    engine_source_sha256 = hashlib.sha256(
        Path(forward_deposition.__code__.co_filename).read_bytes()
    ).hexdigest()
    context = ForwardInputs(
        _TAXA,
        (0.0, 0.0),
        ((1.0, 1.0),),
        (1.0,),
        (2.0, 1.0),
        (_EXTERNALS[0],),
        (_EXTERNALS[1],),
        (_EXTERNALS[2],),
        _EXTERNALS[3],
        "disqover-0.9.14-homogeneous-local-forward",
        f"forward-module-sha256:{engine_source_sha256}",
    )
    for fold in folds:
        target_group = fold.test_group_ids[0]
        target_site = group_owner[target_group]
        training_sites = sorted(group_owner[group] for group in fold.train_group_ids)
        base_graph: dict[str, tuple[str, ...]] = {
            **dict.fromkeys(fold.train_record_ids, ()),
            **dict.fromkeys(_EXTERNALS, ()),
        }
        distances = {
            group: wgs84_inverse_geodesic(
                latitude_a=coordinates[target_site][0],
                longitude_a=coordinates[target_site][1],
                latitude_b=coordinates[group_owner[group]][0],
                longitude_b=coordinates[group_owner[group]][1],
            ).distance_km_unrounded
            for group in fold.train_group_ids
        }
        for control in (
            "nearest_site",
            "shuffled_training_sites",
            "heldout_alias_input",
            "derived_target_input",
        ):
            training = {
                group: truths[group_owner[group]] for group in fold.train_group_ids
            }
            assignment = {site: site for site in training_sites}
            if control == "shuffled_training_sites":
                assignment = {
                    site: training_sites[(index + 1) % len(training_sites)]
                    for index, site in enumerate(training_sites)
                }
                training = {
                    group: truths[assignment[group_owner[group]]]
                    for group in fold.train_group_ids
                }
            graph = dict(base_graph)
            input_ids = fold.train_record_ids
            externals: tuple[str, ...] = _EXTERNALS
            if control == "heldout_alias_input":
                input_ids = (*input_ids, f"{target_site}:alias")
                graph[f"{target_site}:alias"] = ()
            elif control == "derived_target_input":
                graph["synthetic-derived-intermediate"] = (f"{target_site}:pollen",)
                graph["synthetic-derived-product"] = ("synthetic-derived-intermediate",)
                graph[f"{target_site}:pollen"] = ()
                input_ids = (*input_ids, "synthetic-derived-product")
                externals = (
                    *externals,
                    "synthetic-derived-product",
                    "synthetic-derived-intermediate",
                )
            counter = _ForwardCounter()
            row: JsonObject = {
                "case_id": f"{target_site}-{control}",
                "target_site_id": target_site,
                "control": control,
                "fold": fold.as_dict(),
                "excluded_target_record_ids": fold.test_record_ids,
                "training_site_assignment": assignment,
                "training_compositions": training,
                "training_input_ids": input_ids,
                "dependency_graph": graph,
                "admitted_synthetic_external_ids": externals,
                "distances_km": distances,
            }
            try:
                prediction = predict_withheld_site(
                    fold,
                    target_group,
                    training,
                    context,
                    counter,
                    spatial_method="nearest_site",
                    training_input_ids=input_ids,
                    dependency_graph=graph,
                    admitted_external_ids=externals,
                    distances_km=distances,
                )
            except ValidationRefusal as error:
                row.update(
                    status="refused",
                    reason_code=error.reason_code,
                    detail=str(error),
                    numerical_calls=counter.calls,
                    contract_status="passed"
                    if control in {"heldout_alias_input", "derived_target_input"}
                    and error.reason_code == "withheld_input_leakage"
                    and counter.calls == 0
                    else "failed",
                )
                cases.append(row)
                continue
            # Independent expected nearest-site value uses only admitted training
            # identities and the predeclared permutation, never target truth.
            nearest_group = min(distances, key=lambda group: (distances[group], group))
            expected_cover = truths[assignment[group_owner[nearest_group]]]
            expected_pollen = _pollen(expected_cover)
            cover = dict(prediction.vegetation_fraction)
            pollen = dict(prediction.pollen_fraction)
            calculation_error = max(
                abs(cover[taxon] - expected_cover[taxon]) for taxon in _TAXA
            )
            pollen_error = max(
                abs(pollen[taxon] - expected_pollen[taxon]) for taxon in _TAXA
            )
            frozen = prediction.prediction_manifest_sha256
            # Target outcomes enter after the immutable prediction has been made.
            truth = (
                truths[target_site]
                if scoring_truth is None
                else scoring_truth[target_site]
            )
            truth_pollen = _pollen(truth)
            vegetation_score = score_vegetation(cover, truth)
            pollen_mae = sum(
                abs(pollen[taxon] - truth_pollen[taxon]) for taxon in _TAXA
            ) / len(_TAXA)
            passed = (
                calculation_error <= 1e-12
                and pollen_error <= 1e-12
                and control in {"nearest_site", "shuffled_training_sites"}
            )
            row.update(
                status="scored",
                contract_status="passed" if passed else "failed",
                numerical_calls=counter.calls,
                prediction_manifest_sha256=frozen,
                prediction_manifest=json.loads(prediction.input_manifest_json),
                prediction_frozen_before_truth_scoring=True,
                predicted_vegetation_fraction=cover,
                predicted_pollen_fraction=pollen,
                independent_expected_vegetation_fraction=expected_cover,
                independent_expected_pollen_fraction=expected_pollen,
                calculation_max_abs_error=calculation_error,
                pollen_calculation_max_abs_error=pollen_error,
                synthetic_truth_fraction=truth,
                synthetic_pollen_truth_fraction=truth_pollen,
                vegetation_score=vegetation_score.as_dict(),
                pollen_mae_fraction=pollen_mae,
                pollen_hellinger=hellinger_distance(pollen, truth_pollen),
            )
            cases.append(row)
    scored = [case for case in cases if case["status"] == "scored"]
    summaries = {}
    for control in ("nearest_site", "shuffled_training_sites"):
        selected = [case for case in scored if case["control"] == control]
        summaries[control] = {
            "sites_scored": len(selected),
            "site_macro_vegetation_mae_fraction": sum(
                cast(float, cast(JsonObject, case["vegetation_score"])["mae_fraction"])
                for case in selected
            )
            / len(selected)
            if selected
            else None,
            "site_macro_pollen_mae_fraction": sum(
                cast(float, case["pollen_mae_fraction"]) for case in selected
            )
            / len(selected)
            if selected
            else None,
            "site_macro_pollen_hellinger": sum(
                cast(float, case["pollen_hellinger"]) for case in selected
            )
            / len(selected)
            if selected
            else None,
        }
    return {
        "schema_version": "pollenomics-synthetic-site-leakage.v1",
        "profile": "grouped-synthetic-withheld-site-challenge",
        "source_kind": "fabricated_coordinates_and_independent_piecewise_constant_site_truth",
        "source_sites": [
            {
                "site_id": name,
                "latitude": lat,
                "longitude": lon,
                "true_vegetation_fraction": truths[name],
            }
            for name, lat, lon, _ in _SITES
        ],
        "source_sha256": manifest_sha256(_SITES),
        "prospective_contract": {
            "eligible_groups": 6,
            "attempts_per_group": 4,
            "requested_attempts": 24,
            "calculation_absolute_tolerance": 1e-12,
            "shuffle": "cyclic_shift_of_only_outer_training_site_compositions",
            "expected_alias_and_derived_refusal": "withheld_input_leakage_before_numerical_call",
            "distances": "unrounded_WGS84_inverse_metres_divided_by_1000",
            "distance_library": distance_identity.distance_library,
            "distance_library_version": distance_identity.distance_library_version,
            "truth_support": "same_two_category_synthetic_site_estimand_at_one_declared_fixture_time",
            "forward_context": context.as_dict(),
        },
        "cases": cases,
        "summaries": summaries,
        "denominators": {
            "requested": 24,
            "attempted": len(cases),
            "predicted": len(scored),
            "scored": len(scored),
            "refused": len(cases) - len(scored),
            "numerical_calls": sum(
                cast(int, case["numerical_calls"]) for case in cases
            ),
            "contract_passed": sum(
                case["contract_status"] == "passed" for case in cases
            ),
            "contract_failed": sum(
                case["contract_status"] == "failed" for case in cases
            ),
        },
        "claims": {
            "synthetic_only": True,
            "real_observations_used": False,
            "empirical_ecological_accuracy": False,
            "reviewed_source_crosswalk": False,
            "predictive_intervals_calibrated": False,
            "synthetic_crosswalk_complete_by_construction": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_site_leakage_challenge()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    counts = cast(dict[str, int], report["denominators"])
    print(json.dumps({"output": str(args.output), **counts}))
    return 0 if counts["contract_passed"] == counts["requested"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
