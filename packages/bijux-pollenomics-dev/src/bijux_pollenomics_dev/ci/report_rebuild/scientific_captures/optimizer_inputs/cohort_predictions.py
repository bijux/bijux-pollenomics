"""Admit the complete cohort freeze before decoding new scoring observations."""

from __future__ import annotations

from typing import Any

from bijux_pollenomics.analysis.lra_validation.experiments.inputs import SAMPLE_FIELDS

from .withheld_fold import _canonical_sha, _decode, _same_pin
from .withheld_pollen import METHODS, _object, _require, validate_pollen_scores


def validate_frozen(
    report: dict[str, Any],
    frozen: dict[str, Any],
    access: list[dict[str, Any]],
    pins: dict[str, dict[str, Any]],
    pool_result: dict[str, Any],
    experiment: dict[str, Any],
) -> dict[str, Any]:
    """Validate every slot, ancestry, refusal, geometry identity and freeze handoff."""
    folds = pool_result["folds"]
    pool = pool_result["pool"]
    logical = pool_result["logical"]
    _require(
        frozen["profile"] == report["profile"]
        and _same_pin(frozen["training"], pins["training"])
        and _same_pin(report["prediction_freeze"], pins["prediction_freeze"]),
        "cohort freeze or training content identity differs",
    )
    _require(
        frozen["folds"] == [folds[key] for key in sorted(folds)],
        "fifteen original folds differ",
    )
    slots = frozen["slots"]
    _require(
        len(slots) == 45
        and {(row["fold_id"], row["baseline"]) for row in slots}
        == {(fold, method) for fold in folds for method in METHODS},
        "complete45-slot inventory required before scoring",
    )
    sites = {row["record_id"]: row for row in experiment["sites"]}
    failures = []
    successful = {}
    for fold_id, fold in sorted(folds.items()):
        rows = [row for row in logical if row["fold_id"] == fold_id]
        target = fold["test_record_ids"][0]
        missing = [
            {"request_sha256": row["request_sha256"], "ring_index": ring}
            for row in rows
            for ring, choice in enumerate(pool[row["request_sha256"]]["selections"])
            if choice is None
        ]
        own = [row for row in slots if row["fold_id"] == fold_id]
        _require(
            len(own) == 3 and all(row["record_id"] == target for row in own),
            "three exact own-target slots required",
        )
        if missing:
            failures.append(
                {
                    "fold_id": fold_id,
                    "reason": "training_ring_has_no_accepted_fixed_start",
                    "missing": missing,
                }
            )
            _require(
                all(
                    row
                    == {
                        "fold_id": fold_id,
                        "record_id": target,
                        "baseline": row["baseline"],
                        "status": "refused",
                        "reason": "training_ring_has_no_accepted_fixed_start",
                    }
                    for row in own
                ),
                "refused fold supplied prediction or lost refusal",
            )
            continue
        _require(
            all(row["status"] == "predicted" for row in own),
            "complete training fold lost its predictions",
        )
        anchor = rows[0]["regional_anchor_record_id"]
        groups = pool_result["groups"]
        predictor_groups = sorted(groups[row["local_record_id"]] for row in rows)
        regional = pool[rows[0]["request_sha256"]]["regional_cover"]
        _require(
            all(
                pool[row["request_sha256"]]["regional_cover"] == regional
                for row in rows
            ),
            "per-fold raw regional background differs",
        )
        for row in own:
            prediction = row["prediction"]
            geometry = row["geometry"]
            manifest = _object(prediction["prediction_manifest"])
            _require(
                prediction["fold_id"] == fold_id
                and prediction["record_id"] == target
                and prediction["baseline"] == row["baseline"]
                and prediction["prediction_manifest_sha256"]
                == _canonical_sha(manifest),
                "saved prediction identity or manifest differs",
            )
            _require(
                manifest["schema_version"] == "lra-heldout-prediction.v1"
                and manifest["fold"] == fold
                and manifest["target_group_id"] == fold["test_group_ids"][0]
                and manifest["pollen_fraction"] == prediction["pollen_fraction"]
                and manifest["vegetation_fraction"] == prediction["vegetation_fraction"]
                and manifest["spatial_method"] == row["baseline"],
                "prediction content differs from its manifest",
            )
            closure = manifest["allowed_input_closure"]
            lineage = manifest["input_lineage"]
            forbidden = {target, *fold["test_group_ids"]}
            _require(
                type(closure) is list
                and len(closure) == len(set(closure))
                and not set(closure) & forbidden
                and set(fold["train_record_ids"]).issubset(closure)
                and set(lineage) == set(closure)
                and all(
                    set(deps).issubset(closure) and not set(deps) & forbidden
                    for deps in lineage.values()
                ),
                "withheld ancestry entered prediction dependency closure",
            )
            _require(
                manifest["experiment"] == "all_target_pollen_withheld"
                and manifest["uncertainty_status"]
                == "deterministic_point_prediction_no_predictive_intervals"
                and manifest["scientific_acceptance"] == "not_evaluated_by_prediction"
                and manifest["predictor_group_ids"] == predictor_groups,
                "prediction scope or13 predictor groups differs",
            )
            _require(
                geometry["support_profile"] == experiment["support_profile"]
                and geometry["local_support_radius_m"]
                == experiment["local_support_radius_m"]
                and geometry["outer_fold"] == fold
                and geometry["regional_anchor_record_id"] == anchor
                and geometry["regional_value_source_record_ids"] == [anchor]
                and list(geometry["regional_identity_source_record_ids"])
                == fold["train_record_ids"]
                and geometry["regional_identity_policy"]
                == "conservative_all_training_fit_receipts"
                and sorted(geometry["predictor_group_ids"]) == predictor_groups
                and geometry["regional_cover"] == regional
                and geometry["target_geometry_sha256"]
                == sites[target]["geometry"]["sha256"],
                "original per-fold geometry or source handoff differs",
            )
        successful[fold_id] = own
    _require(
        report["failures"] == failures
        and report["refused_folds"] == len(failures)
        and report["predicted_folds"] == len(successful)
        and len(successful) + len(failures) == 15,
        "fold refusal or prediction denominators differ",
    )
    _require(
        len(access) == len(successful)
        and [row["fold_id"] for row in access] == sorted(successful),
        "one scoring access per complete fold required",
    )
    for event in access:
        fold = folds[event["fold_id"]]
        _require(
            event["record_id"] == fold["test_record_ids"][0]
            and _same_pin(event["prediction_freeze"], pins["prediction_freeze"])
            and event["ordering"]
            == "complete45_slot_freeze_reopened_before_new_cohort_scoring",
            "scoring access is not bound to complete45-slot freeze",
        )
    _require(
        len(report["scores"]) == len(successful) * 3
        and {(row["fold_id"], row["baseline"]) for row in report["scores"]}
        == {(fold, method) for fold in successful for method in METHODS},
        "score population differs from frozen complete folds",
    )
    return successful


def validate_scores(
    successful: dict[str, Any],
    report: dict[str, Any],
    experiment: dict[str, Any],
    inputs: dict[str, bytes],
) -> list[dict[str, Any]]:
    """Decode scoring labels only after all45 slots and every access pass admission."""
    sites = {row["record_id"]: row for row in experiment["sites"]}
    results = []
    for fold_id, slots in successful.items():
        target = slots[0]["record_id"]
        site = sites[target]
        outcome = _object(_decode(inputs[site["raw"]["path"]]))
        geometry = _object(_decode(inputs[site["geometry"]["path"]]))
        sample = _object(outcome["sample"])
        metadata = _object(geometry["sample_metadata"])
        _require(
            set(outcome) == {"data_kind", "taxa", "sample"}
            and outcome["data_kind"] == "source_observations"
            and set(sample) == SAMPLE_FIELDS | {"counts"}
            and all(sample.get(key) == metadata[key] for key in SAMPLE_FIELDS)
            and sample["site_id"] == site["site_id"],
            "exact sample, chronology and support source identity differs",
        )
        taxa = outcome["taxa"]
        counts = sample["counts"]
        _require(
            taxa == experiment["request_template"]["taxa"]
            and len(taxa) == len(set(taxa)) == len(counts) == 30
            and all(type(value) is int and value >= 0 for value in counts)
            and all(row["prediction"]["bin_id"] == sample["bin_id"] for row in slots),
            "source scoring axis or integer-count support differs",
        )
        predictions = [row["prediction"] for row in slots]
        scored = [row for row in report["scores"] if row["fold_id"] == fold_id]
        _require(
            all(row["record_id"] == target for row in scored),
            "score belongs to another held site",
        )
        result = validate_pollen_scores(
            predictions, scored, dict(zip(taxa, counts, strict=True)), target=target
        )
        results.append({"fold_id": fold_id, "record_id": target, **result})
    return results
